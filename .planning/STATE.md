# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Local, privacy-respecting text translation via self-hosted LibreTranslate — no cloud, no API limits
**Current focus:** v1.1 Enhancement — deploy validation, auto-detect language, card polish

## Current Position

Phase: 4+ (Deploy Validation — in progress, ad-hoc)
Status: Integration deploys to real HA hardware, config flow works, but entities not appearing in States
Last activity: 2026-02-21 — Debugging entity registration on live HA instance

Progress: [███░░░░░░░] 33% (v1.1 phases 4-6)

## Deploy Validation Session (2026-02-21)

### What Works
- Files rsync to QNAP HA Docker container successfully
- HA recognizes the custom integration (shows in Add Integration list)
- Config flow loads, validates connection to LibreTranslate on QNAP:5500
- Integration entry is created successfully
- `curl` from inside HA container to LibreTranslate returns valid language data
- LibreTranslate server is healthy with 20+ language pairs

### What's Broken
- **Entities not registering**: After adding integration, only "+1 disabled entity" (language count sensor) shows. No binary sensor (connectivity) visible. No entities appear in Developer Tools > States when searching "argos".
- Root cause unknown — no errors in HA logs related to entity setup

### Changes Made During Session
1. **config_flow.py**: Name field made optional (default "LibreTranslate"), Port defaults to 5000, form retains values on error via `add_suggested_values_to_schema()`
2. **api.py**: Replaced `raise_for_status()` with explicit `status >= 400` check wrapped in `CannotConnectError` — prevents unhandled `ClientResponseError` falling through to "unknown" error
3. **strings.json + translations/en.json**: Error messages made more descriptive (connection, auth, no languages, unknown)
4. **__init__.py**: Added debug logging to `async_setup_entry` (coordinator refresh, platform forwarding)
5. **test_coordinator.py**: Fixed `test_coordinator_update_failed` — was incorrectly expecting `UpdateFailed` raise from `async_refresh()` (coordinator catches it internally)

### Next Steps (Resume Here)
1. Rsync latest code to QNAP, restart HA
2. Enable debug logging: `docker logs homeassistant --since 2m 2>&1 | grep -i -E "argos|forward.*platform"`
3. Check if coordinator first refresh succeeds (look for "Coordinator data:" in logs)
4. Check if platform forwarding completes (look for "Platform setup complete" in logs)
5. If platforms set up but no entities, investigate entity registry
6. Test translate service: Developer Tools > Services > `argos_translate.translate`

### Environment
- HA: Docker container on QNAP NAS (192.168.50.250)
- LibreTranslate: Docker container on same QNAP, port 5500 (internal 5000)
- Connectivity confirmed: `docker exec homeassistant curl http://192.168.50.250:5500/languages` returns valid JSON
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

### Pending Todos

None.

### Blockers/Concerns

- Entity registration issue on live HA needs debugging (debug logging added, awaiting next deploy cycle)

## Session Continuity

Last session: 2026-02-21
Stopped at: Debugging entity registration — debug logging added to async_setup_entry, awaiting rsync + restart + log review
Resume action: Rsync code to QNAP, restart HA, check debug logs for entity setup flow, then test translate service
