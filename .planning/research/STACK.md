# Stack Research

**Domain:** Home Assistant HACS custom integration — v1.1 enhancement
**Researched:** 2026-02-21
**Confidence:** HIGH

## Scope

This document covers only net-new stack requirements for the three v1.1 features:
- Auto-detect source language (`source="auto"` + `/detect` endpoint)
- Reconfigure flow for credentials (host/port/API key without re-adding integration)
- Lovelace card polish (theming, accessibility, mobile responsiveness)

The existing validated stack (Python, aiohttp, voluptuous, DataUpdateCoordinator, LitElement) is established. No new core technologies are needed. All three features are pure extensions of existing code.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python (existing) | 3.12+ | Integration logic | No changes needed at the language/runtime level |
| aiohttp (existing) | HA-bundled | `async_detect()` + extended `async_translate()` | Already handles all HTTP; add one method and change one return type in `api.py` |
| LitElement (existing) | HA-bundled | Card UI with Auto-detect option | Existing component tree; only template and CSS changes needed |
| voluptuous (existing) | HA-bundled | Service schema — source field made optional | Already in use; minor schema change only |

### New HA Framework Patterns

These are HA-provided patterns, not new dependencies. They require import changes only.

| Pattern | Import | Purpose | Why This One |
|---------|--------|---------|--------------|
| `OptionsFlowWithReload` | `homeassistant.config_entries` | Replace `OptionsFlow` in options handler | Automatically reloads coordinator after save; eliminates need for manual `add_update_listener`. Available since HA 2025.8. |
| `async_step_reconfigure` | Method on `ConfigFlow` | Allow changing host/port/API key via "Reconfigure" menu item | HA-idiomatic for non-optional config data changes (credentials, host). Uses `async_update_reload_and_abort` — single call updates + reloads + closes flow. Preferred over OptionsFlow for credentials per HA developer docs. |
| `async_update_reload_and_abort` | Method on `ConfigFlow` | Save reconfigure data and reload | Eliminates the manual `async_update_entry` + separate reload that the existing OptionsFlow uses. |
| `_get_reconfigure_entry()` | Method on `ConfigFlow` | Access the entry being reconfigured | Required by `async_step_reconfigure` pattern. |

### Supporting Libraries

No new Python packages. No new JS imports.

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None (new) | — | — | Not justified for these features |

---

## Feature Stack Details

### Feature 1: Auto-Detect Source Language

**What needs to change:** `api.py` (add method, change return type), `services.py` (make source optional), `services.yaml` + `strings.json` (update docs), `argos_translate-card.js` (add "auto" option in source dropdown).

**LibreTranslate API — verified against official docs** (HIGH confidence):

**Pattern A: `source="auto"` in `/translate`** — RECOMMENDED:
```python
# Request
POST /translate
{"q": "Ciao!", "source": "auto", "target": "en", "api_key": "..."}

# Response
{
    "translatedText": "Hello!",
    "detectedLanguage": {"confidence": 83, "language": "it"}
}
```
Single round-trip. Detection + translation in one call. `detectedLanguage` is only present when `source="auto"`. Parse conditionally.

**Pattern B: Standalone `/detect` endpoint** — OPTIONAL:
```python
# Request
POST /detect
{"q": "Ciao!"}

# Response
[{"confidence": 90.0, "language": "fr"}, ...]   # sorted descending by confidence
```
Use only if the card needs to display the detected language name in the dropdown before the user hits Translate. Adds a round-trip; defer to future iteration.

**Concrete file changes:**

`api.py` — `async_translate` return type changes from `str` to `dict` (or keep str, add separate detect method):
```python
async def async_translate(self, text: str, source: str, target: str) -> dict[str, Any]:
    """Translate text. Returns dict with translatedText and optional detectedLanguage."""
    payload = {"q": text, "source": source, "target": target}
    if self._api_key:
        payload["api_key"] = self._api_key
    result = await self._request("POST", "/translate", json=payload)
    return result  # caller reads result["translatedText"] and result.get("detectedLanguage")

async def async_detect(self, text: str) -> list[dict[str, Any]]:
    """Detect language. Returns [{confidence, language}, ...] sorted by confidence."""
    return await self._request("POST", "/detect", json={"q": text})
```

`services.py` — source validation must be skipped when `source == "auto"` (server handles it):
```python
vol.Optional(ATTR_SOURCE, default="auto"): cv.string,
```

`argos_translate-card.js` — source dropdown adds "Auto-detect" as first option (value `"auto"`); after translation when source was "auto", optionally show detected language code in output area.

### Feature 2: Reconfigure Flow

**Decision: Add `async_step_reconfigure` to `ArgosTranslateConfigFlow`.**

The existing `OptionsFlowHandler` calls `async_update_entry(data=merged)` manually. This does NOT trigger a coordinator reload — settings apply only after a manual reload or HA restart. The fix is `async_step_reconfigure` which calls `async_update_reload_and_abort`.

`async_step_reconfigure` is accessed from the three-dot menu on the integration card → "Reconfigure". It updates `config_entry.data` (not options), which is correct since host/port/API key are setup-level credentials, not runtime preferences.

**Concrete code pattern** (HIGH confidence, from HA developer docs):
```python
async def async_step_reconfigure(
    self, user_input: dict[str, Any] | None = None
) -> ConfigFlowResult:
    """Allow reconfiguring connection credentials."""
    errors: dict[str, str] = {}
    entry = self._get_reconfigure_entry()

    if user_input is not None:
        merged = {**entry.data, **user_input}
        try:
            await _async_validate_connection(self.hass, merged)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except NoLanguages:
            errors["base"] = "no_languages"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_update_reload_and_abort(
                entry,
                data_updates=user_input,
            )

    return self.async_show_form(
        step_id="reconfigure",
        data_schema=vol.Schema({
            vol.Optional(CONF_HOST, default=entry.data.get(CONF_HOST, "")): str,
            vol.Optional(CONF_PORT, default=entry.data.get(CONF_PORT)): int,
            vol.Optional(CONF_USE_SSL, default=entry.data.get(CONF_USE_SSL, False)): bool,
            vol.Optional(CONF_API_KEY, default=entry.data.get(CONF_API_KEY, "")): str,
        }),
        errors=errors,
    )
```

**What about the existing OptionsFlowHandler?**

Option A — Keep it, convert to `OptionsFlowWithReload`:
```python
from homeassistant.config_entries import (
    ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlowWithReload,
)

class OptionsFlowHandler(OptionsFlowWithReload):  # was OptionsFlow
    ...
    # async_create_entry(data={}) now triggers automatic reload
```

Option B — Remove it. The "Reconfigure" flow covers all credential changes. Only keep OptionsFlow if there are genuine optional runtime preferences (e.g., polling interval). v1.1 has none.

**Recommendation: Add reconfigure + remove or simplify the options flow.** No optional runtime preferences exist yet, so the options flow adds UI noise without value.

`strings.json` additions required:
```json
"config": {
  "step": {
    "reconfigure": {
      "title": "Reconfigure LibreTranslate",
      "data": { "host": "Host", "port": "Port", "use_ssl": "Use HTTPS", "api_key": "API Key (optional)" }
    }
  }
}
```

### Feature 3: Card Polish

**No new imports. Pure CSS and HTML attribute additions.**

**Theming — use existing CSS variable pattern:**
The card already uses `--primary-color`, `--card-background-color`, `--primary-text-color`. Additions:
- `--secondary-background-color` for output textarea (already used but verify dark mode behavior)
- Explicit `outline: 2px solid var(--primary-color)` on `:focus` for `<select>` and `<textarea>` (many themes reset outline to none)
- `transition: opacity 0.15s ease` on the translate button for smooth disabled/enabled state

**Accessibility — ARIA additions:**
```html
<!-- Source textarea -->
<textarea aria-label="Text to translate" ...></textarea>

<!-- Output textarea -->
<textarea aria-label="Translation" readonly ...></textarea>

<!-- Swap button — currently only has title="" -->
<ha-icon-button aria-label="Swap source and target languages" ...></ha-icon-button>

<!-- Status / error area — announces changes to screen readers -->
<div role="status" aria-live="polite">
  ${this._error ? html`<ha-alert ...>` : ""}
</div>

<!-- Translate button during loading -->
<button aria-busy="${this._loading}" ...>
```

Add `<label>` elements (or `aria-label`) to both `<select>` elements — they currently have no accessible name.

**Mobile responsiveness — touch targets:**
```css
/* Swap button is the critical one — currently inherits 24px icon size */
ha-icon-button {
  min-width: 44px;
  min-height: 44px;
}

/* Textareas need a floor on mobile */
textarea {
  min-height: 80px;
}

/* Translate button already full-width, adequate target */
```

The `.lang-row` flex layout already wraps correctly on narrow viewports. No grid changes needed.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `source="auto"` in `/translate` (single round-trip) | Separate `POST /detect` then `/translate` | Only if card must show the detected language name in the source dropdown before user hits Translate; adds UX complexity for marginal gain |
| `async_step_reconfigure` for credential changes | Keeping existing `OptionsFlow` + `async_update_entry` | Existing flow works functionally but does not reload coordinator; use reconfigure for cleaner HA-idiomatic behavior |
| `OptionsFlowWithReload` (if keeping options flow) | Manual `entry.add_update_listener(update_listener)` in `__init__.py` | Listener pattern works but requires cleanup registration; OptionsFlowWithReload eliminates boilerplate |
| Raw `<select>` with CSS variables | `ha-select` (HA web component) | `ha-select` is an internal HA component with no stable custom-card API; risks breakage across HA versions |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| New `pip` requirements in `manifest.json` | Zero-pip constraint; aiohttp already bundled | aiohttp for all HTTP calls |
| External JS libraries (select2, choices.js) | Single JS file constraint; no build tooling | Native `<select>` with CSS variables |
| Card-mod as a dependency | Requires users to install a separate HACS package just for styling | Inline `static get styles()` CSS |
| `OptionsFlow` + `async_update_entry(data=merged)` without reload | Coordinator picks up stale settings until manual reload | `async_step_reconfigure` + `async_update_reload_and_abort` |
| Standalone `POST /detect` as primary auto-detect path | Extra round-trip; `source="auto"` on `/translate` returns `detectedLanguage` anyway | `source="auto"` on `/translate` |
| `ha-select` web component in card | Internal HA component; no documented API for custom cards; breaks across HA versions | Native `<select>` with HA CSS variables |

---

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|-----------------|-------|
| `OptionsFlowWithReload` | HA 2025.8+ | Introduced in HA 2025.8; project targets 2025.7+ — verify actual installed version before using; fall back to `OptionsFlow` + listener if needed |
| `async_step_reconfigure` | HA 2024.x+ | Longer-established; safe to use without version concerns |
| `async_update_reload_and_abort` | HA 2024.x+ | Stable helper; confirmed in 2025 docs |
| `source="auto"` on `/translate` | LibreTranslate 1.2+ | Confirmed working in 1.6.x and 1.8.x (latest as of 2026-02-21) |
| `POST /detect` endpoint | LibreTranslate 1.0+ | Core endpoint; stable across all versions |
| `detectedLanguage` in translate response | LibreTranslate 1.2+ | Only present when `source="auto"`; parse with `.get()` |

---

## Integration Architecture — Changed Files

```
api.py
  CHANGE: async_translate returns dict (was str)
  ADD:    async_detect(text) → list[dict]   # optional; for future UX

services.py
  CHANGE: ATTR_SOURCE optional (default="auto")
  CHANGE: skip language pair validation when source == "auto"
  CHANGE: read result["translatedText"] from dict return

config_flow.py
  ADD:    ArgosTranslateConfigFlow.async_step_reconfigure()
  CHANGE: OptionsFlowHandler(OptionsFlowWithReload)  # if retaining
            OR remove OptionsFlowHandler entirely

strings.json
  ADD:    config.step.reconfigure strings
  CHANGE: services.translate.fields.source — mark optional, document "auto"

services.yaml
  CHANGE: source field — mark required: false, add default and description update

argos_translate-card.js
  ADD:    "Auto-detect" as first <option value="auto"> in source select
  ADD:    Show detectedLanguage.language after translate (when source was "auto")
  ADD:    aria-label on both <textarea> elements
  ADD:    aria-label on swap ha-icon-button
  ADD:    role="status" aria-live="polite" on error/status container
  ADD:    aria-busy on translate button during loading
  ADD:    min 44px touch target CSS for ha-icon-button
  ADD:    min-height on textareas
  ADD:    explicit :focus outline styles for <select> and <textarea>
```

---

## Sources

- [LibreTranslate API Usage Guide](https://docs.libretranslate.com/guides/api_usage/) — /detect endpoint format, source="auto" behavior with confidence response (HIGH confidence — official docs)
- [LibreTranslate /translate endpoint reference](https://docs.libretranslate.com/api/operations/translate/) — detectedLanguage field in response, request parameters (HIGH confidence — official docs)
- [HA Options Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — OptionsFlowWithReload import path and code example (HIGH confidence — official HA developer docs)
- [HA Config Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — async_step_reconfigure, async_update_reload_and_abort, _get_reconfigure_entry (HIGH confidence — official HA developer docs)
- [HA developers.home-assistant GitHub](https://github.com/home-assistant/developers.home-assistant/blob/master/docs/config_entries_options_flow_handler.md) — OptionsFlowWithReload code example confirming import path (HIGH confidence)
- [HA Community: OptionsFlow data vs options](https://community.home-assistant.io/t/strange-behavior-with-optionflow-in-data-and-options-config-entry/855931/6) — async_step_reconfigure recommended over OptionsFlow for credential changes (MEDIUM confidence — community discussion)

---
*Stack research for: ha-argos-translate v1.1 (auto-detect, reconfigure, card polish)*
*Researched: 2026-02-21*
