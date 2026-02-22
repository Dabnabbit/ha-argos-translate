---
phase: 05-auto-detect-card-polish
plan: "02"
subsystem: ui
tags: [lovelace, lit-element, css-container-queries, aria, accessibility, responsive-layout]

# Dependency graph
requires:
  - phase: 04-options-flow
    provides: Working card v0.3.1 with entity auto-detect and grid sizing
provides:
  - ARIA labels on all form controls (source/target selects, input/output textareas, swap button)
  - Discriminating error handler distinguishing 4 error categories in catch block
  - _getDisabledReason() method with inline hint div below translate button
  - CSS container queries for auto-responsive horizontal/vertical layout at 580px breakpoint
  - data-layout attribute with forced horizontal/vertical override via config
  - Layout dropdown in card editor (auto/horizontal/vertical)
  - Flex-wrap on language row for narrow-width wrapping
affects: [05-03-card-auto-detect-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CSS container queries (container-type: inline-size) for component-width-based layout instead of viewport media queries"
    - "data-layout host attribute pattern for CSS override of container-query defaults"
    - "IIFE in lit-html template for conditional rendering with non-null guard"

key-files:
  created: []
  modified:
    - custom_components/argos_translate/frontend/argos_translate-card.js

key-decisions:
  - "Layout breakpoint at 580px card width (container query) switches to side-by-side panels"
  - "Hint div placed below translate button (not above) for visual flow: input -> action -> reason"
  - "textarea rows bumped from 3 to 4 in horizontal mode for better panel height"
  - "getGridOptions columns changed from 6 to 12 to accommodate wider horizontal layout"

patterns-established:
  - "CSS container queries on :host for card-width-responsive layouts in Lovelace custom cards"
  - "Error discrimination by err.code before err.message for HA WebSocket error objects"

requirements-completed:
  - CPOL-01
  - CPOL-02
  - CPOL-03
  - CPOL-04

# Metrics
duration: 3min
completed: 2026-02-22
---

# Phase 5 Plan 02: Card Polish Summary

**ARIA accessibility labels, 4-category error discrimination, disabled-button hint text, and CSS container query responsive layout (vertical/horizontal at 580px) with config override — card v0.4.0**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-22T06:03:02Z
- **Completed:** 2026-02-22T06:05:36Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- All interactive form controls have `aria-label` attributes (source select, target select, input textarea, output textarea, swap button)
- Error catch block now discriminates: connection lost (numeric/no code), timeout (home_assistant_error + "timeout"), server unreachable (home_assistant_error + "connect"), bad request (service_validation_error), and generic fallback
- Disabled translate button shows inline hint text below explaining why (server offline / no text / no language selected)
- Card layout uses CSS container queries — narrow cards stack vertically, wide cards (>=580px) show input left / output right side-by-side
- Config `layout` field ("auto"/"horizontal"/"vertical") allows forcing layout override via `data-layout` host attribute
- Card editor has Layout dropdown to set config.layout
- Language row wraps cleanly with `flex-wrap: wrap` at narrow widths

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ARIA labels, error discrimination, and disabled button reason** - `034d882` (feat)
2. **Task 2: Add responsive layout with CSS container queries and layout config override** - `2bbad41` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `custom_components/argos_translate/frontend/argos_translate-card.js` - Card v0.4.0 with ARIA, error discrimination, hint text, container queries, layout config

## Decisions Made

- Layout breakpoint at 580px card width (matches plan spec, enough room for two usable panels)
- Hint div placed after the translate button, not before — so users see: [input area] -> [button] -> [why disabled]
- textarea rows increased from 3 to 4 in the new panel structure for better visual balance
- `getGridOptions()` columns changed from 6 to 12 (plan spec) to accommodate wider default horizontal layout

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed on first attempt with syntax checks passing and all grep assertions passing.

## User Setup Required

None - no external service configuration required. To deploy: rsync the updated JS to HA and hard-refresh browser (Ctrl+Shift+R). Optionally bump Lovelace resource URL version to `?v=0.4.0` to force cache bust.

## Next Phase Readiness

- Card v0.4.0 is accessible, informative about errors and disabled states, and responsive to container width
- Ready for Phase 5 Plan 03 (card auto-detect UI improvements)
- No blockers

## Self-Check: PASSED

- FOUND: custom_components/argos_translate/frontend/argos_translate-card.js
- FOUND: .planning/phases/05-auto-detect-card-polish/05-02-SUMMARY.md
- FOUND commit: 034d882 (Task 1)
- FOUND commit: 2bbad41 (Task 2)

---
*Phase: 05-auto-detect-card-polish*
*Completed: 2026-02-22*
