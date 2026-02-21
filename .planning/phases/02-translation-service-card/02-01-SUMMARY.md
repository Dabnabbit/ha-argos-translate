---
phase: 02-translation-service-card
plan: 01
subsystem: services
tags: [translate, service-response, voluptuous, language-validation]

requires:
  - phase: 01-api-client-data-layer
    provides: ArgosTranslateApiClient.async_translate() and ArgosCoordinator with language data
provides:
  - argos_translate.translate service with SupportsResponse.ONLY
  - Language pair validation against coordinator data
  - ServiceValidationError with localized messages for invalid inputs
  - language_targets sensor attribute mapping source codes to target code lists
affects: [translate-card, testing]

tech-stack:
  added: []
  patterns: [response-only-service, nested-async-handler, service-validation-error]

key-files:
  created: []
  modified:
    - custom_components/argos_translate/const.py
    - custom_components/argos_translate/services.py
    - custom_components/argos_translate/services.yaml
    - custom_components/argos_translate/sensor.py
    - custom_components/argos_translate/strings.json
    - custom_components/argos_translate/translations/en.json

key-decisions:
  - "Service handler nested inside async_register_services to capture hass from enclosing scope"
  - "ServiceValidationError with translation_key/translation_placeholders for localized errors"
  - "language_targets added as dict comprehension in sensor extra_state_attributes"
  - "First config entry used for coordinator lookup (single-instance primary use case)"

patterns-established:
  - "response-only-service: SupportsResponse.ONLY, handler returns dict, no return_response check"
  - "service-validation: ServiceValidationError with translation_domain/translation_key for user-facing errors"
  - "language-targets-attribute: {code: [targets]} dict in sensor attributes for frontend filtering"

requirements-completed: [SRVC-01, SRVC-02, SRVC-03, SRVC-04]

duration: 8min
completed: 2026-02-20
---

# Plan 02-01: Translate Service Summary

**Translate service with SupportsResponse.ONLY, language pair validation, and language_targets sensor attribute for card filtering**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-20
- **Completed:** 2026-02-20
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Translate service registered with SupportsResponse.ONLY, accepts text/source/target
- Language pair validation checks source exists and target is in source's targets list
- ServiceValidationError with localized messages for invalid source, invalid target, no config entry
- language_targets dict added to sensor extra_state_attributes for frontend dropdown filtering
- Service and exception strings localized in strings.json and translations/en.json

## Task Commits

1. **Task 1: Add service constants and update services.py** - `40bfe2d` (feat)
2. **Task 2: Add language_targets attribute and service translations** - `a7b6ca6` (feat)

## Files Created/Modified
- `custom_components/argos_translate/const.py` - SERVICE_TRANSLATE, ATTR_TEXT, ATTR_SOURCE, ATTR_TARGET constants
- `custom_components/argos_translate/services.py` - Complete rewrite: translate handler with validation, SupportsResponse.ONLY
- `custom_components/argos_translate/services.yaml` - Translate schema with text (multiline), source, target fields
- `custom_components/argos_translate/sensor.py` - Added language_targets dict to extra_state_attributes
- `custom_components/argos_translate/strings.json` - Added services and exceptions sections
- `custom_components/argos_translate/translations/en.json` - Mirror of strings.json additions

## Decisions Made
None - followed plan as specified

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Translate service ready for card integration (Plan 02-02)
- language_targets attribute available in sensor state for dropdown filtering
- Service callable from Developer Tools and automations

---
*Phase: 02-translation-service-card*
*Completed: 2026-02-20*
