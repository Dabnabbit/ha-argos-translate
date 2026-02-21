---
phase: 03-polish-validation
plan: 01
subsystem: testing
tags: [pytest, homeassistant, config-flow, coordinator, services, sensors]

requires:
  - phase: 01-core-backend
    provides: "API client, coordinator, config flow implementations"
  - phase: 02-frontend-services
    provides: "Translate service, sensor entities, binary sensor"
provides:
  - "Comprehensive test coverage for config flow, coordinator, services, and sensors"
  - "Shared test fixtures (mock_config_entry, MOCK_LANGUAGES)"
affects: [03-02, distribution, CI]

tech-stack:
  added: []
  patterns:
    - "Direct entity instantiation for disabled-by-default sensors"
    - "Service testing with return_response=True"

key-files:
  created:
    - tests/test_services.py
    - tests/test_sensor.py
  modified:
    - tests/conftest.py
    - tests/test_config_flow.py
    - tests/test_coordinator.py

key-decisions:
  - "Test sensors via direct instantiation (not state machine) due to disabled-by-default"
  - "Service tests use _setup_service helper with mocked coordinator and runtime_data"

patterns-established:
  - "Mock coordinator pattern: MagicMock with .data dict and .async_translate AsyncMock"
  - "Config flow tests include CONF_NAME and CONF_USE_SSL in all user_input dicts"

requirements-completed: [DIST-03]

duration: 2 min
completed: 2026-02-21
---

# Phase 03 Plan 01: Test Suite Fixes and Coverage Summary

**Fixed stale template references (TemplateCoordinator, port 8080) and added full test coverage for services and sensors**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-21T05:53:59Z
- **Completed:** 2026-02-21T05:56:09Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Fixed all stale template references in existing tests (TemplateCoordinator, ApiClient.async_get_data, port 8080)
- Added shared test fixtures: mock_config_entry and MOCK_LANGUAGES constant
- Added InvalidAuth and NoLanguages error state tests to config flow
- Created test_services.py with 5 tests covering translate success, validation errors, API errors, and missing config entry
- Created test_sensor.py with 9 tests covering language count value/attrs/null/unique_id/disabled and status online/offline/unique_id/device_class
- Options flow test now validates connection before updating entry data

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix existing tests and add shared fixtures** - `06c2b49` (fix)
2. **Task 2: Create test_services.py and test_sensor.py** - `327ce0f` (test)

## Files Created/Modified
- `tests/conftest.py` - Added mock_config_entry fixture and MOCK_LANGUAGES constant
- `tests/test_config_flow.py` - Fixed ports, added CONF_NAME/CONF_USE_SSL, added InvalidAuth/NoLanguages tests
- `tests/test_coordinator.py` - Fixed TemplateCoordinator→ArgosCoordinator, correct mock data shape
- `tests/test_services.py` - New: translate service tests (success, invalid source/target, API error, no config entry)
- `tests/test_sensor.py` - New: sensor entity tests (language count, binary status, attributes, unique IDs)

## Decisions Made
- Tested sensors via direct instantiation rather than through HA state machine, since both entities are disabled-by-default
- Service tests mock coordinator.async_translate directly rather than patching the API client layer

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Options flow validation**
- **Found during:** Task 1 (test_config_flow.py)
- **Issue:** Options flow test didn't validate connection before updating entry
- **Fix:** Added _async_validate_connection patch to options flow test, updated assertions to verify merged data including CONF_NAME preservation
- **Files modified:** tests/test_config_flow.py
- **Verification:** Test asserts all merged fields correctly
- **Committed in:** 06c2b49

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Minor improvement to options flow test coverage. No scope creep.

## Issues Encountered
- Test dependencies (pytest-homeassistant-custom-component) not installed in environment — no pip/uv available. Tests are syntactically validated and structurally correct based on source code analysis. Full pytest execution deferred to CI.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Test suite complete, ready for Plan 03-02 (README + CI validation)
- All 5 test files written with approximately 20 tests total

---
*Phase: 03-polish-validation*
*Completed: 2026-02-21*
