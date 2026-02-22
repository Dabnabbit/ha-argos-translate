# Phase 5: Auto-Detect + Card Polish - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can translate without selecting a source language (auto-detect), see the detected language in the card, and interact with an accessible, mobile-friendly card with specific error messages. This phase covers: auto-detect service support, detection feedback in the card UI, specific error/disabled state messaging, ARIA labels, and responsive layout with vertical/horizontal modes.

</domain>

<decisions>
## Implementation Decisions

### Detection feedback display
- After auto-detect translation, the source dropdown label updates from "Auto-detect" to show the detected language (e.g., "Auto (French)")
- Detection results include candidate languages above a confidence threshold, shown as options in the source dropdown (e.g., "Auto (French)", "Auto (Spanish)")
- Selecting a detected candidate re-translates using that language as a fixed source — lets users correct a bad detection
- Dropdown label auto-updates immediately after translation completes (no need to open dropdown to see result)

### Auto-detect dropdown behavior
- "Auto-detect" appears as the first item in the source dropdown, visually separated from the alphabetical language list
- "Auto-detect" is the default source selection when the card first loads
- When source is "Auto-detect", the target dropdown shows all available languages (not filtered by source)

### Mobile layout & responsive behavior
- Card supports both vertical (stacked) and horizontal (side-by-side like Google Translate) layouts
- Default behavior is auto-responsive: wide cards show horizontal layout (input left, output right), narrow cards stack vertically
- Card config provides a layout override: user can force "Horizontal", "Vertical", or "Auto" (default)
- Language row (dropdowns + swap button) wraps cleanly at narrow widths

### Accessibility
- ARIA labels on all form controls are sufficient — no additional keyboard navigation or high contrast requirements beyond standard HA card behavior

### Claude's Discretion
- Error message presentation style (inline, banner, or below output) — pick what fits HA card conventions
- Disabled button explanation approach (tooltip vs helper text) — pick what works on both desktop and mobile
- Error auto-dismiss behavior (timed vs persistent)
- Error visual treatment (uniform style vs severity-based colors)
- Whether to show an indication that target filtering is off when source is Auto-detect
- Message wording for uninstalled detected language case

</decisions>

<specifics>
## Specific Ideas

- Detection candidates in dropdown: user envisions detected languages appearing in the source dropdown prepended with "Auto-" (e.g., "Auto (French)", "Auto (Spanish)") so auto-detect results are immediately visible
- Horizontal layout reference: "like Google Translate" for wide cards — input on left, output on right, language dropdowns above each panel
- The responsive breakpoint should be smart about HA dashboard panel widths, which vary a lot based on user dashboard configuration

</specifics>

<deferred>
## Deferred Ideas

- Dropdown usage history — frequently/recently used languages migrate toward the top of language dropdowns (requires persistent storage, separate feature)

</deferred>

---

*Phase: 05-auto-detect-card-polish*
*Context gathered: 2026-02-21*
