# Argos Translate

## What This Is

A Home Assistant HACS integration that provides local, privacy-respecting text translation via a self-hosted LibreTranslate/Argos Translate server. Exposes a `translate` service call for automations, sensors for server health, and a Lovelace card with language dropdowns and real-time translation.

## Core Value

Users can translate text between languages entirely on their local network — no cloud services, no API limits, no privacy concerns — directly from a HA dashboard card or automation.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Config flow with host/port/API key fields and connection validation (ping /languages endpoint)
- [ ] DataUpdateCoordinator polling /languages endpoint for available languages and server status
- [ ] Status sensor (online/error)
- [ ] Available languages count sensor
- [ ] `argos_translate.translate` service call accepting text, source language, target language
- [ ] Service call returns translated text as response data
- [ ] Lovelace card with source/target language dropdowns
- [ ] Language swap button on card
- [ ] Text input area and read-only output area
- [ ] Translate button triggering the service call
- [ ] Status indicator on card (server online/offline + language count)
- [ ] Visual card editor
- [ ] HACS-compatible distribution (hacs.json, manifest.json, GitHub Actions)
- [ ] Frontend card served via integration's static path registration
- [ ] Dynamic language list populated from server (not hardcoded)
- [ ] Error handling for server unavailable, translation timeout, unsupported language pairs

### Out of Scope

- Argos Translate library bundled directly (requires separate server) — too complex for HA integration, LibreTranslate Docker container is the deployment model
- Auto-detect source language — LibreTranslate API supports it but adds complexity; explicit selection first
- Translation history/memory — deferred to v2
- Batch translation — deferred to v2
- Speech-to-text-to-translate pipeline — future integration with Whisper
- Language package management from HA — manage via LibreTranslate admin UI

## Context

- **Homelab**: LibreTranslate already running on QNAP at port 5500 (mapped from internal 5000)
- **Current languages**: en↔es, en↔ja installed, plus ~20 bundled with the image
- **LibreTranslate API**: Simple REST API — GET /languages, POST /translate, GET /detect
- **Argos Translate**: The underlying engine; LibreTranslate is the web server wrapping it
- **HA ecosystem gap**: No existing local-only translation integration for HA — Whisper (STT) and Piper (TTS) exist but translation is missing
- **HACS template**: Scaffolded from ha-hacs-template with config flow, coordinator, sensors, LitElement card
- **Server runs as UID 1032**: Known quirk, doesn't affect API access
- **Future**: Could replace LibreTranslate with a custom FastAPI wrapper (ha-argos-translate project idea from homelab notes) but this integration works with existing LibreTranslate

## Constraints

- **Tech stack**: Python (HA integration) + JavaScript/LitElement (Lovelace card)
- **HACS compliance**: Must pass hacs/action and hassfest validation
- **No pip requirements**: aiohttp already in HA for API calls
- **Single JS file**: No build tooling, LitElement from HA's built-in instance
- **LibreTranslate API**: REST over HTTP, no WebSocket support
- **Server dependency**: Requires a running LibreTranslate instance (Docker container)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Wrap LibreTranslate API (not bundle Argos directly) | LibreTranslate is already deployed, well-maintained, and provides a clean REST API | — Pending |
| Service call with response data | HA's SupportsResponse.ONLY pattern lets automations use translated text | — Pending |
| Dynamic language list from server | Avoids hardcoding, adapts to whatever packages are installed | — Pending |
| Single config entry per server | One LibreTranslate server per integration instance | — Pending |

---
*Last updated: 2026-02-19 after initialization*
