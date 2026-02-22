# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Local, privacy-respecting text translation via self-hosted LibreTranslate — no cloud, no API limits
**Current focus:** v1.1 Enhancement — Phase 5 planned, ready for execution

## Current Position

Phase: 5 (Auto-Detect + Card Polish — COMPLETE)
Current Plan: 05-03 complete — all plans done
Status: All 3/3 plans complete. Auto-detect UI (dropdown, feedback, candidates) delivered. Card v0.5.0.
Last activity: 2026-02-22 — 05-03 auto-detect card UI executed

Progress: [██████████] 85% (v1.1 phases 4-6)

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
- [Phase 05-02]: CSS container queries (container-type: inline-size on :host) used for card-width-responsive layout, not viewport media queries
- [Phase 05-02]: Layout breakpoint at 580px card width switches to side-by-side panels
- [Phase 05-02]: Error discrimination by err.code (numeric vs string) before err.message for HA WebSocket error objects
- [Phase 05]: auto: prefix in option values encodes candidate codes for re-translation without polluting language lists
- [Phase 05]: Detection candidates fetched via argos_translate.detect service post-translation (best-effort, silent catch)
- [Phase 05]: DETECTION_CONFIDENCE_THRESHOLD = 50.0 applied client-side to filter dropdown candidate options

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-22
Stopped at: Completed 05-03-PLAN.md — card auto-detect UI (auto-detect dropdown, detection feedback, candidates, card v0.5.0)
Resume action: Phase 5 complete. Run `/gsd:execute-phase 6` for next phase.
Resume file: N/A — Phase 5 all plans complete
