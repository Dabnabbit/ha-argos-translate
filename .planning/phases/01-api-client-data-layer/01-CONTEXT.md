# Phase 1: API Client + Data Layer - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Connect to a self-hosted LibreTranslate server, poll available languages, and expose server status and language information as Home Assistant entities. This phase covers the config flow, API client, coordinator, and sensors. Translation service and Lovelace card are Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Config flow experience
- No default port — require user to enter their port explicitly
- Separate host and port fields with an HTTP/HTTPS toggle (HTTP default)
- Validate connection by hitting GET /languages before allowing setup to complete — hard gate, no skip
- User-provided name field for the integration entry (used as device name and entity prefix)
- API key field always visible but optional — masked (password-style) input
- Full options flow for reconfiguration (change host, port, API key, SSL) — validates connection on save

### Sensor presentation
- **Status sensor:** Binary sensor with `device_class: connectivity` — on when server is reachable, off when not
- **Status sensor:** Minimal — just the on/off state, no extra attributes
- **Language count sensor:** State is the installed language count (numeric) — disabled by default
- **Language count sensor attributes:** List of installed languages with English + native names (e.g., "Japanese (日本語)"), plus total available count if the API provides it
- **Icons:** `mdi:server` for status, `mdi:translate` for language count
- **Status sensor enabled by default, language count sensor disabled by default**
- Create an HA device per config entry — groups sensors under the user-provided name

### Server connection behavior
- Use HA's built-in DataUpdateCoordinator unavailability handling — no custom offline logic
- Entities go unavailable when server is unreachable, restore automatically when it returns
- No custom log warnings on failure — HA's coordinator logging is sufficient
- Connection validation on both initial setup and options flow save

### API key handling
- API key is optional — blank means no auth (most local setups)
- Always visible in config flow, not hidden behind an advanced toggle
- Masked input (password-style) in the config UI
- API key sent in POST request body per LibreTranslate's documented API standard

### Claude's Discretion
- Polling interval for coordinator (language list rarely changes)
- API request timeout value
- Entity ID naming pattern (include instance name vs fixed pattern for multi-instance support)
- Whether to include translation pairs as a sensor attribute
- Whether to fetch total available language count from Argos package index

</decisions>

<specifics>
## Specific Ideas

- Architecture is intentional "thin HA client + fat Docker server" — mirrors how Whisper and Piper work in HA
- Single server is the primary use case, but don't block multi-instance by design
- User's LibreTranslate runs on QNAP at port 5500 (mapped from internal 5000), no API key currently

</specifics>

<deferred>
## Deferred Ideas

- Lightweight LibreTranslate Docker image without web GUI — future project (custom FastAPI wrapper)
- Auto-detect source language support — Phase 2 or later
- Translation pairs display (which languages can translate to which) — evaluate during Phase 2 card work

</deferred>

---

*Phase: 01-api-client-data-layer*
*Context gathered: 2026-02-20*
