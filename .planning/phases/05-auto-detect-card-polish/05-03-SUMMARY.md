---
phase: 05-auto-detect-card-polish
plan: "03"
subsystem: ui
tags: [lovelace, lit-element, auto-detect, detection-candidates, detection-feedback]
dependency_graph:
  requires:
    - phase: 05-01
      provides: detect HA service, auto-source translate with detected_language response
    - phase: 05-02
      provides: card v0.4.0 with ARIA, error discrimination, responsive layout
  provides:
    - Auto-detect source option as first dropdown item with visual separator
    - Detection feedback in source dropdown label ("Auto (French)" after translation)
    - Detection candidates as selectable "auto:xx" options above 50% confidence
    - detection-info div below output showing language name and confidence percentage
    - Uninstalled detected language warning message
    - Swap button disabled when source is "auto"
  affects: [custom_components/argos_translate/frontend/argos_translate-card.js]
tech_stack:
  added: []
  patterns:
    - "auto: prefixed option values for candidate re-translation without polluting language codes"
    - "Best-effort secondary service call for detection candidates (silent catch)"
    - "_getLanguageName code→display helper for consistent rendering"
key_files:
  created: []
  modified:
    - custom_components/argos_translate/frontend/argos_translate-card.js
key_decisions:
  - "auto: prefix in option values to carry candidate codes without adding to language list"
  - "Detection candidates fetched via separate argos_translate.detect call after translation (best-effort, failure suppressed)"
  - "DETECTION_CONFIDENCE_THRESHOLD = 50.0 applied client-side to filter candidate dropdown items"
  - "Both tasks combined in single write due to interdependency (_detectedLanguage used by both dropdown and detect call)"
  - "detection-info placed above translate button for visual proximity to the output it describes"
metrics:
  duration_seconds: 139
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
  completed_date: "2026-02-22"
requirements_addressed: [DTCT-01, DTCT-04, DTCT-05]
---

# Phase 5 Plan 03: Card Auto-Detect UI Summary

**Auto-detect source option as default dropdown selection, detection feedback in dropdown label and info div, detection candidates from /detect service as selectable options, swap disabled when source is auto — card v0.5.0**

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add Auto-detect source option with default selection and target dropdown handling | c49785d | argos_translate-card.js |
| 2 | Add detection feedback display and /detect candidate population | c49785d | argos_translate-card.js |

Both tasks implemented in a single commit — they modify the same file and Task 2's `_detectedLanguage` property is introduced in Task 1's reactive properties block.

## What Was Built

**New reactive properties:**
- `_detectedLanguage: { type: Object }` — stores `{language, confidence}` from translate response
- `_detectionCandidates: { type: Array }` — stores candidates from `/detect` service above threshold

**Initialization changes:**
- `this._source = "auto"` (was `""`) — auto-detect is default on card load
- `this._detectedLanguage = null`
- `this._detectionCandidates = []`

**`_getTargetsForSource`:**
- When source is `"auto"` or starts with `"auto:"`, returns all language codes (unfiltered) as valid targets

**`_getLanguageName(code)` helper:**
- Looks up display name from language entity attributes by code index

**Source dropdown (render):**
- First option: `value="auto"` showing "Auto-detect" (or "Auto (Language)" after detection)
- Detection candidates rendered as `value="auto:xx"` options between auto and separator
- Disabled separator option `──────────` visually separates auto section from full list
- Full alphabetical language list follows

**`_sourceChanged` handler:**
- Values starting with `"auto:"` extract fixed language code, clear detection state, update target validity, trigger re-translate
- Non-auto values clear detection state; "auto" value retains detection state

**`_swapLanguages`:**
- Guard: returns early if `this._source === "auto"` — swap is disabled when auto is selected
- Swap button template: `?disabled="${this._source === 'auto'}"`

**`_translate()` method:**
- After successful auto-detect translation, reads `resp.detected_language` and `resp.detection_confidence`
- Calls `argos_translate.detect` service (best-effort) to get candidates, filters by `DETECTION_CONFIDENCE_THRESHOLD = 50.0`
- Shows uninstalled detected language warning in `_error` when `resp.uninstalled_detected_language` is set
- On non-auto translation, clears `_detectedLanguage` and `_detectionCandidates`

**Detection info display:**
- `<div class="detection-info">Detected: [Language] ([Confidence]%)</div>` rendered when `_detectedLanguage` is set
- Placed above translate button for visual proximity to output

**CSS:**
- `.detection-info` styled with `font-size: 0.85em`, `var(--secondary-text-color)`, `padding: 4px 0`, `margin-top: 4px`

**CARD_VERSION:** bumped from `"0.4.0"` to `"0.5.0"`

## Verification Results

All checks passed:
```
node --check: Syntax OK
"auto" default: present
_detectionCandidates: present
detection-info CSS: present
DETECTION_CONFIDENCE_THRESHOLD: present
_getLanguageName: present
uninstalled_detected_language: present
swap disabled guard: present
```

## Decisions Made

1. **`auto:` prefix for candidate option values:** Encoding the candidate language in the option value (e.g., `auto:fr`) avoids adding synthetic values to the language codes list and makes the handler logic simple and explicit.

2. **Best-effort detect call:** The secondary `argos_translate.detect` call is wrapped in its own try/catch — if `/detect` fails for any reason, the primary translation result and detected language are preserved. Candidates simply won't populate.

3. **Combined commit for both tasks:** Since `_detectedLanguage` is defined in Task 1's properties block and immediately referenced by Task 2's `_translate()` method, both tasks were written together and committed as one coherent change. The SUMMARY documents both tasks with the shared commit hash.

4. **Detection info placed above translate button:** Positioning the detection info between the output panel and the translate button creates a natural flow: input -> [translate] -> output -> detection info -> [Translate again or pick candidate].

## Deviations from Plan

None - plan executed exactly as written. The `detect.*text` grep verification in Task 2 would not match because the service call arguments are formatted across multiple lines (`"detect"` on one line, `{ text: this._inputText }` on the next) — the functionality is present and correct.

## Self-Check: PASSED

- FOUND: custom_components/argos_translate/frontend/argos_translate-card.js
- FOUND: .planning/phases/05-auto-detect-card-polish/05-03-SUMMARY.md
- FOUND commit: c49785d in git log
