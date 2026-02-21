# Feature Research

**Domain:** Home Assistant HACS integration — local translation via LibreTranslate
**Researched:** 2026-02-21
**Confidence:** HIGH (LibreTranslate API docs + HA developer docs verified; existing code read directly)

---

## Scope Note

This is a subsequent-milestone research file for v1.1. v1.0 is already shipped. All table stakes
below are NEW features for v1.1. Existing code is referenced to clarify what is built vs. what
still needs work.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the milestone explicitly targets. Missing these = milestone is incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Auto-detect source language (card UI) | Every translation UI offers this; users often don't know source language | MEDIUM | Add "Auto" option to source dropdown; call `/translate` with `source="auto"`; target dropdown must show all targets when auto is selected |
| Auto-detect source language (service call) | Automation authors need `source: "auto"` for unknown-language inputs | MEDIUM | Current `services.py` validation rejects "auto" (not in language list) — add special-case bypass before language-pair check |
| Options flow reloads integration on save | HA convention: connection-critical changes (host/port) must reload the coordinator | LOW | `OptionsFlowHandler` is coded but extends plain `OptionsFlow` not `OptionsFlowWithReload`; coordinator uses stale connection params until HA restarts |
| Card shows meaningful error messages | "Translation failed" is insufficient for debugging | LOW | Current `_translate()` catch block shows raw `err.message`; map connection errors vs. bad-request errors to user-readable strings |
| Card explains why translate button is disabled | Greyed button with no explanation is confusing | LOW | `canTranslate` check exists; needs a helper text below button when server is offline or no text entered |

### Differentiators (Competitive Advantage)

Features beyond the minimum that meaningfully improve UX for this integration.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Detected language label in card output | Shows "Detected: French (90% confidence)" after auto-translate | LOW | When `source="auto"`, `/translate` response includes `detectedLanguage: {language: "fr", confidence: 90.0}`; surface in card output area |
| Detected language in service response | Automation authors can branch on what language was detected | LOW | Add `detected_language` and `detection_confidence` to service response dict when source was "auto" |
| ARIA labels on form controls | Screen reader support; accessibility hygiene | LOW | Add `aria-label` to `<select>` and `<textarea>` elements; purely additive to existing HTML |
| Mobile layout stacking | On narrow screens, source/swap/target row is cramped | LOW | Add `flex-wrap: wrap` and `min-width` to `.lang-row` selects; swap button collapses gracefully |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-translate on typing (debounced) | Feels like Google Translate | API call per keystroke; no WebSocket streaming in LibreTranslate; bad UX mid-word | Keep explicit Translate button; add Ctrl+Enter shortcut if needed |
| HA native form elements (`ha-select`, `ha-textfield`) | Consistent with HA theme | Medium refactor; HA frontend components change API between releases; current CSS vars already provide theming | Keep native HTML elements with CSS var theming |
| Translation history in card | Review past translations | Lost on reload (JS memory); storing in HA requires new entity or persistent_storage; out of scope per PROJECT.md | Explicitly out of scope for v1.1 |
| Language auto-install from card | Manage language packages from HA | Requires LibreTranslate admin API or docker exec; well outside integration scope | Direct user to LibreTranslate admin UI |
| Copy-to-clipboard button | Convenient for taking translated text | Low complexity but not core to translation function | Defer to v1.2+ as a nice-to-have |

---

## Feature Dependencies

```
[Options flow reload]
    └──requires──> OptionsFlowWithReload base class (HA built-in)
                       └──triggers──> async_unload_entry + async_setup_entry automatically
                                          └──recreates coordinator with new host/port/API key

[Auto-detect: service call]
    └──requires──> Bypass source validation when source == "auto"
    └──requires──> api.py async_translate returns full response (not just translatedText string)
    └──enables──> Detected language in service response (differentiator)

[Auto-detect: card UI]
    └──requires──> [Auto-detect: service call] (card calls the service)
    └──requires──> "Auto" option added to source <select>
    └──requires──> Target dropdown shows all targets when source is "auto"
    └──enables──> Detected language label in card output (differentiator)

[Detected language label in card] ──requires──> [Auto-detect: card UI]
[Detected language in service response] ──requires──> [Auto-detect: service call]

[ARIA labels] ──independent──> all other features
[Mobile layout fix] ──independent──> all other features
[Card error messages] ──independent──> all other features
```

### Dependency Notes

- **Options flow reload:** `OptionsFlowWithReload` is a drop-in replacement for `OptionsFlow` as the base class for `OptionsFlowHandler`. HA calls `async_unload_entry` + `async_setup_entry` automatically after the options are saved. The coordinator `__init__` reads from `entry.data`, so the new connection params take effect without any additional code. The existing `async_update_entry` call writes to `entry.data` which is unconventional (HA convention stores mutable settings in `entry.options`) but is functional; keep it to avoid a larger refactor. (Source: HA options flow docs, HIGH confidence)

- **Auto-detect service: validation bypass:** `services.py` iterates `coordinator.data["languages"]` to find the source language object. It must `if source == "auto": skip_validation = True` before that loop. When skip_validation is True, also skip the `target not in source_lang["targets"]` check, since "auto" has no targets list in the language data. LibreTranslate accepts any valid target code when `source="auto"`.

- **Auto-detect API response shape:** When `source != "auto"`, `async_translate` returns a plain string (`result["translatedText"]`). When `source == "auto"`, the response includes `detectedLanguage: {language: str, confidence: float}`. Two options: (a) always return the full response dict and let callers extract `translatedText`; (b) add a separate method `async_detect_and_translate` that returns a dict. Option (a) is simpler but breaks the existing callers. Recommended: add a new `async_detect_and_translate` method and call it from the service handler when `source == "auto"`.

- **Target dropdown when source=auto:** The card's `_getTargetsForSource(sourceCode)` method returns `targets[sourceCode] || []`. When `sourceCode == "auto"`, this returns an empty array. The fix: collect all unique target codes across all languages when source is "auto". This requires a new helper method in the card.

---

## MVP Definition

### Launch With (v1.1)

Minimum viable feature set for this milestone.

- [ ] Options flow reloads integration after save — one-line base class change, critical correctness fix
- [ ] Auto-detect source language in service call — bypass validation, return detected language data
- [ ] Auto-detect source language in card — "Auto" option, target dropdown all-codes mode
- [ ] Card error messages distinguish server-down from bad request
- [ ] Card explains disabled translate button state

### Add After Validation (v1.1 bonus, within milestone)

Features to add once core is working, within the same iteration.

- [ ] Detected language label in card output — triggered only when auto-detect was used
- [ ] Detected language in service response dict — useful for automation authors
- [ ] ARIA labels on form controls — small effort, accessibility improvement
- [ ] Mobile layout flex-wrap on language row — small CSS fix

### Future Consideration (v2+)

Features to defer.

- [ ] Copy-to-clipboard button on output — independent, low risk, not core translation flow
- [ ] HA native form elements (`ha-select`, `ha-textfield`) — medium refactor, breaking risk
- [ ] Keyboard shortcut Ctrl+Enter for translate — enhancement
- [ ] Translation history — requires persistent storage, scope too large for this milestone

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Options flow reload (OptionsFlowWithReload) | HIGH | LOW (1-line change) | P1 |
| Auto-detect in service (validation bypass + response) | HIGH | LOW | P1 |
| Auto-detect in card UI | HIGH | MEDIUM | P1 |
| Card error message improvements | MEDIUM | LOW | P1 |
| Disabled button explanation | MEDIUM | LOW | P1 |
| Detected language label in card | MEDIUM | LOW | P2 |
| Detected language in service response | MEDIUM | LOW | P2 |
| ARIA labels | LOW | LOW | P2 |
| Mobile layout fix | MEDIUM | LOW | P2 |
| Copy-to-clipboard | LOW | LOW | P3 |
| HA native form elements | LOW | MEDIUM | P3 |

**Priority key:** P1 = must have for v1.1 launch / P2 = should have, add in same milestone /
P3 = nice to have, future milestone

---

## Existing Code Assessment

### Already Built (No Work Needed)

| Component | Status | Notes |
|-----------|--------|-------|
| OptionsFlowHandler form | Done | Shows host/port/SSL/API key with current values pre-filled |
| OptionsFlowHandler connection validation | Done | Calls `_async_validate_connection` before saving |
| `strings.json` options step labels | Done | All labels and error messages defined |
| API client `async_translate` base | Done | Passes `source` to LibreTranslate unchanged — "auto" string goes through correctly at HTTP level |
| Card source/target dropdown filtering | Done | `_getTargetsForSource` correctly filters by source code |
| Card error display surface | Done | `ha-alert` renders error text; content is generic but surface exists |
| Card loading spinner | Done | `_loading` state and `ha-spinner` are implemented |
| Card swap button | Done | Swaps source/target codes and moves output to input |

### Needs Work

| Component | Gap | Effort |
|-----------|-----|--------|
| `OptionsFlowHandler` base class | Extends `OptionsFlow`; must extend `OptionsFlowWithReload` | LOW |
| `services.py` source validation | Rejects `source="auto"` — not in coordinator language list | LOW |
| `api.py` async_translate | Returns `str` only; loses `detectedLanguage` from response | LOW-MEDIUM |
| Card source dropdown | No "Auto" option at top of list | LOW |
| Card `_getTargetsForSource` when source=auto | Returns `[]` for "auto"; must return all target codes | LOW |
| Card output area | No detected language display after auto-translate | LOW |
| Card `_translate` error handling | Generic `err.message`; no error type mapping | LOW |
| Card disabled button UX | No explanation when `!canTranslate` | LOW |

---

## LibreTranslate /detect and auto Behavior Notes

The `/detect` endpoint exists (`POST /detect`, body `{"q": "text"}`) but is redundant when
using `source="auto"` in `/translate`. Avoid adding a separate detect API call.

When `source="auto"` in `/translate`, the response is:
```json
{
  "translatedText": "Hello!",
  "detectedLanguage": {
    "language": "fr",
    "confidence": 90.0
  }
}
```

Confidence is a float 0-100. Values below ~50 indicate uncertain detection and should be
communicated to the user ("Detected: French (low confidence)").

**Server-side caveat:** Auto-detect depends on LexiLang and langdetect libraries on the
LibreTranslate server. Languages that were recently added to the instance via argos-translate
models may not be detectable even when translation works. This is a server limitation, not an
integration bug. Detection works reliably for the major languages (en, es, fr, de, ja, zh).
(Source: LibreTranslate community, MEDIUM confidence)

---

## Sources

- [LibreTranslate API Usage](https://docs.libretranslate.com/guides/api_usage/) — HIGH confidence
- [LibreTranslate /translate endpoint spec](https://docs.libretranslate.com/api/operations/translate/) — HIGH confidence; confirms `source="auto"` and `detectedLanguage` response shape
- [LibreTranslate community: auto-detect requirements](https://community.libretranslate.com/t/no-auto-detect-after-adding-a-language/1068) — MEDIUM confidence; LexiLang/langdetect dependency
- [HA Config Flow handler docs](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — HIGH confidence; reconfigure vs. options flow distinction
- [HA Options Flow handler docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — HIGH confidence; `OptionsFlowWithReload` pattern confirmed
- [HA Custom Card developer docs](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/) — MEDIUM confidence; native component catalog not well documented
- Existing codebase (`config_flow.py`, `api.py`, `services.py`, `coordinator.py`, card JS) — HIGH confidence; read directly

---

*Feature research for: HA Argos Translate v1.1 milestone (auto-detect, options flow, card polish)*
*Researched: 2026-02-21*
