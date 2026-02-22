---
phase: 05-auto-detect-card-polish
plan: "05"
subsystem: api
tags: [home-assistant, libretranslate, aiohttp, pytest, error-handling, binary-sensor]

# Dependency graph
requires:
  - phase: 05-auto-detect-card-polish
    provides: CannotConnectError handling in services.py, auto-detect translate path

provides:
  - TranslationError exception class in api.py for HTTP 4xx semantic errors
  - async_set_update_error usage for immediate binary_sensor status flip on connection failure
  - Detect-first fallback in auto-source translate path returning partial response on pair unavailable
  - 11 passing unit tests covering all error paths and fallback behavior

affects:
  - Phase 5 UAT re-test (status indicator and auto-detect issues)
  - binary_sensor.libretranslate_status (now flips offline immediately on CannotConnectError)
  - card JS (receives partial response with detected_language when pair unavailable)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TranslationError vs CannotConnectError: HTTP 4xx semantic errors (server reachable, request rejected) are distinct from connection failures (server unreachable)"
    - "async_set_update_error for immediate coordinator state propagation: synchronous @callback, no debouncer delay"
    - "Detect-first pattern: call /detect before /translate for auto source so detection result is available if /translate fails"
    - "Partial response on pair unavailable: return dict with translated_text='' + error + detected_language instead of raising HomeAssistantError"

key-files:
  created: []
  modified:
    - custom_components/argos_translate/api.py
    - custom_components/argos_translate/services.py
    - tests/test_services.py

key-decisions:
  - "TranslationError(Exception) added to api.py for HTTP 4xx non-auth errors — keeps CannotConnectError for true connection failures (network, timeout)"
  - "async_set_update_error(err) replaces await coordinator.async_request_refresh() in both CannotConnectError handlers — async_request_refresh has 10s debouncer cooldown that silently drops calls made within 10s of integration reload"
  - "Detect-first approach in auto-source path: /detect is called before /translate as best-effort; if /translate returns TranslationError, partial response is returned (not raised) so card can show detected language + descriptive error"
  - "TranslationError on non-auto source raises HomeAssistantError without marking coordinator as failed — server IS reachable"
  - "Partial response when auto detect pair unavailable: translated_text='' + error field + detected_language/detection_confidence from /detect result"

patterns-established:
  - "Error discrimination: CannotConnectError = server unreachable (mark coordinator failed), TranslationError = server reachable but rejected request (do NOT mark coordinator failed)"
  - "Partial responses: when auto-detect pair is unavailable, return structured dict instead of raising — enables card to show what was detected alongside the error"

requirements-completed:
  - DTCT-02
  - DTCT-03
  - DTCT-05
  - DTCT-06
  - CPOL-01

# Metrics
duration: 3min
completed: 2026-02-22
---

# Phase 5 Plan 05: Backend Error Handling & Auto-Detect Fallback Summary

**TranslationError class + async_set_update_error for immediate binary_sensor flip + detect-first fallback returning partial response when auto-detect pair unavailable**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-22T16:44:45Z
- **Completed:** 2026-02-22T16:47:38Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Fixed binary_sensor status indicator not flipping to offline on connection failures: replaced `await coordinator.async_request_refresh()` (debouncer-susceptible, async) with `coordinator.async_set_update_error(err)` (synchronous @callback, immediate)
- Added `TranslationError` exception to api.py distinguishing HTTP 4xx semantic errors from true connection failures — enables services.py to handle pair-unavailable errors without marking the coordinator as offline
- Implemented detect-first fallback for `source='auto'`: calls `/detect` before `/translate`; if `/translate` returns HTTP 400 (pair unavailable), returns a partial response with `detected_language`, `detection_confidence`, and a descriptive error message instead of raising `HomeAssistantError`
- All 11 unit tests pass (8 original + 3 new covering pair-unavailable scenarios and non-auto TranslationError)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix status indicator with async_set_update_error and add TranslationError to api.py** - `dadd71e` (fix)
2. **Task 2: Add detect-first fallback for auto source and update tests** - `e307b00` (feat)

**Plan metadata:** committed with final docs commit

## Files Created/Modified
- `custom_components/argos_translate/api.py` - Added `TranslationError` exception class; changed HTTP 400+ handler from `CannotConnectError` to `TranslationError`
- `custom_components/argos_translate/services.py` - Imported `TranslationError`; replaced `async_request_refresh` with `async_set_update_error` in both CannotConnectError handlers; added detect-first logic for auto-source path; added `TranslationError` except blocks in both service handlers
- `tests/test_services.py` - Imported `TranslationError`; added `async_set_update_error = MagicMock()` to `_setup_service`; updated `test_translate_api_error` to assert `async_set_update_error`; added 3 new tests

## Decisions Made
- **async_set_update_error vs async_request_refresh:** `async_request_refresh()` uses a Debouncer with `REQUEST_REFRESH_DEFAULT_COOLDOWN=10s`. When called shortly after integration reload, the debouncer silently drops the request — sensor stays green. `async_set_update_error(err)` is a synchronous `@callback` that immediately sets `last_update_success=False` and calls `async_update_listeners()` — no debouncing.
- **Detect-first vs translate-first:** Calling `/detect` before `/translate` ensures detection data is available even when `/translate` fails with HTTP 400. This is best-effort — if `/detect` also fails, we still attempt `/translate` (and if that fails too, we return a partial response with just the error).
- **Partial response instead of raising:** When auto-detect pair is unavailable, returning `{"translated_text": "", "detected_language": "fr", "error": "..."}` instead of raising `HomeAssistantError` allows the card to display both what was detected AND the reason translation failed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Test `test_translate_auto_detect_pair_unavailable_no_detect` needed careful interpretation: when `/detect` raises `CannotConnectError` and `/translate` raises `TranslationError`, the service returns a partial response (not raises) because `TranslationError` is caught in the auto-source path and returns gracefully. The test verifies `translated_text == ""`, `"error" in result`, and no `detected_language` in the response.

## User Setup Required

None - no external service configuration required. However, to see the binary_sensor fix in action, the LibreTranslate Docker container must be stopped while testing.

## Next Phase Readiness
- Both backend gap closure issues from UAT re-test are resolved
- Backend is ready for a final UAT re-test to confirm status indicator flips offline and auto-detect returns detected language on pair-unavailable errors
- Card JS may need updates to handle the new partial response format (`error` field alongside `detected_language`) — the card currently only processes `error` on exception, not in a result dict

---
*Phase: 05-auto-detect-card-polish*
*Completed: 2026-02-22*
