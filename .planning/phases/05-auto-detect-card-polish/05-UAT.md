---
status: diagnosed
phase: 05-auto-detect-card-polish
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md]
started: 2026-02-22T06:30:00Z
updated: 2026-02-22T07:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Auto-detect default and translation
expected: Card loads with "Auto-detect" selected in the source dropdown (first item, separated from language list). Type text in a known foreign language (e.g., "Bonjour le monde"), select a target language, and click Translate. Output shows translated text. Below the output, a detection info line appears: "Detected: [Language] ([confidence]%)".
result: pass

### 2. Source dropdown detection feedback
expected: After an auto-detect translation, the source dropdown label updates from "Auto-detect" to "Auto ([Detected Language])" (e.g., "Auto (French)"). Opening the dropdown shows detection candidate languages as additional "Auto ([Language])" options between the primary auto option and the separator line.
result: pass

### 3. Candidate selection re-translates
expected: After auto-detect translation populates candidates, select a different detection candidate from the source dropdown (one of the "Auto ([Language])" options). The card re-translates using that specific language as a fixed source. Source dropdown updates to show the selected language as a regular (non-auto) selection.
result: skipped
reason: LibreTranslate /detect endpoint only returns a single candidate per request — multiple candidates never populate in the dropdown. Feature works in code but untestable with this server.

### 4. Target dropdown unfiltered for auto-detect
expected: When source is "Auto-detect", the target dropdown shows ALL available languages (not filtered by source language pairs). Switching source to a specific language (e.g., English) may reduce the target list to only valid pairs for that source.
result: pass

### 5. Swap button disabled for auto-detect
expected: When source is "Auto-detect", the swap languages button appears disabled and clicking it does nothing. When a specific source language is selected, the swap button becomes active again.
result: issue
reported: "swapping languages left->right causes an issue when the reversed pair doesn't exist (e.g., English->French swaps to French->English but fr->en is not installed). Both sides show French after swap since fr only targets fr."
severity: minor

### 6. Error discrimination
expected: Stop or disconnect the LibreTranslate server, then attempt a translation. The error message should say something specific like "Cannot connect to LibreTranslate server. Check that it is running." instead of the old generic "Translation failed".
result: issue
reported: "correct error message shows, however status indicator still shows as Online (green circle) when server is unreachable"
severity: minor

### 7. Disabled button hint text
expected: With no text entered, the Translate button is disabled and a hint below it says "Enter text to translate". If the server is offline, the hint says "LibreTranslate server is offline". Each disabled condition shows an appropriate reason.
result: pass

### 8. Responsive layout
expected: On a narrow card (< 580px width), input and output textareas stack vertically. On a wide card (>= 580px), they display side-by-side (input left, output right). In the card editor, a Layout dropdown offers "Auto (responsive)", "Horizontal", and "Vertical" — selecting one forces that layout regardless of card width.
result: issue
reported: "input and output boxes never go horizontal automatically, always stacked. Language selectors DO respond to width. Manual layout override (Horizontal/Vertical) works correctly."
severity: major

### 9. ARIA accessibility labels
expected: Inspecting the card's DOM (browser DevTools), all interactive controls have aria-label attributes: source select ("Source language"), target select ("Target language"), input textarea ("Text to translate"), output textarea ("Translated text"), swap button ("Swap languages").
result: pass

### 10. Card height containment
expected: Card fits its content without extending into the "new section" area below. Grid sizing and card height are appropriate for the content.
result: issue
reported: "Card extends too far down into the 'new section' territory below the card content area"
severity: minor

### 11. Textarea resize containment
expected: If textareas are resizable, the card container grows to contain them. Or textareas should not be resizable beyond the card boundary.
result: issue
reported: "Individual text input boxes can be resized via drag handle, but the actual card doesn't resize to contain them — content overflows"
severity: minor

## Summary

total: 11
passed: 5
issues: 5
pending: 0
skipped: 1

## Gaps

- truth: "Swap validates that reversed language pair exists before completing"
  status: failed
  reason: "User reported: swapping languages left->right causes an issue when the reversed pair doesn't exist (e.g., English->French swaps to French->English but fr->en is not installed). Both sides show French after swap since fr only targets fr."
  severity: minor
  test: 5
  root_cause: "_swapLanguages commits swap unconditionally then validates after — too late. Post-swap target fallback silently degrades to only valid target."
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "_swapLanguages lines 199-219 — no pre-swap guard checking if reversed pair exists"
  missing:
    - "Pre-swap check: verify target has source in its targets list before committing swap"
    - "Show error message or disable swap button when reversed pair is invalid"
  debug_session: ".planning/debug/swap-languages-invalid-pair.md"
- truth: "Status indicator updates to offline when server is unreachable"
  status: failed
  reason: "User reported: correct error message shows, however status indicator still shows as Online (green circle) when server is unreachable"
  severity: minor
  test: 6
  root_cause: "Service call failures and status indicator use separate code paths. CannotConnectError in service call never touches coordinator.last_update_success — status only updates on 5-min poll cycle."
  artifacts:
    - path: "custom_components/argos_translate/services.py"
      issue: "Lines 87-92 — catch block re-raises error but doesn't trigger coordinator refresh"
    - path: "custom_components/argos_translate/coordinator.py"
      issue: "last_update_success only set by _async_update_data poll, not by service call failures"
  missing:
    - "Call coordinator.async_request_refresh() after catching CannotConnectError in translate and detect service handlers"
  debug_session: ".planning/debug/status-indicator-not-updating-on-failure.md"
- truth: "Card auto-switches to horizontal layout at >= 580px card width via CSS container queries"
  status: failed
  reason: "User reported: input and output boxes never go horizontal automatically, always stacked. Language selectors DO respond to width. Manual layout override (Horizontal/Vertical) works correctly."
  severity: major
  test: 8
  root_cause: "container-name on :host crosses a shadow DOM boundary to reach .content-area — browsers cannot traverse named container queries across shadow boundaries. Known browser limitation (WebKit bug 267793, W3C csswg-drafts #5984)."
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "Lines 484-488 — container-type/container-name on :host; line 578 — @container rule can't find named container across shadow boundary"
  missing:
    - "Move container-type and container-name from :host to .card-content (direct shadow DOM ancestor of .content-area, no boundary crossing)"
  debug_session: ".planning/debug/container-query-not-triggering.md"
- truth: "Card height fits content without overflowing into new section area"
  status: failed
  reason: "User reported: Card extends too far down into the 'new section' territory below the card content area"
  severity: minor
  test: 10
  root_cause: "getGridOptions() requests rows: 7 and min_rows: 5 — more grid space than content needs. Card stretches to fill allocated space."
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "Lines 87-98 — getCardSize returns 7, getGridOptions rows: 7, min_rows: 5"
  missing:
    - "Reduce rows to 5 and min_rows to 4; update getCardSize to match"
  debug_session: ""
- truth: "Textarea resize is contained within the card or disabled"
  status: failed
  reason: "User reported: Individual text input boxes can be resized via drag handle, but the actual card doesn't resize to contain them — content overflows"
  severity: minor
  test: 11
  root_cause: "resize: vertical on textareas allows user drag beyond card bounds. Lovelace cards have grid-managed height; user-resizable textareas are incompatible."
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "Line 563 — resize: vertical on textarea CSS"
  missing:
    - "Change resize: vertical to resize: none"
  debug_session: ""
