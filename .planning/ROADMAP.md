# Roadmap: Argos Translate

## Overview

Argos Translate delivers a local translation integration for HA in 5 phases: fixing scaffold bugs and establishing the integration foundation, building the config flow with coordinator and sensors, implementing the core translate service call, building the Lovelace card with language dropdowns and translation UI, and packaging for HACS distribution. The build order follows natural dependencies: foundation before data layer, service before card, everything before distribution.

## Phases

- [ ] **Phase 1: Integration Foundation** - Fix scaffold, config flow, coordinator, sensors, static path
- [ ] **Phase 2: Config Flow + Data Layer** - Connect to LibreTranslate, poll languages, expose sensors
- [ ] **Phase 3: Translation Service** - argos_translate.translate service with SupportsResponse.ONLY
- [ ] **Phase 4: Lovelace Card** - Language dropdowns, translation UI, swap button, card editor
- [ ] **Phase 5: HACS Distribution** - Packaging, validation, documentation

## Phase Details

### Phase 1: Integration Foundation
**Goal**: Integration loads on HA 2025.7+ with correct manifest, static path, and session management
**Depends on**: Nothing (first phase)
**Requirements**: SCAF-01, SCAF-02, SCAF-03, DIST-02
**Success Criteria** (what must be TRUE):
  1. Integration installs and loads without errors on HA 2025.7+
  2. No deprecation warnings in HA logs
  3. hassfest validation passes
  4. Card JS file is served at the registered static path
**Plans**: TBD

Plans:
- [ ] 01-01: Fix static path, aiohttp session, manifest, unique_id, and iot_class

### Phase 2: Config Flow + Data Layer
**Goal**: User can configure LibreTranslate connection; sensors show server status and language count
**Depends on**: Phase 1
**Requirements**: CONF-01, CONF-02, CONF-03, SENS-01, SENS-02, SENS-03, SENS-04
**Success Criteria** (what must be TRUE):
  1. Config flow validates connection to LibreTranslate via GET /languages
  2. Optional API key field works (blank for no-auth instances)
  3. Status sensor shows "online" when server is reachable
  4. Language count sensor shows correct number with language list in attributes
  5. Sensors update every 5 minutes via coordinator
**Plans**: TBD

Plans:
- [ ] 02-01: Implement config flow with connection validation
- [ ] 02-02: Implement coordinator, API client, and sensors

### Phase 3: Translation Service
**Goal**: Automations can translate text via `argos_translate.translate` service call
**Depends on**: Phase 2
**Requirements**: SRVC-01, SRVC-02, SRVC-03, SRVC-04, SRVC-05
**Success Criteria** (what must be TRUE):
  1. Service callable from Developer Tools → Services
  2. Service returns translated_text in response data
  3. Invalid language pair returns clear error message
  4. Service works from automation YAML (SupportsResponse.ONLY)
  5. services.yaml present and service appears in automation UI
**Plans**: TBD

Plans:
- [ ] 03-01: Implement translate service with SupportsResponse.ONLY and services.yaml

### Phase 4: Lovelace Card
**Goal**: Users can translate text from a Lovelace dashboard card with language dropdowns
**Depends on**: Phase 3
**Requirements**: CARD-01, CARD-02, CARD-03, CARD-04, CARD-05, CARD-06, CARD-07, CARD-08
**Success Criteria** (what must be TRUE):
  1. Card shows source and target language dropdowns populated from server
  2. Target dropdown filters to valid targets when source changes
  3. Swap button exchanges languages and text
  4. Translate button calls service and displays result
  5. Loading spinner shows during translation
  6. Status indicator shows server online/offline state
  7. Visual card editor works for all config fields
**Plans**: TBD

Plans:
- [ ] 04-01: Build LitElement card with translation UI
- [ ] 04-02: Build visual card editor

### Phase 5: HACS Distribution
**Goal**: Integration is ready for public HACS distribution
**Depends on**: Phase 4
**Requirements**: DIST-01, DIST-03
**Success Criteria** (what must be TRUE):
  1. hassfest CI passes
  2. hacs/action CI passes
  3. Tagged release created on GitHub
  4. Integration installable via HACS custom repository
**Plans**: TBD

Plans:
- [ ] 05-01: HACS packaging, CI validation, and release prep

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Integration Foundation | 0/1 | Not started | - |
| 2. Config Flow + Data Layer | 0/2 | Not started | - |
| 3. Translation Service | 0/1 | Not started | - |
| 4. Lovelace Card | 0/2 | Not started | - |
| 5. HACS Distribution | 0/1 | Not started | - |
