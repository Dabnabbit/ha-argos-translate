# Phase 1: API Client + Data Layer - Research

**Researched:** 2026-02-20
**Domain:** LibreTranslate API integration for Home Assistant (custom component)
**Confidence:** HIGH

## Summary

Phase 1 customizes an existing ha-hacs-template scaffold to connect to a self-hosted LibreTranslate server. The template already provides correct patterns for `DataUpdateCoordinator`, `CoordinatorEntity`, `ConfigEntry.runtime_data`, `config_flow` with `unique_id`, options flow, and `async_get_clientsession`. The work is purely LibreTranslate-specific: replacing placeholder endpoints with `/languages` and `/translate`, changing auth from Bearer header to POST body API key, creating a binary connectivity sensor and a language count sensor, and updating config flow fields.

LibreTranslate's API is simple and well-documented: `GET /languages` returns `[{code, name, targets}]`, `POST /translate` accepts `{q, source, target, api_key}`. The `/languages` endpoint serves double duty as both the health check and the data source, simplifying the coordinator.

**Primary recommendation:** Keep changes minimal and surgical — the template patterns are correct, only the endpoint URLs, auth mechanism, field schemas, and sensor entities need replacing. Do not restructure the integration architecture.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- No default port — require user to enter their port explicitly
- Separate host and port fields with an HTTP/HTTPS toggle (HTTP default)
- Validate connection by hitting GET /languages before allowing setup to complete — hard gate, no skip
- User-provided name field for the integration entry (used as device name and entity prefix)
- API key field always visible but optional — masked (password-style) input
- Full options flow for reconfiguration (change host, port, API key, SSL) — validates connection on save
- **Status sensor:** Binary sensor with `device_class: connectivity` — on when server is reachable, off when not
- **Status sensor:** Minimal — just the on/off state, no extra attributes
- **Language count sensor:** State is the installed language count (numeric) — disabled by default
- **Language count sensor attributes:** List of installed languages with English + native names (e.g., "Japanese (日本語)"), plus total available count if the API provides it
- **Icons:** `mdi:server` for status, `mdi:translate` for language count
- **Status sensor enabled by default, language count sensor disabled by default**
- Create an HA device per config entry — groups sensors under the user-provided name
- Use HA's built-in DataUpdateCoordinator unavailability handling — no custom offline logic
- Entities go unavailable when server is unreachable, restore automatically when it returns
- No custom log warnings on failure — HA's coordinator logging is sufficient
- Connection validation on both initial setup and options flow save
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

### Deferred Ideas (OUT OF SCOPE)
- Lightweight LibreTranslate Docker image without web GUI — future project (custom FastAPI wrapper)
- Auto-detect source language support — Phase 2 or later
- Translation pairs display (which languages can translate to which) — evaluate during Phase 2 card work
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONF-01 | User can configure LibreTranslate host and port with connection validation (GET /languages) | LibreTranslate GET /languages returns language array; empty or error = invalid. Template config_flow pattern already validates connection. |
| CONF-02 | User can optionally configure API key (blank for instances without auth) | API key goes in POST body `api_key` field. vol.Optional with default="" handles blank. |
| CONF-03 | Config flow shows clear error for connection refused, invalid API key, or empty language list | CannotConnectError covers connection refused/timeout. InvalidAuthError covers 403. Empty language list needs explicit check. |
| SENS-01 | Status sensor shows "online" or "error" based on coordinator poll success | BinarySensorEntity with device_class CONNECTIVITY. is_on derives from coordinator last_update_success. |
| SENS-02 | Language count sensor shows number of available source languages | SensorEntity with native_value = len(coordinator.data["languages"]). |
| SENS-03 | Language count sensor attributes include language list (codes + names) | extra_state_attributes returns language list from coordinator data. /languages provides code + name. |
| SENS-04 | Sensors update via DataUpdateCoordinator polling /languages every 5 minutes | Template coordinator already uses DataUpdateCoordinator. Set update_interval=timedelta(seconds=300). |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| homeassistant | 2025.7+ | Integration host framework | Target platform |
| aiohttp | (bundled with HA) | HTTP client for LibreTranslate API calls | HA provides shared session via async_get_clientsession |
| voluptuous | (bundled with HA) | Config flow schema validation | Standard HA config validation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| homeassistant.helpers.update_coordinator | bundled | DataUpdateCoordinator for polling | All data fetching |
| homeassistant.components.binary_sensor | bundled | BinarySensorEntity + BinarySensorDeviceClass | Status connectivity sensor |
| homeassistant.components.sensor | bundled | SensorEntity | Language count sensor |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| aiohttp (shared session) | httpx | aiohttp is HA standard; httpx would add dependency |
| DataUpdateCoordinator | Manual polling | Coordinator handles retry, backoff, unavailability for free |

**Installation:** No additional packages needed — all from HA core.

## Architecture Patterns

### Recommended Project Structure
```
custom_components/argos_translate/
├── __init__.py          # Entry setup, runtime_data, platform forwarding
├── api.py               # LibreTranslate API client (aiohttp)
├── config_flow.py       # Config + Options flows with connection validation
├── const.py             # Domain, defaults, field constants
├── coordinator.py       # DataUpdateCoordinator polling /languages
├── sensor.py            # Language count sensor (SensorEntity)
├── binary_sensor.py     # Status connectivity sensor (BinarySensorEntity) — NEW file
├── manifest.json        # Integration metadata
├── services.py          # Service registration (Phase 2)
├── services.yaml        # Service schema (Phase 2)
├── strings.json         # Config flow strings
├── translations/en.json # English translations
└── frontend/            # Lovelace card (Phase 2)
```

### Pattern 1: Coordinator Data Shape
**What:** Coordinator's `_async_update_data` returns a typed dict with status and language data.
**When to use:** Every coordinator poll cycle.
**Example:**
```python
# coordinator.py — _async_update_data return shape
{
    "languages": [
        {"code": "en", "name": "English", "targets": ["es", "fr", ...]},
        {"code": "es", "name": "Spanish", "targets": ["en", "fr", ...]},
    ],
    "language_count": 48,
}
```
The coordinator does NOT store "status" explicitly — the coordinator's own `last_update_success` property handles that. When the API call fails, `UpdateFailed` is raised, coordinator sets `last_update_success = False`, and entities using `CoordinatorEntity` automatically go unavailable.

### Pattern 2: Binary Sensor from Coordinator Success
**What:** Status sensor derives `is_on` from `self.coordinator.last_update_success`.
**When to use:** When you need a connectivity binary sensor that reflects whether the polled service is reachable.
**Example:**
```python
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class ArgosStatusSensor(CoordinatorEntity[ArgosCoordinator], BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success
```

### Pattern 3: API Key in POST Body (Not Header)
**What:** LibreTranslate expects `api_key` in the POST request body, not as a Bearer token header.
**When to use:** All POST requests to LibreTranslate.
**Example:**
```python
# api.py — translate method
async def async_translate(self, text: str, source: str, target: str) -> str:
    payload = {"q": text, "source": source, "target": target}
    if self._api_key:
        payload["api_key"] = self._api_key
    result = await self._request("POST", "/translate", json=payload)
    return result["translatedText"]
```

### Pattern 4: Config Flow with HTTP/HTTPS Toggle
**What:** Use a boolean `use_ssl` field in config to toggle between http:// and https:// base URL.
**When to use:** Config flow and API client URL construction.
**Example:**
```python
# const.py
CONF_USE_SSL = "use_ssl"

# config_flow.py schema
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT): int,  # No default — user must enter
    vol.Optional(CONF_USE_SSL, default=False): bool,
    vol.Optional(CONF_API_KEY, default=""): str,
})

# api.py — URL construction
scheme = "https" if use_ssl else "http"
self._base_url = f"{scheme}://{host}:{port}"
```

### Pattern 5: Disabled-by-Default Entity
**What:** Language count sensor is disabled by default in entity registry.
**When to use:** Sensors that most users won't need.
**Example:**
```python
class ArgosLanguageCountSensor(CoordinatorEntity[ArgosCoordinator], SensorEntity):
    _attr_entity_registry_enabled_default = False
    _attr_has_entity_name = True
```

### Anti-Patterns to Avoid
- **Custom unavailability logic:** Don't add custom retry/offline handling — DataUpdateCoordinator handles this. Setting `last_update_success` and entity `available` property is automatic.
- **Storing status in coordinator data:** Don't put "online"/"error" in the data dict. Use `coordinator.last_update_success` instead.
- **Bearer auth header for LibreTranslate:** The API key goes in the POST body, not as `Authorization: Bearer`. GET requests to /languages don't need auth.
- **Polling /health or /translate for status:** /languages is the canonical health check AND data source. One endpoint, one poll.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Polling with retry/backoff | Custom timer + retry loop | DataUpdateCoordinator | Handles retry, exponential backoff, unavailability, logging |
| Entity unavailability | Custom `available` property + tracking | CoordinatorEntity base class | Automatic — goes unavailable when coordinator fails |
| HTTP session management | Create/close aiohttp sessions | async_get_clientsession(hass) | HA manages session lifecycle |
| Unique ID dedup | Custom duplicate checking | _abort_if_unique_id_configured() | Built-in config flow method |
| Config validation UI | Custom error rendering | Config flow errors dict | HA renders error strings from strings.json |

**Key insight:** The ha-hacs-template already provides all of these patterns correctly. The customization is endpoint-specific, not architectural.

## Common Pitfalls

### Pitfall 1: Auth Header vs Body
**What goes wrong:** Sending API key as Bearer token header when LibreTranslate expects it in the POST body.
**Why it happens:** The template uses Bearer header auth by default.
**How to avoid:** Remove `_get_auth_headers()` override, add `api_key` to POST body payloads when key is non-empty. GET /languages does NOT need auth.
**Warning signs:** 403 errors or "invalid API key" from LibreTranslate.

### Pitfall 2: Empty Language List as Success
**What goes wrong:** GET /languages returns 200 with `[]` (no language models installed), treated as successful connection.
**Why it happens:** HTTP status is 200 so no error is raised.
**How to avoid:** After GET /languages, check `if not languages:` and raise a specific error (e.g., "no_languages" error key in config flow).
**Warning signs:** Config flow accepts setup but sensors show 0 languages.

### Pitfall 3: Binary Sensor Needs Separate Platform
**What goes wrong:** Trying to create a BinarySensorEntity in `sensor.py`.
**Why it happens:** Template only has sensor.py, not binary_sensor.py.
**How to avoid:** Create `binary_sensor.py` as a new file. Add `Platform.BINARY_SENSOR` to PLATFORMS list in `__init__.py`.
**Warning signs:** Entity doesn't appear as binary sensor in HA, wrong icon/states.

### Pitfall 4: Missing CONF_NAME in Config Entry
**What goes wrong:** User-provided name not stored, entry title defaults to hostname.
**Why it happens:** Template uses `title=user_input[CONF_HOST]` instead of user name.
**How to avoid:** Add `CONF_NAME` to schema and config entry data, use for `async_create_entry(title=...)`.
**Warning signs:** Device shows as "192.168.1.100" instead of "My LibreTranslate".

### Pitfall 5: Options Flow Not Validating Connection
**What goes wrong:** User changes host/port in options but new values aren't validated.
**Why it happens:** Template options flow updates entry data without calling `_async_validate_connection`.
**How to avoid:** Add connection validation to options flow's `async_step_init` before updating entry.
**Warning signs:** Options save succeeds but coordinator immediately fails on next poll.

### Pitfall 6: Config Flow API Key as Required
**What goes wrong:** User can't complete setup without entering an API key.
**Why it happens:** Template has `vol.Required(CONF_API_KEY)`.
**How to avoid:** Change to `vol.Optional(CONF_API_KEY, default="")`. Most local LibreTranslate instances don't use API keys.
**Warning signs:** Config flow validation fails with "required field" error for keyless servers.

## Code Examples

### LibreTranslate /languages Response
```json
[
  {
    "code": "en",
    "name": "English",
    "targets": ["ar", "az", "bg", "bn", "ca", "cs", "da", "de", "el", "eo", "es", "et", "fa", "fi", "fr", "ga", "he", "hi", "hu", "id", "it", "ja", "ko", "lt", "lv", "ms", "nb", "nl", "pl", "pt", "ro", "ru", "sk", "sl", "sq", "sr", "sv", "tl", "th", "tr", "uk", "ur", "vi", "zh", "zh-Hant", "zt"]
  },
  {
    "code": "ja",
    "name": "Japanese",
    "targets": ["en", "es", "fr", ...]
  }
]
```
Source: Direct fetch from https://libretranslate.com/languages (HIGH confidence)

### LibreTranslate /translate Request/Response
```
POST /translate
Content-Type: application/json

{
  "q": "Hello, how are you?",
  "source": "en",
  "target": "es",
  "api_key": ""
}

Response:
{
  "translatedText": "Hola, \u00bfc\u00f3mo est\u00e1s?"
}
```
Source: https://docs.libretranslate.com/guides/api_usage/ (HIGH confidence)

### Coordinator _async_update_data
```python
async def _async_update_data(self) -> dict[str, Any]:
    """Fetch language data from LibreTranslate."""
    try:
        languages = await self.client.async_get_languages()
    except CannotConnectError as err:
        raise UpdateFailed(f"Error communicating with API: {err}") from err

    return {
        "languages": languages,
        "language_count": len(languages),
    }
```

### Language Count Sensor with Attributes
```python
class ArgosLanguageCountSensor(CoordinatorEntity[ArgosCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:translate"
    _attr_native_unit_of_measurement = "languages"

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("language_count")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.coordinator.data is None:
            return None
        languages = self.coordinator.data.get("languages", [])
        return {
            "languages": [
                f"{lang['name']}" for lang in languages
            ],
            "language_codes": [lang["code"] for lang in languages],
        }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `async_register_static_paths` as list | `StaticPathConfig` dataclass | HA 2025.7 | Template already uses new pattern |
| `hass.data[DOMAIN]` dict | `ConfigEntry.runtime_data` typed dataclass | HA 2024.x | Template uses typed runtime_data |
| `should_poll = True` | CoordinatorEntity (should_poll=False) | HA 2020 | Standard for coordinated entities |
| `entity_platform.EntityPlatformModule` | `Platform` enum | HA 2023.x | Template uses `Platform.SENSOR` etc. |

**Deprecated/outdated:**
- `hass.data[DOMAIN][entry.entry_id]` dict pattern: Use `ConfigEntry.runtime_data` typed dataclass instead
- `async_register_static_paths` with raw args: Use `StaticPathConfig` dataclass

## Open Questions

1. **Native language names in attributes**
   - What we know: User wants "Japanese (日本語)" format. LibreTranslate /languages only returns English name.
   - What's unclear: Whether LibreTranslate provides native names or if we need a mapping table.
   - Recommendation: Start with English names from API. Note in sensor attributes that native names could be added later if a mapping source is found. Keep it simple for Phase 1.

2. **Translation pairs as sensor attribute**
   - What we know: User marked this as Claude's discretion. /languages returns `targets` array per language.
   - What's unclear: Whether this data is useful in Phase 1 (before the card exists).
   - Recommendation: Skip for Phase 1. The `targets` data is stored in coordinator data and accessible. Phase 2 card will use it directly. No need to expose as sensor attribute yet.

3. **Total available language count from Argos package index**
   - What we know: User asked whether to fetch this. It's available from Argos Translate package index.
   - What's unclear: Whether this adds value when the user can see installed count already.
   - Recommendation: Skip. This would require an additional HTTP call to an external service, which conflicts with "local only" philosophy. Only show installed languages.

## Sources

### Primary (HIGH confidence)
- LibreTranslate /languages endpoint — direct fetch confirms `[{code, name, targets}]` response format
- https://docs.libretranslate.com/guides/api_usage/ — /translate POST parameters and response format
- https://developers.home-assistant.io/docs/core/entity/binary-sensor/ — BinarySensorEntity with device_class CONNECTIVITY
- https://developers.home-assistant.io/docs/integration_fetching_data/ — DataUpdateCoordinator pattern

### Secondary (MEDIUM confidence)
- https://aarongodfrey.dev/home%20automation/use-coordinatorentity-with-the-dataupdatecoordinator/ — CoordinatorEntity usage patterns
- Template codebase (custom_components/argos_translate/) — existing patterns to customize

### Tertiary (LOW confidence)
- None — all findings verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are HA built-in, no external dependencies
- Architecture: HIGH — template provides correct patterns, customization is straightforward
- Pitfalls: HIGH — all identified from direct code review of template + LibreTranslate API docs
- LibreTranslate API: HIGH — response formats verified against live endpoint

**Research date:** 2026-02-20
**Valid until:** 2026-03-20 (stable — HA core patterns and LibreTranslate API are mature)
