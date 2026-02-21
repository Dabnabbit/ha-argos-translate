# Research Summary: HA Argos Translate v1.1

**Project:** ha-argos-translate — Home Assistant HACS integration for local text translation via LibreTranslate
**Domain:** Home Assistant custom integration enhancement
**Researched:** 2026-02-21
**Confidence:** HIGH

---

## Executive Summary

The v1.1 milestone is a focused enhancement of an already-shipped v1.0 integration. Three features are in scope: auto-detect source language, an options flow that correctly reloads the coordinator on save, and Lovelace card polish (theming, accessibility, mobile). None of these require new dependencies, new files, or architectural redesign. All three are pure extensions of existing modules — the largest single change is the Lovelace card at approximately 80–120 lines added.

The recommended approach is ordered by dependency: fix the options flow reload bug first (isolated, high user value, touches only `config_flow.py`), then implement auto-detect on the Python side (`api.py` → `coordinator.py` → `services.py`), then extend the card with auto-detect UI and polish changes. Testing can follow each feature or be batched at the end. The `async_step_reconfigure` pattern documented in HA 2024 is acknowledged as the HA-idiomatic alternative for credential changes, but the existing `OptionsFlowHandler` approach is simpler and correct once the missing `async_reload` call is added — keep it.

The primary risks are operational rather than architectural. The coordinator silently continues using stale credentials until a reload is triggered — this is the v1.0 bug being fixed and must be verified on real hardware before closing the phase. Auto-detect has a known edge case: LibreTranslate's detector operates on a broader vocabulary than the installed language set, meaning a successful detection result may still be untranslatable. Confidence thresholds and installed-language validation must be applied before surfacing detection results to the user. Browser caching of the card JS after updates is a deploy concern that requires a versioned URL strategy.

---

## Key Findings

### Recommended Stack

No new technologies are introduced in v1.1. The existing stack (Python 3.12+, aiohttp, voluptuous, LitElement, DataUpdateCoordinator) requires only pattern additions from HA's own framework.

**Core technologies (unchanged):**
- Python / aiohttp (HA-bundled) — `async_translate` return type changes from `str` to `dict`; no new packages
- LitElement (HA-bundled) — card UI additions; no new JS imports or build tooling
- voluptuous (HA-bundled) — `source` field made optional with `default="auto"`

**New HA patterns (import changes only, no new dependencies):**
- `OptionsFlowWithReload` (HA 2025.8+) — drop-in base class for `OptionsFlowHandler`; triggers automatic reload after save. Verify HA version before using; fall back to explicit `async_reload` if needed.
- `async_step_reconfigure` + `async_update_reload_and_abort` (HA 2024+) — alternative pattern for credential changes; acknowledged but not recommended as primary path since the existing options flow already works.

**Critical version note:** `OptionsFlowWithReload` requires HA 2025.8+. The project targets 2025.7+. Safest path: keep the existing `OptionsFlow` base class and add an explicit `await self.hass.config_entries.async_reload(entry.entry_id)` after `async_update_entry`. This works on all supported HA versions and is the approach used in the architecture research.

See `.planning/research/STACK.md` for full file-by-file change map.

### Expected Features

This is a v1.1 milestone targeting three features. All "table stakes" below are net-new additions.

**Must have (table stakes for v1.1):**
- Options flow saves then reloads integration — currently coordinator uses stale credentials until HA restart
- Auto-detect source language in service call — `source: "auto"` bypass in `services.py`; API already passes it through
- Auto-detect source language in card UI — "Auto-detect" as first option in source dropdown; all-targets mode when auto selected
- Card error messages distinguish server-offline from bad-request — currently shows raw `err.message`
- Card explains disabled translate button state — no current feedback when `canTranslate` is false

**Should have (v1.1 bonus within same milestone):**
- Detected language label in card output — "Detected: French (90%)" when `source="auto"` was used
- Detected language in service response — `detected_language` and `detection_confidence` fields for automation authors
- ARIA labels on card form controls — `aria-label` on both `<select>` and `<textarea>` elements
- Mobile layout fix — flex-wrap on language row; minimum 44px touch targets on swap button

**Defer to v2+:**
- Copy-to-clipboard on output
- HA native form elements (`ha-select`, `ha-textfield`) — medium refactor, breaking risk across HA versions
- Translation history — requires persistent storage, out of scope per PROJECT.md
- Keyboard shortcut Ctrl+Enter for translate

See `.planning/research/FEATURES.md` for prioritization matrix and existing-code assessment.

### Architecture Approach

V1.1 makes no structural changes to the integration. Every feature integrates into existing files. The largest modification is the Lovelace card. The data flow for auto-detect follows a clean path from card through service to API: `source: "auto"` passes through unchanged to LibreTranslate's `/translate` endpoint, which returns `detectedLanguage` in the same response. No separate `/detect` call is needed.

**Modified components and scope:**

| File | Change | Scope |
|------|--------|-------|
| `api.py` | `async_translate` returns `dict` instead of `str` | ~15 lines |
| `coordinator.py` | Propagates dict return from API | ~2 lines |
| `services.py` | Accept `source="auto"`, skip validation, enrich response | ~20 lines |
| `config_flow.py` | Add `async_reload` after successful options save | ~3 lines |
| `translations/en.json` | Document `"auto"` source value | ~5 lines |
| `frontend/argos_translate-card.js` | Auto-detect option, detected language display, ARIA, CSS | ~80–120 lines |
| `tests/test_config_flow.py` | Options flow test coverage | ~40 lines |
| `tests/test_services.py` | `source="auto"` service call coverage | ~30 lines |

**Key patterns established by research:**
1. `source="auto"` pass-through — do not validate against the language list; let LibreTranslate handle it
2. Reload-on-update — any change to coordinator-consumed `entry.data` values must be followed by `async_reload`
3. Card reads language data from sensor attributes — unchanged from v1.0; do not alter this pattern

See `.planning/research/ARCHITECTURE.md` for data flow diagrams and anti-patterns.

### Critical Pitfalls

**Top 5 pitfalls for v1.1:**

1. **Coordinator not rebuilt after options save** — The existing code calls `async_update_entry` but does not trigger a reload. Without an explicit `await hass.config_entries.async_reload(entry.entry_id)`, the coordinator continues using the old host/port/API key indefinitely. Verify on real HA by changing the host address and confirming the integration fails (as it should) pointing at the non-existent new host.

2. **Detected language not in available languages list** — LibreTranslate's detector operates on a global vocabulary; only installed model pairs are in `coordinator.data["languages"]`. Always validate the detected language code against installed codes before using it in the UI. Show a message when detection succeeds but the language is not installed.

3. **Auto-detect with low or zero confidence** — The `/detect` endpoint (and inline detection via `source="auto"`) returns a confidence float. Below ~50.0, results are unreliable. Short inputs (< 5 characters) frequently trigger incorrect detections. Apply a minimum confidence threshold and surface the confidence value to the user rather than silently applying the result.

4. **Browser cache serves stale card JS after update** — `StaticPathConfig(cache_headers=True)` causes browsers (especially iOS Companion App) to cache the card JS indefinitely. Append a version query parameter to the registered Lovelace resource URL (e.g., `?v=0.3.0`) and update `CARD_VERSION` on every card change.

5. **Options data written to `entry.options` instead of `entry.data`** — The coordinator constructor reads `entry.data` exclusively. The options flow must continue writing merged credentials to `entry.data` via `async_update_entry` before returning `async_create_entry(data={})`. The current implementation does this correctly; preserve the pattern and add a comment explaining the intentional deviation from the standard options pattern.

See `.planning/research/PITFALLS.md` for the full "looks done but isn't" verification checklist.

---

## Implications for Roadmap

Based on combined research, a 3-phase structure is appropriate for v1.1. Features are ordered by dependency; the options flow fix is isolated and high-value so it ships first.

### Phase 1: Options Flow Fix

**Rationale:** The most isolated change in v1.1 — only `config_flow.py` and one test file. Ships a critical correctness fix immediately for users who deployed v1.0 and need to change their server address. Unblocks safe deployment testing for phases 2 and 3.

**Delivers:**
- Options flow saves new host/port/API key and immediately reloads the integration
- Coordinator rebuilds with new credentials on save
- Connection validation errors shown before saving (already works; preserve it)

**Addresses:** Options flow reload (P1 must-have), options translation string verification

**Avoids:**
- PITFALL-01: Coordinator using stale credentials (the core bug being fixed)
- PITFALL-04: Data written to wrong entry property
- PITFALL-08: Translation strings missing for options step

**Verification gate:** After saving a changed host address to a non-existent server, HA logs must show `async_setup_entry` being called and a connection failure to the new address — not continued success on the old address.

Research flag: NO — standard HA patterns, well-documented.

---

### Phase 2: Auto-Detect and Card Polish

**Rationale:** Auto-detect Python changes must precede card UI changes because the card calls the service. Python side can be tested via HA Developer Tools independently of the card. Card polish and auto-detect UI are combined in the same phase because both modify `argos_translate-card.js` — one session avoids double-touching the file.

**Delivers:**
- `source: "auto"` accepted in service call; validation bypassed; detected language returned
- "Auto-detect" option in card source dropdown
- Target dropdown shows all available languages when source is "auto"
- Detected language displayed in card output ("Detected: French (90%)")
- ARIA labels on form controls
- Minimum 44px touch targets on swap button
- Responsive CSS for narrow viewports
- Improved error messages distinguishing server-offline from bad-request
- Disabled button explanation text

**Addresses:** All P1 must-haves (auto-detect service, auto-detect card UI, error messages, button state UX) and all P2 should-haves (detected language label, ARIA, mobile layout)

**Avoids:**
- PITFALL-02: Low-confidence detection applied silently — apply 50.0 threshold
- PITFALL-03: Detected language not in installed list — validate before use
- PITFALL-05: Auto-detect firing on every keypress — keep explicit Translate button
- PITFALL-07: Dark theme select readability — test on real hardware

**Implementation order within phase:**
1. `api.py` — `async_translate` returns `dict`
2. `coordinator.py` — propagate dict return
3. `services.py` — accept `"auto"`, skip validation, enrich response
4. `tests/test_services.py` — coverage for auto-detect path
5. `argos_translate-card.js` — auto-detect UI, ARIA, CSS polish

Research flag: NO — patterns are documented in research files with verified code examples.

---

### Phase 3: Deploy Validation and Stabilization

**Rationale:** After functional implementation, real-hardware verification catches issues that unit tests miss. Browser caching, dark theme rendering, mobile layout, and coordinator reload behavior all require live HA validation. This phase also ensures HACS and hassfest compliance after all changes.

**Delivers:**
- Verified options flow reload on real HA instance
- Card tested on light and dark themes
- Card tested on mobile viewport
- Browser cache busting via versioned URL (bump `CARD_VERSION`, update Lovelace resource URL)
- hassfest validation passing for any new service definitions
- HACS action passing

**Addresses:** All items on the "looks done but isn't" checklist from PITFALLS.md

**Avoids:**
- PITFALL-06: Browser cache serving stale card JS
- PITFALL-07: Dark theme select unreadable
- hassfest failure if detect service is added

Research flag: NO — standard HACS/hassfest patterns; PITFALLS.md covers all edge cases.

---

### Phase Ordering Rationale

- **Options flow first:** Standalone; ships a real bug fix immediately; establishes deployment testing confidence before touching the API and card.
- **Python before JS:** `services.py` must accept `source="auto"` before the card can send it; Python path testable via Developer Tools without any card changes.
- **Auto-detect and polish in one session:** Both touch `argos_translate-card.js`; combining avoids revisiting the same file in a separate phase.
- **Deploy validation last:** Real-hardware issues (caching, themes, mobile) cannot be caught in unit tests; dedicate a phase to them rather than mixing with feature work.

### Research Flags

| Phase | Needs Research Phase? | Reason |
|-------|----------------------|--------|
| Phase 1: Options Flow Fix | NO | Well-documented HA patterns; 3-line fix with known implementation |
| Phase 2: Auto-Detect and Card Polish | NO | STACK.md and ARCHITECTURE.md contain verified code examples for every change |
| Phase 3: Deploy Validation | NO | Verification checklist in PITFALLS.md covers all known edge cases |

No research phases are needed. All three features have high-confidence, implementation-ready patterns documented in the research files.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies are existing; new patterns (`OptionsFlowWithReload`, `async_step_reconfigure`) confirmed from official HA developer docs |
| Features | HIGH | Feature list derived from direct codebase inspection (existing code read in FEATURES.md); gaps are unambiguous |
| Architecture | HIGH | HA coordinator and options flow patterns confirmed from official docs; LibreTranslate API behavior confirmed from official API docs |
| Pitfalls | HIGH (HA) / MEDIUM (LibreTranslate detection) | HA patterns from official docs; LibreTranslate detection edge cases from community sources (CLD2 limitations, LexiLang hybrid detector) |

**Overall confidence: HIGH**

The v1.1 scope is well-bounded and all three features have direct precedent in official HA developer documentation. The only medium-confidence area is LibreTranslate's detection behavior for edge-case inputs (short text, obscure languages), which is handled by the confidence threshold mitigation and user-visible confidence display.

### Gaps to Address

1. **`OptionsFlowWithReload` version compatibility** — requires HA 2025.8+; project targets 2025.7+. Use the explicit `async_reload` approach from ARCHITECTURE.md instead. This is documented and the fallback is clear, but should be called out explicitly in the Phase 1 plan.

2. **Confidence threshold tuning** — The 50.0 confidence threshold is a starting point. Real-world testing may reveal it is too conservative (high-confidence detections rejected) or too lenient (wrong detections accepted). Document as a known limitation; make the threshold visible in debug logs.

3. **Card version bump strategy** — The specific mechanism for appending `?v=VERSION` to the Lovelace resource URL depends on how the integration registers resources (auto via `hacs.json` or documented as a manual step). Confirm the mechanism during Phase 3 planning.

---

## Sources

### Primary (HIGH confidence)
- [LibreTranslate /translate endpoint reference](https://docs.libretranslate.com/api/operations/translate/) — `source="auto"` behavior, `detectedLanguage` response shape
- [LibreTranslate API Usage Guide](https://docs.libretranslate.com/guides/api_usage/) — `/detect` endpoint format, confidence response
- [HA Config Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/) — `async_step_reconfigure`, `async_update_reload_and_abort`, `_get_reconfigure_entry`
- [HA Options Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — `OptionsFlowWithReload` import path and code example
- [HA reconfigure step blog](https://developers.home-assistant.io/blog/2024/03/21/config-entry-reconfigure-step/) — reconfigure vs. options flow distinction
- Existing codebase (`config_flow.py`, `api.py`, `services.py`, `coordinator.py`, card JS) — read directly; HIGH confidence

### Secondary (MEDIUM confidence)
- [LibreTranslate community: auto-detect requirements](https://community.libretranslate.com/t/no-auto-detect-after-adding-a-language/1068) — LexiLang/langdetect dependency for detection
- [LibreTranslate language detection issue #395](https://github.com/LibreTranslate/LibreTranslate/issues/395) — CLD2 failures for German, Japanese, English; hybrid detector implemented Oct 2023
- [HA community: OptionsFlow data vs options](https://community.home-assistant.io/t/strange-behavior-with-optionflow-in-data-and-options-config-entry/855931/6) — reconfigure recommended over OptionsFlow for credential changes
- [HA static path async registration](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/) — cache_headers=True sets long-lived headers
- [HA frontend cache issues iOS](https://github.com/home-assistant/iOS/issues/3738) — persistent browser cache on mobile requires manual reset
- [CLD2 design limitations](https://github.com/CLD2Owners/cld2) — designed for 200+ character texts

---
*Research completed: 2026-02-21*
*Milestone: v1.1 (auto-detect, options flow reload, card polish)*
*Ready for roadmap: yes*
