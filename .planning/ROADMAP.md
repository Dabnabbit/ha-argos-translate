# Roadmap: Argos Translate

## Overview

Argos Translate delivers a local translation integration for HA in 3 phases. The ha-hacs-template v1.0 overlay provides the scaffold, CI/CD, test framework, and service registration patterns — eliminating the original Phase 1 (scaffold fixes) and Phase 5 (HACS distribution). The remaining work is LibreTranslate-specific: API client + data layer, translation service + card, and final validation.

## Template Baseline (Satisfied by ha-hacs-template v1.0)

The following requirements are satisfied by the template overlay and do not need dedicated phases:

| Requirement | What the Template Provides |
|-------------|---------------------------|
| SCAF-01 | `async_register_static_paths` + `StaticPathConfig` (HA 2025.7+) |
| SCAF-02 | Valid manifest.json with `iot_class`, `version`, `dependencies: [frontend, http]` |
| SCAF-03 | `unique_id` from host:port, `_abort_if_unique_id_configured()` |
| DIST-01 | HACS-compatible file structure (hacs.json, manifest.json) |
| DIST-02 | Frontend card served via async static path registration |
| DIST-03 | CI workflows (hassfest + hacs/action) in `.github/workflows/validate.yml` |
| SRVC-05 | Service registered in `async_setup` (domain-scoped) |

## Phases

- [x] **Phase 1: API Client + Data Layer** — LibreTranslate API client, coordinator, config flow, sensors (completed 2026-02-21)
- [ ] **Phase 2: Translation Service + Card** — Translate service, Lovelace card with language UI
- [ ] **Phase 3: Polish + Validation** — End-to-end testing, CI validation, documentation

## Phase Details

### Phase 1: API Client + Data Layer
**Goal**: Integration connects to LibreTranslate, polls languages, exposes status and language count sensors
**Depends on**: Template overlay (done)
**Requirements**: CONF-01, CONF-02, CONF-03, SENS-01, SENS-02, SENS-03, SENS-04
**Files to customize**:
  - `const.py` — Port default (5000), scan interval (300s), LibreTranslate-specific constants
  - `api.py` — Replace generic endpoints with `/languages` and `/translate`, API key in POST body
  - `coordinator.py` — Poll `/languages`, return `{status, languages, language_count}`
  - `config_flow.py` — Optional API key, port 5000 default, LibreTranslate descriptions
  - `sensor.py` — Two sensors: status (online/error) + language count (with attributes)
  - `strings.json` + `translations/en.json` — LibreTranslate-specific wording
**Success Criteria**:
  1. Config flow validates connection to LibreTranslate via GET /languages
  2. Optional API key field works (blank for no-auth instances)
  3. Status sensor shows "online" when server is reachable
  4. Language count sensor shows correct number with language list in attributes
  5. Sensors update every 5 minutes via coordinator

**Plans:** 2/2 plans complete

Plans:
- [ ] 01-01-PLAN.md — API foundation: customize const.py, api.py, coordinator.py for LibreTranslate
- [ ] 01-02-PLAN.md — Config flow + sensors: config_flow.py, binary_sensor.py, sensor.py, strings, __init__.py

### Phase 2: Translation Service + Card
**Goal**: Users can translate text via service call and Lovelace card
**Depends on**: Phase 1
**Requirements**: SRVC-01, SRVC-02, SRVC-03, SRVC-04, CARD-01, CARD-02, CARD-03, CARD-04, CARD-05, CARD-06, CARD-07, CARD-08
**Files to customize**:
  - `services.py` — Translate service with SupportsResponse.ONLY, language validation
  - `services.yaml` — Translate schema (text, source, target)
  - `frontend/argos_translate-card.js` — Translation UI with language dropdowns, swap, translate button
**Success Criteria**:
  1. `argos_translate.translate` service callable from Developer Tools
  2. Service returns `{translated_text}` in response data
  3. Invalid language pair returns clear error
  4. Card shows language dropdowns populated from server
  5. Translate button calls service and displays result
  6. Swap button, loading spinner, and status indicator work
  7. Visual card editor works

**Plans:** 2 plans

Plans:
- [ ] 02-01-PLAN.md — Translate service: const.py, services.py, services.yaml, sensor.py, strings.json, translations/en.json
- [ ] 02-02-PLAN.md — Lovelace card: frontend/argos_translate-card.js (translation UI + editor)

### Phase 3: Polish + Validation
**Goal**: Integration passes all CI checks and is ready for HACS distribution
**Depends on**: Phase 2
**Requirements**: DIST-01, DIST-03 (validation)
**Files to update**:
  - `tests/` — Update test fixtures and assertions for LibreTranslate-specific logic
  - `README.md` — Final documentation with screenshots, examples
**Success Criteria**:
  1. hassfest CI passes
  2. hacs/action CI passes
  3. All tests pass
  4. README documents installation, configuration, card usage, service examples

Plans:
- [ ] 03-01: Update tests for LibreTranslate-specific logic and validate CI

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. API Client + Data Layer | 0/2 | Complete    | 2026-02-21 |
| 2. Translation Service + Card | 0/2 | Not started | - |
| 3. Polish + Validation | 0/1 | Not started | - |
