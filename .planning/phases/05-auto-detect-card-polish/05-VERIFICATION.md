---
phase: 05-auto-detect-card-polish
verified: 2026-02-22T18:30:00Z
status: gaps_found
score: 19/20 must-haves verified
re_verification:
  previous_status: passed
  previous_score: 16/16
  gaps_closed:
    - "TranslationError added to api.py for HTTP 4xx — semantic distinction from CannotConnectError (plan 05-05)"
    - "async_set_update_error replaces async_request_refresh in both CannotConnectError handlers — immediate binary_sensor flip (plan 05-05)"
    - "Detect-first fallback for auto source — returns partial response with detected_language when pair unavailable (plan 05-05)"
    - "11 tests pass including 3 new tests covering pair-unavailable scenarios (plan 05-05)"
    - ":host { height: 100%; box-sizing: border-box } — card constrained to grid slot (plan 05-06)"
    - ".container-wrap div with container-type: inline-size wraps .content-area — Approach A fix (plan 05-06)"
    - "CARD_VERSION bumped to 0.5.2 (plan 05-06)"
    - "getCardSize() returns 4; getGridOptions() rows:4, min_rows:3 (plan 05-06)"
  gaps_remaining:
    - "Card does not read resp.error from partial response — user sees empty output with no error explanation when auto-detect pair is unavailable"
  regressions: []
gaps:
  - truth: "Card shows descriptive error when auto-detect pair is unavailable"
    status: failed
    reason: "The backend (plan 05-05) returns a partial response dict with an 'error' field when auto-detect hits HTTP 400 (pair unavailable). The card's _translate() method reads resp.translated_text, resp.detected_language, resp.detection_confidence, and resp.uninstalled_detected_language from a successful call — but NEVER reads resp.error. The descriptive 'Detected French but French → Spanish translation pair is not available.' message is silently dropped. User sees empty output box and detected-language label but no error explanation."
    artifacts:
      - path: "custom_components/argos_translate/frontend/argos_translate-card.js"
        issue: "_translate() lines 250-291: resp.error is never checked in the success path. After setting this._outputText = resp.translated_text and this._detectedLanguage, there is no if (resp.error) { this._error = resp.error; } branch."
    missing:
      - "Add resp.error check in the success path of _translate() — after setting _detectedLanguage, if resp.error exists set this._error = resp.error so the ha-alert renders the descriptive pair-unavailable message"
human_verification:
  - test: "Responsive horizontal layout at >= 580px"
    expected: "Place card in a panel wider than 580px. Input and output textareas appear side-by-side. Narrow panel (<580px): textareas stack vertically."
    why_human: "CSS container query on .container-wrap requires a live browser inside HA shadow DOM to confirm it fires. Approach A (container-wrap div) was verified by commit; whether browser renders it as expected requires live confirmation."
  - test: "Card height fits grid slot without overflow"
    expected: "Card fills its 4-row grid allocation and does not overflow into adjacent dashboard sections. Content that exceeds the slot scrolls internally."
    why_human: "Dashboard grid slot calculation and visual overflow require a live HA instance."
  - test: "Status indicator flips offline immediately on CannotConnectError"
    expected: "Stop LibreTranslate server, click Translate. Binary sensor state in Developer Tools shows 'off' within ~1 second of the failed call — no 5-minute poll delay."
    why_human: "Requires live HA instance with coordinator running to observe binary_sensor state change timing."
---

# Phase 5: Auto-Detect + Card Polish — Re-Verification Report (Post Plans 05-05 and 05-06)

**Phase Goal:** Users can translate without selecting a source language, see the detected language in the card, and interact with an accessible and mobile-friendly card
**Verified:** 2026-02-22T18:30:00Z
**Status:** GAPS_FOUND
**Re-verification:** Yes — after gap closure plans 05-05 (backend) and 05-06 (card CSS)

---

## Re-Verification Scope

This re-verification covers plans 05-05 and 05-06, which were executed after the previous
VERIFICATION.md (status: passed, 16/16 truths). The UAT re-test revealed 4 gaps; two plans
were written to close them. This report verifies those fixes against the actual codebase and
checks for any new issues introduced.

**Plans covered:**
- **05-05**: TranslationError class, async_set_update_error, detect-first fallback
- **05-06**: :host height constraint, .container-wrap for container query, version 0.5.2

---

## Plan 05-05: Backend Error Handling and Auto-Detect Fallback

### Fix A: TranslationError class in api.py

**Claim:** `TranslationError(Exception)` added to api.py. HTTP 400+ raises `TranslationError`
instead of `CannotConnectError`.

**Evidence from codebase:**

- `api.py:24-29` — `class TranslationError(Exception): """Raised when the server returns a semantic error (HTTP 4xx, excluding 401/403)."""`
- `api.py:75-78` — `if response.status >= 400: raise TranslationError(f"Server returned HTTP {response.status}: {response.reason}")`
- `CannotConnectError` is only raised for `aiohttp.ClientConnectionError`, `aiohttp.ClientError`, and `asyncio.TimeoutError` (lines 63-68) — true connection failures

**Status: VERIFIED**

---

### Fix B: async_set_update_error replaces async_request_refresh in both CannotConnectError handlers

**Claim:** Both `CannotConnectError` handlers in services.py use
`coordinator.async_set_update_error(err)` (synchronous @callback, no debounce). No
`async_request_refresh` calls remain in services.py.

**Evidence from codebase:**

- `services.py:138` — auto-source CannotConnectError handler: `coordinator.async_set_update_error(err)`
- `services.py:149` — non-auto source CannotConnectError handler: `coordinator.async_set_update_error(err)`
- `services.py:204` — detect handler CannotConnectError: `coordinator.async_set_update_error(err)`
- `async_request_refresh` — 0 occurrences in services.py (grep confirmed)

**Test coverage:**

- `test_services.py:37-39` — `mock_coordinator.async_request_refresh = AsyncMock()` (kept for non-assertion safety) and `mock_coordinator.async_set_update_error = MagicMock()` (synchronous mock)
- `test_services.py:122` — `mock_coordinator.async_set_update_error.assert_called_once()` in `test_translate_api_error`

**Status: VERIFIED**

---

### Fix C: Detect-first fallback for auto source returning partial response

**Claim:** When `source == AUTO_SOURCE`, services.py calls `/detect` first (best-effort), then
`/translate`. If `/translate` raises `TranslationError` (HTTP 4xx), returns a partial dict
`{"translated_text": "", "detected_language": ..., "error": ...}` instead of raising
`HomeAssistantError`.

**Evidence from codebase:**

- `services.py:88-141` — `if source == AUTO_SOURCE:` block
- `services.py:91-94` — detect-first: `detect_result = await coordinator.async_detect_languages(text)` inside try/except that swallows errors (best-effort)
- `services.py:96-134` — translate call inside separate try: `TranslationError` caught at line 98, partial response built with `translated_text: ""`, `detected_language`, `detection_confidence`, and descriptive `error` message; returns at line 134 without raising
- `services.py:135-141` — `CannotConnectError` in auto path still calls `async_set_update_error` and raises `HomeAssistantError`

**Test coverage (3 new tests):**

- `test_translate_auto_detect_pair_unavailable` — mocks TranslationError on translate, detect returns `[{"language": "fr", "confidence": 92.0}]`; asserts `result["translated_text"] == ""`, `result["detected_language"] == "fr"`, `result["detection_confidence"] == 92.0`, `"error" in result`, `async_set_update_error NOT called`
- `test_translate_auto_detect_pair_unavailable_no_detect` — detect raises CannotConnectError, translate raises TranslationError; asserts partial response: `translated_text == ""`, `"error" in result`, no `detected_language`
- `test_translate_translation_error_non_auto` — non-auto source, translate raises TranslationError; asserts `HomeAssistantError` raised, `async_set_update_error NOT called`

**Status: VERIFIED**

---

### Test Results (Plan 05-05)

```
tests/test_services.py::test_translate_success                                   PASSED
tests/test_services.py::test_translate_invalid_source                           PASSED
tests/test_services.py::test_translate_invalid_target                           PASSED
tests/test_services.py::test_translate_api_error                                PASSED
tests/test_services.py::test_translate_no_config_entry                          PASSED
tests/test_services.py::test_translate_auto_detect_success                      PASSED
tests/test_services.py::test_translate_auto_detect_uninstalled_language         PASSED
tests/test_services.py::test_translate_auto_detect_no_validation_error          PASSED
tests/test_services.py::test_translate_auto_detect_pair_unavailable             PASSED
tests/test_services.py::test_translate_auto_detect_pair_unavailable_no_detect   PASSED
tests/test_services.py::test_translate_translation_error_non_auto               PASSED

11 passed in 0.16s
```

**Status: ALL TESTS PASS**

---

## Plan 05-06: Card CSS Gap Closure

### Fix 1: :host height constraint

**Claim:** `:host { display: block; height: 100%; box-sizing: border-box; }` chains to
`ha-card { height: 100% }` and `.card-content { flex: 1; overflow: auto }` so the card
fills its grid slot and scrolls internally.

**Evidence from codebase:**

- `argos_translate-card.js:492-496` — `:host { display: block; height: 100%; box-sizing: border-box; }`
- `argos_translate-card.js:497-502` — `ha-card { overflow: hidden; height: 100%; display: flex; flex-direction: column; }`
- `argos_translate-card.js:503-507` — `.card-content { padding: 0 16px 16px; flex: 1; overflow: auto; }` — no container-type (moved to .container-wrap)

**Status: VERIFIED**

---

### Fix 2: .container-wrap div for container query (Approach A)

**Claim:** A new `.container-wrap` wrapper div is inserted in render() around `.content-area`.
`container-type: inline-size` and `container-name: argos-card` are moved from `.card-content`
to `.container-wrap`. `.card-content` retains only `flex: 1; overflow: auto`.

**Evidence from codebase:**

- `argos_translate-card.js:437-458` — `<div class="container-wrap"><div class="content-area">...</div></div>` in render()
- `argos_translate-card.js:508-511` — `.container-wrap { container-type: inline-size; container-name: argos-card; }`
- `argos_translate-card.js:503-507` — `.card-content` has no container-type or container-name
- `argos_translate-card.js:590-599` — `@container argos-card (min-width: 580px) { .content-area { flex-direction: row; } ... }` — unchanged, targets same name
- No `ResizeObserver` and no `data-wide` attribute in codebase

**Note on SUMMARY inconsistency:** The 05-06-SUMMARY narrative states "Approach B
(ResizeObserver) used" but the actual commit `f586c2a` message says "Approach A
(container-wrap div)" and the code confirms Approach A. The SUMMARY narrative appears
to be erroneous; it may have been drafted assuming Approach B was needed but the
implementation settled on Approach A. The codebase and commit message are consistent —
Approach A was implemented. Whether `.container-wrap` without `overflow: auto` or `flex: 1`
(unlike `.card-content`) allows the container query to resolve correctly at runtime is a
live-browser verification item.

**Status: VERIFIED (code is consistent; Approach A implemented)**

---

### Fix 3: Version bump and grid options

**Claim:** `CARD_VERSION = "0.5.2"`, `getCardSize()` returns 4, `getGridOptions()` rows:4/min_rows:3.

**Evidence from codebase:**

- `argos_translate-card.js:14` — `const CARD_VERSION = "0.5.2";`
- `argos_translate-card.js:87-89` — `getCardSize() { return 4; }`
- `argos_translate-card.js:91-97` — `getGridOptions() { return { rows: 4, columns: 12, min_rows: 3, min_columns: 4 }; }`

**Status: VERIFIED**

---

### JS Syntax Check

```
node --check argos_translate-card.js: SYNTAX OK
```

---

## Commit Verification

| Commit | Message | Files Changed |
|--------|---------|---------------|
| `dadd71e` | fix(05-05): add TranslationError, async_set_update_error for immediate status flip | `api.py` (+10/-1) |
| `e307b00` | feat(05-05): detect-first fallback for auto source; update and add tests | `services.py` (+91 net), `test_services.py` |
| `f586c2a` | feat(05-06): card v0.5.2 — height constraint, container query fix | `argos_translate-card.js` (+28/-22) |

All three commits exist in git history and match the file changes claimed in the summaries.

---

## GAP FOUND: Card does not display resp.error from partial response

### Root cause

The backend's detect-first fallback (plan 05-05) returns a partial response dict for the
service call when auto-detect hits an unavailable pair:

```python
# services.py lines 98-134
except TranslationError as err:
    response = {"translated_text": "", "error": str(err)}
    if detect_result:
        ...
        response["error"] = f"Detected {detected_name} but {detected_name} → {target_name} translation pair is not available."
    return response
```

This is NOT an exception — it is a successful service call returning a structured dict.

The card's `_translate()` handles this in the `try` block (success path), reading
`result.response`:

```javascript
// argos_translate-card.js lines 250-291
const resp = result.response;
this._outputText = resp.translated_text;       // sets to ""
if (sourceToSend === "auto" && resp.detected_language) {
    this._detectedLanguage = { ... };           // sets detected language
    if (resp.uninstalled_detected_language) {   // checks this field
        this._error = `...`;
    }
}
// NO check for resp.error here
```

`resp.error` is never read. The descriptive "Detected French but French → Spanish
translation pair is not available." message is silently discarded. The user sees:
- Output textarea: empty
- Detection label: "Detected: French (92%)"
- Error alert: not shown

The user cannot tell WHY translation failed — they only see an empty output with the
detected language. This breaks the DTCT-06 requirement for showing a user-visible
message when the pair is unavailable.

### Impact

- **DTCT-06**: "Card handles case where detected language is not installed (shows
  user-visible message)" — PARTIAL. The `uninstalled_detected_language` path (line 261)
  is still handled for the case where the language is not installed. But the pair-unavailable
  case (language IS detected, pair just not installed) shows no error.

### Fix required

In `_translate()`, after setting `this._detectedLanguage` and checking
`resp.uninstalled_detected_language`, add:

```javascript
if (resp.error) {
    this._error = resp.error;
}
```

This surfaces the descriptive error from the backend partial response so the user sees
"Detected French but French → Spanish translation pair is not available."

---

## Full Observable Truths Verification

### Previously Verified (Regression Check)

| # | Truth | Status | Regression Check |
|---|-------|--------|-----------------|
| 1 | Service accepts source='auto' without ServiceValidationError | VERIFIED | `services.py:65` guard unchanged |
| 2 | Service returns translated_text + detected_language + detection_confidence | VERIFIED | `services.py:159-174` response dict unchanged |
| 3 | Uninstalled detected language returns uninstalled_detected_language warning | VERIFIED | `services.py:169-172` unchanged |
| 4 | /detect endpoint returns candidates array | VERIFIED | `services.py:199-214` detect handler unchanged |
| 5 | HA detect service callable from card | VERIFIED | `services.py:216-222` registration unchanged |
| 6 | Card shows 4-category error discrimination | VERIFIED | `argos_translate-card.js:292-311` unchanged |
| 7 | Disabled translate button shows hint text | VERIFIED | `_getDisabledReason()` lines 317-325 unchanged; hint IIFE lines 477-480 unchanged |
| 8 | All 5 interactive controls have aria-label | VERIFIED | Lines 386, 416, 421, 443, 453 — 5 aria-label attributes present |
| 9 | CSS container query responds to card width | VERIFIED (code) | Approach A .container-wrap confirmed; live behavior is human verification item |
| 10 | Layout config override (auto/horizontal/vertical) works | VERIFIED | `argos_translate-card.js:373-374, 600-609` unchanged |
| 11 | Auto-detect is first option and constructor default | VERIFIED | `constructor:41 this._source = "auto"`; option at lines 390-394 unchanged |
| 12 | Target dropdown shows all languages when source is auto | VERIFIED | `_getTargetsForSource("auto")` at lines 113-117 unchanged |
| 13 | Source dropdown label updates to Auto (Language) after detection | VERIFIED | `argos_translate-card.js:391-393` unchanged |
| 14 | Detection candidates above 50% shown as auto:XX options | VERIFIED | Filter at lines 280-282; render at lines 395-401 unchanged |
| 15 | Selecting candidate re-translates with fixed source | VERIFIED | `_sourceChanged` at lines 159-187 unchanged |
| 16 | Swap button blocks swap when source is auto | VERIFIED | `argos_translate-card.js:200` guard present |

### New Truths from Plans 05-05 and 05-06

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 17 | Status indicator flips offline immediately on CannotConnectError (no debounce) | VERIFIED (code) | `services.py:138, 149, 204` — async_set_update_error called synchronously; test asserts it at line 122; async_request_refresh has 0 occurrences in services.py |
| 18 | HTTP 400 from LibreTranslate is TranslationError, not CannotConnectError | VERIFIED | `api.py:75-78` — `raise TranslationError(...)` for status >= 400 |
| 19 | Auto-detect with pair unavailable returns partial response with detected_language | VERIFIED | `services.py:98-134` — TranslationError caught, returns dict with detected_language; test_translate_auto_detect_pair_unavailable passes |
| 20 | Card displays descriptive error from partial response when auto-detect pair unavailable | FAILED | `argos_translate-card.js:250-291` — resp.error never checked in success path; error message silently dropped |

**Score: 19/20 truths verified — 1 gap**

---

## Required Artifacts

| Artifact | Provides | Exists | Substantive | Wired | Status |
|----------|----------|--------|-------------|-------|--------|
| `custom_components/argos_translate/api.py` | TranslationError class; HTTP 4xx raises TranslationError | Yes | Yes — 128 lines, TranslationError at lines 24-29, raised at line 76 | Imported by services.py line 19 | VERIFIED |
| `custom_components/argos_translate/services.py` | async_set_update_error; detect-first auto path; partial response | Yes | Yes — 223 lines, 3x async_set_update_error, detect-first at line 92, partial response at lines 98-134 | Called by HA service dispatch | VERIFIED |
| `tests/test_services.py` | 11 tests including 3 new pair-unavailable tests | Yes | Yes — 291 lines, 11 test functions; all pass | 11/11 pass | VERIFIED |
| `custom_components/argos_translate/frontend/argos_translate-card.js` | :host height:100%; .container-wrap; v0.5.2 | Yes | Yes — 791 lines; all CSS fixes confirmed; resp.error NOT handled in success path | Loaded by HA Lovelace | PARTIAL (resp.error gap) |

---

## Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `services.py CannotConnectError handlers` | `coordinator.async_set_update_error(err)` | synchronous @callback — no debouncing | WIRED | `services.py:138, 149, 204` — 3 occurrences; 0 occurrences of async_request_refresh |
| `services.py auto-detect path` | `coordinator.async_detect_languages()` | detect-first call before translate attempt | WIRED | `services.py:92` before `services.py:97` |
| `services.py TranslationError handler (auto path)` | `return response dict` | partial response instead of raise | WIRED | `services.py:103-134` — returns `{"translated_text": "", "error": ..., "detected_language": ...}` |
| `argos_translate-card.js _translate() success path` | `resp.error` | read error field from partial response | NOT WIRED | `argos_translate-card.js:250-291` — resp.error never read; only resp.translated_text, resp.detected_language, resp.detection_confidence, resp.uninstalled_detected_language are read |
| `:host CSS` | `ha-card height:100%` | height:100% on :host constrains to grid slot | WIRED | `:host` line 494: `height: 100%`; `ha-card` line 499: `height: 100%` |
| `.container-wrap CSS` | `@container argos-card (min-width: 580px)` | container-type on .container-wrap enables container query for child .content-area | WIRED (code) | `.container-wrap:508-511` declares container; `@container argos-card` at line 590 targets it; requires live-browser confirmation |

---

## Requirements Coverage

All 10 Phase 5 requirement IDs cross-referenced against REQUIREMENTS.md:

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DTCT-01 | 05-03, 05-06 | User can select "Auto" as source language in the card dropdown | SATISFIED | `constructor:41`, option at lines 390-394; plan 05-06 adjustments did not regress this |
| DTCT-02 | 05-01, 05-05 | Service accepts source="auto", returns translated text with detected language info | SATISFIED | `services.py:65` bypass; detect-first at line 92; `services.py:159-174` response; partial response at lines 103-134 |
| DTCT-03 | 05-01, 05-05 | Service response includes detected_language code and detection_confidence | SATISFIED | `services.py:165-166` (normal path), `services.py:111-112` (partial path) |
| DTCT-04 | 05-03, 05-06 | Card target dropdown shows all available targets when source is "Auto" | SATISFIED | `_getTargetsForSource("auto"):113-117` returns all codes |
| DTCT-05 | 05-03, 05-05 | Card displays detected language label after auto-translate | SATISFIED | `.detection-info` div at lines 460-465 |
| DTCT-06 | 05-01, 05-05 | Card handles case where detected language is not installed (shows user-visible message) | PARTIAL | Backend returns `error` field in partial response (services.py:124-127); uninstalled_detected_language handled in card (lines 261-263); BUT `resp.error` from pair-unavailable partial response is NOT read by card (gap) |
| CPOL-01 | 05-02, 05-05 | Specific error messages (connection error vs. bad request vs. timeout) | SATISFIED | 4-branch catch at lines 292-311; TranslationError now distinct from CannotConnectError at API level |
| CPOL-02 | 05-02 | Translate button disabled with explanation | SATISFIED | `_getDisabledReason()` lines 317-325; hint div lines 477-480 |
| CPOL-03 | 05-02 | ARIA labels on all form controls | SATISFIED | Lines 386 (source), 416 (swap), 421 (target), 443 (input textarea), 453 (output textarea) — 5 labels |
| CPOL-04 | 05-02, 05-04, 05-06 | Card layout stacks properly on mobile/narrow screens | SATISFIED (code) | `flex-wrap: wrap` at line 553; `.container-wrap` container-type for responsive layout at lines 508-511; `:host { height: 100% }` for grid slot containment; live-browser confirmation pending |

**DTCT-06 is partially satisfied.** The `uninstalled_detected_language` warning path works
(when the language itself is not installed). The pair-unavailable error path (language IS
detected but the translation pair is not installed) does not surface a visible error to the
user because `resp.error` is not read in the card success path.

No orphaned requirements. REQUIREMENTS.md traceability table lists all 10 Phase 5 IDs
as Complete. STAB-04 is also satisfied.

---

## Anti-Patterns Found

Grep for `TODO|FIXME|XXX|HACK|PLACEHOLDER` in all modified files: 0 matches.
Grep for stub patterns (`return null`, `return {}`, etc.) in card render(): none.
The word "placeholder" appears only in HTML `placeholder` attributes (legitimate UX text).

No anti-patterns.

---

## Human Verification Required

### 1. Responsive horizontal layout at >= 580px (Approach A container-wrap)

**Test:** Place card in a dashboard panel >= 580px wide and in a narrow column (< 580px).
**Expected:** Wide panel: input and output textareas appear side-by-side (horizontal). Narrow: textareas stack vertically.
**Why human:** The `.container-wrap` div (no overflow:auto, no flex) should allow `container-type: inline-size` to resolve correctly, enabling `@container argos-card (min-width: 580px)`. The 05-06-SUMMARY claims this was human-verified passing on the live HA instance, but the SUMMARY narrative incorrectly described the approach as "Approach B (ResizeObserver)" while the code shows Approach A. A fresh live-browser check is warranted to confirm the container query actually fires.

### 2. Card height fits grid slot without overflow

**Test:** Add card to a dashboard grid. Observe whether it overflows into the section below.
**Expected:** Card fills 4 grid rows and stops; no content bleeds into adjacent sections; excess content scrolls internally.
**Why human:** Dashboard layout and visual overflow require a live HA instance.

### 3. Status indicator flips offline immediately on CannotConnectError

**Test:** Stop the LibreTranslate server. Click Translate from the card. Observe Developer Tools > States > binary_sensor.libretranslate_status.
**Expected:** Status flips to 'off' within ~1 second — no 5-minute poll delay.
**Why human:** Requires live HA instance with running coordinator and actual network failure to observe binary_sensor state change timing.

### 4. Auto-detect pair-unavailable shows error message in card (blocked by code gap)

**Test:** With auto-detect selected, type text in a language whose detected language has no translation pair to the selected target. Click Translate.
**Expected:** Card shows detected language label AND an error alert with the descriptive message "Detected [Language] but [Language] → [Target] translation pair is not available."
**Current behavior (code analysis):** Card shows detected language label only; error alert is NOT shown. This is the gap — resp.error is not read.
**Why human (after fix):** End-to-end requires live HA + LibreTranslate to confirm actual behavior.

---

## Gaps Summary

One gap was found that was not present in any previous verification: the card's `_translate()`
method in the success path does not read `resp.error` from the partial response returned by
the backend when auto-detect encounters an unavailable translation pair. The backend change
(plan 05-05) correctly returns the descriptive error in the response dict, but the card
(plan 05-06 and earlier) has no code to display it.

This gap breaks **DTCT-06** for the pair-unavailable case — the user sees an empty output
and the detected language label but no explanation of why translation failed. The fix is
a single conditional in `_translate()`:

```javascript
// After setting this._detectedLanguage and checking resp.uninstalled_detected_language:
if (resp.error) {
    this._error = resp.error;
}
```

All other 05-05 and 05-06 changes are confirmed in the codebase and verified against the
plan must-haves. 11/11 tests pass. JS syntax is valid. No anti-patterns. No regressions
on the 16 previously verified observable truths.

---

_Verified: 2026-02-22T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification after: plans 05-05 (backend error handling + detect-first) and 05-06 (card CSS — height constraint + container query)_
