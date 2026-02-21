# Pitfalls Research

**Domain:** Home Assistant HACS integration — v1.1 milestone pitfalls
**Researched:** 2026-02-21
**Confidence:** HIGH (HA integration patterns from official docs), MEDIUM (LibreTranslate detection edge cases from community sources)

This document covers two scopes:
1. **v1.0 pitfalls** (carried forward from initial research — already avoided in implementation)
2. **v1.1 pitfalls** (new — specific to auto-detect language, options flow, card polish, and deploy)

---

## Critical Pitfalls

### Pitfall 1: Coordinator Not Rebuilt After Options Flow Saves New Connection Details

**What goes wrong:**
The options flow calls `async_update_entry(config_entry, data=merged)` and returns `async_create_entry(data={})`. HA reloads the entry (calls `async_setup_entry` again), which creates a new `ArgosCoordinator`. The coordinator constructor reads `entry.data` to build the API client — but if the new data is written to `entry.options` (not `entry.data`), the coordinator still uses the old host/port/API key. Translation continues going to the old server silently.

**Why it happens:**
Options flow `async_create_entry(data={})` stores the return value in `entry.options`, not `entry.data`. The current implementation merges and writes to `entry.data` via `async_update_entry` before calling `async_create_entry`, which is correct — but it is fragile and non-standard. The HA-idiomatic path for connection credential changes is the `reconfigure` step, not an options flow. If a future refactor changes where data is read from, or if the merge logic has a bug, the wrong client gets constructed silently.

**How to avoid:**
The current implementation writes merged credentials back to `entry.data` using `async_update_entry` before returning from the options flow. Verify the coordinator reads exclusively from `entry.data` (not `entry.options`). Add a log line in coordinator `__init__` confirming the host being used, so real-world deployment can verify the reload picked up the new address.

The HA docs recommend `async_step_reconfigure` for changing non-optional connection parameters (host, port, API key). Consider documenting that the options flow is the reconfiguration mechanism for this integration, since adding a separate reconfigure step would be redundant.

**Warning signs:**
- After saving new host in options flow, translation still succeeds (it should fail if server is unreachable)
- Logs show old host URL in coordinator after reload
- No `async_setup_entry` log entry for the new host after saving options

**Phase to address:** Phase 1 (options flow implementation) — verify reload behavior with a real HA instance before considering done

---

### Pitfall 2: /detect Endpoint Returns Empty Array or Zero-Confidence Result

**What goes wrong:**
LibreTranslate `/detect` returns `[{"confidence": 5.0, "language": "en"}]` for short text or ambiguous input. The array is sorted by confidence descending. For very short text (< 5 characters), single words, or text in poorly-supported languages, CLD2 (the underlying detector) returns low confidence values and may return results that are outright wrong. If the integration takes `result[0]["language"]` blindly and populates the source dropdown, users get a wrong language pre-selected silently.

The `/detect` endpoint does not return HTTP errors for low-confidence detection — it always returns a 200 with the best guess. The endpoint can also return an empty array `[]` if the text is empty or whitespace-only (LibreTranslate strips whitespace before sampling).

**Why it happens:**
CLD2 is designed for pages of 200+ characters. Single words ("hello"), proper nouns, and short phrases fail reliably. LibreTranslate's hybrid detector (CLD2 + LexiLang since 2023) improves short-text handling but does not eliminate low-confidence results. The client bears full responsibility for interpreting confidence thresholds.

**How to avoid:**
Apply a minimum confidence threshold before accepting the result. A threshold of 50.0 is reasonable:
```javascript
// In card JS
async _detectLanguage(text) {
  if (!text || text.trim().length < 5) return null; // too short to detect reliably
  try {
    const result = await this.hass.callService("argos_translate", "detect", { text }, {}, true, true);
    const detected = result.response?.detected_language;
    const confidence = result.response?.confidence ?? 0;
    if (!detected || confidence < 50) return null; // insufficient confidence
    return detected;
  } catch {
    return null; // detection failure is non-fatal
  }
}
```
Or in the Python service handler, return `null`/`None` for confidence below 50 and let the card treat it as "no detection available."

Display confidence to the user so they can judge: "Detected: English (87%)" rather than silently setting the dropdown.

**Warning signs:**
- Auto-detect pre-selects the wrong language for short inputs
- Detection works for long paragraphs but fails for single words
- Languages not installed on the LibreTranslate server may be "detected" (the detector is language-agnostic, it can detect beyond the installed set)

**Phase to address:** Phase 2 (auto-detect feature) — design the confidence threshold and UX flow before implementing

---

### Pitfall 3: Detected Language Not in Available Languages List

**What goes wrong:**
LibreTranslate's `/detect` endpoint detects from the full CLD2/LexiLang set, which includes hundreds of languages. The `/languages` endpoint only returns languages with installed models. A user types French text; `/detect` returns `"fr"` with high confidence; `"fr"` is not in the coordinator's language list (only `en`, `es`, `ja` installed). The card silently ignores the detection result or throws an error when trying to set the source dropdown to an unknown code.

**Why it happens:**
Detection and translation use different language sets. The detector operates on a global vocabulary; the translator only works with installed model pairs. There is no API constraint linking detection to installed languages.

**How to avoid:**
After receiving a detection result, validate the code against the coordinator's known language codes before using it:
```javascript
const { codes } = this._getLanguages();
if (detected && codes.includes(detected)) {
  this._source = detected;
} else {
  // Show message: "Detected: French (not installed)"
  this._detectionMessage = `Detected ${detectedName} — not available on this server`;
}
```
Show a user-visible message when detection succeeds but the language is not installable, rather than failing silently.

**Warning signs:**
- Detection returns a code not present in the source dropdown
- No error is shown but the source dropdown does not change after clicking detect
- Console errors about unknown language code

**Phase to address:** Phase 2 (auto-detect) — validate against available languages before applying

---

## Moderate Pitfalls

### Pitfall 4: Options Flow Storing Data in entry.options Instead of entry.data

**What goes wrong:**
If `async_create_entry(data=user_input)` is called in the options flow handler (which stores data in `entry.options`), the coordinator which reads from `entry.data` will not pick up the changed values. The old host/port is used after reload, but the options flow shows the new values — a confusing mismatch.

**Why it happens:**
The standard OptionsFlow pattern stores values in `entry.options`. The current implementation avoids this by calling `async_update_entry(config_entry, data=merged)` before returning `async_create_entry(data={})`. This is non-standard but intentional because connection credentials belong in `entry.data`.

**How to avoid:**
Keep the current pattern: merge credentials into `entry.data` via `async_update_entry`, then return `async_create_entry(data={})` to signal completion. Add a comment explaining why this deviates from the standard options pattern. Verify in real HA deployment that after saving options, the coordinator logs show the new host being used.

**Warning signs:**
- `entry.options` has the new values but `entry.data` still has old values after options flow completes
- Coordinator connects to old server after options are saved

**Phase to address:** Phase 1 (options flow) — add verification step in deployment testing

---

### Pitfall 5: Auto-Detect Triggering on Every Keypress (Debounce Missing)

**What goes wrong:**
If auto-detect fires on the `input` event of the textarea (every keypress), the card calls the translate service or a detect service for each character typed. On a local network this is low-latency, but it creates rapid-fire service calls visible in HA logs and unnecessary load on LibreTranslate. LibreTranslate may also have rate limiting enabled.

**Why it happens:**
LitElement's `@input` event fires synchronously on each keystroke. Without debouncing, binding detection to this event sends requests on every character.

**How to avoid:**
Debounce the detection call with a 600–800ms delay:
```javascript
_inputChanged(ev) {
  this._inputText = ev.target.value;
  clearTimeout(this._detectTimeout);
  this._detectTimeout = setTimeout(() => this._autoDetect(), 700);
}
```
Or use a manual "Detect Language" button instead of auto-detection on input, which avoids the debounce problem entirely and gives the user explicit control.

**Warning signs:**
- HA log shows dozens of detect service calls per second while typing
- LibreTranslate server shows high request rate from HA
- Network tab in browser DevTools shows rapid-fire requests

**Phase to address:** Phase 2 (auto-detect feature) — decide on button vs. auto-detect and implement debounce if choosing auto

---

### Pitfall 6: Browser Caches Old Card JS After Update

**What goes wrong:**
When the card JS is updated (e.g., from v0.2.0 to v0.3.0), the browser serves the cached version. The static path is registered with `cache_headers=True`, which sets long cache headers. Users see the old card behavior even after HA restarts. This is especially problematic on mobile (iOS Companion App has a persistent cache).

**Why it happens:**
`StaticPathConfig(cache_headers=True)` tells HA to set long-lived `Cache-Control` headers. Browser caches respect these headers until they expire. The integration does not include a version query parameter in the URL.

**How to avoid:**
Use a versioned URL or query parameter that changes when the file changes. The community convention is to append `?v=VERSION`:
```python
FRONTEND_SCRIPT_URL = f"/{DOMAIN}/{DOMAIN}-card.js"
# In Lovelace resource registration:
versioned_url = f"{FRONTEND_SCRIPT_URL}?v={CARD_VERSION}"
```
Alternatively, tell users in the README to do Settings > Developer Tools > Empty Browser Cache after updates, or use the iOS Companion App's "Reset frontend cache" button.

Update the `CARD_VERSION` constant in the JS file on every change — browsers will treat the new query string as a new resource.

**Warning signs:**
- After deploying updated card, behavior matches old version
- `console.log` in the new card is not visible in browser DevTools
- iOS app shows old card after HA restart

**Phase to address:** Phase 3 (deploy + stabilize) — before doing real-hardware deploy, ensure versioning strategy is in place

---

### Pitfall 7: Card UX — select Elements Do Not Match HA Theme

**What goes wrong:**
Native `<select>` elements use OS-default styling and do not inherit HA's CSS variables properly. On dark theme, `<select>` dropdowns may show white text on white background or black text on dark background, making the dropdown unreadable. This is particularly broken on mobile Safari (iOS), where select styling is heavily controlled by the OS.

**Why it happens:**
Shadow DOM encapsulation of LitElement prevents external CSS from reaching the card's internal elements. Native `<select>` elements are also styled by the browser/OS, not by HA themes. HA's theme CSS variables (like `--card-background-color`, `--primary-text-color`) are accessible inside shadow DOM but are not automatically applied to form controls.

**How to avoid:**
Explicitly apply HA CSS variables to select elements in the card's `static get styles()`:
```css
select {
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color, #000);
  border: 1px solid var(--divider-color, #ccc);
}
/* For dark theme compatibility: */
@media (prefers-color-scheme: dark) {
  select option {
    background: var(--card-background-color, #1a1a1a);
    color: var(--primary-text-color, #fff);
  }
}
```
The existing card already applies these variables, but test on both light and dark theme with real HA to verify the select element remains readable.

Prefer HA's `<ha-select>` web component over native `<select>` — it handles theming automatically — but note it requires importing from HA's internal module path, which may change between HA versions.

**Warning signs:**
- Source/target dropdowns unreadable in dark mode
- Dropdown options invisible (same color as background)
- iOS shows unstyled iOS-native picker

**Phase to address:** Phase 2 (card polish) — test on dark theme before shipping

---

### Pitfall 8: Options Flow Translation Strings Missing for "init" Step

**What goes wrong:**
The options flow `async_step_init` form shows raw field keys (`host`, `port`, etc.) instead of human-readable labels if the `strings.json` file is missing the `options.step.init` section. HA's config flow UI uses these translations to render field labels and descriptions. Missing translations cause the form to render with internal key names.

**Why it happens:**
`strings.json` has separate sections for `config` (initial setup) and `options` (options flow). The `options.step.init` section must mirror the field keys shown in the options form. If it was not added when the options flow was implemented, the UI renders bare keys.

**How to avoid:**
The existing `strings.json` already has the `options.step.init` section with `host`, `port`, `use_ssl`, and `api_key` labels and descriptions — this is correctly implemented. Also ensure `translations/en.json` is kept in sync with `strings.json`. Run `hassfest` locally to verify:
```bash
python -m script.hassfest --action validate
```

**Warning signs:**
- Options form shows `host` and `port` as field labels instead of "Host" and "Port"
- hassfest validation outputs translation warnings
- Options flow form looks different from the config flow form for same fields

**Phase to address:** Phase 1 (options flow) — hassfest check before real deployment

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store connection credentials in `entry.data` via `async_update_entry` from options flow (non-standard) | Connection credentials accessible in coordinator constructor without reading options | Confusing for future maintainers; HA may enforce stricter data/options separation | Acceptable for this integration's lifetime — document the pattern |
| Native `<select>` instead of `<ha-select>` | No HA module import required, simpler code | Theming inconsistency across HA themes and platforms | Acceptable if explicit CSS variable overrides are applied |
| Auto-detect calls translate service (not a dedicated detect endpoint call) | Reuses existing service machinery | Adds latency (services go through HA's event bus) — consider direct API call from Python | Acceptable for v1.1 — revisit if latency is a user complaint |
| Single JS file (no build toolchain) | Zero build complexity, simpler deployment | No TypeScript, no minification, larger files, harder to add dependencies | Acceptable for this project's scope indefinitely |
| Hardcoded confidence threshold (50.0) | Simple to implement | May be too high or too low for specific language pairs; no tuning path | Acceptable for v1.1 — document as a known limitation |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LibreTranslate /detect | Treating the first array element as definitive | Check confidence score; show uncertainty to user; validate against installed languages |
| LibreTranslate /detect | Calling detect with empty or whitespace-only string | Guard: `if text.strip()` before calling; return `None` for empty input |
| HA options flow | Saving data to `entry.options` when coordinator reads from `entry.data` | Explicitly call `async_update_entry(entry, data=new_data)` before `async_create_entry` |
| HA static path | Cache headers cause stale JS after card update | Append version query parameter to registered Lovelace resource URL |
| HA config entry reload | Coordinator holds old client object after options flow reload | Verify coordinator `__init__` re-reads `entry.data` on each reload; log the host being used |
| LitElement shadow DOM | CSS theme variables not reaching `<select>` option elements | Override `select` and `select option` in `static get styles()` with explicit HA CSS variable values |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Auto-detect on every keypress | Rapid service calls, slow UI, server overload | Debounce 600–800ms or use explicit detect button | Immediately if not debounced |
| Coordinator polling interval too short | LibreTranslate gets polled every 30s instead of every 5min | Keep `DEFAULT_SCAN_INTERVAL = 300`; `/languages` is stable data | N/A — current setting is correct |
| Translation timeout too short | "Request timed out" on longer texts on slow hardware | Use 30s timeout (already implemented) | Texts > ~200 words on QNAP Celeron |
| Card re-renders on every hass update | Unnecessary DOM churn | LitElement's reactive properties already handle this correctly; no action needed | N/A — current implementation is correct |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging API key in coordinator or config flow | API key exposed in HA logs | Never log `CONF_API_KEY` value; log only its presence/absence |
| Sending detected text to external service | Privacy: user text leaves local network | /detect endpoint is on the local LibreTranslate instance — no external calls; document this |
| Accepting raw language codes from /detect in service calls | Injection if detect result used directly in API calls | Language codes are simple ISO 639-1 strings; no injection risk from their structure, but validate against known codes anyway |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No feedback when auto-detect returns low-confidence result | User does not know detection was uncertain; may translate from wrong language | Show confidence indicator: "Detected: English (62%)" with visual cue for low confidence |
| Detect button active when text is empty | Clicking detect on empty input triggers an API call that returns empty array | Disable detect button when input is empty/whitespace (< 3 characters) |
| Source dropdown changes silently when auto-detect fires | User may be mid-selection when detect fires and overrides their choice | Only apply detection result if source is still at default/initial value, not if user explicitly selected |
| No "detected language not available" message | User types text, detection succeeds, but nothing happens — source dropdown unchanged | Show message when detected language is not in installed list |
| Mobile: textarea too small to type comfortably | On phone, 4-row textarea is cramped | Use `min-height: 120px` and `resize: vertical` to give mobile users room; test on real mobile |
| Dark mode: translate button uses `--primary-color` which may have poor contrast | Text unreadable on some themes | Explicitly set `color: var(--text-primary-color, white)` on button — already done, verify on real hardware |

---

## "Looks Done But Isn't" Checklist

These items appear complete from code review but require real-HA validation to confirm.

- [ ] **Options flow saves to entry.data:** After saving options, verify `entry.data` (not just `entry.options`) has the new values via HA Settings > Integrations > integration detail view
- [ ] **Coordinator rebuilt after options:** After saving options, check HA logs for `async_setup_entry` being called and coordinator connecting to the new host
- [ ] **Auto-detect: detected language code validated against installed languages:** Verify with a language not installed on the server (e.g., type Portuguese text when only en/es/ja are installed)
- [ ] **Auto-detect: confidence threshold applied:** Test with a single word — verify no auto-apply happens, or a "low confidence" indicator shows
- [ ] **Dark theme card readability:** Load card on HA dark theme — verify both dropdowns, textareas, and button are readable
- [ ] **Mobile layout:** View card on phone-sized screen — verify no horizontal scroll, dropdowns usable, textareas touchable
- [ ] **Browser cache after JS update:** After bumping `CARD_VERSION`, verify new behavior appears without manual cache clear (versioned URL strategy)
- [ ] **hassfest passes after adding detect service:** If a `detect` service is added to `services.yaml` and `strings.json`, run hassfest before deploying
- [ ] **HACS action passes:** Run the HACS validation GitHub Action after any changes to `manifest.json`, `hacs.json`, or `strings.json`
- [ ] **Options form labels correct:** Open the options flow on real HA — verify field labels are "Host", "Port", "Use HTTPS", "API Key" not bare keys

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Coordinator uses old host after options save | LOW | Reload integration manually from Integrations UI; verify logs |
| Auto-detect fires on every keypress | LOW | Add debounce setTimeout, bump card version, reload browser |
| Browser serving stale card JS | LOW | Hard-refresh (Ctrl+Shift+R), or Settings > Developer Tools > Empty cache in HA |
| Detected language not available on server | LOW | Show user-visible message; no code crash |
| Options translation strings missing | LOW | Add to strings.json and translations/en.json; restart HA |
| Dark theme select unreadable | LOW | Add CSS override in static get styles(); bump CARD_VERSION |
| hassfest fails after adding detect service | LOW | Fix strings.json schema, re-run hassfest, push fix |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Coordinator not rebuilt after options flow | Phase 1 — options flow implementation | Real HA test: change host, verify coordinator reconnects |
| /detect returns empty or low-confidence | Phase 2 — auto-detect feature | Test with 1-char, 3-char, 10-char inputs; verify threshold behavior |
| Detected language not in available list | Phase 2 — auto-detect feature | Test with language not installed on LibreTranslate server |
| Options data stored in wrong property | Phase 1 — options flow | Inspect `config_entries.async_entries(DOMAIN)[0].data` after save |
| Auto-detect without debounce | Phase 2 — auto-detect feature | Monitor HA logs while typing rapidly |
| Browser cache stale card JS | Phase 3 — deploy + stabilize | Deploy updated card to real HA; verify new behavior without cache clear |
| Dark theme select unreadable | Phase 2 — card polish | Test on HA dark theme on real hardware |
| Options flow translation strings missing | Phase 1 — options flow | Run hassfest locally before deploying |

---

## Carried-Forward Pitfalls (v1.0 — Already Avoided)

The following pitfalls from v1.0 research are already correctly handled in the codebase and are recorded here for reference only.

| Pitfall | Status |
|---------|--------|
| `register_static_path` removed in HA 2025.7 | RESOLVED — `async_register_static_paths` with `StaticPathConfig` used |
| aiohttp session leak | RESOLVED — `async_get_clientsession(hass)` used throughout |
| Service registered in `async_setup_entry` | RESOLVED — Service registered in `async_setup` |
| Missing `unique_id` on config entry | RESOLVED — `host:port` used as unique_id |
| API key in POST body (not header) | RESOLVED — `payload["api_key"]` pattern used |
| `iot_class` mismatch in manifest | RESOLVED — `local_polling` set |
| Language pair validation before API call | RESOLVED — validated in service handler |
| Translation timeout | RESOLVED — `DEFAULT_TIMEOUT = 30` |
| `callService` with `returnResponse` compatibility | RESOLVED — `min_version` set in manifest |
| Empty input handling | RESOLVED — button disabled when input empty |

---

## Sources

- [Home Assistant Options Flow documentation](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — OptionsFlowWithReload, data vs options storage
- [Home Assistant Config Flow documentation](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — reconfigure vs options flow distinction
- [LibreTranslate API Usage docs](https://docs.libretranslate.com/guides/api_usage/) — /detect response format (`[{"confidence": 90.0, "language": "fr"}]`)
- [LibreTranslate /detect community discussion](https://community.libretranslate.com/t/does-detect-return-false/2033) — confidence threshold is client responsibility, not server
- [LibreTranslate language detection issue #395](https://github.com/LibreTranslate/LibreTranslate/issues/395) — CLD2 failures for German, Japanese, English; hybrid detector implemented Oct 2023
- [CLD2 design limitations](https://github.com/CLD2Owners/cld2) — designed for 200+ character texts; quadgrams ignored for very short text
- [HA static path async registration](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — cache_headers=True sets long-lived headers
- [HA frontend cache issues iOS](https://github.com/home-assistant/iOS/issues/3738) — persistent browser cache on mobile requires manual reset
- [HA hassfest deprecation: options flow config_entry explicit](https://github.com/hacs/integration/issues/4314) — HA 2025.1 deprecated explicit config_entry in options flow
- [LibreTranslate LexiLang](https://github.com/LibreTranslate/LexiLang) — dictionary-based short-text detector, < 20 char focus

---
*Pitfalls research for: Home Assistant HACS integration v1.1 milestone*
*Researched: 2026-02-21*
