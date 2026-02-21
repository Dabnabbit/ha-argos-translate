---
phase: 01-api-client-data-layer
plan: 01
subsystem: api
tags: [aiohttp, libretranslate, coordinator, polling]

requires:
  - phase: template
    provides: Generic API client, coordinator, and constants scaffolding
provides:
  - ArgosTranslateApiClient with /languages and /translate endpoints
  - ArgosCoordinator polling /languages every 300s
  - LibreTranslate-specific constants (port 5000, 300s interval, SSL toggle)
affects: [config-flow, sensors, services, translate-card]

tech-stack:
  added: []
  patterns: [api-key-in-post-body, coordinator-language-data-shape]

key-files:
  created: []
  modified:
    - custom_components/argos_translate/const.py
    - custom_components/argos_translate/api.py
    - custom_components/argos_translate/coordinator.py

key-decisions:
  - "API key sent in POST body, not Authorization header (LibreTranslate convention)"
  - "GET /languages serves as both health check and data source (single endpoint)"
  - "Empty language list raises CannotConnectError, not treated as success"
  - "Coordinator data shape: {languages: [{code, name, targets}], language_count: int}"

patterns-established:
  - "api-key-in-post-body: LibreTranslate API key included in POST json payload, not headers"
  - "coordinator-data-shape: _async_update_data returns {languages, language_count} dict"
  - "ssl-toggle: use_ssl bool config controls http:// vs https:// scheme"

requirements-completed: [CONF-01, CONF-02, SENS-04]

duration: 8min
completed: 2026-02-20
---

# Plan 01-01: API Foundation Summary

**LibreTranslate API client with /languages polling coordinator and HTTPS toggle**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-20
- **Completed:** 2026-02-20
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced generic template API client with LibreTranslate-specific ArgosTranslateApiClient
- Coordinator polls GET /languages every 5 minutes, returns structured {languages, language_count}
- Connection test validates non-empty language list (catches server with no models installed)
- API key sent in POST body per LibreTranslate convention, removed Bearer header auth

## Task Commits

1. **Task 1: Customize const.py and api.py** - `0b0a6f3` (feat)
2. **Task 2: Customize coordinator.py** - `d554c7f` (feat)

## Files Created/Modified
- `custom_components/argos_translate/const.py` - DEFAULT_PORT=5000, DEFAULT_SCAN_INTERVAL=300, CONF_USE_SSL, CONF_NAME
- `custom_components/argos_translate/api.py` - ArgosTranslateApiClient with /languages GET, /translate POST, api_key in body
- `custom_components/argos_translate/coordinator.py` - ArgosCoordinator polling /languages, async_translate() for Phase 2

## Decisions Made
None - followed plan as specified

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- API client and coordinator ready for config_flow (Plan 01-02) to use for connection validation
- Coordinator data shape ready for sensors to consume
- async_translate() method staged for Phase 2 service implementation

---
*Phase: 01-api-client-data-layer*
*Completed: 2026-02-20*
