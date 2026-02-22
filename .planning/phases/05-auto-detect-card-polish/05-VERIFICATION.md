---
phase: 05-auto-detect-card-polish
verified: 2026-02-22T08:30:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
---

# Phase 5: Auto-Detect + Card Polish Verification Report

**Phase Goal:** Users can translate without selecting a source language, see the detected language in the card, and interact with an accessible and mobile-friendly card
**Verified:** 2026-02-22T08:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

The must-haves from the three plan frontmatter blocks are aggregated and verified individually.

**Plan 01 must-haves (DTCT-02, DTCT-03, DTCT-06 — backend):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Service call with source='auto' returns translated text plus detected_language and detection_confidence fields | VERIFIED | `services.py:94-101` — result dict enriched with both fields when `detectedLanguage` in response |
| 2 | Service call with source='auto' does not raise ServiceValidationError for unknown source | VERIFIED | `services.py:65` — `if source != AUTO_SOURCE:` guard bypasses all validation; confirmed by `test_translate_auto_detect_no_validation_error` |
| 3 | When detected language code is not in installed languages, response includes uninstalled_detected_language warning field | VERIFIED | `services.py:103-107` — explicit check against `installed_codes`; confirmed by `test_translate_auto_detect_uninstalled_language` |
| 4 | api.py /detect endpoint returns array of candidate objects with language and confidence | VERIFIED | `api.py:110-119` — `async_detect_languages` POSTs to `/detect`, returns full response |
| 5 | HA detect service is callable from the card and returns candidate languages array | VERIFIED | `services.py:119-148` — `_async_handle_detect` registered with `SERVICE_DETECT`, returns `{"detections": candidates}` |

**Plan 02 must-haves (CPOL-01, CPOL-02, CPOL-03, CPOL-04 — card polish):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | Card shows specific error messages distinguishing connection failure, timeout, bad request, and generic errors | VERIFIED | `argos_translate-card.js:288-305` — 4-branch catch: numeric/no code, home_assistant_error+timeout, home_assistant_error+connect, service_validation_error |
| 7 | Disabled translate button has helper text below it explaining why | VERIFIED | `argos_translate-card.js:311-318` — `_getDisabledReason()` returns 4 distinct reasons; `argos_translate-card.js:469-472` — IIFE renders `.hint` div |
| 8 | All select elements and textareas have aria-label attributes; swap button has aria-label | VERIFIED | Lines 380, 415, 436, 444, 410 — all five interactive controls carry explicit `aria-label` attributes |
| 9 | Card uses CSS container queries so layout responds to card width, not viewport width | VERIFIED | `argos_translate-card.js:484-487` — `:host` has `container-type: inline-size; container-name: argos-card`; `argos_translate-card.js:578-587` — `@container argos-card (min-width: 580px)` switches to row layout |
| 10 | Card config supports layout override with values 'auto', 'horizontal', 'vertical' | VERIFIED | `argos_translate-card.js:367-368` — `data-layout` set from config; CSS at lines 588-598 enforces forced layouts |

**Plan 03 must-haves (DTCT-01, DTCT-04, DTCT-05 — card auto-detect UI):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 11 | Source dropdown has 'Auto-detect' as first item with visual separator from alphabetical list | VERIFIED | `argos_translate-card.js:384-396` — `value="auto"` option first, followed by candidates, then `<option disabled>──────────</option>`, then full language list |
| 12 | Auto-detect is the default source selection when the card first loads | VERIFIED | `argos_translate-card.js:41` — `this._source = "auto"` in constructor; `updated()` guard at line 143 uses `!this._source` (falsy) so "auto" never gets overwritten |
| 13 | When source is 'Auto-detect', target dropdown shows all available languages | VERIFIED | `argos_translate-card.js:113-120` — `_getTargetsForSource("auto")` returns `codes` (all languages) |
| 14 | After auto-detect translation, source dropdown label updates to show detected language | VERIFIED | `argos_translate-card.js:385-387` — option text is `\`Auto (${this._getLanguageName(this._detectedLanguage.language)})\`` when `_detectedLanguage` is set |
| 15 | Detection candidates above 50% confidence appear as selectable options in source dropdown | VERIFIED | `argos_translate-card.js:15` — `DETECTION_CONFIDENCE_THRESHOLD = 50.0`; `argos_translate-card.js:274-276` — candidates filtered by threshold; `argos_translate-card.js:389-395` — candidates rendered as `auto:XX` options |
| 16 | Selecting a candidate re-translates using that language as a fixed source | VERIFIED | `argos_translate-card.js:161-174` — `_sourceChanged` handles `val.startsWith("auto:")`, extracts fixed code, clears detection state, calls `_translate()` |

**Score: 16/16 observable truths verified** (the plan frontmatter listed fewer truths at a higher abstraction; all 16 behavioural truths derived from those entries verify clean)

---

## Required Artifacts

| Artifact | Provides | Exists | Substantive | Wired | Status |
|----------|----------|--------|-------------|-------|--------|
| `custom_components/argos_translate/api.py` | `async_translate` returns full dict; `async_detect_languages` method | Yes | Yes — 119 lines, both methods fully implemented | Used by coordinator | VERIFIED |
| `custom_components/argos_translate/coordinator.py` | Passthrough for both methods with `dict[str, Any]` return types | Yes | Yes — both methods delegate to `self.client` | Called by services.py | VERIFIED |
| `custom_components/argos_translate/services.py` | Auto source bypass, detection field enrichment, `detect` service | Yes | Yes — 149 lines, both services registered | Called by card via HA WebSocket | VERIFIED |
| `custom_components/argos_translate/const.py` | `SERVICE_DETECT = "detect"` | Yes | Yes — constant present at line 13 | Imported by services.py | VERIFIED |
| `custom_components/argos_translate/strings.json` | `source` field describes 'auto'; new `detect` service block | Yes | Yes — both changes at lines 69 and 77-86 | Used by HA UI | VERIFIED |
| `custom_components/argos_translate/translations/en.json` | Mirrors strings.json for English locale | Yes | Yes — identical detect service block and updated source description | Used by HA UI | VERIFIED |
| `tests/test_services.py` | Auto-detect tests: success, uninstalled language, no validation error | Yes | Yes — 3 new tests at lines 133-193, all substantive assertions | All 8 tests pass | VERIFIED |
| `custom_components/argos_translate/frontend/argos_translate-card.js` | All card polish + auto-detect UI features | Yes | Yes — 779 lines, v0.5.0, all features implemented | Loaded by HA Lovelace | VERIFIED |

---

## Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `api.py` | LibreTranslate `/translate` endpoint | `async_translate` returns full response dict | WIRED | `api.py:108` — `return await self._request("POST", "/translate", json=payload)` — full dict returned, not just `["translatedText"]` |
| `api.py` | LibreTranslate `/detect` endpoint | `async_detect_languages` POSTs to `/detect` | WIRED | `api.py:118-119` — `return await self._request("POST", "/detect", json=payload)` |
| `services.py` | `coordinator.py` | `coordinator.async_translate` returns dict; services extracts `result["translatedText"]` | WIRED | `services.py:88, 94` — `result = await coordinator.async_translate(...)` then `result["translatedText"]` |
| `services.py` | `coordinator.py` | detect service calls `coordinator.async_detect_languages` | WIRED | `services.py:134` — `candidates = await coordinator.async_detect_languages(text)` |
| `argos_translate-card.js` | `argos_translate.translate` service | `callService` with `source="auto"`, reads `detected_language` from response | WIRED | `argos_translate-card.js:231-245` — callService call; `argos_translate-card.js:248-252` — reads `resp.detected_language` and `resp.detection_confidence` |
| `argos_translate-card.js` | `argos_translate.detect` service | After auto-detect translation, calls detect service to get candidates | WIRED | `argos_translate-card.js:264-281` — inner try block calls `hass.callService("argos_translate", "detect", { text: this._inputText }, ...)` |
| `argos_translate-card.js` | `container-type: inline-size` CSS | `:host` declares container; `@container argos-card` rule responds | WIRED | `argos_translate-card.js:486-487` — `:host { container-type: inline-size; container-name: argos-card; }`; `argos_translate-card.js:578` — `@container argos-card (min-width: 580px)` |
| `argos_translate-card.js` | `err.code` error discrimination | catch block inspects `err?.code` for 4-way branching | WIRED | `argos_translate-card.js:288-305` — `const code = err?.code; const msg = err?.message || "";` followed by full branch tree |

---

## Requirements Coverage

All 10 requirement IDs claimed by the three plans are accounted for:

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DTCT-01 | 05-03 | User can select "Auto" as source language in card dropdown | SATISFIED | `argos_translate-card.js:384` — `value="auto"` option as first item, default on load (`constructor: this._source = "auto"`) |
| DTCT-02 | 05-01 | Service call accepts `source: "auto"` and returns translated text with detected language info | SATISFIED | `services.py:65` — bypass guard; `services.py:94-101` — detected_language/detection_confidence in response; `test_translate_auto_detect_success` passes |
| DTCT-03 | 05-01 | Service response includes `detected_language` code and `detection_confidence` when source was "auto" | SATISFIED | `services.py:96-101` — both fields set; verified by test assertion at `test_services.py:149-151` |
| DTCT-04 | 05-03 | Card target dropdown shows all available targets when source is "Auto" | SATISFIED | `argos_translate-card.js:113-116` — `_getTargetsForSource("auto")` returns all `codes` |
| DTCT-05 | 05-03 | Card displays detected language label after auto-translate | SATISFIED | `argos_translate-card.js:452-457` — `.detection-info` div renders `Detected: [Language] ([Confidence]%)` |
| DTCT-06 | 05-01 | Card handles case where detected language is not installed | SATISFIED | Backend: `services.py:103-107` — `uninstalled_detected_language` field; Frontend: `argos_translate-card.js:255-258` — warning message set in `_error` |
| CPOL-01 | 05-02 | Card shows specific error messages (connection vs. bad request vs. timeout) | SATISFIED | `argos_translate-card.js:286-305` — 4 distinct error categories |
| CPOL-02 | 05-02 | Card explains why translate button is disabled | SATISFIED | `argos_translate-card.js:311-318` — `_getDisabledReason()` with 4 reasons; hint div at lines 469-472 |
| CPOL-03 | 05-02 | All form controls have ARIA labels for screen reader accessibility | SATISFIED | Lines 380 (source select), 415 (target select), 436 (input textarea), 444 (output textarea), 410 (swap button) |
| CPOL-04 | 05-02 | Card layout stacks properly on mobile/narrow screens | SATISFIED | `argos_translate-card.js:536-542` — `.lang-row { flex-wrap: wrap; }` with `flex: 1 1 120px` on selects; container query at line 578 for textarea panels |

No orphaned requirements found. The REQUIREMENTS.md traceability table lists all 10 IDs under Phase 5 with status Complete.

---

## Anti-Patterns Found

No blockers or stubs detected. Grep scan of all 8 phase-modified files returned only legitimate matches:

- `translation_placeholders` — HA i18n API parameter name (not a stub)
- `return null` — intentional return value from `_getDisabledReason()` meaning "no reason"
- HTML `placeholder` attributes — textarea hint text (correct usage)

No `TODO`, `FIXME`, `XXX`, `HACK`, empty implementations, or incomplete wiring found.

---

## Human Verification Required

The following items cannot be verified programmatically:

### 1. Auto-detect label update in source dropdown

**Test:** Load card in HA, enter French text (e.g., "Bonjour le monde"), select "Auto-detect" source, select "English" target, click Translate.
**Expected:** Source dropdown label changes from "Auto-detect" to "Auto (French)" immediately after translation completes.
**Why human:** Reactive property update and LitElement re-render require a live browser to confirm DOM update.

### 2. Detection candidates in source dropdown

**Test:** After auto-translate with French text, open the source dropdown.
**Expected:** One or more "Auto (Language)" candidate options appear above the separator, each representing a language detected above 50% confidence.
**Why human:** Requires a live LibreTranslate server returning `/detect` candidates; cannot mock at the browser level.

### 3. Horizontal/vertical responsive layout

**Test:** Place the card in a narrow dashboard column (< 580px) and a full-width panel (> 580px).
**Expected:** Narrow width stacks input/output textareas vertically; wide width shows them side-by-side.
**Why human:** CSS container query rendering requires a live browser; cannot be verified by static analysis.

### 4. Swap button disabled state when source is Auto

**Test:** Load card with "Auto-detect" source. Observe swap button.
**Expected:** Swap button appears visually disabled (grayed out) and clicking it does nothing.
**Why human:** Visual state requires browser; `?disabled` binding only verifiable in live DOM.

### 5. ARIA label screen reader accessibility

**Test:** Navigate card with a screen reader (e.g., NVDA + Firefox or VoiceOver + Safari).
**Expected:** Each control is announced with its aria-label: "Source language", "Target language", "Text to translate", "Translated text", "Swap languages".
**Why human:** Screen reader behavior requires assistive technology and a live browser.

---

## Test Results

```
tests/test_services.py::test_translate_success                           PASSED
tests/test_services.py::test_translate_invalid_source                   PASSED
tests/test_services.py::test_translate_invalid_target                   PASSED
tests/test_services.py::test_translate_api_error                        PASSED
tests/test_services.py::test_translate_no_config_entry                  PASSED
tests/test_services.py::test_translate_auto_detect_success              PASSED
tests/test_services.py::test_translate_auto_detect_uninstalled_language PASSED
tests/test_services.py::test_translate_auto_detect_no_validation_error  PASSED

8 passed in 0.12s

node --check argos_translate-card.js: SYNTAX OK
```

---

## Summary

Phase 5 goal is fully achieved. All 10 requirements (DTCT-01 through DTCT-06, CPOL-01 through CPOL-04) are implemented and verified against the actual codebase — not just SUMMARY claims:

- **Backend (Plans 01):** `api.py` and `coordinator.py` return full LibreTranslate response dicts enabling detected language surfacing. `services.py` accepts `source="auto"` without validation, enriches the response with detection fields, and registers a working `detect` HA service. All 8 tests pass including 3 new auto-detect tests.
- **Card Polish (Plan 02):** 4-category error discrimination in catch block, `_getDisabledReason()` with hint div, ARIA labels on all 5 interactive controls, CSS container queries for responsive layout, and config `layout` override — all present and wired.
- **Card Auto-Detect UI (Plan 03):** "Auto-detect" is first dropdown item and constructor default. `_getTargetsForSource("auto")` returns all codes. Detection feedback renders in dropdown label and `.detection-info` div. Candidates fetched via `detect` service and filtered at 50% confidence. Selecting a candidate re-translates with fixed source.

Five items flagged for human verification cover visual/browser behavior that cannot be asserted through static code analysis.

---

_Verified: 2026-02-22T08:30:00Z_
_Verifier: Claude (gsd-verifier)_
