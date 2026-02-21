# Argos Translate

## What This Is

A Home Assistant HACS integration that provides local, privacy-respecting text translation via a self-hosted LibreTranslate/Argos Translate server. Exposes a `translate` service call for automations, sensors for server health, and a Lovelace card with language dropdowns and real-time translation.

## Core Value

Users can translate text between languages entirely on their local network — no cloud services, no API limits, no privacy concerns — directly from a HA dashboard card or automation.

## Requirements

### Validated

- [x] Config flow with host/port/API key fields and connection validation (ping /languages endpoint) — Phase 1
- [x] DataUpdateCoordinator polling /languages endpoint for available languages and server status — Phase 1
- [x] Status sensor (online/error) — Phase 1
- [x] Available languages count sensor — Phase 1
- [x] `argos_translate.translate` service call accepting text, source language, target language — Phase 2
- [x] Service call returns translated text as response data — Phase 2
- [x] Lovelace card with source/target language dropdowns — Phase 2
- [x] Language swap button on card — Phase 2
- [x] Text input area and read-only output area — Phase 2
- [x] Translate button triggering the service call — Phase 2
- [x] Status indicator on card (server online/offline + language count) — Phase 2
- [x] Visual card editor — Phase 2
- [x] HACS-compatible distribution (hacs.json, manifest.json, GitHub Actions) — Template + Phase 3
- [x] Frontend card served via integration's static path registration — Template
- [x] Dynamic language list populated from server (not hardcoded) — Phase 1
- [x] Error handling for server unavailable, translation timeout, unsupported language pairs — Phases 1-2

### Active

- [ ] Deploy to real HA instance and stabilize (manual install → HACS validation)
- [ ] Auto-detect source language via /detect endpoint
- [ ] Options flow to reconfigure host/port/API key without removing integration
- [ ] Card polish — theming, accessibility, error states, mobile responsiveness

### Out of Scope

- Argos Translate library bundled directly (requires separate server) — too complex for HA integration, LibreTranslate Docker container is the deployment model
- Translation history/memory — deferred to future
- Batch translation — deferred to future
- Speech-to-text-to-translate pipeline — future integration with Whisper
- Language package management from HA — manage via LibreTranslate admin UI

## Current Milestone: v1.1 Enhancement

**Goal:** Deploy v1.0 to real hardware, stabilize through real-world testing, then add auto-detect language, options flow, and card polish.

**Target features:**
- Deploy + stabilize on real HA instance (manual install, then HACS)
- Auto-detect source language via LibreTranslate /detect endpoint
- Options flow for reconfiguring credentials without re-adding
- Card UX improvements (theming, accessibility, error states, mobile)

## Current State

Shipped v1.0 with 2,052 LOC (Python + JS + JSON + YAML).
Tech stack: Python (HA integration), JavaScript/LitElement (Lovelace card), aiohttp (API client).
3 phases, 6 plans, 13 tasks completed in 3 days.

## Context

- **Homelab**: LibreTranslate already running on QNAP at port 5500 (mapped from internal 5000)
- **Current languages**: en↔es, en↔ja installed, plus ~20 bundled with the image
- **LibreTranslate API**: Simple REST API — GET /languages, POST /translate, GET /detect
- **Argos Translate**: The underlying engine; LibreTranslate is the web server wrapping it
- **HA ecosystem gap**: No existing local-only translation integration for HA — Whisper (STT) and Piper (TTS) exist but translation is missing
- **HACS template**: Re-scaffolded from ha-hacs-template v1.0 via `copier copy` (2026-02-20). Template provides correct HA 2025.7+ patterns, CI, tests, and service framework.
- **Server runs as UID 1032**: Known quirk, doesn't affect API access
- **Copier answers**: `.copier-answers.yml` tracks template version (v1.0) and variables; `copier update` pulls future template improvements

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
| Wrap LibreTranslate API (not bundle Argos directly) | LibreTranslate is already deployed, well-maintained, and provides a clean REST API | Validated — clean REST client works well |
| Service call with response data | HA's SupportsResponse.ONLY pattern lets automations use translated text | Validated — response_variable pattern works |
| Dynamic language list from server | Avoids hardcoding, adapts to whatever packages are installed | Validated — coordinator polls /languages |
| Single config entry per server | One LibreTranslate server per integration instance | Validated — works for typical use case |
| API key in POST body | LibreTranslate convention (not HTTP header) | Validated — Phase 1 |
| Test sensors via direct instantiation | Disabled-by-default entities can't be tested through state machine | Validated — Phase 3 |
| Text descriptions only (no screenshots) | Simpler maintenance, HACS images check ignored | Validated — Phase 3 |

---
*Last updated: 2026-02-21 after v1.1 milestone start*
