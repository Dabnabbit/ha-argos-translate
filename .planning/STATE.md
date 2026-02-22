# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Local, privacy-respecting text translation via self-hosted LibreTranslate — no cloud, no API limits
**Current focus:** v1.1 Enhancement — deploy validation complete, ready for Phase 5

## Current Position

Phase: 5 (Auto-Detect + Card Polish — CONTEXT GATHERED)
Status: Phase 5 context captured. Ready for research and planning.
Last activity: 2026-02-21 — Phase 5 discuss-phase complete

Progress: [█████░░░░░] 50% (v1.1 phases 4-6)

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

## Accumulated Context

### Decisions

All architectural decisions logged in PROJECT.md Key Decisions table.

**v1.1 specific:**
- Options flow uses explicit `async_reload` (not `OptionsFlowWithReload`) for HA 2025.7+ compatibility
- Options flow reload pattern: async_update_entry -> await async_reload(entry_id) -> async_create_entry(data={})
- No rollback logic on post-reload failure: HA default behavior (integration shows failed) is acceptable
- Auto-detect uses `source="auto"` pass-through to LibreTranslate `/translate`; no separate `/detect` call needed
- Confidence threshold of 50.0 applied before surfacing detection results; value logged for tuning
- Card JS version bump strategy: append `?v=VERSION` query param to Lovelace resource URL on each card change
- LibreTranslate has no network discovery (no mDNS/Zeroconf/SSDP) — config flow requires manual host entry
- Entity IDs use device name ("libretranslate") not integration domain ("argos_translate") — card search must match both
- JS-only changes don't need HA restart — just rsync + browser hard refresh (Ctrl+Shift+R)

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-21
Stopped at: Phase 5 context gathered — detection feedback, error states, dropdown behavior, responsive layout decisions captured
Resume action: Run `/gsd:plan-phase 5` to plan Auto-Detect + Card Polish phase
Resume file: .planning/phases/05-auto-detect-card-polish/05-CONTEXT.md
