# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Local, privacy-respecting text translation via self-hosted LibreTranslate — no cloud, no API limits
**Current focus:** v1.1 Enhancement — deploy validation complete, bug fixes + remaining phases

## Current Position

Phase: 4+ (Deploy Validation — COMPLETE)
Status: Full end-to-end deployment verified on real HA hardware — config flow, entities, translate service, Lovelace card all working
Last activity: 2026-02-21 — Deploy validation passed, bug discovered during testing

Progress: [████░░░░░░] 45% (v1.1 phases 4-6)

## Deploy Validation Session (2026-02-21) — COMPLETE

### Verified Working
- Files rsync to QNAP HA Docker container successfully
- HA recognizes the custom integration (shows in Add Integration list)
- Config flow: loads, validates connection, retains values on error, descriptive error messages
- Integration entry created successfully with optional Name (default "LibreTranslate")
- Coordinator fetches 22 languages from LibreTranslate in ~3ms
- Both platforms forward successfully (sensor + binary_sensor)
- `binary_sensor.libretranslate_status` shows "on" (connected)
- `sensor.libretranslate_language_count` shows 22 languages (enabled by default)
- **Translate service works end-to-end** via Developer Tools > Actions (en->es confirmed)
- **Lovelace card works end-to-end** — dropdowns populated, swap button, translation confirmed on dashboard
- Card auto-detects entities during setup
- Card fits properly in dashboard grid (overflow fixed)

### All Changes Made During Session
1. **config_flow.py**: Name optional (default "LibreTranslate"), Port defaults to 5000, form retains values on error
2. **api.py**: Replaced `raise_for_status()` with explicit HTTP status check
3. **strings.json + translations/en.json**: Descriptive error messages
4. **__init__.py**: Debug logging in `async_setup_entry`
5. **test_coordinator.py**: Fixed `test_coordinator_update_failed` assertion
6. **sensor.py**: Language count sensor enabled by default (card requires it)
7. **test_sensor.py**: Updated test for enabled-by-default
8. **argos_translate-card.js v0.3.1**: Entity auto-detect matches "libretranslate" IDs, card size increased (7 rows), overflow contained, textareas 3 rows

### Environment
- HA: Docker container on QNAP NAS (192.168.50.250:8123)
- LibreTranslate: Docker container on same QNAP, port 5500 (internal 5000)
- Dev machine: WSL2, rsync push to QNAP
- Debug logging enabled in configuration.yaml: `custom_components.argos_translate: debug`

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

- Bug found during testing — details TBD

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-21
Stopped at: Deploy validation complete, bug discovered during live testing
Resume action: Fix reported bug, then proceed to Phase 5 (Auto-Detect + Card Polish) or Phase 6 (Deploy Stabilization)
