# Pitfalls Research

**Domain:** Home Assistant HACS integration pitfalls for LibreTranslate translation
**Researched:** 2026-02-19
**Confidence:** HIGH (HA integration patterns), MEDIUM (LibreTranslate API edge cases)

## Pitfall Catalog

### PITFALL-01: `register_static_path` Removed in HA 2025.7

**Severity:** CRITICAL — Integration fails to load on modern HA
**Phase Impact:** Phase 1 (integration setup)

**Problem:**
The old `hass.http.register_static_path()` is synchronous and was deprecated in HA 2024.x, then removed in HA 2025.7. If the scaffold template still uses it, the integration will crash on modern HA.

**Fix:**
```python
from homeassistant.components.http import StaticPathConfig

await hass.http.async_register_static_paths([
    StaticPathConfig(
        url_path=f"/{DOMAIN}/argos-translate-card.js",
        path=str(Path(__file__).parent / "argos-translate-card.js"),
        cache_headers=True,
    )
])
```

**Detection:** hassfest and hacs/action will flag this.

### PITFALL-02: aiohttp Session Leak

**Severity:** HIGH — Connection pool exhaustion over time
**Phase Impact:** Phase 1 (API client)

**Problem:**
Creating `aiohttp.ClientSession()` manually instead of using HA's shared session. Manual sessions leak if not explicitly closed, and even if closed, duplicate HA's connection pool management.

**Fix:**
```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession
session = async_get_clientsession(hass)
```

Never call `session.close()` — HA manages lifecycle.

**Detection:** hassfest `inject-websession` quality scale rule.

### PITFALL-03: Service Registration in `async_setup_entry`

**Severity:** MEDIUM — Service re-registered on reload, unregistered on entry removal
**Phase Impact:** Phase 2 (service call)

**Problem:**
If the `translate` service is registered in `async_setup_entry`, it gets re-registered each time the config entry reloads and unregistered when the entry is removed. Since the service name is domain-scoped (`argos_translate.translate`), this causes:
- Duplicate registration warnings in logs
- Service disappearing when entry is reloaded
- Potential race conditions with multiple entries

**Fix:**
Register in `async_setup` (which runs once per domain) and dynamically look up the active config entry in the handler:
```python
async def async_setup(hass, config):
    async def handle_translate(call):
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries or not entries[0].runtime_data:
            raise HomeAssistantError("Argos Translate not configured")
        # use entries[0].runtime_data.coordinator.client
    hass.services.async_register(DOMAIN, "translate", handle_translate, ...)
```

### PITFALL-04: Missing `unique_id` on Config Entry

**Severity:** MEDIUM — Allows duplicate config entries
**Phase Impact:** Phase 1 (config flow)

**Problem:**
If `ConfigFlow.async_step_user` doesn't set a `unique_id` and call `self._abort_if_unique_id_configured()`, users can add the same LibreTranslate server multiple times.

**Fix:**
```python
async def async_step_user(self, user_input=None):
    if user_input:
        unique_id = f"{user_input['host']}:{user_input['port']}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
```

### PITFALL-05: LibreTranslate API Key in POST Body (Not Header)

**Severity:** LOW — Subtle API difference causes auth failures
**Phase Impact:** Phase 2 (service call)

**Problem:**
Unlike arr services that use `X-Api-Key` header, LibreTranslate expects the API key in the POST body as `api_key` field, not as a header. Using a header will silently succeed on instances without auth but fail on auth-required instances.

**Fix:**
```python
async def translate(self, text, source, target):
    payload = {"q": text, "source": source, "target": target}
    if self._api_key:
        payload["api_key"] = self._api_key
    async with self._session.post(f"{self._base_url}/translate", json=payload) as resp:
        data = await resp.json()
        return data["translatedText"]
```

### PITFALL-06: `iot_class` Mismatch in `manifest.json`

**Severity:** LOW — Fails hassfest validation
**Phase Impact:** Phase 1 (manifest)

**Problem:**
The scaffold might default to `cloud_polling` or leave `iot_class` blank. Since LibreTranslate is on the local network, it should be `local_polling`.

**Fix:**
```json
{
    "iot_class": "local_polling"
}
```

### PITFALL-07: Language Pair Not Available

**Severity:** MEDIUM — Silent translation failure or error
**Phase Impact:** Phase 2 (service call), Phase 3 (card)

**Problem:**
Not all source→target combinations are available in LibreTranslate. If a user requests en→ja but Japanese isn't installed, LibreTranslate returns an error. The card and service need to validate before sending.

**Fix:**
- Service handler: Validate against coordinator's language data before calling API
- Card: Filter target dropdown based on source language's `targets[]` array
- Return clear error: "Translation from {source} to {target} is not available"

### PITFALL-08: Translation Timeout on Slow Hardware

**Severity:** MEDIUM — UX issue, potential timeout error
**Phase Impact:** Phase 2 (service call), Phase 3 (card)

**Problem:**
On QNAP's Celeron J4125, Argos Translate can take 5-15 seconds for longer texts. Default aiohttp timeout (5s) or HA service call timeout (10s) may not be enough.

**Fix:**
- API client: Use `timeout=aiohttp.ClientTimeout(total=30)` for translate calls
- Card: Show loading spinner immediately, don't freeze UI
- Service: Document that translation is async and may take time

### PITFALL-09: `callService` with `returnResponse` Compatibility

**Severity:** MEDIUM — Card translation broken on older HA
**Phase Impact:** Phase 3 (card)

**Problem:**
The `returnResponse: true` option for `this.hass.callService()` was added in HA 2023.12. On older HA versions, the card can't receive translation results through the service call.

**Fix:**
- Set `"min_version": "2024.1.0"` in manifest.json (conservative minimum)
- Alternative: Register a WebSocket command instead of using service response
- Preference: Use `returnResponse` — it's simpler and the min_version covers it

### PITFALL-10: Empty/Whitespace Input Translation

**Severity:** LOW — UX issue
**Phase Impact:** Phase 3 (card)

**Problem:**
User clicks Translate with empty input. LibreTranslate will return an empty string or error.

**Fix:**
- Card: Disable Translate button when input is empty/whitespace
- Service: Return empty translated_text for empty input (don't error)

### PITFALL-11: services.yaml Missing or Malformed

**Severity:** MEDIUM — Service doesn't appear in Developer Tools / automations
**Phase Impact:** Phase 2 (service registration)

**Problem:**
If `services.yaml` is missing or doesn't match the registered service schema, the service won't appear in HA's Developer Tools → Services and won't be usable in the automation UI.

**Fix:**
```yaml
translate:
  name: Translate text
  description: Translate text between languages using LibreTranslate
  fields:
    text:
      name: Text
      description: The text to translate
      required: true
      example: "Hello, how are you?"
      selector:
        text:
    source:
      name: Source language
      description: Source language code (ISO 639-1)
      required: true
      example: "en"
      selector:
        text:
    target:
      name: Target language
      description: Target language code (ISO 639-1)
      required: true
      example: "es"
      selector:
        text:
```

### PITFALL-12: Card Resource Registration

**Severity:** MEDIUM — Card not found in Lovelace
**Phase Impact:** Phase 3 (card)

**Problem:**
Even after `async_register_static_paths`, the card JS file needs to be registered as a Lovelace resource. Users must manually add it or the integration must register it automatically.

**Fix:**
Two approaches:
1. **Manual:** Document in README that user must add `/argos-translate/argos-translate-card.js` as a resource
2. **Auto-register:** Use `lovelace_resources` in manifest or call `async_register_panel`

HACS handles this automatically via `hacs.json`:
```json
{
    "name": "Argos Translate",
    "render_readme": true,
    "content_in_root": false
}
```

But the integration still needs to register the static path. HACS registration of the resource URL happens at HACS install time.

### PITFALL-13: Coordinator Not Ready When Service Called

**Severity:** MEDIUM — Error on first call after restart
**Phase Impact:** Phase 2 (service call)

**Problem:**
If the service is called immediately after HA restart, the coordinator may not have completed its first poll yet. `entry.runtime_data` could be None or coordinator.data could be empty.

**Fix:**
```python
async def handle_translate(call):
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise HomeAssistantError("Argos Translate not configured")
    entry = entries[0]
    if not hasattr(entry, 'runtime_data') or not entry.runtime_data:
        raise HomeAssistantError("Argos Translate is still initializing")
    coordinator = entry.runtime_data.coordinator
    if not coordinator.data:
        raise HomeAssistantError("Waiting for language data from LibreTranslate")
```

## Phase-to-Pitfall Mapping

| Phase | Relevant Pitfalls |
|-------|-------------------|
| Phase 1: Integration Core | PITFALL-01, 02, 04, 06 |
| Phase 2: Service Call | PITFALL-03, 05, 07, 08, 11, 13 |
| Phase 3: Lovelace Card | PITFALL-09, 10, 12 |
| Phase 4: HACS Distribution | PITFALL-01, 06, 12 |

## "Looks Done But Isn't" Checklist

- [ ] `register_static_path` replaced with `async_register_static_paths`
- [ ] `async_get_clientsession(hass)` used (not manual session)
- [ ] `unique_id` set in config flow
- [ ] `iot_class: local_polling` in manifest
- [ ] `services.yaml` present and matches registered service
- [ ] Language pair validation before API call
- [ ] API key in POST body (not header)
- [ ] 30-second timeout on translate calls
- [ ] Empty input handling in card
- [ ] `min_version` set in manifest for `returnResponse` compatibility
- [ ] Service registered in `async_setup` (not `async_setup_entry`)
- [ ] Coordinator readiness check in service handler

## Recovery Strategies

| Pitfall | If Hit During Development | If Hit In Production |
|---------|--------------------------|---------------------|
| PITFALL-01 | Replace in code, test with hassfest | Urgent patch release |
| PITFALL-02 | Refactor to use shared session | May need HA restart to clear leaked connections |
| PITFALL-03 | Move registration to async_setup | Service may disappear on reload until fixed |
| PITFALL-05 | Check LibreTranslate logs for auth errors | Update API client |
| PITFALL-07 | Add validation before API call | Users see error message |
| PITFALL-08 | Increase timeout | Users wait longer but it works |
| PITFALL-09 | Add WebSocket fallback or set min_version | Users must update HA |
