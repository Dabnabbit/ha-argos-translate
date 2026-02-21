---
phase: 02-translation-service-card
status: passed
verified: 2026-02-20
---

# Phase 2: Translation Service + Card - Verification

**Phase Goal:** Users can translate text via service call and Lovelace card
**Status:** PASSED

## Requirement Coverage

| ID | Description | Status | Evidence |
|----|-------------|--------|----------|
| SRVC-01 | Service accepts text, source, target | PASSED | services.py: SERVICE_SCHEMA with ATTR_TEXT, ATTR_SOURCE, ATTR_TARGET |
| SRVC-02 | Service returns {translated_text} via SupportsResponse.ONLY | PASSED | services.py: supports_response=SupportsResponse.ONLY, returns {"translated_text": translated_text} |
| SRVC-03 | Service validates language pair against coordinator data | PASSED | services.py: checks source in coordinator.data["languages"], target in source_lang["targets"] |
| SRVC-04 | Clear error for unavailable pair, server down, timeout | PASSED | services.py: ServiceValidationError for invalid_source, invalid_target, no_config_entry; HomeAssistantError for CannotConnectError |
| CARD-01 | Language dropdowns populated from server | PASSED | argos_translate-card.js: _getLanguages() reads sensor attributes, populates <select> elements |
| CARD-02 | Swap button exchanges source and target | PASSED | argos_translate-card.js: _swapLanguages() method, ha-icon-button with swap icon |
| CARD-03 | Multi-line text input and read-only output | PASSED | argos_translate-card.js: two <textarea> elements, rows="4", output has readonly |
| CARD-04 | Translate button calls service and displays result | PASSED | argos_translate-card.js: _translate() calls hass.callService, sets _outputText from response |
| CARD-05 | Loading indicator during translation | PASSED | argos_translate-card.js: ha-spinner inside button when _loading, "Translating..." text |
| CARD-06 | Status indicator (online/offline + language count) | PASSED | argos_translate-card.js: status-dot (green/red/gray) + statusText from binary_sensor |
| CARD-07 | Target dropdown filters to valid targets for source | PASSED | argos_translate-card.js: _getTargetsForSource() uses language_targets attribute |
| CARD-08 | Visual card editor for configuration | PASSED | argos_translate-card.js: ArgosTranslateCardEditor with 5 fields (entity, language_entity, header, default_source, default_target) |

## Must-Haves Verification

### Plan 02-01

| Truth | Status | Evidence |
|-------|--------|----------|
| Service accepts text, source, target | PASSED | services.py: vol.Required(ATTR_TEXT), vol.Required(ATTR_SOURCE), vol.Required(ATTR_TARGET) |
| Service returns {translated_text} via SupportsResponse.ONLY | PASSED | services.py line 91: supports_response=SupportsResponse.ONLY, line 84: return {"translated_text": ...} |
| Service validates language pair before API call | PASSED | services.py: source_lang lookup in coordinator.data["languages"], target check in source_lang["targets"] |
| Service returns clear error for invalid pair | PASSED | services.py: 3 distinct ServiceValidationError raises (no_config_entry, invalid_source, invalid_target) |
| Service returns clear error when server unreachable | PASSED | services.py: CannotConnectError caught, re-raised as HomeAssistantError |
| Language count sensor includes language_targets | PASSED | sensor.py: extra_state_attributes has "language_targets" dict comprehension |

### Plan 02-02

| Truth | Status | Evidence |
|-------|--------|----------|
| Card displays language dropdowns populated from server | PASSED | card.js: <select> elements populated from _getLanguages().codes/names |
| Target dropdown filters to valid targets | PASSED | card.js: validTargets = _getTargetsForSource(this._source) |
| Swap button exchanges selections | PASSED | card.js: _swapLanguages() swaps _source/_target |
| Card has multi-line input and readonly output | PASSED | card.js: two <textarea> with rows="4", output has readonly attribute |
| Translate button calls service and displays result | PASSED | card.js: _translate() calls hass.callService("argos_translate", "translate", ...) |
| Card shows loading spinner | PASSED | card.js: ha-spinner rendered when _loading is true |
| Card shows server status indicator | PASSED | card.js: status-dot with online/offline/unavailable classes |
| Visual card editor works | PASSED | card.js: ArgosTranslateCardEditor with ha-entity-picker and ha-textfield elements |

## Artifact Check

| File | Exists | Key Content |
|------|--------|-------------|
| const.py | Yes | SERVICE_TRANSLATE, ATTR_TEXT, ATTR_SOURCE, ATTR_TARGET |
| services.py | Yes | SupportsResponse.ONLY, ServiceValidationError, language validation |
| services.yaml | Yes | translate with text (multiline), source, target fields |
| sensor.py | Yes | language_targets dict in extra_state_attributes |
| strings.json | Yes | services.translate, exceptions (no_config_entry, invalid_source, invalid_target) |
| translations/en.json | Yes | Mirrors strings.json services and exceptions |
| frontend/argos_translate-card.js | Yes | ArgosTranslateCard, ArgosTranslateCardEditor, callService with returnResponse |

## Key Links Verification

| From | To | Via | Status |
|------|----|-----|--------|
| services.py | coordinator.py | coordinator.async_translate() | PASSED |
| services.py | coordinator.py | coordinator.data["languages"] for validation | PASSED |
| __init__.py | services.py | async_register_services(hass) in async_setup | PASSED |
| card.js | argos_translate.translate | hass.callService with returnResponse: true | PASSED |
| card.js | sensor attributes | language_targets for dropdown filtering | PASSED |
| card.js | binary_sensor state | status indicator from hass.states | PASSED |

## No Template Remnants

| Pattern | Files Checked | Found | Status |
|---------|---------------|-------|--------|
| SERVICE_QUERY | services.py | 0 | PASSED |
| query | services.py, services.yaml | 0 | PASSED |
| SupportsResponse.OPTIONAL | services.py | 0 | PASSED |
| TODO | services.py | 0 | PASSED |
| template | card.js (in description) | 0 | PASSED |

## Score

**12/12 requirements verified. All must-haves confirmed. All artifacts present. All key links wired.**

## Conclusion

Phase 2 goal achieved: Users can translate text via the `argos_translate.translate` service call (with language validation and clear errors) and the Lovelace translation card (with language dropdowns, swap, translate button, loading spinner, status indicator, and visual editor). No gaps found.
