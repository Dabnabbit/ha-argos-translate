---
phase: 04-options-flow-fix
plan: 01
subsystem: config-flow
tags: [home-assistant, options-flow, async-reload, config-entries, pytest]

# Dependency graph
requires: []
provides:
  - Options flow reload: saving new credentials triggers async_reload so coordinator rebuilds immediately
  - Test coverage: 3 new/updated tests covering success reload and no-reload on error paths
affects: [05-auto-detect, 06-card-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "OptionsFlowHandler uses explicit await async_reload(entry_id) after async_update_entry on success path"
    - "Test pattern: patch.object(hass.config_entries, 'async_reload') to mock reload in options flow tests"

key-files:
  created: []
  modified:
    - custom_components/argos_translate/config_flow.py
    - tests/test_config_flow.py

key-decisions:
  - "Used explicit await async_reload instead of OptionsFlowWithReload for HA 2025.7+ compatibility (pre-existing decision from STATE.md)"
  - "No rollback logic on post-reload failure: HA default behavior (integration shows as failed) is acceptable"
  - "pre-existing coordinator test failures (test_coordinator_update_failed, test_coordinator_update) are out of scope — verified pre-existing before this plan"

patterns-established:
  - "Options flow success path: async_update_entry -> await async_reload -> async_create_entry(data={})"
  - "Options flow test pattern: patch validation AND patch.object reload, assert reload called/not_called"

requirements-completed: [OPTS-01, OPTS-02]

# Metrics
duration: 14min
completed: 2026-02-21
---

# Phase 4 Plan 01: Options Flow Fix Summary

**Added `await async_reload` to OptionsFlowHandler success path so saving new host/API key immediately reconnects the integration without HA restart**

## Performance

- **Duration:** 14 min
- **Started:** 2026-02-21T21:13:14Z
- **Completed:** 2026-02-21T21:27:14Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Fixed OPTS-02: options changes (host, port, API key, SSL) now take effect immediately via async_reload
- Added reload assertion to existing `test_options_flow` — now asserts reload called once with correct entry_id
- Added `test_options_flow_no_reload_on_connection_error` — verifies reload NOT called and data NOT saved when CannotConnect
- Added `test_options_flow_no_reload_on_auth_error` — verifies reload NOT called and data NOT saved when InvalidAuth
- All 8 config flow tests pass with 0 failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Add async_reload call to OptionsFlowHandler** - `1f58228` (fix)
2. **Task 2: Add options flow reload test assertions** - `8c31dab` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `custom_components/argos_translate/config_flow.py` - Added 8 lines: comment block + await async_reload call on options flow success path
- `tests/test_config_flow.py` - Updated test_options_flow with reload assertion; added 2 new test functions for error paths

## Decisions Made
- Used `patch.object(hass.config_entries, "async_reload", return_value=True)` for reload mocking (cleaner than string path for built-in HA methods)
- No rollback logic added: accepted HA default behavior on post-reload failure per plan specification
- Pre-existing `test_coordinator_update_failed` failure is out of scope — confirmed pre-existing before this plan's changes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing test dependencies (pytest, pytest-homeassistant-custom-component, home-assistant-frontend)**
- **Found during:** Task 2 verification
- **Issue:** pytest not installed in project; tests could not run. After installing pytest/pytest-homeassistant-custom-component, `hass_frontend` module was missing causing `DependencyError` for all tests
- **Fix:** Created `.venv`, installed `pytest pytest-homeassistant-custom-component pytest-asyncio`, then installed `home-assistant-frontend` to satisfy HA frontend dependency
- **Files modified:** `.venv/` (virtual environment, not committed)
- **Verification:** All 8 config flow tests pass
- **Committed in:** N/A (environment setup, no source files changed)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing test infrastructure)
**Impact on plan:** Auto-fix was necessary to run the test suite. No scope creep.

## Issues Encountered
- Pre-existing coordinator test failures (`test_coordinator_update_failed`, lingering thread teardown error in `test_coordinator_update`) were present before this plan's changes. Confirmed via `git stash` + re-run. Out of scope per deviation rules. Logged to deferred-items if needed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Options flow bug fixed: OPTS-01 and OPTS-02 both now satisfied
- Integration reconnects immediately after saving new credentials in options
- Ready for Phase 5: Auto-detect language feature

---
*Phase: 04-options-flow-fix*
*Completed: 2026-02-21*

## Self-Check: PASSED

- FOUND: custom_components/argos_translate/config_flow.py
- FOUND: tests/test_config_flow.py
- FOUND: .planning/phases/04-options-flow-fix/04-01-SUMMARY.md
- FOUND: commit 1f58228 (fix: add async_reload)
- FOUND: commit 8c31dab (test: reload assertions)
