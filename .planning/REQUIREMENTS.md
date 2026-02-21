# Requirements: Argos Translate

**Defined:** 2026-02-19
**Updated:** 2026-02-20 (template overlay applied, scaffold/distribution requirements satisfied)
**Core Value:** Users can translate text between languages entirely on their local network — no cloud services, no API limits, no privacy concerns — directly from a HA dashboard card or automation.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Scaffold & Foundation (Satisfied by Template)

- [x] **SCAF-01**: Integration loads on HA 2025.7+ without deprecation warnings (async static paths, shared aiohttp session) — *Template: async_register_static_paths, async_get_clientsession*
- [x] **SCAF-02**: `manifest.json` passes hassfest validation (correct `iot_class: local_polling`, `version`, `unique_id` support) — *Template: correct manifest with dependencies [frontend, http]*
- [x] **SCAF-03**: Config entry has unique_id derived from host:port to prevent duplicate entries — *Template: unique_id + _abort_if_unique_id_configured()*

### Configuration

- [ ] **CONF-01**: User can configure LibreTranslate host and port with connection validation (GET /languages)
- [ ] **CONF-02**: User can optionally configure API key (blank for instances without auth)
- [ ] **CONF-03**: Config flow shows clear error for connection refused, invalid API key, or empty language list

### Sensors

- [ ] **SENS-01**: Status sensor shows "online" or "error" based on coordinator poll success
- [ ] **SENS-02**: Language count sensor shows number of available source languages
- [ ] **SENS-03**: Language count sensor attributes include language list (codes + names)
- [ ] **SENS-04**: Sensors update via DataUpdateCoordinator polling /languages every 5 minutes

### Service Call

- [ ] **SRVC-01**: `argos_translate.translate` service accepts text, source language code, and target language code
- [ ] **SRVC-02**: Service returns `{translated_text: "..."}` via SupportsResponse.ONLY pattern
- [ ] **SRVC-03**: Service validates source/target language pair against coordinator data before calling API
- [ ] **SRVC-04**: Service returns clear error for unavailable language pair, server down, or timeout
- [x] **SRVC-05**: Service registered in `async_setup` (domain-scoped, not entry-scoped) — *Template: async_register_services() called in async_setup()*

### Card UI

- [ ] **CARD-01**: Card displays source and target language dropdowns populated from server
- [ ] **CARD-02**: Card has swap button to exchange source and target languages
- [ ] **CARD-03**: Card has text input area (multi-line) and read-only output area
- [ ] **CARD-04**: Card has Translate button that calls the service and displays result
- [ ] **CARD-05**: Card shows loading indicator during translation
- [ ] **CARD-06**: Card shows server status indicator (online/offline dot + language count)
- [ ] **CARD-07**: Target language dropdown filters to valid targets for selected source
- [ ] **CARD-08**: Visual card editor for configuration (entity, title, default languages)

### Distribution (Satisfied by Template)

- [x] **DIST-01**: HACS-compatible (hacs.json, manifest.json, correct file structure) — *Template: correct structure*
- [x] **DIST-02**: Frontend card served via integration's async static path registration — *Template: StaticPathConfig in async_setup()*
- [x] **DIST-03**: CI passes hassfest and hacs/action validation — *Template: .github/workflows/validate.yml*

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Features

- **ENHC-01**: Auto-detect source language via /detect endpoint
- **ENHC-02**: Translation history with persistent storage
- **ENHC-03**: Batch translation (multiple texts in one call)
- **ENHC-04**: Reconfigure flow to update credentials

### Integration

- **INTG-01**: Whisper STT → Translate → Piper TTS pipeline documentation
- **INTG-02**: Template sensor examples for translated values

## Out of Scope

| Feature | Reason |
|---------|--------|
| Bundling Argos Translate directly | Too complex; LibreTranslate Docker container is the deployment model |
| Language package management from HA | LibreTranslate admin UI handles this |
| Speech-to-text-to-translate pipeline | Future integration with Whisper; separate project |
| Pivot translation (A→B→C) | Complex routing; LibreTranslate handles some internally |
| Real-time translation-as-you-type | Wasteful API calls, poor UX on slow hardware |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCAF-01 | Template | **Done** |
| SCAF-02 | Template | **Done** |
| SCAF-03 | Template | **Done** |
| CONF-01 | Phase 1 | Pending |
| CONF-02 | Phase 1 | Pending |
| CONF-03 | Phase 1 | Pending |
| SENS-01 | Phase 1 | Pending |
| SENS-02 | Phase 1 | Pending |
| SENS-03 | Phase 1 | Pending |
| SENS-04 | Phase 1 | Pending |
| SRVC-01 | Phase 2 | Pending |
| SRVC-02 | Phase 2 | Pending |
| SRVC-03 | Phase 2 | Pending |
| SRVC-04 | Phase 2 | Pending |
| SRVC-05 | Template | **Done** |
| CARD-01 | Phase 2 | Pending |
| CARD-02 | Phase 2 | Pending |
| CARD-03 | Phase 2 | Pending |
| CARD-04 | Phase 2 | Pending |
| CARD-05 | Phase 2 | Pending |
| CARD-06 | Phase 2 | Pending |
| CARD-07 | Phase 2 | Pending |
| CARD-08 | Phase 2 | Pending |
| DIST-01 | Template | **Done** |
| DIST-02 | Template | **Done** |
| DIST-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Satisfied by template: 7 (SCAF-01/02/03, DIST-01/02/03, SRVC-05)
- Remaining: 19
- Mapped to phases: 26
- Unmapped: 0

---
*Requirements defined: 2026-02-19*
*Last updated: 2026-02-20 after template overlay*
