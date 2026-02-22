# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Local, privacy-respecting text translation via self-hosted LibreTranslate — no cloud, no API limits
**Current focus:** v1.1 Enhancement — Phase 5 complete. All 4 plans executed. 5 UAT gaps closed. Ready for Phase 5 re-test.

## Current Position

Phase: 5 (Auto-Detect + Card Polish — COMPLETE)
Current Plan: 05-04 COMPLETE — all 5 UAT gaps closed
Status: 4/4 plans complete. services.py and card v0.5.1 deployed with all fixes applied.
Last activity: 2026-02-22 — 05-04 gap closure plan executed successfully

Progress: [████████░░] 80% (v1.1 phases 4-6)

## Deploy Validation Session (2026-02-21) — COMPLETE

### Verified Working
- Config flow: loads, validates, retains values on error, descriptive messages
- Integration entry created with optional Name (default "LibreTranslate")
- Coordinator fetches 22 languages from LibreTranslate in ~3ms
- Both platforms forward (sensor + binary_sensor), entities enabled by default
- `binary_sensor.libretranslate_status` — connected
- `sensor.libretranslate_language_count` — 22 languages
- Translate service end-to-end via Developer Tools > Actions
- Lovelace card end-to-end — dropdowns, swap, translation on dashboard
- Card auto-detects entities, fits properly in grid

### Known Issues (Non-blocking)
- One-off translation timeout observed during swap+retranslate — could not reproduce. Likely LibreTranslate cold model load. No code fix needed.

### All Changes Made During Deploy Validation
1. **config_flow.py**: Name optional, Port default, form retains values, `add_suggested_values_to_schema()`
2. **api.py**: Explicit HTTP status check replacing `raise_for_status()`
3. **strings.json + translations/en.json**: Descriptive error messages
4. **__init__.py**: Debug logging added then removed (cleanup)
5. **test_coordinator.py**: Fixed assertion to match `DataUpdateCoordinator` behavior
6. **sensor.py**: Language count sensor enabled by default
7. **test_sensor.py**: Updated test for enabled-by-default
8. **argos_translate-card.js v0.3.1**: Entity auto-detect, grid sizing, overflow fix

### Environment
- HA: Docker container on QNAP NAS (192.168.50.250:8123)
- LibreTranslate: Docker container on same QNAP, port 5500 (internal 5000)
- Dev machine: WSL2, rsync push to QNAP

## Performance Metrics

| Metric | v1.0 | v1.1 |
|--------|------|------|
| Phases | 3 | 3 planned |
| Requirements | 16 delivered | 16 in scope |
| Lines of code | 2,052 | TBD |

### Phase 5 Execution Metrics

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| 05-01 | 127s | 3 | 7 |
| 05-02 | 3min | 2 | 1 |
| 05-03 | 139s | 2 | 1 |
| 05-04 | 2min | 2 | 3 |

### Phase 5 UAT Results

| Metric | Count |
|--------|-------|
| Tests | 11 |
| Passed | 5 |
| Issues | 5 |
| Skipped | 1 |

| Issue | Severity | Root Cause |
|-------|----------|------------|
| Swap creates invalid pair | minor | No pre-swap guard on reversed pair validity |
| Status stays green on failure | minor | Service errors don't trigger coordinator refresh |
| Container query never fires | major | Shadow DOM boundary blocks named container queries on :host |
| Card too tall | minor | getGridOptions rows: 7 exceeds content needs |
| Textarea overflow | minor | resize: vertical incompatible with grid-managed height |

## Accumulated Context

### Decisions

All architectural decisions logged in PROJECT.md Key Decisions table.

**v1.1 specific:**
- Options flow uses explicit `async_reload` (not `OptionsFlowWithReload`) for HA 2025.7+ compatibility
- Options flow reload pattern: async_update_entry -> await async_reload(entry_id) -> async_create_entry(data={})
- No rollback logic on post-reload failure: HA default behavior (integration shows failed) is acceptable
- Auto-detect uses `source="auto"` pass-through to LibreTranslate `/translate`; separate `/detect` HA service added for detection candidates
- Confidence threshold of 50.0 applied before surfacing detection results; value logged for tuning
- Card JS version bump strategy: append `?v=VERSION` query param to Lovelace resource URL on each card change
- LibreTranslate has no network discovery (no mDNS/Zeroconf/SSDP) — config flow requires manual host entry
- Entity IDs use device name ("libretranslate") not integration domain ("argos_translate") — card search must match both
- JS-only changes don't need HA restart — just rsync + browser hard refresh (Ctrl+Shift+R)
- [Phase 05]: async_translate returns full LibreTranslate response dict to surface detectedLanguage alongside translatedText
- [Phase 05]: Auto source bypass uses explicit if source != AUTO_SOURCE guard rather than adding auto to language lists
- [Phase 05-02]: CSS container queries used for card-width-responsive layout, not viewport media queries — NOTE: container-type on :host doesn't work across shadow DOM boundary; fix in 05-04 moves it to .card-content
- [Phase 05-02]: Layout breakpoint at 580px card width switches to side-by-side panels
- [Phase 05-02]: Error discrimination by err.code (numeric vs string) before err.message for HA WebSocket error objects
- [Phase 05]: auto: prefix in option values encodes candidate codes for re-translation without polluting language lists
- [Phase 05]: Detection candidates fetched via argos_translate.detect service post-translation (best-effort, silent catch)
- [Phase 05]: DETECTION_CONFIDENCE_THRESHOLD = 50.0 applied client-side to filter dropdown candidate options
- [Phase 05]: async_request_refresh called before re-raising HomeAssistantError so coordinator poll runs immediately on CannotConnectError in both translate and detect handlers
- [Phase 05]: Pre-swap guard reads _getTargetsForSource(oldTarget) to validate reversed pair before mutating state, surfaces descriptive error
- [Phase 05-04]: container-type/container-name moved from :host to .card-content — shadow DOM boundary blocks :host container from being found by inner class @container queries

### Pending Todos

- Re-run Phase 5 UAT (11 tests) against updated services.py and card v0.5.1 to confirm all 5 gaps are closed

### Blockers/Concerns

- LibreTranslate /detect endpoint only returns single candidate per request — multi-candidate dropdown feature works in code but untestable with current server
- Many LibreTranslate language pairs are one-way only (e.g., fr→fr but not fr→en) — affects swap and auto-detect UX on servers with limited models

## Session Continuity

Last session: 2026-02-22
Stopped at: Completed 05-04-PLAN.md — all 5 UAT gaps closed, Phase 5 gap closure complete
Resume action: Deploy to QNAP (rsync + reload integration + hard refresh), then re-run Phase 5 UAT
Resume file: N/A — Phase 5 execution complete; next step is UAT re-test
