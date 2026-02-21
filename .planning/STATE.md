# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Local, privacy-respecting text translation via self-hosted LibreTranslate — no cloud, no API limits
**Current focus:** Phase 2 context gathered. Ready to plan Phase 2.

## Current Position

Phase: 2 of 3 (Translation Service + Card)
Plan: Not started
Status: Context gathered, ready to plan
Last activity: 2026-02-20 — Phase 2 context captured (translate service + card decisions)

Progress: [█████░░░░░] 50% (Phase 1 of 3 complete)

## What the Template Provides (Already Done)

The ha-hacs-template v1.0 overlay satisfies these requirements out of the box:

- **SCAF-01**: Modern `async_register_static_paths` + `StaticPathConfig` (HA 2025.7+)
- **SCAF-02**: Valid `manifest.json` with correct `iot_class`, `version`, `dependencies`
- **SCAF-03**: `unique_id` from host:port with `_abort_if_unique_id_configured()`
- **DIST-01**: HACS-compatible structure (hacs.json, manifest.json, file layout)
- **DIST-02**: Frontend card served via async static path registration
- **DIST-03**: CI workflows (hassfest + hacs/action validation)
- **SRVC-05**: Service registered in `async_setup` (domain-scoped, not entry-scoped)

Also provides correct patterns for:
- Shared aiohttp session via `async_get_clientsession(hass)`
- `ConfigEntry.runtime_data` typed dataclass
- `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)`
- `CoordinatorEntity` sensor base class
- Test scaffold (conftest, config_flow tests, coordinator tests)
- Options flow

## What Needs Customization (File-by-File)

Each template file contains generic placeholder logic that must be replaced with LibreTranslate-specific implementation:

### const.py
- Change `DEFAULT_PORT` from 8080 → 5000 (LibreTranslate default)
- Change `DEFAULT_SCAN_INTERVAL` from 30 → 300 (5 min for language polling)
- Add `SERVICE_TRANSLATE = "translate"` and field constants (`ATTR_TEXT`, `ATTR_SOURCE`, `ATTR_TARGET`)

### api.py
- Replace `/health` endpoint → `GET /languages` for connection test
- Replace `/api/data` endpoint → `GET /languages` for data polling
- Add `async_translate()` method → `POST /translate` with `{q, source, target, format, api_key}`
- Change auth from Bearer header → API key in POST body (LibreTranslate convention)
- Response parsing: `/languages` returns `[{code, name, targets: []}]`

### coordinator.py
- Customize `_async_update_data()` to return `{status, languages, language_count}`
- Add `async_translate()` method that delegates to `self.client.async_translate()`
- Parse language list from API response into structured data

### config_flow.py
- Change `CONF_API_KEY` from `vol.Required` → `vol.Optional` (many LibreTranslate instances have no auth)
- Change `DEFAULT_PORT` default from 8080 → 5000
- Update config flow title format
- Update strings.json descriptions to reference LibreTranslate

### sensor.py
- Replace single generic sensor with two sensors: `ArgosStatusSensor` and `ArgosLanguageCountSensor`
- Status sensor: shows "online"/"error" from coordinator data
- Language count sensor: shows count, language list in `extra_state_attributes`
- Set appropriate icons (mdi:translate, mdi:earth)

### services.py
- Replace generic "query" service → "translate" service
- Schema: `{text: str, source: str, target: str}`
- Change `SupportsResponse.OPTIONAL` → `SupportsResponse.ONLY`
- Add language pair validation against coordinator data
- Handler must look up coordinator from `hass.data[DOMAIN]`

### services.yaml
- Replace query schema → translate fields (text, source, target)
- Set `response: required` (not optional)

### frontend/argos_translate-card.js
- Complete rewrite: language dropdowns populated from sensor attributes
- Input/output text areas, translate button calling service with returnResponse
- Swap button, loading spinner, status indicator
- Card editor with entity picker, header, default languages

### strings.json + translations/en.json
- Update step title: "Connect to LibreTranslate Server"
- Update field descriptions for LibreTranslate context
- Make API key description note it's optional

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: iot_class is `local_polling` (LibreTranslate on local network)
- [Init]: API key goes in POST body, not HTTP header (LibreTranslate convention)
- [Init]: Service registered in async_setup (domain-scoped, not entry-scoped)
- [Init]: Card uses callService with returnResponse:true (requires HA 2024.1+)
- [Init]: 30-second timeout for translate calls (slow hardware)
- [Template]: Re-scaffolded from ha-hacs-template v1.0 (2026-02-20)

### Pending Todos

None yet.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-20
Stopped at: Phase 2 context gathered, ready for planning
Resume action: /gsd:plan-phase 2 --auto
