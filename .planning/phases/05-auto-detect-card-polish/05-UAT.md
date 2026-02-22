---
status: complete
phase: 05-auto-detect-card-polish
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md]
started: 2026-02-22T09:00:00Z
updated: 2026-02-22T09:30:00Z
re_test: true
previous_session: "2026-02-22T06:30:00Z — 5 passed, 5 issues, 1 skipped"
---

## Current Test

[testing complete]

## Tests

### 1. Swap blocks invalid reversed pair
expected: With a specific source language selected (e.g., English), select a target language whose reverse pair is NOT installed. Click swap. An error message appears saying the reversed pair is not installed. Source and target dropdowns remain unchanged (no silent degradation).
result: pass

### 2. Status indicator goes offline on server failure
expected: Stop or disconnect the LibreTranslate server, then attempt a translation. The error message shows the connection failure AND the status indicator (binary_sensor) turns to offline/red immediately — not after waiting for the 5-minute poll cycle. (Reload integration or check Developer Tools > States for binary_sensor.libretranslate_status = off)
result: issue
reported: "Server stopped, 'cannot connect' error shows correctly, but green status indicator stays green the whole time. Integration was reloaded before testing."
severity: major

### 3. Container query horizontal layout
expected: Place the card in a wide dashboard column (>= 580px card width). The input and output textareas display side-by-side (horizontal). On a narrow column (< 580px), they stack vertically. The container query now fires correctly inside the shadow DOM.
result: issue
reported: "Still stays vertical when in auto mode — container query still not switching to horizontal layout"
severity: major

### 4. Card height fits content
expected: Card fits its content area without extending into the "new section" territory below. Grid sizing is 5 rows (reduced from 7). Card height is appropriate for the content — no excessive empty space below.
result: issue
reported: "Card definitely does not fit, might be worse than before"
severity: minor

### 5. Textarea resize disabled
expected: Textareas no longer have drag handles for resizing. The resize cursor does not appear when hovering over textarea edges. Content stays contained within the card boundary.
result: pass

### 6. Regression: Auto-detect translation still works
expected: Card loads with "Auto-detect" selected. Type foreign language text, select target, click Translate. Output shows translation with "Detected: [Language] ([confidence]%)" below.
result: issue
reported: "Auto-detect works when pair is valid (fr→fr), but fails with HTTP 400 when detected language can't translate to selected target (fr→en). Should detect and show result even when translation pair is unavailable."
severity: minor

### 7. Regression: Error messages still specific
expected: Error messages are specific (e.g., "HTTP 400: Bad Request", "Cannot connect to LibreTranslate server") — not generic "Translation failed".
result: pass

## Summary

total: 7
passed: 3
issues: 4
pending: 0
skipped: 0

## Gaps

- truth: "Status indicator updates to offline when server is unreachable"
  status: failed
  reason: "User reported: Server stopped, 'cannot connect' error shows correctly, but green status indicator stays green the whole time. Integration was reloaded before testing."
  severity: major
  test: 2
  artifacts:
    - path: "custom_components/argos_translate/services.py"
      issue: "async_request_refresh() added in CannotConnectError handlers but status indicator still doesn't update"
  missing: []
  debug_session: ""
- truth: "Card auto-switches to horizontal layout at >= 580px card width via CSS container queries"
  status: failed
  reason: "User reported: Still stays vertical when in auto mode — container query still not switching to horizontal layout"
  severity: major
  test: 3
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "container-type moved from :host to .card-content but container query still not firing"
  missing: []
  debug_session: ""
- truth: "Card height fits content without overflowing into new section area"
  status: failed
  reason: "User reported: Card definitely does not fit, might be worse than before"
  severity: minor
  test: 4
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "getGridOptions rows reduced to 5 but card still overflows"
  missing: []
  debug_session: ""
- truth: "Auto-detect shows detected language even when translation pair is unavailable"
  status: failed
  reason: "User reported: Auto-detect works when pair is valid (fr→fr), but fails with HTTP 400 when detected language can't translate to selected target (fr→en). Should detect and show result even when translation pair is unavailable."
  severity: minor
  test: 6
  artifacts:
    - path: "custom_components/argos_translate/services.py"
      issue: "Auto-detect uses single /translate call with source=auto — fails entirely if pair is invalid"
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "No detect-first fallback when translate with auto fails"
  missing:
    - "Detect language first via /detect, show result, then attempt translation"
    - "Parse HTTP 400 response body for more descriptive error message"
  debug_session: ""
