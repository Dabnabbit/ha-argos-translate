# Stack Research

**Domain:** Home Assistant HACS custom integration with embedded Lovelace card for LibreTranslate
**Researched:** 2026-02-19
**Confidence:** HIGH (Python/HA stack), MEDIUM (LibreTranslate API — verified against training data, not live docs)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ (HA-bundled) | Integration backend | HA 2024.1+ ships Python 3.12; no choice, no installation needed |
| `aiohttp` | HA-bundled (~3.9.x) | All HTTP calls to LibreTranslate | Already in HA's virtualenv; adding to `requirements` would install a conflicting copy |
| `voluptuous` | HA-bundled | Config flow schema validation | Bundled, do not re-require |
| LitElement | HA-bundled (via shadow DOM) | Lovelace card UI | Single-file no-build approach; avoids npm/webpack entirely |
| JavaScript (ES2020+) | No build step | Card logic | HA's built-in LitElement supports all modern JS |

### External APIs (No Python Libraries Needed)

All API communication is raw HTTP via `aiohttp.ClientSession`.

| API | Base URL | Auth | Notes |
|-----|----------|------|-------|
| LibreTranslate `/languages` | `GET http://{host}:{port}/languages` | Optional API key | Returns array of `{code, name, targets[]}` — the language catalog |
| LibreTranslate `/translate` | `POST http://{host}:{port}/translate` | Optional API key | Body: `{q, source, target, api_key?}` → Response: `{translatedText}` |
| LibreTranslate `/detect` | `POST http://{host}:{port}/detect` | Optional API key | Body: `{q}` → Response: `[{confidence, language}]` — out of scope for v1 |
| LibreTranslate `/frontend/settings` | `GET http://{host}:{port}/frontend/settings` | None | Returns server config including `apiKeys`, `suggestions` flags |

### HA Integration Patterns

| Pattern | Import | Purpose | Why |
|---------|--------|---------|-----|
| `ConfigFlow` | `homeassistant.config_entries` | Setup UI with host/port/API key | Required for HACS; enables UI-only setup |
| `DataUpdateCoordinator` | `homeassistant.helpers.update_coordinator` | Poll `/languages` for language list + server health | Single source of truth for available languages and server status |
| `CoordinatorEntity` | `homeassistant.helpers.update_coordinator` | Entity linked to coordinator | Auto-handles state updates and availability |
| `SensorEntity` | `homeassistant.components.sensor` | Status + language count sensors | Keep scaffold pattern |
| `SupportsResponse.ONLY` | `homeassistant.core` | Service call returns translated text | Lets automations use the response data directly |
| `async_register_static_paths` | `homeassistant.components.http` | Serve the .js card file | The old `register_static_path` is deprecated; removed in HA 2025.7 |
| `StaticPathConfig` | `homeassistant.components.http` | Path config dataclass | Required arg for `async_register_static_paths` |
| `runtime_data` on `ConfigEntry` | `homeassistant.config_entries` | Store coordinator on entry | Modern 2025 pattern replacing `hass.data[DOMAIN][entry.entry_id]` |

### Supporting Libraries (None — Zero pip Dependencies)

The `requirements` array in `manifest.json` should remain empty (`[]`). `aiohttp` handles all HTTP. `voluptuous` handles validation. `homeassistant.*` provides all framework patterns.

## Critical Stack Decisions

### 1. Service Registration Location

**Use `async_setup` (not `async_setup_entry`)** for the `translate` service.

**Why:** Services registered in `async_setup_entry` get re-registered on each config entry reload and unregistered on entry removal. Since the service name (`argos_translate.translate`) is domain-scoped (not entry-scoped), register once in `async_setup` and look up the active entry dynamically. This matches the HA pattern for domain-level services.

**Confidence:** HIGH — this is a well-documented HA pattern. `SupportsResponse.ONLY` services should use `async_setup` registration.

### 2. Service Call Response Pattern

**Use `SupportsResponse.ONLY`** — the translate service returns data as its primary function.

```python
hass.services.async_register(
    DOMAIN,
    "translate",
    handle_translate,
    schema=TRANSLATE_SCHEMA,
    supports_response=SupportsResponse.ONLY,
)
```

The handler returns `{"translated_text": "..."}` which automations can use in templates.

**Confidence:** HIGH — SupportsResponse was added in HA 2023.7 and is the standard pattern for data-returning services.

### 3. Card-to-Backend Communication

**Use `this.hass.callService()`** from the card to trigger translation.

The card calls the registered service and receives the response. This is simpler than WebSocket commands and works because `SupportsResponse` services return data through `callService`.

**Actually — correction:** `callService` in the frontend does NOT return response data in standard Lovelace card context. The card needs to use `this.hass.callWS()` with a custom WebSocket command, OR use the newer `this.hass.callService()` with `returnResponse: true` (added in HA 2023.12+).

**Recommended:** Use `this.hass.callService("argos_translate", "translate", {text, source, target}, {returnResponse: true})` — this was added specifically for `SupportsResponse` services.

**Confidence:** MEDIUM — the `returnResponse` parameter in frontend callService is relatively new. Verify against current HA frontend source.

### 4. Static Path Registration (HA 2025.7+)

**Use `async_register_static_paths`** with `StaticPathConfig`:

```python
from homeassistant.components.http import StaticPathConfig

async def async_setup(hass, config):
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            url_path="/argos-translate/argos-translate-card.js",
            path=str(Path(__file__).parent / "argos-translate-card.js"),
            cache_headers=True,
        )
    ])
```

The old `register_static_path()` is synchronous and was removed in HA 2025.7.

**Confidence:** HIGH — this migration is well-documented in HA developer docs.

### 5. aiohttp Session Management

**Use `async_get_clientsession(hass)`** — never create your own `aiohttp.ClientSession`.

```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession

session = async_get_clientsession(hass)
```

HA manages session lifecycle. Creating your own session leaks connections and fails the hassfest `inject-websession` quality scale rule.

**Confidence:** HIGH — mandatory HA pattern since 2023.

## Dependency Graph

```
LibreTranslate Server (Docker container, port 5500)
    ↑ HTTP (aiohttp)
    |
HA Integration (Python)
    ├── config_flow.py     → validates connection via GET /languages
    ├── coordinator.py     → polls GET /languages every 5 min
    ├── sensor.py          → status + language count from coordinator
    ├── __init__.py        → registers translate service + static path
    └── argos-translate-card.js → Lovelace card (LitElement)
         ↓ callService (with returnResponse)
         HA Integration → POST /translate → LibreTranslate
```

## Version Compatibility

| Component | Min Version | Notes |
|-----------|-------------|-------|
| Home Assistant | 2025.7+ | For `async_register_static_paths` |
| Python | 3.12+ | HA 2024.1+ requirement |
| LibreTranslate | 1.5+ | Stable REST API; `/languages` endpoint present since early versions |
| HACS | 2.0+ | For custom integration distribution |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LibreTranslate API changes | LOW — API has been stable for years | Pin to known-working endpoints |
| `returnResponse` not available in older HA | MEDIUM — breaks card translation | Set `min_version: "2024.1.0"` in manifest, document requirement |
| LibreTranslate server down | LOW — graceful degradation | Coordinator marks unavailable, card shows offline status |
| Slow translation on underpowered hardware | LOW — UX issue | Show loading spinner, consider timeout |
