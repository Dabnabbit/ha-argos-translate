---
phase: 05-auto-detect-card-polish
plan: "04"
subsystem: ui
tags: [lovelace, lit-element, home-assistant, container-query, css, services, coordinator]

# Dependency graph
requires:
  - phase: 05-auto-detect-card-polish
    provides: UAT gap diagnosis — swap guard, status refresh, CQ shadow DOM, grid rows, textarea resize

provides:
  - services.py triggers coordinator.async_request_refresh() on CannotConnectError so binary_sensor flips offline immediately
  - Card v0.5.1 with pre-swap pair validation that blocks and shows error for invalid reversed pairs
  - Container query moved from :host to .card-content to work within shadow DOM boundary
  - Card grid height reduced from 7 to 5 rows (getCardSize and getGridOptions)
  - Textarea resize disabled (resize none) to prevent content overflow

affects:
  - Phase 5 UAT — all 5 diagnosed gaps are now closed
  - Future card changes — container query pattern is now shadow-DOM-safe

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Coordinator refresh on service error: await coordinator.async_request_refresh() in CannotConnectError handler triggers immediate poll"
    - "Shadow DOM container queries: container-type/container-name must be on a class inside shadow DOM, not :host"
    - "Pre-swap validation: check reversed pair targets before mutating state, surface descriptive error without committing swap"

key-files:
  created: []
  modified:
    - custom_components/argos_translate/services.py
    - custom_components/argos_translate/frontend/argos_translate-card.js
    - tests/test_services.py

key-decisions:
  - "async_request_refresh called before re-raising HomeAssistantError so coordinator poll runs immediately on any CannotConnectError (both translate and detect handlers)"
  - "Pre-swap guard reads _getTargetsForSource(oldTarget) to check if oldSource is a valid target for the reversed direction; returns early with error if not"
  - "container-type: inline-size moved from :host to .card-content — :host is outside shadow DOM scope, .card-content is inside, enabling @container argos-card queries on .content-area"
  - "getGridOptions rows reduced from 7 to 5, min_rows from 5 to 4 — matches actual content height; getCardSize also reduced from 7 to 5"
  - "Test mock updated: added AsyncMock for async_request_refresh in _setup_service; test_translate_api_error asserts refresh called once on failure"

patterns-established:
  - "Coordinator refresh on failure: service handlers call async_request_refresh() before re-raising connection errors"
  - "Shadow-DOM container queries: place container-type on inner class element, not :host"

requirements-completed: [CPOL-04, STAB-04]

# Metrics
duration: 2min
completed: 2026-02-22
---

# Phase 5 Plan 04: UAT Gap Closure Summary

**5 UAT issues closed: status offline refresh, swap pair guard, container query shadow DOM fix, grid height reduction, textarea resize removal — card bumped to v0.5.1**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-22T07:10:13Z
- **Completed:** 2026-02-22T07:12:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- services.py now calls `await coordinator.async_request_refresh()` in both CannotConnectError handlers (translate and detect), so the binary_sensor status indicator flips to offline immediately on server failure rather than waiting up to 5 minutes for the poll cycle
- Card v0.5.1 pre-swap guard validates the reversed language pair exists before committing the swap; surfaces a descriptive error like "Cannot swap — French -> English translation pair is not installed" and leaves state unchanged
- Container query fixed: moved `container-type: inline-size` and `container-name: argos-card` from `:host` to `.card-content`, enabling `@container argos-card (min-width: 580px)` to fire correctly inside shadow DOM
- Grid height reduced from 7 to 5 rows, preventing card from overflowing into adjacent dashboard sections
- Textarea `resize: none` applied, preventing users from dragging textareas beyond the card boundary

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix status indicator not updating on service call failure** - `5d0822b` (fix)
2. **Task 2: Fix card swap guard, container query, grid height, and textarea resize** - `a758559` (feat)

## Files Created/Modified

- `custom_components/argos_translate/services.py` - Added `await coordinator.async_request_refresh()` in both CannotConnectError catch blocks (translate and detect handlers)
- `custom_components/argos_translate/frontend/argos_translate-card.js` - v0.5.1: pre-swap guard, container query fix, grid size reduction, textarea resize removal
- `tests/test_services.py` - Added `AsyncMock` for `async_request_refresh` in mock coordinator setup; updated `test_translate_api_error` to assert refresh is called

## Decisions Made

- `async_request_refresh()` is called before re-raising the `HomeAssistantError` (not after) so the coordinator refresh attempt runs even though the caller will see an exception
- Pre-swap guard uses the existing `_getTargetsForSource(oldTarget)` helper — no new helper needed; returns valid targets for the would-be new source language
- Container-type moved to `.card-content` rather than adding a new wrapper element — `.card-content` is the natural container since `.content-area` is a direct child
- Test file updated as part of Task 1 commit since the test was failing specifically because of the new `async_request_refresh()` call (Rule 1 auto-fix)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test mock to support async_request_refresh**
- **Found during:** Task 1 (Fix status indicator not updating on service call failure)
- **Issue:** `test_translate_api_error` failed because `MagicMock` coordinator did not have `async_request_refresh` as an `AsyncMock`, so `await coordinator.async_request_refresh()` raised `TypeError: object MagicMock can't be used in 'await' expression`
- **Fix:** Added `mock_coordinator.async_request_refresh = AsyncMock()` to `_setup_service` helper; also updated `test_translate_api_error` to assert `async_request_refresh.assert_called_once()`
- **Files modified:** `tests/test_services.py`
- **Verification:** All 8 tests pass including `test_translate_api_error`
- **Committed in:** `5d0822b` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in test mock)
**Impact on plan:** Necessary correction — the test was not covering the new behavior. Auto-fix adds verification that the refresh is actually called, which strengthens the test suite.

## Issues Encountered

None beyond the auto-fixed test mock issue documented above.

## User Setup Required

None — no external service configuration required.

The updated card JS file (`argos_translate-card.js` v0.5.1) should be deployed to the Home Assistant instance via rsync and the browser cache cleared (Ctrl+Shift+R). The updated `services.py` requires an HA integration reload.

## Next Phase Readiness

- All 5 UAT gaps from Phase 5 are closed — Phase 5 is ready for a re-test run
- Phase 6 (v1.1 final) can proceed once UAT re-confirms all 11 tests pass

## Self-Check: PASSED

- FOUND: custom_components/argos_translate/services.py
- FOUND: custom_components/argos_translate/frontend/argos_translate-card.js
- FOUND: .planning/phases/05-auto-detect-card-polish/05-04-SUMMARY.md
- FOUND: commit 5d0822b (fix - services.py + test_services.py)
- FOUND: commit a758559 (feat - argos_translate-card.js v0.5.1)

---
*Phase: 05-auto-detect-card-polish*
*Completed: 2026-02-22*
