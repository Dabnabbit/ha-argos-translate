"""Service handlers for the Argos Translate integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import CannotConnectError, TranslationError
from .const import ATTR_SOURCE, ATTR_TARGET, ATTR_TEXT, DOMAIN, SERVICE_DETECT, SERVICE_TRANSLATE

_LOGGER = logging.getLogger(__name__)

AUTO_SOURCE = "auto"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TEXT): cv.string,
        vol.Required(ATTR_SOURCE): cv.string,
        vol.Required(ATTR_TARGET): cv.string,
    }
)

DETECT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TEXT): cv.string,
    }
)


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register integration service actions for Argos Translate."""

    async def _async_handle_translate(call: ServiceCall) -> ServiceResponse:
        """Handle the translate service call."""
        text: str = call.data[ATTR_TEXT]
        source: str = call.data[ATTR_SOURCE]
        target: str = call.data[ATTR_TARGET]

        # Look up coordinator from first config entry
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_config_entry",
            )

        entry = entries[0]
        coordinator = entry.runtime_data.coordinator

        # Validate language pair against coordinator data
        languages = coordinator.data.get("languages", []) if coordinator.data else []

        if source != AUTO_SOURCE:
            source_lang = None
            for lang in languages:
                if lang["code"] == source:
                    source_lang = lang
                    break

            if source_lang is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_source",
                    translation_placeholders={"source": source},
                )

            if target not in source_lang.get("targets", []):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_target",
                    translation_placeholders={"source": source, "target": target},
                )

        # Call translation API
        if source == AUTO_SOURCE:
            # Detect-first: call /detect before /translate so we can surface the
            # detected language even when the translation pair is unavailable (HTTP 400).
            detect_result: list = []
            try:
                detect_result = await coordinator.async_detect_languages(text)
            except (CannotConnectError, TranslationError):
                pass  # Best-effort — if /detect fails, still attempt /translate

            try:
                result = await coordinator.async_translate(text, source, target)
            except TranslationError as err:
                # Server returned HTTP 4xx (e.g., pair not available).
                # Server IS reachable — do NOT mark coordinator as failed.
                # Surface the detection result from the pre-flight /detect call
                # instead of raising, so the card can show what was detected.
                response: dict = {"translated_text": "", "error": str(err)}
                if detect_result:
                    top = next(
                        (d for d in detect_result if d.get("confidence", 0) >= 50.0),
                        None,
                    )
                    if top:
                        detected_code = top["language"]
                        response["detected_language"] = detected_code
                        response["detection_confidence"] = top["confidence"]

                        # Compose a descriptive error naming the detected language
                        # and the unsupported pair instead of a raw HTTP error.
                        detected_name = detected_code
                        target_name = target
                        for lang in languages:
                            if lang["code"] == detected_code:
                                detected_name = lang.get("name", detected_code)
                            if lang["code"] == target:
                                target_name = lang.get("name", target)

                        response["error"] = (
                            f"Detected {detected_name} but {detected_name} \u2192"
                            f" {target_name} translation pair is not available."
                        )

                        # Check if detected language is installed (DTCT-06)
                        installed_codes = [lang["code"] for lang in languages]
                        if detected_code not in installed_codes:
                            response["uninstalled_detected_language"] = detected_code

                return response
            except CannotConnectError as err:
                # True connection failure — server unreachable.
                # Flip coordinator to error state immediately.
                coordinator.async_set_update_error(err)
                raise HomeAssistantError(
                    f"Translation failed: {err}"
                ) from err
        else:
            # Non-auto source — validate pair and translate directly.
            try:
                result = await coordinator.async_translate(text, source, target)
            except CannotConnectError as err:
                # Immediately flip coordinator to error state so binary_sensor goes
                # offline without waiting for the 5-min poll cycle.
                coordinator.async_set_update_error(err)
                raise HomeAssistantError(
                    f"Translation failed: {err}"
                ) from err
            except TranslationError as err:
                # HTTP 4xx from server — server IS reachable, do NOT mark coordinator failed.
                raise HomeAssistantError(
                    f"Translation failed: {err}"
                ) from err

        response = {"translated_text": result["translatedText"]}

        if "detectedLanguage" in result:
            dl = result["detectedLanguage"]
            detected_code = dl.get("language")
            detected_confidence = dl.get("confidence")
            response["detected_language"] = detected_code
            response["detection_confidence"] = detected_confidence

            # Check if detected language is installed (DTCT-06)
            if detected_code:
                installed_codes = [lang["code"] for lang in languages]
                if detected_code not in installed_codes:
                    response["uninstalled_detected_language"] = detected_code

        return response

    hass.services.async_register(
        DOMAIN,
        SERVICE_TRANSLATE,
        _async_handle_translate,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    async def _async_handle_detect(call: ServiceCall) -> ServiceResponse:
        """Handle the detect service call — returns language detection candidates."""
        text: str = call.data[ATTR_TEXT]

        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_config_entry",
            )

        entry = entries[0]
        coordinator = entry.runtime_data.coordinator

        try:
            candidates = await coordinator.async_detect_languages(text)
        except CannotConnectError as err:
            # Immediately flip coordinator to error state so binary_sensor goes
            # offline without waiting for the 5-min poll cycle. async_set_update_error
            # is a synchronous @callback — no await needed, no debouncer delay.
            coordinator.async_set_update_error(err)
            raise HomeAssistantError(
                f"Language detection failed: {err}"
            ) from err
        except TranslationError as err:
            # HTTP 4xx from server — server IS reachable, do NOT mark coordinator failed.
            raise HomeAssistantError(
                f"Language detection failed: {err}"
            ) from err

        return {"detections": candidates}

    hass.services.async_register(
        DOMAIN,
        SERVICE_DETECT,
        _async_handle_detect,
        schema=DETECT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
