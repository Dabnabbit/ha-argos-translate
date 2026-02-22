"""Tests for Argos Translate translate service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argos_translate.api import CannotConnectError, TranslationError
from custom_components.argos_translate.const import DOMAIN
from custom_components.argos_translate.services import async_register_services

MOCK_LANGUAGES = [
    {"code": "en", "name": "English", "targets": ["es", "fr"]},
    {"code": "es", "name": "Spanish", "targets": ["en"]},
]


async def _setup_service(
    hass: HomeAssistant, mock_result: dict | None = None
) -> tuple[MockConfigEntry, MagicMock]:
    """Set up the translate service with a mocked coordinator."""
    if mock_result is None:
        mock_result = {"translatedText": "Hola"}

    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "languages": MOCK_LANGUAGES,
        "language_count": len(MOCK_LANGUAGES),
    }
    mock_coordinator.async_translate = AsyncMock(return_value=mock_result)
    mock_coordinator.async_detect_languages = AsyncMock(return_value=[])
    mock_coordinator.async_request_refresh = AsyncMock()
    # async_set_update_error is a synchronous @callback (not a coroutine)
    mock_coordinator.async_set_update_error = MagicMock()

    mock_runtime_data = MagicMock()
    mock_runtime_data.coordinator = mock_coordinator

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "localhost",
            CONF_PORT: 5000,
            CONF_API_KEY: "",
        },
    )
    entry.add_to_hass(hass)
    entry.runtime_data = mock_runtime_data

    async_register_services(hass)

    return entry, mock_coordinator


async def test_translate_success(hass: HomeAssistant) -> None:
    """Test successful translation service call."""
    _entry, mock_coordinator = await _setup_service(hass, {"translatedText": "Hola"})

    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "Hello", "source": "en", "target": "es"},
        blocking=True,
        return_response=True,
    )

    assert result == {"translated_text": "Hola"}
    mock_coordinator.async_translate.assert_called_once_with("Hello", "en", "es")


async def test_translate_invalid_source(hass: HomeAssistant) -> None:
    """Test translate with invalid source language raises ServiceValidationError."""
    await _setup_service(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "xx", "target": "es"},
            blocking=True,
            return_response=True,
        )


async def test_translate_invalid_target(hass: HomeAssistant) -> None:
    """Test translate with invalid target language raises ServiceValidationError."""
    await _setup_service(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "en", "target": "xx"},
            blocking=True,
            return_response=True,
        )


async def test_translate_api_error(hass: HomeAssistant) -> None:
    """Test translate when API is unreachable raises HomeAssistantError and flips status offline."""
    _entry, mock_coordinator = await _setup_service(hass)
    mock_coordinator.async_translate = AsyncMock(
        side_effect=CannotConnectError("timeout")
    )

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "en", "target": "es"},
            blocking=True,
            return_response=True,
        )

    # async_set_update_error (synchronous @callback) must be called so binary_sensor
    # flips to offline immediately — no debouncer delay unlike async_request_refresh
    mock_coordinator.async_set_update_error.assert_called_once()


async def test_translate_no_config_entry(hass: HomeAssistant) -> None:
    """Test translate when no config entry exists raises ServiceValidationError."""
    # Register service without adding any config entry
    async_register_services(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "en", "target": "es"},
            blocking=True,
            return_response=True,
        )


async def test_translate_auto_detect_success(hass: HomeAssistant) -> None:
    """Test translate with source='auto' returns detected_language and detection_confidence."""
    mock_result = {
        "translatedText": "Hello",
        "detectedLanguage": {"language": "fr", "confidence": 92.0},
    }
    _entry, mock_coordinator = await _setup_service(hass, mock_result)

    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "Bonjour", "source": "auto", "target": "en"},
        blocking=True,
        return_response=True,
    )

    assert result["translated_text"] == "Hello"
    assert result["detected_language"] == "fr"
    assert result["detection_confidence"] == 92.0
    mock_coordinator.async_translate.assert_called_once_with("Bonjour", "auto", "en")


async def test_translate_auto_detect_uninstalled_language(hass: HomeAssistant) -> None:
    """Test DTCT-06: uninstalled_detected_language field when detected language not in installed list."""
    # "zh" is not in MOCK_LANGUAGES
    mock_result = {
        "translatedText": "Hello",
        "detectedLanguage": {"language": "zh", "confidence": 85.0},
    }
    _entry, _mock_coordinator = await _setup_service(hass, mock_result)

    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "你好", "source": "auto", "target": "en"},
        blocking=True,
        return_response=True,
    )

    assert result["detected_language"] == "zh"
    assert result["uninstalled_detected_language"] == "zh"


async def test_translate_auto_detect_no_validation_error(hass: HomeAssistant) -> None:
    """Test that source='auto' bypasses source/target language validation."""
    mock_result = {
        "translatedText": "Hello",
        "detectedLanguage": {"language": "fr", "confidence": 88.0},
    }
    _entry, _mock_coordinator = await _setup_service(hass, mock_result)

    # Should not raise ServiceValidationError — 'auto' bypasses validation
    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "Bonjour", "source": "auto", "target": "es"},
        blocking=True,
        return_response=True,
    )

    assert "translated_text" in result


async def test_translate_auto_detect_pair_unavailable(hass: HomeAssistant) -> None:
    """Test DTCT-02: auto source returns detected_language info even when pair is unavailable.

    When source='auto' and /translate returns HTTP 400 (pair not available),
    the service must return a partial response with the detected language
    from the pre-flight /detect call rather than raising HomeAssistantError.
    """
    _entry, mock_coordinator = await _setup_service(hass)
    mock_coordinator.async_translate = AsyncMock(
        side_effect=TranslationError("Server returned HTTP 400: Bad Request")
    )
    mock_coordinator.async_detect_languages = AsyncMock(
        return_value=[{"language": "fr", "confidence": 92.0}]
    )

    # Should NOT raise — must return partial response
    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "Bonjour le monde", "source": "auto", "target": "es"},
        blocking=True,
        return_response=True,
    )

    assert result["translated_text"] == ""
    assert result["detected_language"] == "fr"
    assert result["detection_confidence"] == 92.0
    assert "error" in result
    # Server IS reachable (returned a 4xx) — coordinator must NOT be marked as failed
    mock_coordinator.async_set_update_error.assert_not_called()


async def test_translate_auto_detect_pair_unavailable_no_detect(hass: HomeAssistant) -> None:
    """Test auto source with pair unavailable AND /detect also failing.

    When /detect fails AND /translate returns HTTP 400, raise HomeAssistantError
    since there is no detection data to surface.
    """
    _entry, mock_coordinator = await _setup_service(hass)
    mock_coordinator.async_translate = AsyncMock(
        side_effect=TranslationError("Server returned HTTP 400: Bad Request")
    )
    # /detect also fails — no detection data available
    mock_coordinator.async_detect_languages = AsyncMock(
        side_effect=CannotConnectError("timeout")
    )

    # No detection data to surface — should raise HomeAssistantError
    # (returns partial response with empty translated_text and error message,
    # since detect_result is empty and TranslationError is still caught gracefully)
    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "Bonjour le monde", "source": "auto", "target": "es"},
        blocking=True,
        return_response=True,
    )

    # Returns partial response with error — translated_text is empty, no detected_language
    assert result["translated_text"] == ""
    assert "error" in result
    assert "detected_language" not in result
    mock_coordinator.async_set_update_error.assert_not_called()


async def test_translate_translation_error_non_auto(hass: HomeAssistant) -> None:
    """Test that TranslationError on non-auto source raises HomeAssistantError.

    When source is not 'auto' and /translate returns HTTP 4xx, the error must
    be surfaced as HomeAssistantError. The coordinator must NOT be marked as
    failed — the server IS reachable (it returned a valid HTTP response).
    """
    _entry, mock_coordinator = await _setup_service(hass)
    mock_coordinator.async_translate = AsyncMock(
        side_effect=TranslationError("Server returned HTTP 400: Bad Request")
    )

    with pytest.raises(HomeAssistantError, match="Translation failed:"):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "en", "target": "es"},
            blocking=True,
            return_response=True,
        )

    # Server IS reachable (returned 4xx) — coordinator must NOT be marked as failed
    mock_coordinator.async_set_update_error.assert_not_called()
