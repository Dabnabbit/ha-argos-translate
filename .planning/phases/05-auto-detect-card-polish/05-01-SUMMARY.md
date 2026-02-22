---
phase: 05-auto-detect-card-polish
plan: "01"
subsystem: backend-services
tags: [auto-detect, services, api, coordinator, libretranslate]
dependency_graph:
  requires: []
  provides: [auto-detect-translate-service, detect-language-service]
  affects: [custom_components/argos_translate/api.py, custom_components/argos_translate/coordinator.py, custom_components/argos_translate/services.py]
tech_stack:
  added: []
  patterns: [dict-passthrough, auto-source-bypass, service-response-enrichment]
key_files:
  created: []
  modified:
    - custom_components/argos_translate/api.py
    - custom_components/argos_translate/coordinator.py
    - custom_components/argos_translate/services.py
    - custom_components/argos_translate/const.py
    - custom_components/argos_translate/strings.json
    - custom_components/argos_translate/translations/en.json
    - tests/test_services.py
decisions:
  - "async_translate returns full LibreTranslate response dict to surface detectedLanguage alongside translatedText"
  - "Auto source bypass uses explicit if source != AUTO_SOURCE guard rather than adding 'auto' to language lists"
  - "detect service reuses ATTR_TEXT constant from translate service"
metrics:
  duration_seconds: 127
  tasks_completed: 3
  tasks_total: 3
  files_modified: 7
  completed_date: "2026-02-22"
requirements_addressed: [DTCT-02, DTCT-03, DTCT-06]
---

# Phase 5 Plan 01: Backend Auto-Detect Language Support Summary

Backend auto-detect support added: translate service accepts source='auto', returns detected_language/detection_confidence fields, flags uninstalled detected languages, and a new detect HA service provides full candidate array via LibreTranslate /detect endpoint.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend api.py and coordinator.py for auto-detect | 86c5429 | api.py, coordinator.py |
| 2 | Update services.py for auto-detect with detect service | 46988be | services.py, const.py, strings.json, translations/en.json |
| 3 | Update test_services.py for auto-detect and dict return type | 531a1b1 | tests/test_services.py |

## What Was Built

**api.py:**
- `async_translate` return type changed from `str` to `dict[str, Any]` — returns full LibreTranslate response including optional `detectedLanguage` object
- New `async_detect_languages(text)` method calling `/detect` endpoint, returns candidate list

**coordinator.py:**
- `async_translate` return type updated to `dict[str, Any]` with updated docstring
- New `async_detect_languages` passthrough method added

**services.py:**
- `AUTO_SOURCE = "auto"` module-level constant
- Source/target validation wrapped in `if source != AUTO_SOURCE:` guard — auto bypasses all language validation
- Response enrichment: when `detectedLanguage` present in result, adds `detected_language`, `detection_confidence`, and optionally `uninstalled_detected_language` fields
- New `detect` HA service registered with `DETECT_SCHEMA`, calls `coordinator.async_detect_languages`, returns `{"detections": candidates}`

**const.py:** `SERVICE_DETECT = "detect"` constant added

**strings.json / translations/en.json:** Source field description updated to mention 'auto'; new `detect` service block added with name, description, and fields

**tests/test_services.py:**
- `_setup_service` updated to accept `dict` mock result (default `{"translatedText": "Hola"}`)
- `async_detect_languages` mock added to coordinator mock
- 3 new tests: `test_translate_auto_detect_success`, `test_translate_auto_detect_uninstalled_language`, `test_translate_auto_detect_no_validation_error`
- All 8 tests pass

## Verification Results

```
tests/test_services.py::test_translate_success PASSED
tests/test_services.py::test_translate_invalid_source PASSED
tests/test_services.py::test_translate_invalid_target PASSED
tests/test_services.py::test_translate_api_error PASSED
tests/test_services.py::test_translate_no_config_entry PASSED
tests/test_services.py::test_translate_auto_detect_success PASSED
tests/test_services.py::test_translate_auto_detect_uninstalled_language PASSED
tests/test_services.py::test_translate_auto_detect_no_validation_error PASSED

8 passed in 0.12s
```

All Python files parse correctly. Both JSON files are valid.

## Decisions Made

1. **async_translate returns full dict:** Rather than extracting just `translatedText`, the full response is returned through the stack so services.py can access `detectedLanguage` without a second API call.

2. **Auto source bypass is explicit guard:** Using `if source != AUTO_SOURCE:` rather than adding "auto" to any language list keeps the installed-language validation clean and avoids contaminating coordinator data.

3. **ATTR_TEXT reused for detect service:** No separate `ATTR_DETECT_TEXT` constant needed — the detect service takes the same `text` field as the translate service.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

All files confirmed present on disk. All commits (86c5429, 46988be, 531a1b1) verified in git log.
