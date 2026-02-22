# Phase 5: Auto-Detect + Card Polish - Research

**Researched:** 2026-02-22
**Domain:** LibreTranslate auto-detect API, HA service layer, Lovelace LitElement card polish
**Confidence:** HIGH (backend), HIGH (card UI patterns), MEDIUM (error code discrimination)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Detection feedback display:**
- After auto-detect translation, the source dropdown label updates from "Auto-detect" to show the detected language (e.g., "Auto (French)")
- Detection results include candidate languages above a confidence threshold, shown as options in the source dropdown (e.g., "Auto (French)", "Auto (Spanish)")
- Selecting a detected candidate re-translates using that language as a fixed source — lets users correct a bad detection
- Dropdown label auto-updates immediately after translation completes (no need to open dropdown to see result)

**Auto-detect dropdown behavior:**
- "Auto-detect" appears as the first item in the source dropdown, visually separated from the alphabetical language list
- "Auto-detect" is the default source selection when the card first loads
- When source is "Auto-detect", the target dropdown shows all available languages (not filtered by source)

**Mobile layout & responsive behavior:**
- Card supports both vertical (stacked) and horizontal (side-by-side like Google Translate) layouts
- Default behavior is auto-responsive: wide cards show horizontal layout (input left, output right), narrow cards stack vertically
- Card config provides a layout override: user can force "Horizontal", "Vertical", or "Auto" (default)
- Language row (dropdowns + swap button) wraps cleanly at narrow widths

**Accessibility:**
- ARIA labels on all form controls are sufficient — no additional keyboard navigation or high contrast requirements beyond standard HA card behavior

### Claude's Discretion

- Error message presentation style (inline, banner, or below output) — pick what fits HA card conventions
- Disabled button explanation approach (tooltip vs helper text) — pick what works on both desktop and mobile
- Error auto-dismiss behavior (timed vs persistent)
- Error visual treatment (uniform style vs severity-based colors)
- Whether to show an indication that target filtering is off when source is Auto-detect
- Message wording for uninstalled detected language case

### Deferred Ideas (OUT OF SCOPE)

- Dropdown usage history — frequently/recently used languages migrate toward the top of language dropdowns (requires persistent storage, separate feature)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DTCT-01 | User can select "Auto" as source language in the card dropdown | Card JS: add sentinel value `"auto"` as first `<option>` in source `<select>`; initializes to `"auto"` by default |
| DTCT-02 | Service call accepts `source: "auto"` and returns translated text with detected language info | `api.py` `async_translate` passes source through to LibreTranslate which accepts `"auto"` natively; `services.py` must skip source-language validation when source is `"auto"` and parse `detectedLanguage` from response |
| DTCT-03 | Service response includes `detected_language` code and `detection_confidence` when source was "auto" | LibreTranslate returns `{"translatedText": "...", "detectedLanguage": {"language": "fr", "confidence": 90.0}}`; `api.py` must return full dict instead of just `result["translatedText"]`; service handler surfaces these fields in `ServiceResponse` |
| DTCT-04 | Card target dropdown shows all available targets when source is "Auto" | Card JS: when `_source === "auto"`, compute `validTargets` as union of all language codes instead of `targets[source]` |
| DTCT-05 | Card displays detected language label (e.g. "Detected: French (90%)") after auto-translate | Card JS: new reactive property `_detectedLanguage`; populate from service response; display below output textarea |
| DTCT-06 | Card handles case where detected language is not installed (shows user-visible message) | Service: when detected language code is not in the installed languages list, raise `HomeAssistantError` with a descriptive message rather than silently returning empty translation |
| CPOL-01 | Card shows specific error messages (connection error vs. bad request vs. timeout) | HA WebSocket error object has `{code, message}` properties; `code` can be `"home_assistant_error"` (from `HomeAssistantError`), `"service_validation_error"` (from `ServiceValidationError`), `"unknown_error"`, `"request_error"` (connection lost/network); card JS `catch` block should inspect `err.code` and `err.message` to compose specific messages |
| CPOL-02 | Card explains why translate button is disabled | Card JS: compute a `_disabledReason` string derived from which condition is blocking translate; render it as helper text beneath the button |
| CPOL-03 | All form controls have ARIA labels for screen reader accessibility | Card JS: add `aria-label` attributes to `<select>` and `<textarea>` elements; `<ha-icon-button>` already accepts `title` but also needs `aria-label`; no external library required |
| CPOL-04 | Card layout stacks properly on mobile/narrow screens (flex-wrap on language row) | Card JS CSS: `flex-wrap: wrap` on `.lang-row` already partially there; add responsive two-column layout using CSS `container queries` or `ResizeObserver` |
</phase_requirements>

---

## Summary

Phase 5 has two distinct work streams that touch different layers of the stack: (1) backend auto-detect support and (2) card UI polish. Both are well-scoped and low-risk.

**Backend auto-detect** is straightforward. LibreTranslate natively accepts `source: "auto"` on its `/translate` endpoint and returns a `detectedLanguage` object with `language` (ISO code) and `confidence` (float 0–100) in the response. The `/detect` endpoint returns an *array* of candidates ordered by confidence. The card's context decision specifies showing multiple candidates from a `/detect`-style call, but the `/translate` endpoint only returns the single highest-confidence language. To present candidates in the dropdown, the implementation must either (a) call `/detect` separately before or after translation, or (b) accept that only one candidate is shown per translation. The `services.py` source-language validation currently rejects `"auto"` as an unknown language code — that guard must be bypassed for `source == "auto"`. The `api.py` `async_translate` currently returns only `result["translatedText"]` and must be extended to return the full response dict (or a structured object) when auto-detect is requested.

**Card polish** involves four areas: specific error messages (map WebSocket error codes/types to user-friendly strings), disabled-button explanation (compute reason string from current state), ARIA labels (add `aria-label` to selects and textareas — pure HTML attributes), and responsive layout. The responsive layout is the most design-intensive item: the user wants a Google Translate-style horizontal split (input left, output right) on wide cards and vertical stacking on narrow ones, with an override config option. The card already uses `flex` but lacks the two-pane structure. CSS container queries are the modern approach and are supported by all current browsers, though they require the card's `:host` to be set as a container. `ResizeObserver` is a fallback approach that sets a data attribute to drive CSS classes.

**Primary recommendation:** Use a single `/detect` call to get candidates for the dropdown (make it a separate API method), pass `source: "auto"` to `/translate` directly, then merge results. Implement the responsive layout with CSS container queries — they work inside Shadow DOM without any JavaScript.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| LitElement (via HA host element) | Same HA version as deployed | Card reactive rendering | Already the project's card foundation |
| aiohttp | Already in HA | HTTP client for `/detect` and `/translate` | Already in use via `api.py` |
| voluptuous | Already in HA | Service schema validation | Already in use via `services.py` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| CSS Container Queries (native browser) | Baseline 2023+ | Responsive card layout without JS | When responsive layout should respond to card width, not viewport width |
| ResizeObserver (native browser) | Baseline 2020+ | JS-driven layout class based on rendered width | Fallback if container queries cause Shadow DOM issues |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS container queries | Media queries | Media queries respond to viewport, not card width — wrong for Lovelace panels |
| CSS container queries | ResizeObserver + JS class | More code, same result; container queries are simpler |
| Separate `/detect` call for candidates | Parsing `/translate` response only | `/translate` only returns one candidate; `/detect` returns array with multiple candidates |

**Installation:** No new packages required. All dependencies already present.

---

## Architecture Patterns

### Recommended Project Structure

No structural changes needed. All changes land in:

```
custom_components/argos_translate/
├── api.py              # new: async_detect_languages(), extend async_translate() return type
├── coordinator.py      # new: async_detect_languages() passthrough
├── services.py         # modify: skip source validation for "auto", return detected_language fields
├── strings.json        # new: translation keys for auto-detect errors
└── frontend/
    └── argos_translate-card.js   # bulk of changes: auto-detect UI, layout, errors, ARIA
```

---

### Pattern 1: LibreTranslate Auto-Detect Response

**What:** LibreTranslate `/translate` with `source: "auto"` returns `detectedLanguage` in addition to `translatedText`.

**When to use:** Any time `source == "auto"` is passed.

**Example:**
```json
// POST /translate  {"q": "Ciao!", "source": "auto", "target": "en"}
// Response (HTTP 200):
{
  "translatedText": "Bye!",
  "detectedLanguage": {
    "language": "it",
    "confidence": 83.0
  }
}
```

Source: [https://docs.libretranslate.com/api/operations/translate/](https://docs.libretranslate.com/api/operations/translate/)

### Pattern 2: LibreTranslate `/detect` Response

**What:** The `/detect` endpoint returns an *array* of candidates ordered by descending confidence.

**When to use:** To populate multiple detection candidates in the source dropdown.

**Example:**
```json
// POST /detect  {"q": "Ciao!", "api_key": "..."}
// Response (HTTP 200):
[
  {"language": "it", "confidence": 91.0},
  {"language": "pt", "confidence": 42.0}
]
```

Source: [https://docs.libretranslate.com/api/operations/detect/](https://docs.libretranslate.com/api/operations/detect/)

**Key decision:** Only candidates above the configured threshold (50.0, from STATE.md) should be presented to the user.

### Pattern 3: `api.py` — Return Full Dict for Auto-Detect

**What:** `async_translate` currently returns `result["translatedText"]` (a string). For auto-detect support, it must return the full response when auto-detect is used (or always).

**Recommended approach:** Change the return type to a dict. Callers that previously expected a string must be updated.

```python
async def async_translate(
    self, text: str, source: str, target: str
) -> dict[str, Any]:
    """Translate text using LibreTranslate. Returns full response dict."""
    payload: dict[str, str] = {
        "q": text,
        "source": source,
        "target": target,
    }
    if self._api_key:
        payload["api_key"] = self._api_key
    return await self._request("POST", "/translate", json=payload)
    # Callers access result["translatedText"] and result.get("detectedLanguage")
```

### Pattern 4: `services.py` — Source Validation Bypass for "auto"

**What:** The current service handler validates `source` against the installed languages list. `"auto"` is not in that list and will raise `ServiceValidationError`. This guard must be bypassed.

**Recommended approach:**

```python
AUTO_SOURCE = "auto"

# In _async_handle_translate:
if source != AUTO_SOURCE:
    source_lang = next(
        (l for l in languages if l["code"] == source), None
    )
    if source_lang is None:
        raise ServiceValidationError(...)
    if target not in source_lang.get("targets", []):
        raise ServiceValidationError(...)
# When source == "auto", skip both validations above
```

For the response, include detection info when available:

```python
result = await coordinator.async_translate(text, source, target)
response: ServiceResponse = {
    "translated_text": result["translatedText"],
}
if "detectedLanguage" in result:
    dl = result["detectedLanguage"]
    response["detected_language"] = dl.get("language")
    response["detection_confidence"] = dl.get("confidence")
return response
```

### Pattern 5: Service Error for Uninstalled Detected Language (DTCT-06)

**What:** When LibreTranslate detects a language and returns it, but that language code is not in the installed languages list, the translation may succeed (LibreTranslate may still translate from it) or may fail silently. The requirement is to show a user-visible message.

**Recommended approach:** After translation, check if `detected_language` code is present in `coordinator.data["languages"]`. If not, include a warning in the response or raise a `HomeAssistantError` with a descriptive message. Given the requirement says "shows user-visible message", the card should handle this by checking for an absence of the detected language in its known codes list. The service layer can include an `uninstalled_source_warning` field in the response for the card to display.

```python
if "detectedLanguage" in result:
    detected_code = result["detectedLanguage"].get("language")
    installed_codes = [l["code"] for l in languages]
    if detected_code and detected_code not in installed_codes:
        response["uninstalled_detected_language"] = detected_code
```

### Pattern 6: Card Source Dropdown with Auto-Detect

**What:** `"auto"` is a sentinel value prepended to the language list in the source dropdown. It is visually separated from the alphabetical list via an `<optgroup>` or a disabled spacer `<option>`.

**Example (LitElement template):**

```javascript
// Source dropdown in render():
html`
<select
  .value="${this._source}"
  @change="${this._sourceChanged}"
  aria-label="Source language"
>
  <option value="auto" ?selected="${this._source === 'auto'}">
    ${this._autoLabel}
  </option>
  <option disabled>──────────</option>
  ${codes.map((code, i) => html`
    <option value="${code}" ?selected="${code === this._source}">
      ${names[i]} (${code})
    </option>
  `)}
  ${this._detectionCandidates.map(c => html`
    <option value="auto:${c.language}" ?selected="${...}">
      Auto (${this._getLanguageName(c.language)})
    </option>
  `)}
</select>
`
```

`_autoLabel` defaults to "Auto-detect" and updates to "Auto (French)" after a successful auto-detect. `_detectionCandidates` stores `/detect` results above threshold.

When a candidate like `"auto:fr"` is selected, the card re-translates using `source: "fr"` (the fixed language), not `source: "auto"`.

### Pattern 7: Responsive Layout — CSS Container Queries

**What:** The card should show a two-column (horizontal) layout when wide and stack vertically when narrow. CSS container queries let the card respond to its *own rendered width*, not the viewport. This is the correct tool for Lovelace cards which can be placed in narrow or wide columns.

**Example:**

```css
:host {
  display: block;
  container-type: inline-size;
  container-name: translate-card;
}

/* Default: vertical layout */
.content-area {
  display: flex;
  flex-direction: column;
}

/* Auto-responsive: horizontal at >= 600px card width */
@container translate-card (min-width: 600px) {
  .content-area {
    flex-direction: row;
    gap: 16px;
  }
  .input-panel, .output-panel {
    flex: 1;
    min-width: 0;
  }
}
```

**For the layout override config option** (`layout: "horizontal" | "vertical" | "auto"`), apply a `data-layout` attribute on the root element and override the container query with explicit class:

```javascript
// In render():
// Apply layout class to .card-content based on config.layout and card width
```

For forced horizontal/vertical override, apply a CSS class that ignores the container query:

```css
:host([data-layout="horizontal"]) .content-area {
  flex-direction: row;
}
:host([data-layout="vertical"]) .content-area {
  flex-direction: column;
}
```

**Browser support:** Container queries are supported in all modern browsers (Chrome 105+, Firefox 110+, Safari 16+). Home Assistant requires a modern browser, so this is safe. (Confidence: HIGH)

### Pattern 8: WebSocket Error Code Discrimination (CPOL-01)

**What:** When `hass.callService(...)` throws, the error object has `{code: string, message: string}`.

**Known error codes from HA WebSocket layer:**
- `"home_assistant_error"` — server raised `HomeAssistantError` (operational failure like "Translation failed: connection timed out")
- `"service_validation_error"` — server raised `ServiceValidationError` (bad inputs)
- `"unknown_error"` — unexpected server error
- Connection lost / WebSocket disconnected: the caught error may be a JS `Error` (not from the WS protocol), with `message` like "Connection lost" and no `code` property, OR `code` may be `ERR_CONNECTION_LOST` (numeric `-1` from ha-js-websocket)

**Recommended card error handler:**

```javascript
catch (err) {
  const code = err?.code;
  const msg = err?.message || "";

  if (!code || code < 0) {
    // Negative numeric code = ERR_CONNECTION_LOST from ha-js-websocket
    this._error = "Cannot reach Home Assistant. Check your connection.";
  } else if (code === "home_assistant_error") {
    if (msg.toLowerCase().includes("timeout") || msg.toLowerCase().includes("timed out")) {
      this._error = "Translation timed out. The LibreTranslate server may be busy.";
    } else if (msg.toLowerCase().includes("connection") || msg.toLowerCase().includes("connect")) {
      this._error = "Cannot connect to LibreTranslate server.";
    } else {
      this._error = `Translation error: ${msg}`;
    }
  } else if (code === "service_validation_error") {
    this._error = `Bad request: ${msg}`;
  } else {
    this._error = msg || "Translation failed.";
  }
}
```

Note: Precise error codes at the HA WebSocket layer have limited official documentation. The above pattern is MEDIUM confidence; it should be validated in integration tests against a live HA instance. The `err.message` string content from `CannotConnectError` is already descriptive (`"Request timed out"`, `"Connection error: ..."`) and can be safely matched by substring.

### Pattern 9: Disabled Button Reason (CPOL-02)

**What:** Show helper text below the translate button explaining why it is disabled. This is more accessible and mobile-friendly than a tooltip.

```javascript
_getDisabledReason() {
  if (this._loading) return null; // button shows "Translating..."
  const status = this._getStatus();
  if (!status.online) return "LibreTranslate server is offline";
  if (!this._inputText) return "Enter text to translate";
  if (!this._source) return "Select a source language";
  if (!this._target) return "Select a target language";
  return null;
}
```

Render below button:
```javascript
${reason ? html`<div class="hint">${reason}</div>` : ""}
```

### Pattern 10: ARIA Labels (CPOL-03)

**What:** Add `aria-label` attributes to all interactive form controls without visible `<label>` elements.

```html
<select aria-label="Source language">...</select>
<select aria-label="Target language">...</select>
<textarea aria-label="Text to translate" ...></textarea>
<textarea aria-label="Translated text" readonly ...></textarea>
<ha-icon-button
  aria-label="Swap languages"
  title="Swap languages"
  ...
></ha-icon-button>
```

The translate button already has visible text "Translate" so no `aria-label` needed.

### Anti-Patterns to Avoid

- **Filtering target dropdown when source is auto:** When `_source === "auto"`, the `_getTargetsForSource("auto")` call returns `[]` (no entry in `targets` map). Current code would show an empty target dropdown. Must explicitly handle the auto case to show all installed language codes as targets.
- **Passing source validation for "auto" in service:** The current `services.py` will raise `ServiceValidationError("Unknown source language: auto")` unless explicitly bypassed. Do not add `"auto"` to the `MOCK_LANGUAGES` list in tests — bypass the guard with an explicit `if source != "auto"` check instead.
- **Calling `result["translatedText"]` directly:** Once `api.py` returns the full dict, all callers must update. `coordinator.async_translate` also returns the string today and must propagate the full dict.
- **Using viewport media queries for responsive card layout:** `@media (min-width: 600px)` responds to the browser window, not the card. Cards can appear in 2-column or 4-column layouts at any viewport size. Always use CSS container queries for within-card responsiveness.
- **Exposing `CannotConnectError` details without sanitizing:** Error messages from `aiohttp` can include URLs with credentials. Review that `CannotConnectError` messages sent to the frontend do not include API keys.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Responsive layout based on element width | Custom `ResizeObserver` class + state management | CSS container queries | Zero JS, no re-render needed, handles resize natively |
| Language detection | Custom language detection logic | LibreTranslate `/detect` endpoint | Already available; no new dependency |
| Error categorization | Complex exception hierarchy | Substring match on `err.message` from existing `CannotConnectError` strings | Messages are already descriptive; adding new exception subclasses is overengineering |

**Key insight:** The `/detect` endpoint returning a sorted array of candidates (unlike `/translate` which returns only the top hit) is the right data source for populating dropdown candidates. Don't try to infer candidates from the translate response alone.

---

## Common Pitfalls

### Pitfall 1: Source Dropdown Default Not "Auto-detect" on Initial Load

**What goes wrong:** The `updated()` lifecycle hook currently sets `this._source = codes[0]` when codes are first available. If "auto" is not a real code, this will override the intended default.

**Why it happens:** The `updated()` guard `if (codes.length > 0 && !this._source)` assigns the first real language code. `this._source` starts as `""` (falsy), so the auto-detect default must be pre-set in the constructor to `"auto"` rather than `""`.

**How to avoid:** In `constructor()`, initialize `this._source = "auto"`. Change the `updated()` guard to only set source if `this._source` is empty and is not "auto".

**Warning signs:** Source dropdown shows the first alphabetical language instead of "Auto-detect" on first render.

### Pitfall 2: Target Dropdown Empty When Source is "auto"

**What goes wrong:** `_getTargetsForSource("auto")` returns `[]` because the `targets` map only contains real language codes. The target dropdown renders empty.

**Why it happens:** The existing `_sourceChanged` handler calls `_getTargetsForSource(this._source)` and resets `_target` to `validTargets[0] || ""`. When source is "auto", `validTargets` is empty.

**How to avoid:** In `_getTargetsForSource`, handle the "auto" case:

```javascript
_getTargetsForSource(sourceCode) {
  if (sourceCode === "auto" || sourceCode.startsWith("auto:")) {
    const { codes } = this._getLanguages();
    return codes; // all languages are valid targets
  }
  const { targets } = this._getLanguages();
  return targets[sourceCode] || [];
}
```

**Warning signs:** Target dropdown shows no options after selecting "Auto-detect".

### Pitfall 3: `async_translate` Return Type Change Breaks `coordinator.async_translate`

**What goes wrong:** `coordinator.py` has `async_translate` which just delegates to `self.client.async_translate`. When `api.py` starts returning a dict, `coordinator.async_translate` passes the dict up unchanged — but `services.py` must then extract `["translatedText"]` instead of using the return value directly.

**Why it happens:** Two layers both named `async_translate` with currently-matching return types. Changing one without the other causes a `TypeError`.

**How to avoid:** Change `api.py`, `coordinator.py`, and `services.py` in a single coordinated edit. Update all tests that mock `mock_coordinator.async_translate` to return a dict `{"translatedText": "Hola"}` instead of a string `"Hola"`.

**Warning signs:** `test_services.py` tests fail with `TypeError: string indices must be integers` or `AttributeError: 'str' object has no attribute 'get'`.

### Pitfall 4: Candidate Dropdown Option Values Conflict with Language Codes

**What goes wrong:** Storing candidates as `"auto:fr"` works until the card tries to extract the real code for re-translation. If the extraction logic is not consistent, the wrong source code gets sent to the service.

**Why it happens:** The source `<select>` value is used directly as the `source` field in the service call. Candidates need to be either (a) raw codes that trigger a re-translate with that fixed source, or (b) a sentinel with embedded code that gets parsed.

**How to avoid:** When a candidate option is selected (value matches regex `/^auto:/`), extract the real code and re-translate immediately using that fixed code. The `_sourceChanged` handler should detect this pattern:

```javascript
_sourceChanged(ev) {
  const val = ev.target.value;
  if (val.startsWith("auto:")) {
    // User picked a detection candidate — re-translate with fixed source
    const fixedSource = val.slice(5);
    this._source = fixedSource;
    this._detectionCandidates = [];
    // Trigger re-translate
    if (this._inputText && this._target) this._translate();
  } else {
    this._source = val;
    // ... existing logic
  }
}
```

**Warning signs:** Selecting "Auto (French)" from the dropdown sends `source: "auto:fr"` to the service, which LibreTranslate rejects.

### Pitfall 5: CSS Container Queries and Shadow DOM

**What goes wrong:** Container queries inside a Shadow DOM work correctly per spec, but the container must be declared on `:host` or an element *inside* the shadow root — not on a parent outside it.

**Why it happens:** `container-type: inline-size` on `:host` is the correct approach since the card IS the container.

**How to avoid:** Declare `container-type: inline-size` on `:host` in the LitElement `styles`. The `@container` rule then applies within the shadow DOM. HA's card wrapper does not interfere with this.

**Warning signs:** Layout never switches despite container width — usually caused by putting `container-type` on a parent outside the shadow boundary.

### Pitfall 6: Confidence Threshold Filter Applied in Wrong Layer

**What goes wrong:** The confidence threshold (50.0 from STATE.md decisions) is applied to candidates for the dropdown. If it's applied in `api.py` (the HTTP layer), it reduces flexibility. If it's not applied at all, junk low-confidence candidates clutter the dropdown.

**How to avoid:** Apply the threshold in `services.py` (or a coordinator method), not in `api.py`. The raw `/detect` response can be returned from `api.py` for the coordinator/service to filter. Log the raw candidates at DEBUG for tuning.

---

## Code Examples

Verified patterns from official sources:

### LibreTranslate `/translate` with `source: "auto"` Response

```json
// Source: https://docs.libretranslate.com/api/operations/translate/
{
  "translatedText": "Bye!",
  "detectedLanguage": {
    "language": "it",
    "confidence": 83.0
  }
}
```

### LibreTranslate `/detect` Response (Multiple Candidates)

```json
// Source: https://docs.libretranslate.com/api/operations/detect/
[
  {"language": "it", "confidence": 91.0},
  {"language": "pt", "confidence": 44.0}
]
```

### HA WebSocket Error Object Structure

```javascript
// Source: home-assistant-js-websocket connection.ts (verified via GitHub)
// When success: false on the WebSocket:
{
  code: "home_assistant_error",   // string, from HomeAssistantError
  message: "Translation failed: Request timed out"
}
// Or for connection loss:
{
  code: -1,  // ERR_CONNECTION_LOST numeric constant
  message: "Connection lost"
}
```

### `ha-alert` Component Usage

```html
<!-- Source: HA community verified; all four types are valid -->
<ha-alert alert-type="error">Connection refused</ha-alert>
<ha-alert alert-type="warning">Detected language not installed</ha-alert>
<ha-alert alert-type="info" title="Auto-detect result">Detected: French (83%)</ha-alert>
<ha-alert alert-type="success">...</ha-alert>
```

### CSS Container Query Pattern for Responsive Card

```css
/* Source: MDN Web Docs, CSS Containment Module Level 3 — Baseline 2023 */
:host {
  display: block;
  container-type: inline-size;
  container-name: argos-card;
}

.content-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@container argos-card (min-width: 580px) {
  .content-area {
    flex-direction: row;
  }
  .input-panel,
  .output-panel {
    flex: 1;
    min-width: 0;
  }
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `media` queries for responsive card layout | CSS container queries | Baseline 2023 (CSS Containment L3) | Cards respond to their own width, not viewport |
| Tooltip for disabled-button explanations | Inline helper text | UX best practice 2022+ | Works on touch/mobile where hover doesn't work |
| Manual source/target validation for all values | Bypass guard for "auto" | This phase | Allows pass-through to LibreTranslate's built-in detection |

**Deprecated/outdated:**
- Using `@media` queries for Lovelace card internal responsiveness: responds to viewport, not card width — wrong for dashboards where cards can be any width

---

## Open Questions

1. **Are `/detect` candidates needed, or is the single `/translate` detectedLanguage sufficient?**
   - What we know: `/translate` with `source: "auto"` returns the top-1 detected language. `/detect` returns an array sorted by confidence.
   - What's unclear: The context decision says "candidate languages above a confidence threshold shown as options in the dropdown." This implies multiple candidates, which requires a separate `/detect` call (since `/translate` only returns 1).
   - Recommendation: Call `/detect` after (or instead of relying on `/translate`'s detectedLanguage). Send the `/detect` payload concurrently with or after the translation to populate the candidate options without blocking the translation result. However, this doubles the HTTP calls. Discuss with user whether a separate `/detect` call is acceptable or whether showing only the single top-detected language (from `/translate`) is sufficient for v1.1.

2. **Layout config option in card editor: does the card editor need a new field for "layout"?**
   - What we know: The card config currently has `header`, `entity`, `language_entity`, `default_source`, `default_target`. A `layout` field with values `"auto"`, `"horizontal"`, `"vertical"` is needed per context decisions.
   - What's unclear: Whether the card editor UI (`ArgosTranslateCardEditor`) needs a new `<ha-select>` or just the YAML config is enough.
   - Recommendation: Add a `<ha-select>` for Layout in the card editor for completeness.

3. **Error code for HA WebSocket when HA itself goes offline (HA-side crash)?**
   - What we know: The JS websocket library uses `ERR_CONNECTION_LOST` (a numeric constant, value `-1`) when the connection drops. The `err.code` will be `-1` (number, not string).
   - What's unclear: Whether `err.code` is always present vs. `err` being a raw JS `Error` object.
   - Recommendation: Guard with `typeof err.code === 'string'` vs. `typeof err.code === 'number'` to distinguish HA-protocol errors from connection-layer errors.

---

## Sources

### Primary (HIGH confidence)
- [https://docs.libretranslate.com/api/operations/translate/](https://docs.libretranslate.com/api/operations/translate/) — `/translate` response schema with `detectedLanguage`, `confidence`
- [https://docs.libretranslate.com/api/operations/detect/](https://docs.libretranslate.com/api/operations/detect/) — `/detect` returns array of `{language, confidence}` objects
- Project source code (read directly): `api.py`, `services.py`, `coordinator.py`, `sensor.py`, `__init__.py`, `argos_translate-card.js` — full understanding of existing implementation
- MDN Web Docs (CSS Container Queries) — `container-type: inline-size`, `@container` syntax; Baseline 2023

### Secondary (MEDIUM confidence)
- GitHub: `LibreTranslate/LibreTranslate app.py` (fetched) — confirmed `source="auto"` calls `detect_languages()`, uses `candidate_langs[0]` for translation, returns single `detectedLanguage` object
- GitHub: `home-assistant/home-assistant-js-websocket connection.ts` (fetched) — confirmed error object `{code, message}`, `ERR_CONNECTION_LOST` numeric constant
- HA developer docs: [https://developers.home-assistant.io/blog/2023/11/30/service-exceptions-and-translations/](https://developers.home-assistant.io/blog/2023/11/30/service-exceptions-and-translations/) — `ServiceValidationError` vs `HomeAssistantError` distinction and frontend behavior
- [https://docs.libretranslate.com/guides/api_usage/](https://docs.libretranslate.com/guides/api_usage/) — confirmed auto-detect response structure

### Tertiary (LOW confidence)
- WebSearch results on HA WebSocket error codes: error code values like `"home_assistant_error"`, `"service_validation_error"` — needs runtime validation; the exact string values should be verified by running the integration against a live HA instance

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries needed; existing aiohttp/LitElement/voluptuous are verified
- Architecture (backend): HIGH — LibreTranslate API response structure verified from official docs and source code; service layer pattern is clear from existing code
- Architecture (card UI — container queries): HIGH — CSS container queries are a baseline web standard
- Architecture (card UI — error discrimination): MEDIUM — HA WebSocket error codes partly inferred from library source; exact string values need runtime verification
- Architecture (candidate detection — /detect call): MEDIUM — approach is clear but adds an HTTP round-trip; whether to implement vs. single-candidate is an open design question
- Pitfalls: HIGH — all identified from reading the actual existing code paths

**Research date:** 2026-02-22
**Valid until:** 2026-03-22 (stable APIs; LibreTranslate and HA frontend are not fast-moving in this area)
