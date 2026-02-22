---
phase: 05-auto-detect-card-polish
plan: "06"
subsystem: ui
tags: [lovelace, card, css, container-query, shadow-dom, resize-observer]

# Dependency graph
requires:
  - phase: 05-auto-detect-card-polish
    provides: Card v0.5.1 with swap guard and prior CSS attempts
provides:
  - ":host height:100% constrains card to HA sections grid slot — no overflow"
  - "ResizeObserver fallback replaces broken container query for responsive horizontal layout"
  - "Card version 0.5.2"
affects:
  - 05-auto-detect-card-polish UAT re-test

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ResizeObserver on :host width as fallback when shadow DOM blocks container queries"
    - ":host height:100% + ha-card height:100% + .card-content flex:1/overflow:auto chain for grid slot containment"

key-files:
  created: []
  modified:
    - custom_components/argos_translate/frontend/argos_translate-card.js

key-decisions:
  - "Approach B (ResizeObserver) used instead of Approach A (container-wrap div) — .card-content overflow:auto inside flex layout caused inline-size to resolve to 0, blocking container query; ResizeObserver on :host is reliable"
  - "data-wide attribute toggled on :host at >= 580px via ResizeObserver; :host([data-wide]) CSS selectors replace @container rule"
  - "getGridOptions rows reduced to 4 (from 5), min_rows to 3 — with height:100% the slot allocation is compact and scrolls"

patterns-established:
  - "Shadow DOM card layout: :host{display:block;height:100%;box-sizing:border-box} -> ha-card{height:100%} -> .card-content{flex:1;overflow:auto}"
  - "ResizeObserver pattern for container-query-like behavior in shadow DOM contexts"

requirements-completed: [CPOL-04, DTCT-01, DTCT-04]

# Metrics
duration: ~2hrs (includes checkpoint wait)
completed: 2026-02-22
---

# Phase 5 Plan 06: Card CSS Gap Closure Summary

**Lovelace card v0.5.2 — ResizeObserver replaces broken container query for responsive layout; :host height:100% eliminates grid slot overflow; verified on live HA dashboard**

## Performance

- **Duration:** ~2 hours (includes human verification checkpoint)
- **Started:** 2026-02-22
- **Completed:** 2026-02-22T17:33:29Z
- **Tasks:** 2 (1 code, 1 human verification)
- **Files modified:** 1

## Accomplishments

- Fixed card height overflow: `:host { height: 100%; box-sizing: border-box }` chains to `ha-card { height: 100% }` and `.card-content { flex: 1; overflow: auto }` so the card constrains to its HA sections grid slot and scrolls internally when content exceeds the slot
- Fixed responsive horizontal layout: Approach A (container-wrap div) was attempted but `.card-content` with `overflow: auto` inside a flex layout causes `inline-size` to resolve to 0, blocking the container query. Switched to Approach B: a `ResizeObserver` watches `:host` width, toggles `data-wide` attribute at >= 580px, and CSS `:host([data-wide])` selectors provide side-by-side layout
- Reduced `getGridOptions()` rows from 5 to 4 (min_rows: 3) for a more compact default allocation
- Bumped card version to 0.5.2
- Human verification confirmed all four checks on live HA dashboard (QNAP Docker instance)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix card height constraint and container query, bump version** - `f586c2a` (feat)
2. **Task 2: Verify card CSS fixes on live dashboard** - human-verified, no code commit (checkpoint resolution)

**Plan metadata:** (to be committed with SUMMARY.md)

## Files Created/Modified

- `custom_components/argos_translate/frontend/argos_translate-card.js` - Card v0.5.2: :host height constraint, ResizeObserver for responsive layout, rows:4/min_rows:3 grid options

## Decisions Made

- **ResizeObserver over container-wrap (Approach B over A):** The plan's Approach A — adding a `.container-wrap` div with `container-type: inline-size` inside `.card-content` — was the first attempt. However, `.card-content` has `overflow: auto` and `flex: 1` inside a column flex container, which causes the browser to report its inline-size as 0 during containment resolution. ResizeObserver on `:host` is a reliable, widely-supported fallback that sidesteps shadow DOM and flex layout containment issues entirely.
- **`data-wide` attribute pattern:** Toggling a host attribute via JS and selecting it with `:host([data-wide])` in the shadow DOM stylesheet is the idiomatic Lit/vanilla web component pattern for JS-driven conditional styling.
- **Grid rows reduced to 4:** With height constraint active the card fills its slot compactly. Rows 5 was over-allocated; 4 rows provides adequate space with internal scroll for extra content.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Approach A container-wrap failed — switched to Approach B ResizeObserver**
- **Found during:** Task 1 (Fix card height constraint and container query)
- **Issue:** `.card-content` with `overflow: auto` inside a flex layout causes `inline-size` to resolve to 0, preventing the container query from ever matching. Moving container declaration to a `.container-wrap` child still did not resolve the issue in this layout context.
- **Fix:** Implemented Approach B as specified in the plan's fallback instructions — ResizeObserver on `:host` width, toggles `data-wide` attribute, CSS `:host([data-wide])` selectors. Observer cleaned up in `disconnectedCallback()`.
- **Files modified:** `custom_components/argos_translate/frontend/argos_translate-card.js`
- **Verification:** `node --check` passed. Human verified on live dashboard: textareas go side-by-side in full-width panel (>= 580px), stack vertically in narrow columns.
- **Committed in:** `f586c2a` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug, planned fallback triggered)
**Impact on plan:** Plan explicitly anticipated Approach A might fail and pre-specified Approach B. Deviation followed the plan's own fallback path — no scope creep.

## Issues Encountered

None beyond the expected Approach A container query failure, which the plan pre-documented with a fallback. Approach B worked first time.

## User Setup Required

JS-only change — no HA restart needed. Deployed via rsync + browser hard refresh (Ctrl+Shift+R).

## Next Phase Readiness

- Card v0.5.2 is live and verified on the QNAP HA instance
- Phase 5 all plans (05-01 through 05-06) complete
- UAT re-test should now pass all 4 previously-failing checks: card height, container query layout, status indicator flip, and auto-detect detect-first fallback
- Pending Todos from STATE.md: UAT re-test after 05-06 confirms all 16 requirements met

---
*Phase: 05-auto-detect-card-polish*
*Completed: 2026-02-22*
