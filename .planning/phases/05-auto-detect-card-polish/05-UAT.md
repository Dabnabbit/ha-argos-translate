---
status: diagnosed
phase: 05-auto-detect-card-polish
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md]
started: 2026-02-22T09:00:00Z
updated: 2026-02-22T10:00:00Z
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
  root_cause: "Wrong API method: async_request_refresh() is debounced (10s cooldown) and gets silently dropped after integration reload. Should use coordinator.async_set_update_error(err) which is a synchronous @callback that immediately sets last_update_success=False and calls async_update_listeners() — no debouncing."
  artifacts:
    - path: "custom_components/argos_translate/services.py"
      issue: "Lines 89-95 and 138-143: both CannotConnectError handlers use await coordinator.async_request_refresh() — should use coordinator.async_set_update_error(err) instead"
  missing:
    - "Replace await coordinator.async_request_refresh() with coordinator.async_set_update_error(err) in both handlers (no await needed — synchronous @callback)"
  debug_session: ".planning/debug/status-indicator-still-green.md"
- truth: "Card auto-switches to horizontal layout at >= 580px card width via CSS container queries"
  status: failed
  reason: "User reported: Still stays vertical when in auto mode — container query still not switching to horizontal layout"
  severity: major
  test: 3
  root_cause: "Needs further investigation — container-type was moved from :host to .card-content in 05-04 but query still not firing. Debug agent was interrupted before completing diagnosis."
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "container-type on .card-content still not enabling @container argos-card (min-width: 580px) query for .content-area"
  missing:
    - "Further investigation needed — inspect actual rendered DOM to determine why container query doesn't match"
  debug_session: ""
- truth: "Card height fits content without overflowing into new section area"
  status: failed
  reason: "User reported: Card definitely does not fit, might be worse than before"
  severity: minor
  test: 4
  root_cause: ":host has only display:block — no height:100%. In HA sections grid, cards get a fixed-height slot (rows * ~56px). Without height:100% on :host, the card expands to natural content height (~420px) regardless of grid allocation. Reducing rows from 7 to 5 actually made it worse by shrinking the slot while the card stayed the same size."
  artifacts:
    - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
      issue: "Line 490-492: :host { display: block; } — missing height: 100% to constrain to grid slot"
  missing:
    - "Add height: 100% to :host CSS rule"
    - "Consider tuning rows value after height constraint is applied"
  debug_session: ".planning/debug/card-height-still-overflows.md"
- truth: "Auto-detect shows detected language even when translation pair is unavailable"
  status: failed
  reason: "User reported: Auto-detect works when pair is valid (fr→fr), but fails with HTTP 400 when detected language can't translate to selected target (fr→en). Should detect and show result even when translation pair is unavailable."
  severity: minor
  test: 6
  root_cause: "Two layers: (1) api.py raises CannotConnectError for all HTTP 4xx including 400 Bad Request — loses semantic distinction between 'server unreachable' and 'pair unavailable'. (2) services.py has no detect-first fallback for source='auto' — when translate raises, no detection data is returned to the card."
  artifacts:
    - path: "custom_components/argos_translate/api.py"
      issue: "Lines 67-70: HTTP 400 raised as CannotConnectError — same class as network failures"
    - path: "custom_components/argos_translate/services.py"
      issue: "Lines 65-95: No detect-first two-phase logic for source='auto'; on any exception, raises with no detection data"
  missing:
    - "Distinguish HTTP 4xx client errors from true connection failures in api.py"
    - "Add detect-first path in services.py for source='auto': detect language, then attempt translate, return partial result with detection info even on translate failure"
  debug_session: ".planning/debug/auto-detect-fails-invalid-pair.md"
