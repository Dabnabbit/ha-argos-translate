# Phase 2: Translation Service + Card - Research

**Researched:** 2026-02-20
**Phase Goal:** Users can translate text via service call and Lovelace card

## Domain Research

### 1. SupportsResponse.ONLY Service Pattern

**How HA response-only services work:**

```python
from homeassistant.core import (
    HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse,
)

SERVICE_TRANSLATE = "translate"

SERVICE_SCHEMA = vol.Schema({
    vol.Required("text"): cv.string,
    vol.Required("source"): cv.string,
    vol.Required("target"): cv.string,
})

async def _async_handle_translate(call: ServiceCall) -> ServiceResponse:
    """Handle translate service call."""
    # Must return dict (JSON-serializable)
    return {"translated_text": "..."}

hass.services.async_register(
    DOMAIN,
    SERVICE_TRANSLATE,
    _async_handle_translate,
    schema=SERVICE_SCHEMA,
    supports_response=SupportsResponse.ONLY,
)
```

**Key patterns:**
- `SupportsResponse.ONLY` means service ONLY returns data, never fire-and-forget
- Handler signature: `async def handler(call: ServiceCall) -> ServiceResponse`
- Return value must be a JSON-serializable dict
- No `call.return_response` check needed with `.ONLY` — always returns
- Service is registered in `async_setup` (domain-scoped), already wired in template
- `@callback` decorator must NOT be used on async handlers (only for sync callbacks)

**services.yaml format:**
```yaml
translate:
  fields:
    text:
      required: true
      example: "Hello, how are you?"
      selector:
        text:
    source:
      required: true
      example: "en"
      selector:
        text:
    target:
      required: true
      example: "es"
      selector:
        text:
```

Note: The `response:` field in services.yaml is optional metadata. The response behavior is controlled by `supports_response=SupportsResponse.ONLY` in the Python registration. However, for HA UI clarity, we can omit the response field since `.ONLY` handles it.

### 2. Service Handler Accessing Coordinator Data

**Pattern for looking up coordinator from service handler:**

The service is registered in `async_setup` (domain-scoped), but coordinator instances are per-config-entry. The handler needs to find the right coordinator:

```python
async def _async_handle_translate(call: ServiceCall) -> ServiceResponse:
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ServiceValidationError("No Argos Translate instances configured")

    entry = entries[0]  # Use first entry
    coordinator = entry.runtime_data.coordinator

    # Validate languages against coordinator.data
    languages = coordinator.data.get("languages", [])
    # ... validate source/target ...

    translated = await coordinator.async_translate(text, source, target)
    return {"translated_text": translated}
```

**Error handling imports:**
```python
from homeassistant.exceptions import ServiceValidationError, HomeAssistantError
```
- `ServiceValidationError` — for user input errors (bad language pair)
- `HomeAssistantError` — for server/connection errors during translation

### 3. Language Validation Logic

**LibreTranslate /languages response structure:**
```json
[
  {"code": "en", "name": "English", "targets": ["es", "fr", "de", "ja"]},
  {"code": "es", "name": "Spanish", "targets": ["en", "fr"]},
  {"code": "ja", "name": "Japanese", "targets": ["en"]}
]
```

**Validation steps:**
1. Find source language in `coordinator.data["languages"]` by code
2. If not found → `ServiceValidationError(f"Unknown source language: {source}")`
3. Check if target is in source language's `targets` list
4. If not found → `ServiceValidationError(f"Cannot translate from {source} to {target}")`

### 4. Lovelace Custom Card with hass.callService

**Getting LitElement from HA:**
```javascript
const LitElement = customElements.get("hui-masonry-view")
  ? Object.getPrototypeOf(customElements.get("hui-masonry-view"))
  : Object.getPrototypeOf(customElements.get("hui-view"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;
```

**Calling a service with response:**
```javascript
const result = await this.hass.callService(
  "argos_translate",   // domain
  "translate",         // service
  {                    // serviceData
    text: inputText,
    source: sourceLang,
    target: targetLang,
  },
  {},     // target (empty — no entity targeting)
  true,   // notifyOnError
  true    // returnResponse — REQUIRED for response data
);

// Response structure:
// result.response = { translated_text: "..." }
```

**Key discovery:** The `hass.callService()` function signature is:
```
callService(domain, service, serviceData, target, notifyOnError, returnResponse)
```
The 6th parameter `returnResponse` MUST be `true` to receive response data. Without it, only context (user_id, context_id) is returned.

### 5. Card Dropdown Pattern (ha-select)

**HA native dropdown using `<select>` with Lit:**
```javascript
html`
  <select @change="${this._sourceChanged}">
    ${this._languages.map(lang => html`
      <option value="${lang.code}" ?selected="${lang.code === this._source}">
        ${lang.name} (${lang.code})
      </option>
    `)}
  </select>
`
```

**Alternative using ha-select (HA Material component):**
```javascript
html`
  <ha-select
    .label=${"Source Language"}
    .value=${this._source}
    @selected="${this._sourceChanged}"
    @closed="${(e) => e.stopPropagation()}"
  >
    ${this._languages.map(lang => html`
      <ha-list-item .value="${lang.code}">
        ${lang.name} (${lang.code})
      </ha-list-item>
    `)}
  </ha-select>
`
```

Note: `ha-select` wraps Material Web's `md-select`. The `@closed` handler with `stopPropagation()` prevents the dropdown from closing the card editor dialog. Use `mwc-list-item` or `ha-list-item` for options.

### 6. Card State Management

**Reading sensor attributes for language list:**
```javascript
const entityId = this.config.entity; // binary_sensor.argos_translate_status
const stateObj = this.hass.states[entityId];

// For languages, need the language_count sensor
const langEntity = this.config.language_entity; // sensor.argos_translate_language_count
const langState = this.hass.states[langEntity];
const languages = langState?.attributes?.languages || [];
const languageCodes = langState?.attributes?.language_codes || [];
```

**Issue: Language list is in sensor attributes, but we need the full structure (code, name, targets) for target filtering.**

The language count sensor stores:
- `languages` attribute: list of language names (["English", "Spanish", ...])
- `language_codes` attribute: list of codes (["en", "es", ...])

But `targets` per language is NOT in the sensor attributes. This means:
- **Option A:** Add targets to sensor extra_state_attributes (could be large)
- **Option B:** Card calls GET /languages directly (bypasses HA abstraction)
- **Option C:** Add a separate service `argos_translate.get_languages` that returns full language data
- **Option D:** Store targets in coordinator data and expose via a new attribute format

**Recommendation:** Option A is simplest — add a `language_targets` attribute to the sensor that maps source codes to their target code lists: `{"en": ["es", "fr", "de"], "es": ["en", "fr"]}`. This keeps everything in HA state and avoids extra API calls.

### 7. Card Editor Pattern

```javascript
class ArgosTranslateCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
    };
  }

  setConfig(config) {
    this.config = config;
  }

  render() {
    return html`
      <div class="editor">
        <ha-entity-picker
          label="Status Entity"
          .hass="${this.hass}"
          .value="${this.config.entity || ""}"
          @value-changed="${this._entityChanged}"
          .includeDomains="${["binary_sensor"]}"
          allow-custom-entity
        ></ha-entity-picker>
        <ha-textfield
          label="Header"
          .value="${this.config.header || ""}"
          @input="${this._headerChanged}"
        ></ha-textfield>
      </div>
    `;
  }

  _updateConfig(key, value) {
    const newConfig = { ...this.config, [key]: value };
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: newConfig },
      bubbles: true,
      composed: true,
    }));
  }
}
```

### 8. strings.json for Services

Service descriptions in HA are localized via `strings.json`:

```json
{
  "services": {
    "translate": {
      "name": "Translate text",
      "description": "Translate text between languages using LibreTranslate.",
      "fields": {
        "text": {
          "name": "Text",
          "description": "The text to translate."
        },
        "source": {
          "name": "Source language",
          "description": "The source language code (e.g., 'en')."
        },
        "target": {
          "name": "Target language",
          "description": "The target language code (e.g., 'es')."
        }
      }
    }
  }
}
```

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Response pattern | SupportsResponse.ONLY | Service is read-only, always returns data |
| Error type | ServiceValidationError | HA's built-in error for user input validation |
| Coordinator lookup | First config entry | Single-instance primary use case |
| Language targets in card | Sensor attribute | Avoids extra API calls, keeps data in HA state |
| Card dropdown | `<select>` or `ha-select` | Native HA component for theme compatibility |
| Service callService | returnResponse: true | Required for getting translated text back |

## Codebase Patterns to Follow

From Phase 1 implementation:
- `@callback` decorator only on sync functions (not async handlers)
- `async_register_services` is called in `async_setup` (domain-scoped)
- Coordinator data accessed via `entry.runtime_data.coordinator`
- API errors wrapped in descriptive messages
- CSS uses HA custom properties for theming

## Open Questions Resolved

1. **How does the card get language targets?** → Add `language_targets` dict to sensor `extra_state_attributes`
2. **How does the service find the coordinator?** → `hass.config_entries.async_entries(DOMAIN)[0].runtime_data.coordinator`
3. **What errors does the service raise?** → `ServiceValidationError` for bad input, `HomeAssistantError` for server errors
4. **How does the card call the service with response?** → `hass.callService(domain, service, data, {}, true, true)` — 6th param is `returnResponse`

---

*Phase: 02-translation-service-card*
*Researched: 2026-02-20*
