---
phase: 01-api-client-data-layer
plan: 02
subsystem: ui
tags: [config-flow, binary-sensor, sensor, voluptuous, strings]

requires:
  - phase: 01-api-client-data-layer
    provides: ArgosTranslateApiClient and ArgosCoordinator from plan 01
provides:
  - LibreTranslate config flow with 5 fields and connection validation
  - Status binary sensor (connectivity device class)
  - Language count sensor (disabled by default, language list attributes)
  - Options flow with connection validation
affects: [services, translate-card, testing]

tech-stack:
  added: []
  patterns: [binary-sensor-from-coordinator-success, disabled-by-default-entity]

key-files:
  created:
    - custom_components/argos_translate/binary_sensor.py
  modified:
    - custom_components/argos_translate/config_flow.py
    - custom_components/argos_translate/sensor.py
    - custom_components/argos_translate/__init__.py
    - custom_components/argos_translate/strings.json
    - custom_components/argos_translate/translations/en.json

key-decisions:
  - "Status sensor uses coordinator.last_update_success for is_on (not custom status field)"
  - "NoLanguages exception distinguishes empty server from unreachable server"
  - "CONF_NAME imported from homeassistant.const, CONF_USE_SSL custom in const.py"
  - "Options flow merges new input with existing data before validation"

patterns-established:
  - "binary-sensor-from-coordinator: is_on derives from coordinator.last_update_success"
  - "disabled-by-default: entity_registry_enabled_default = False for secondary sensors"
  - "options-flow-validation: validate connection before saving options changes"

requirements-completed: [CONF-01, CONF-02, CONF-03, SENS-01, SENS-02, SENS-03]

duration: 10min
completed: 2026-02-20
---

# Plan 01-02: Config Flow + Sensors Summary

**LibreTranslate config flow with SSL toggle, connectivity binary sensor, and language count sensor with attributes**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-20
- **Completed:** 2026-02-20
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Config flow with 5 fields: name, host, port (no default), SSL toggle, optional API key
- Connection validation with distinct errors for cannot_connect, invalid_auth, no_languages
- Status binary sensor (connectivity class) driven by coordinator poll success
- Language count sensor disabled by default with language names and codes in attributes
- Options flow validates connection before saving changes

## Task Commits

1. **Task 1: Config flow, strings, translations** - `b1914fb` (feat)
2. **Task 2: Binary sensor, sensor, __init__** - `985cf47` (feat)

## Files Created/Modified
- `custom_components/argos_translate/binary_sensor.py` - NEW: ArgosStatusSensor with connectivity device class
- `custom_components/argos_translate/config_flow.py` - 5-field schema, connection validation, options flow
- `custom_components/argos_translate/sensor.py` - ArgosLanguageCountSensor, disabled by default, extra_state_attributes
- `custom_components/argos_translate/__init__.py` - Platform.BINARY_SENSOR, ArgosCoordinator references
- `custom_components/argos_translate/strings.json` - LibreTranslate-specific config flow strings
- `custom_components/argos_translate/translations/en.json` - English translations matching strings.json

## Decisions Made
None - followed plan as specified

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 1 requirements (CONF-01/02/03, SENS-01/02/03/04) addressed
- Integration can be configured, connected, and monitored via HA UI
- Ready for Phase 2: translation service and Lovelace card

---
*Phase: 01-api-client-data-layer*
*Completed: 2026-02-20*
