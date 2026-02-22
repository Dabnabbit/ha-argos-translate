# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Local, privacy-respecting text translation via self-hosted LibreTranslate — no cloud, no API limits
**Current focus:** v1.1 Enhancement — deploy validation, auto-detect language, card polish

## Current Position

Phase: 4+ (Deploy Validation — in progress, ad-hoc)
Status: Integration deployed to real HA, entities working, translate service confirmed end-to-end, card auto-config fix pending deploy test
Last activity: 2026-02-21 — Live deployment testing on QNAP HA Docker

Progress: [████░░░░░░] 40% (v1.1 phases 4-6)

## Deploy Validation Session (2026-02-21)

### What Works
- Files rsync to QNAP HA Docker container successfully
- HA recognizes the custom integration (shows in Add Integration list)
- Config flow loads, validates connection to LibreTranslate on QNAP:5500
- Integration entry is created successfully
- `curl` from inside HA container to LibreTranslate returns valid language data
- LibreTranslate server is healthy with 22 language pairs
- **Coordinator fetches language data** (22 languages, 0.003s)
- **Both platforms forward successfully** (sensor + binary_sensor)
- **binary_sensor.libretranslate_status** shows "on" (connected)
- **sensor.libretranslate_language_count** shows 22 languages
- **Translate service works end-to-end** via Developer Tools > Actions
- **Lovelace card appears** in card picker

### What Was Fixed
- Entity search in States: entities named `libretranslate_*` not `argos_*` — user needs to search "libretranslate"
- Language count sensor was disabled by default, blocking card setup — now enabled by default
- Card `getStubConfig` searched for "argos_translate" in entity IDs but they're named "libretranslate" — fixed to match both patterns

### Changes Made During Session
1. **config_flow.py**: Name field optional (default "LibreTranslate"), Port defaults to 5000, form retains values on error via `add_suggested_values_to_schema()`
2. **api.py**: Replaced `raise_for_status()` with explicit `status >= 400` check wrapped in `CannotConnectError`
3. **strings.json + translations/en.json**: Error messages made more descriptive
4. **__init__.py**: Added debug logging to `async_setup_entry`
5. **test_coordinator.py**: Fixed `test_coordinator_update_failed` assertion
6. **sensor.py**: Removed `_attr_entity_registry_enabled_default = False` — card needs this entity
7. **argos_translate-card.js**: `getStubConfig` now matches both "libretranslate" and "argos_translate" entity patterns; version bumped to 0.3.0
8. **test_sensor.py**: Updated test to assert sensor enabled by default

### Next Steps (Resume Here)
1. Rsync latest code to QNAP, restart HA, clear browser cache (Ctrl+Shift+R)
2. Delete existing integration, re-add
3. Add Lovelace card — verify entities auto-populate in config
4. Test translation via the card UI
5. If card works, deploy validation is essentially complete
6. Remove debug logging from `__init__.py` (cleanup)

### Environment
- HA: Docker container on QNAP NAS (192.168.50.250:8123)
- LibreTranslate: Docker container on same QNAP, port 5500 (internal 5000)
- Connectivity confirmed: `docker exec homeassistant curl http://192.168.50.250:5500/languages` returns valid JSON
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

### Pending Todos

None.

### Blockers/Concerns

None active — entity registration issue resolved (was searching wrong name pattern).

## Session Continuity

Last session: 2026-02-21
Stopped at: Card entity auto-detection fix applied, awaiting rsync + deploy test
Resume action: Rsync to QNAP, restart HA, clear browser cache, test card setup and translation
