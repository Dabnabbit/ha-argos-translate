# Architecture Research

**Domain:** Home Assistant HACS integration architecture for LibreTranslate
**Researched:** 2026-02-19
**Confidence:** HIGH (HA patterns), MEDIUM (LibreTranslate API specifics)

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Home Assistant                         │
│                                                          │
│  ┌──────────────┐    ┌───────────────────────────────┐  │
│  │  Config Flow  │    │    DataUpdateCoordinator      │  │
│  │              │    │    (polls /languages 5min)     │  │
│  │  host/port/  │    │                               │  │
│  │  api_key     │    │  data: {languages, status}    │  │
│  └──────┬───────┘    └──────────┬────────────────────┘  │
│         │                       │                        │
│         │              ┌────────┼────────┐               │
│         │              │        │        │               │
│         ▼              ▼        ▼        ▼               │
│  ┌─────────────┐ ┌─────────┐ ┌─────────────────┐       │
│  │ __init__.py  │ │ Status  │ │ Language Count   │       │
│  │             │ │ Sensor  │ │ Sensor           │       │
│  │ - service   │ └─────────┘ └─────────────────┘       │
│  │ - static    │                                        │
│  │   path      │                                        │
│  └──────┬──────┘                                        │
│         │                                                │
│  ┌──────▼──────────────────────────────────────────┐    │
│  │          Lovelace Card (LitElement)              │    │
│  │                                                  │    │
│  │  [Source ▼] [⇄] [Target ▼]                      │    │
│  │  ┌──────────────────────┐                        │    │
│  │  │ Input text...        │                        │    │
│  │  └──────────────────────┘                        │    │
│  │  [Translate]                                     │    │
│  │  ┌──────────────────────┐                        │    │
│  │  │ Translated text...   │ (read-only)            │    │
│  │  └──────────────────────┘                        │    │
│  │  ● Online · 24 languages                         │    │
│  │                                                  │    │
│  │  callService → argos_translate.translate          │    │
│  │  ← {translated_text: "..."}                      │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP (aiohttp)
                         ▼
              ┌──────────────────────┐
              │   LibreTranslate     │
              │   (Docker container) │
              │   Port 5500          │
              │                      │
              │   GET /languages     │
              │   POST /translate    │
              └──────────────────────┘
```

## Component Design

### 1. Config Flow (`config_flow.py`)

**Single step:**
- Host (default: `192.168.50.250`)
- Port (default: `5500`)
- API Key (optional — blank means no auth)

**Validation:**
- GET `http://{host}:{port}/languages`
- If 200 + non-empty array → valid
- If connection refused → "Cannot connect to LibreTranslate"
- If 403 → "API key required or invalid"

**Entry data structure:**
```python
{
    "host": "192.168.50.250",
    "port": 5500,
    "api_key": "",  # empty string if no key
}
```

**Use `runtime_data` pattern:**
```python
type ArgosTranslateConfigEntry = ConfigEntry[ArgosTranslateData]

@dataclass
class ArgosTranslateData:
    coordinator: ArgosTranslateCoordinator
```

### 2. API Client (`api.py`)

Separate class for API communication — keeps coordinator clean.

```python
class LibreTranslateClient:
    def __init__(self, session: ClientSession, host: str, port: int, api_key: str = ""):
        self._session = session
        self._base_url = f"http://{host}:{port}"
        self._api_key = api_key

    async def get_languages(self) -> list[dict]:
        """GET /languages → [{code, name, targets}]"""

    async def translate(self, text: str, source: str, target: str) -> str:
        """POST /translate → translatedText"""

    async def validate_connection(self) -> bool:
        """Test connection by fetching languages."""
```

**Key design decisions:**
- Accept `ClientSession` from `async_get_clientsession(hass)` — never create own session
- API key passed in POST body (not header) for `/translate` — LibreTranslate convention
- Timeout: 30 seconds for translate, 10 seconds for languages

### 3. DataUpdateCoordinator (`coordinator.py`)

**Polls:** GET /languages every 300 seconds (5 minutes)

**Stored data:**
```python
@dataclass
class ArgosTranslateCoordinatorData:
    languages: list[Language]  # [{code, name, targets}]
    status: str  # "online" | "error"
    language_count: int
    error_message: str | None
```

**Language data model:**
```python
@dataclass
class Language:
    code: str       # "en"
    name: str       # "English"
    targets: list[str]  # ["es", "ja", "fr", ...]
```

**Why poll /languages?**
- Serves double duty: health check + language catalog
- Languages change rarely (only when packages installed/removed)
- 5-minute interval is appropriate — not time-sensitive data

### 4. Sensors (`sensor.py`)

**Status sensor:**
- `unique_id`: `{entry_id}_status`
- `state`: "online" | "error"
- `device_class`: None (custom states)
- `attributes`: `{last_check, error_message}`

**Language count sensor:**
- `unique_id`: `{entry_id}_language_count`
- `state`: integer (e.g., 24)
- `attributes`: `{languages: [{code, name}]}`

Both extend `CoordinatorEntity` for automatic state management.

### 5. Service Registration (`__init__.py`)

```python
async def async_setup(hass, config):
    """Register translate service and static path."""

    async def handle_translate(call: ServiceCall) -> ServiceResponse:
        # Find active config entry
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("No Argos Translate configured")
        entry = entries[0]
        client = entry.runtime_data.coordinator.client

        text = call.data["text"]
        source = call.data["source"]
        target = call.data["target"]

        # Validate language pair
        languages = entry.runtime_data.coordinator.data.languages
        # ... validation logic ...

        result = await client.translate(text, source, target)
        return {"translated_text": result}

    hass.services.async_register(
        DOMAIN, "translate", handle_translate,
        schema=TRANSLATE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    # Register static path for card
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            url_path=f"/{DOMAIN}/argos-translate-card.js",
            path=str(Path(__file__).parent / "argos-translate-card.js"),
            cache_headers=True,
        )
    ])
```

**Critical:** Service registered in `async_setup` (not `async_setup_entry`) because it's domain-scoped. The handler dynamically looks up the active config entry.

### 6. Lovelace Card (`argos-translate-card.js`)

**State management:**
```javascript
static get properties() {
    return {
        hass: { type: Object },
        config: { type: Object },
        _sourceLanguage: { type: String },
        _targetLanguage: { type: String },
        _inputText: { type: String },
        _outputText: { type: String },
        _loading: { type: Boolean },
        _error: { type: String },
    };
}
```

**Language list from coordinator:**
The card reads language data from the sensor entity's attributes:
```javascript
get _languages() {
    const entity = this.hass.states[this.config.language_count_entity];
    return entity?.attributes?.languages || [];
}
```

**Translation flow:**
```javascript
async _translate() {
    this._loading = true;
    this._error = null;
    try {
        const result = await this.hass.callService(
            "argos_translate", "translate",
            { text: this._inputText, source: this._sourceLanguage, target: this._targetLanguage },
            { returnResponse: true }
        );
        this._outputText = result.response.translated_text;
    } catch (e) {
        this._error = e.message;
    } finally {
        this._loading = false;
    }
}
```

**Target language filtering:**
When source language changes, filter target dropdown to only show valid targets:
```javascript
get _availableTargets() {
    const sourceLang = this._languages.find(l => l.code === this._sourceLanguage);
    return sourceLang ? this._languages.filter(l => sourceLang.targets.includes(l.code)) : [];
}
```

**Swap button logic:**
```javascript
_swapLanguages() {
    const temp = this._sourceLanguage;
    this._sourceLanguage = this._targetLanguage;
    this._targetLanguage = temp;
    // Also swap text if output exists
    if (this._outputText) {
        this._inputText = this._outputText;
        this._outputText = "";
    }
}
```

### 7. Card Editor (`argos-translate-card.js` — same file)

**Editor config fields:**
- `entity` — language count sensor (for language list)
- `title` — card header text (default: "Translate")
- `default_source` — default source language code (default: "en")
- `default_target` — default target language code (default: "es")

## Data Flow

### Translation Request
```
User types text → clicks Translate
    → card.callService("argos_translate", "translate", {...}, {returnResponse: true})
    → HA dispatches to handle_translate()
    → handler validates language pair against coordinator data
    → handler calls client.translate()
    → client POSTs to LibreTranslate /translate
    → LibreTranslate returns {translatedText}
    → handler returns {translated_text}
    → card displays result in output area
```

### Language List Refresh
```
Coordinator timer fires (every 5 min)
    → coordinator calls client.get_languages()
    → client GETs LibreTranslate /languages
    → coordinator stores Language[] in data
    → sensors update (count, status)
    → card reads language list from sensor attributes
    → dropdowns reflect current language availability
```

## File Structure

```
custom_components/argos_translate/
├── __init__.py          # async_setup (service + static path), async_setup_entry
├── config_flow.py       # Single-step: host, port, api_key
├── coordinator.py       # DataUpdateCoordinator polling /languages
├── sensor.py            # Status + Language Count sensors
├── api.py               # LibreTranslateClient wrapper
├── const.py             # DOMAIN, DEFAULT_PORT, etc.
├── manifest.json        # HACS metadata
├── strings.json         # UI strings for config flow
├── services.yaml        # Service definition for translate
├── argos-translate-card.js  # LitElement card + editor
└── translations/
    └── en.json          # English translations
```

## Integration Points

### With HA Automations
```yaml
action:
  - service: argos_translate.translate
    data:
      text: "{{ trigger.payload }}"
      source: "en"
      target: "es"
    response_variable: translation
  - service: notify.mobile_app
    data:
      message: "{{ translation.translated_text }}"
```

### With Other Integrations
- **Whisper**: STT output → translate → TTS (Piper) — full speech translation pipeline
- **Notifications**: Translate notification text before display
- **Template sensors**: Create translated sensor values

## Key Architectural Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Translation latency on QNAP Celeron | 2-10 seconds per request | Loading spinner, 30s timeout, async non-blocking |
| Language list in sensor attributes might be large | Minor — ~30 languages × small objects | Keep it; dropdowns need the full list |
| Service registered in async_setup but entry not loaded yet | Race condition on restart | Guard: check for active entries before translating |
| Card reads from sensor attributes (indirect) | Coupling between card and sensor | Alternative: WebSocket command for language list (more complex) |
| `returnResponse: true` not available in older HA | Card breaks on old HA | Set min_version in manifest |
