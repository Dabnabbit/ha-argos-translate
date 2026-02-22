---
status: complete
phase: 05-auto-detect-card-polish
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md]
started: 2026-02-22T06:30:00Z
updated: 2026-02-22T07:15:00Z
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

## Summary

total: 9
passed: 5
issues: 3
pending: 0
skipped: 1

## Gaps

- truth: "Swap validates that reversed language pair exists before completing"
  status: failed
  reason: "User reported: swapping languages left->right causes an issue when the reversed pair doesn't exist (e.g., English->French swaps to French->English but fr->en is not installed). Both sides show French after swap since fr only targets fr."
  severity: minor
  test: 5
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
- truth: "Status indicator updates to offline when server is unreachable"
  status: failed
  reason: "User reported: correct error message shows, however status indicator still shows as Online (green circle) when server is unreachable"
  severity: minor
  test: 6
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
- truth: "Card auto-switches to horizontal layout at >= 580px card width via CSS container queries"
  status: failed
  reason: "User reported: input and output boxes never go horizontal automatically, always stacked. Language selectors DO respond to width. Manual layout override (Horizontal/Vertical) works correctly."
  severity: major
  test: 8
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
