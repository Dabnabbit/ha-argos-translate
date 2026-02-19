# Research Summary: HA Argos Translate Integration

**Synthesized:** 2026-02-19
**Project:** Home Assistant HACS integration for local text translation via LibreTranslate/Argos Translate
**Researcher Confidence:** HIGH (HA patterns), MEDIUM (LibreTranslate API edge cases)

---

## Executive Summary

This project fills a genuine gap in the Home Assistant ecosystem: there is currently no local text translation integration. Whisper (STT) and Piper (TTS) exist for speech processing, but the middle link — translating text between languages locally — is missing. LibreTranslate (powered by Argos Translate's CTranslate2 backend) is the clear choice as the server backend: it's the dominant self-hosted translation solution, runs as a single Docker container, and exposes a simple REST API with no authentication required for self-hosted instances.

The integration architecture follows well-established HA patterns: a `ConfigFlow` for UI-based setup, a `DataUpdateCoordinator` that polls `/languages` every 5 minutes (serving double duty as health check and language catalog), two `CoordinatorEntity`-based sensors (server status and language count), a domain-scoped `SupportsResponse.ONLY` service call for automation use, and a LitElement Lovelace card with language dropdowns and real-time translation. Zero pip dependencies are needed — everything is raw `aiohttp` against the LibreTranslate REST API, using HA's bundled session management.

The primary risks are all known and preventable: the static path registration API changed in HA 2025.7 (must use `async_register_static_paths`), the translate service must be registered in `async_setup` rather than `async_setup_entry` to avoid duplicate registration on reload, and the card's `returnResponse: true` pattern for receiving service response data requires HA 2023.12+. The target hardware (QNAP Celeron J4125) will produce 5-15 second translation latency for longer texts, requiring loading states and a 30-second timeout. All these are straightforward to implement correctly from the start.

---

## Key Findings

### From STACK.md

| Technology | Rationale |
|------------|-----------|
| Python 3.12+ (HA-bundled) | No choice — HA's virtualenv; no installation needed |
| `aiohttp` (HA-bundled) | All HTTP to LibreTranslate; never create your own session |
| `voluptuous` (HA-bundled) | Config flow schema validation; bundled, do not re-require |
| LitElement (HA-bundled) | Single-file no-build Lovelace card; avoids npm/webpack |
| Zero pip dependencies | `requirements: []` in manifest.json — everything is HA-bundled |

**Critical version requirements:**
- HA 2025.7+ — required for `async_register_static_paths` (old API removed)
- HA 2023.12+ (manifest min: 2024.1.0) — required for `callService` with `returnResponse: true`
- LibreTranslate 1.5+ — stable REST API with `/languages` endpoint

**Settled stack decisions:**
1. `async_get_clientsession(hass)` — mandatory, never create own aiohttp session
2. `SupportsResponse.ONLY` in `async_setup` (not `async_setup_entry`) — domain-scoped service
3. `async_register_static_paths` + `StaticPathConfig` — modern static path API
4. `runtime_data` on `ConfigEntry` — modern 2025 pattern replacing `hass.data[DOMAIN]`
5. `callService` with `returnResponse: true` — card receives translation result directly

**One unresolved medium-confidence item:** The exact response shape from `callService` with `returnResponse` (whether it's `result.response.translated_text` or `result.translated_text`) needs verification against current HA frontend source before card implementation.

### From FEATURES.md

**Must-have for v1 (P0):**
- Config Flow: host/port/api_key (optional) with `/languages` connection validation
- DataUpdateCoordinator: polls `/languages` every 5 minutes
- `argos_translate.translate` service call (SupportsResponse.ONLY)
- Lovelace card: source/target dropdowns, textarea input, translated output, translate button, swap button, status indicator

**Should-have for v1 (P1):**
- Status sensor: "online"/"error" with last_check and error_message attributes
- Language count sensor: integer count with full language list in attributes
- Visual card editor: entity picker, title, default source/target

**Nice-to-have for v1.x (P2, do not block v1):**
- Language pair validation (disable Translate if pair unavailable) — actually this IS needed in service; card filtering is P2
- Loading state/spinner during translation

**Deferred to v2+:**
- Auto-detect source language
- Translation history
- Batch translation
- Pivot translation (A→B via C)
- Speech-to-translate pipeline (Whisper → Translate → Piper)

**Scope assessment:** Current v1 scope is right-sized. The Lovelace card is the largest single item (~500-800 lines of JS) and warrants its own phase.

### From ARCHITECTURE.md

**File structure (6 Python files + 1 JS + supporting files):**
```
custom_components/argos_translate/
├── __init__.py          # async_setup (service + static path) + async_setup_entry
├── config_flow.py       # Single-step: host, port, api_key
├── coordinator.py       # DataUpdateCoordinator polling /languages every 5 min
├── sensor.py            # Status + Language Count CoordinatorEntity sensors
├── api.py               # LibreTranslateClient wrapper (separate from coordinator)
├── const.py             # DOMAIN, DEFAULT_PORT, scan intervals
├── manifest.json        # HACS metadata, min_version, iot_class
├── strings.json         # Config flow UI strings
├── services.yaml        # Service definition (required for automation UI)
├── argos-translate-card.js  # LitElement card + editor (single file)
└── translations/en.json # English translations for config flow
```

**Key architectural patterns:**
- **Separate `api.py`** from `coordinator.py` — keeps concerns clean; coordinator orchestrates, client communicates
- **Card reads language data from sensor attributes** — indirect coupling avoids custom WebSocket commands; language count entity required in card config
- **Service handler in `async_setup` dynamically looks up config entry** — `hass.config_entries.async_entries(DOMAIN)[0]` — works for single-entry use case
- **API key in POST body** (not header) — LibreTranslate convention, not HTTP header auth
- **Target language filtering** — `sourceLang.targets[]` from /languages response drives dropdown filtering

**Data flows:**
- Translation: card → `callService(returnResponse: true)` → `handle_translate()` → `client.translate()` → POST `/translate` → return `{translated_text}`
- Language refresh: coordinator timer → GET `/languages` → sensors update → card reads attributes → dropdowns update

### From PITFALLS.md

**Top pitfalls with prevention (all must be addressed from day 1):**

| # | Pitfall | Severity | Prevention |
|---|---------|----------|------------|
| 01 | `register_static_path` removed in HA 2025.7 | CRITICAL | Use `async_register_static_paths` + `StaticPathConfig` from the start |
| 02 | aiohttp session leak | HIGH | Always `async_get_clientsession(hass)`, never manual session |
| 03 | Service in `async_setup_entry` | MEDIUM | Register in `async_setup`; dynamic entry lookup in handler |
| 04 | Missing `unique_id` in config flow | MEDIUM | `f"{host}:{port}"` as unique_id + `_abort_if_unique_id_configured()` |
| 05 | API key in header (not body) | LOW | POST body: `{"api_key": key}` not `X-Api-Key` header |
| 06 | Wrong `iot_class` in manifest | LOW | `"iot_class": "local_polling"` |
| 07 | Language pair not validated | MEDIUM | Validate against coordinator data before API call; filter card dropdowns |
| 08 | Translation timeout on slow hardware | MEDIUM | `aiohttp.ClientTimeout(total=30)` on translate calls; loading spinner |
| 09 | `returnResponse` not in older HA | MEDIUM | `"min_version": "2024.1.0"` in manifest |
| 10 | Empty/whitespace input | LOW | Disable Translate button; return empty string from service |
| 11 | Missing/malformed `services.yaml` | MEDIUM | Required for Developer Tools and automation UI |
| 12 | Card resource not auto-registered | MEDIUM | Document manual resource addition; HACS handles at install time |
| 13 | Coordinator not ready at service call | MEDIUM | Guard checks in handler: entries exist, runtime_data set, coordinator.data populated |

**"Looks done but isn't" checklist from PITFALLS.md** should be used as a phase exit criterion for each implementation phase.

---

## Implications for Roadmap

The research points clearly to a 4-phase structure. The phases are ordered by dependency: core integration before service, service before card, everything before HACS packaging.

### Suggested Phase Structure

**Phase 1: Integration Core**
*Rationale: Everything else depends on this. Sets up the HA integration scaffold, config flow, coordinator, and sensors. No UI, no service — just the data foundation.*

Delivers:
- HACS-installable integration that connects to LibreTranslate
- Status sensor and language count sensor appearing in HA
- Config flow with connection validation and duplicate prevention

Features: Config Flow (P0), Coordinator (P0), Status Sensor (P1), Language Count Sensor (P1)

Must avoid: PITFALL-01 (static path), PITFALL-02 (session leak), PITFALL-04 (unique_id), PITFALL-06 (iot_class)

Research flag: Standard HA patterns — NO research phase needed. Patterns are well-documented.

---

**Phase 2: Translation Service**
*Rationale: The service call is the core value proposition. Automations can use it without the card existing. Must be solid before building UI on top of it.*

Delivers:
- `argos_translate.translate` service callable from automations
- Language pair validation before API calls
- `services.yaml` for automation UI integration
- Proper error handling for server unavailability

Features: Translate service call (P0), services.yaml (required)

Must avoid: PITFALL-03 (service in wrong place), PITFALL-05 (API key in header), PITFALL-07 (pair validation), PITFALL-08 (timeout), PITFALL-11 (services.yaml), PITFALL-13 (coordinator readiness)

Research flag: Standard HA patterns — NO research phase needed. `SupportsResponse.ONLY` is well-documented.

---

**Phase 3: Lovelace Card**
*Rationale: UI layer on top of working backend. The card is the largest single deliverable (~500-800 lines of JS). Keep it in its own phase to avoid entangling JS complexity with Python backend work.*

Delivers:
- LitElement card with source/target dropdowns
- Dynamic target language filtering based on source selection
- Textarea input + read-only output area
- Translate button with loading state
- Swap button (languages + text)
- Status indicator (online/offline + language count)
- Visual card editor (entity, title, defaults)

Features: Lovelace card (P0), card editor (P1), loading state (P2)

Must avoid: PITFALL-09 (returnResponse compatibility), PITFALL-10 (empty input), PITFALL-12 (resource registration)

Research flag: CONSIDER research phase for `callService` `returnResponse` response shape — the exact `result.response.translated_text` path needs verification against current HA frontend source before implementation.

---

**Phase 4: HACS Packaging and Distribution**
*Rationale: Once the integration works end-to-end, package it for HACS distribution. Involves HACS validation, hassfest compliance, documentation.*

Delivers:
- `hacs.json` with correct metadata
- README with installation instructions and resource registration steps
- hassfest validation passing
- HACS validation passing

Features: HACS distribution, documentation

Must avoid: PITFALL-01 (hassfest will catch static path issues), PITFALL-06 (iot_class triggers hassfest)

Research flag: Standard HACS patterns — NO research phase needed.

---

## Research Flags

| Phase | Needs Research Phase? | Reason |
|-------|----------------------|--------|
| Phase 1: Integration Core | NO | Well-documented HA patterns; coordinator + sensors are standard |
| Phase 2: Translation Service | NO | `SupportsResponse.ONLY` is well-documented since HA 2023.7 |
| Phase 3: Lovelace Card | MAYBE | Verify `callService` `returnResponse` response shape before JS implementation |
| Phase 4: HACS Packaging | NO | Standard HACS pattern; PITFALLS.md covers all edge cases |

**If research is done for Phase 3**, the specific question to answer is:
> What is the exact response shape returned by `this.hass.callService("domain", "service", data, {returnResponse: true})`? Is it `result.response.field` or `result.field`?

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack choices | HIGH | Python/HA patterns are established; aiohttp, LitElement, SupportsResponse all verified |
| Feature scope | HIGH | Features are well-scoped; v1 vs v2 split is clear and defensible |
| Architecture | HIGH | Component boundaries are clean; HA patterns applied correctly |
| Pitfall avoidance | HIGH | 13 pitfalls documented with specific fixes; all preventable |
| LibreTranslate API | MEDIUM | Trained on API docs, not live docs; API has been stable for years |
| Card `returnResponse` shape | MEDIUM | Exact response object path needs verification against HA frontend source |
| Competitive landscape | MEDIUM | No known existing HA local translation integration; may be obscure community entries not in training data |

**Overall confidence: HIGH** — The HA integration patterns are well-established and the research is comprehensive. The one medium-confidence item (response shape of callService with returnResponse) is a small, localized concern that won't affect phase 1 or 2.

---

## Gaps to Address During Planning

1. **`callService` response shape verification** — Before Phase 3 implementation, verify whether `this.hass.callService(..., {returnResponse: true})` returns `result.response.translated_text` or `result.translated_text`. Check current HA frontend source or test with a known SupportsResponse service.

2. **Card resource auto-registration vs manual** — Research confirms HACS handles resource URL registration at install time, but the exact mechanism should be confirmed during Phase 4 planning. Some integrations auto-register via `lovelace_resources` in manifest; document which approach is used.

3. **Single-entry assumption** — The service handler uses `entries[0]`, assuming one LibreTranslate server. This is fine for v1 but should be documented as a known limitation. Multi-server support is a v2+ concern.

4. **Hardware performance baseline** — QNAP Celeron J4125 translation latency of 5-15 seconds is documented but not measured. The 30-second timeout should be validated against actual translation times for long texts during Phase 2 testing.

5. **Language pair availability for common pairs** — The research assumes en↔es, en↔de, etc. are installed. The integration should handle the case where NO language packages are installed (coordinator returns empty list).

---

## Aggregated Sources

*Compiled from all 4 research files. Confidence levels reflect training data vs live documentation.*

### Home Assistant Patterns (HIGH confidence)
- HA Developer Docs: ConfigFlow, DataUpdateCoordinator, CoordinatorEntity
- HA Developer Docs: `async_register_static_paths` + `StaticPathConfig` (2025.7+ API)
- HA Developer Docs: `SupportsResponse.ONLY` service pattern (added 2023.7)
- HA Developer Docs: `runtime_data` on ConfigEntry (modern 2025 pattern)
- HA Developer Docs: `async_get_clientsession(hass)` mandatory pattern
- hassfest quality scale rules: `inject-websession`, `iot_class`
- HACS Developer Docs: `hacs.json` metadata, resource registration

### LibreTranslate API (MEDIUM confidence — training data, not live docs)
- LibreTranslate REST API: `GET /languages`, `POST /translate`, `POST /detect`
- LibreTranslate auth convention: API key in POST body (`api_key` field), not HTTP header
- LibreTranslate Docker deployment: `libretranslate/libretranslate`, port 5500 default
- Argos Translate engine: CTranslate2 backend, ~30+ language pairs

### Frontend Patterns (MEDIUM confidence)
- HA Frontend: `this.hass.callService()` with `returnResponse: true` (added 2023.12)
- LitElement: single-file no-build Lovelace card pattern
- HA Frontend: `this.hass.states[entityId].attributes` for reading entity attributes

### Community/Ecosystem (MEDIUM confidence — training data)
- Competitive analysis: No existing HA local text translation integration
- HACS ecosystem: Custom integration distribution conventions
- LibreTranslate active development status and license (AGPL-3.0)
