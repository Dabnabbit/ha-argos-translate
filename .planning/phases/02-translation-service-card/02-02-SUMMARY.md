---
phase: 02-translation-service-card
plan: 02
subsystem: frontend
tags: [lovelace, lit-element, custom-card, translation-ui]

requires:
  - phase: 02-translation-service-card
    provides: argos_translate.translate service and language_targets sensor attribute from plan 01
provides:
  - Lovelace translation card with language dropdowns, swap, translate, and status display
  - Visual card editor with entity pickers and default language configuration
affects: [testing]

tech-stack:
  added: []
  patterns: [callService-returnResponse, select-dropdown-filtering, status-indicator]

key-files:
  created: []
  modified:
    - custom_components/argos_translate/frontend/argos_translate-card.js

key-decisions:
  - "Used native <select> elements instead of ha-select for simpler dropdown rendering"
  - "SVG path used directly for swap icon (mdi:swap-horizontal) via ha-icon-button .path"
  - "Output text swaps to input on language swap for convenient back-translation"
  - "Card disables translate button when offline, loading, or missing input/languages"

patterns-established:
  - "callService-returnResponse: hass.callService(domain, service, data, {}, true, true) for response data"
  - "select-dropdown-filtering: target dropdown repopulated when source changes using language_targets"
  - "status-indicator: colored dot + text from binary_sensor state for connection status"

requirements-completed: [CARD-01, CARD-02, CARD-03, CARD-04, CARD-05, CARD-06, CARD-07, CARD-08]

duration: 10min
completed: 2026-02-20
---

# Plan 02-02: Lovelace Translation Card Summary

**Translation card with language dropdowns, swap button, text input/output, translate button with loading spinner, server status indicator, and visual card editor**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-20
- **Completed:** 2026-02-20
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Source and target language dropdowns populated from sensor language_targets attribute
- Target dropdown filters to valid targets for selected source language
- Swap button exchanges languages and moves output to input for back-translation
- Translate button calls argos_translate.translate service with returnResponse: true
- Loading spinner inside translate button during translation
- Server status indicator (green/red/gray dot with text) from binary sensor
- Visual card editor with 5 fields: status entity, language entity, header, default source, default target
- Entity pickers filtered to binary_sensor and sensor domains

## Task Commits

1. **Task 1+2: Rewrite card with translation UI and editor** - `95c5805` (feat)

## Files Created/Modified
- `custom_components/argos_translate/frontend/argos_translate-card.js` - Complete rewrite with translation UI, service integration, and card editor

## Decisions Made
- Used native `<select>` elements for language dropdowns (simpler than ha-select, works reliably in shadow DOM)
- Used ha-icon-button with SVG path for swap icon instead of mdi icon name (more reliable in custom cards)
- Swap button moves output text to input for convenient back-translation workflow

## Deviations from Plan
None - plan executed exactly as written (Tasks 1 and 2 combined into single commit since they modify the same file)

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 2 requirements (SRVC-01/02/03/04, CARD-01/02/03/04/05/06/07/08) addressed
- Card and service fully functional, ready for Phase 3 testing and validation

---
*Phase: 02-translation-service-card*
*Completed: 2026-02-20*
