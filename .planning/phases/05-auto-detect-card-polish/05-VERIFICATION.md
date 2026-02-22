---
phase: 05-auto-detect-card-polish
verified: 2026-02-22T12:00:00Z
status: passed
score: 5/5 gap-closure fixes verified; 16/16 observable truths verified
re_verification:
  previous_status: passed
  previous_score: 11/11
  gaps_closed:
    - "Swap button now validates reversed pair before committing swap (pre-swap guard)"
    - "Status indicator turns offline immediately on CannotConnectError (coordinator refresh)"
    - "Container query moved from :host to .card-content for shadow DOM compatibility"
    - "Card grid height reduced from 7 to 5 rows (getCardSize + getGridOptions)"
    - "Textarea resize: none — overflow into card boundary prevented"
  gaps_remaining: []
  regressions: []
---

# Phase 5: Auto-Detect + Card Polish — Re-Verification Report (Post Plan 04)

**Phase Goal:** Users can translate without knowing the source language; card is accessible and responsive
**Verified:** 2026-02-22T12:00:00Z
**Status:** PASSED
**Re-verification:** Yes — after gap closure plan 05-04 (5 UAT fixes)

---

## Re-Verification Scope

This re-verification focuses on the 5 UAT gaps closed by plan 05-04, plus regression
checks on all previously-verified items. The initial verification (08:30 UTC same day)
passed 11/11 must-have truths derived from the three plan frontmatter blocks, but those
truths were defined before the UAT run that exposed the 5 runtime issues. This report
adds explicit verification of each UAT fix.

---

## Gap-Closure Fix Verification (Plan 05-04)

### Fix 1: Pre-swap pair validation (UAT issue — invalid swap silently committed state)

**Claim:** `_swapLanguages()` checks `_getTargetsForSource(oldTarget)` and blocks swap if
reversed pair does not exist, showing a descriptive error without mutating state.

**Evidence from codebase:**

- `argos_translate-card.js:204-211` — `const reversedTargets = this._getTargetsForSource(oldTarget); if (!reversedTargets.includes(oldSource)) { ... this._error = ...; this.requestUpdate(); return; }` — early return before any state mutation when reversed pair absent
- Error message at line 209: `Cannot swap \u2014 ${targetName} \u2192 ${sourceName} translation pair is not installed.` — descriptive, names both languages
- `_source` and `_target` are only mutated at lines 214-215, AFTER the guard passes
- Auto-detect guard still present at line 200: `if (this._source === "auto") return;`
- On successful swap, `this._error = null` at line 223 clears previous error

**Status: VERIFIED**

---

### Fix 2: Status indicator immediate refresh on connection failure (UAT issue — stayed green after server unreachable)

**Claim:** `services.py _async_handle_translate` and `_async_handle_detect` both call
`await coordinator.async_request_refresh()` inside their `CannotConnectError` handlers
before re-raising as `HomeAssistantError`.

**Evidence from codebase:**

- `services.py:89-95` — translate handler: `except CannotConnectError as err: await coordinator.async_request_refresh(); raise HomeAssistantError(...) from err`
- `services.py:138-144` — detect handler: identical pattern, `await coordinator.async_request_refresh()` before re-raise
- `async_request_refresh` appears exactly 2 times in services.py (once per handler)

**Test coverage:**

- `tests/test_services.py:37` — `mock_coordinator.async_request_refresh = AsyncMock()` — mock registered
- `tests/test_services.py:119` — `mock_coordinator.async_request_refresh.assert_called_once()` — asserted in `test_translate_api_error`
- All 8 tests pass: `8 passed in 0.12s`

**Status: VERIFIED**

---

### Fix 3: Container query moved from :host to .card-content (UAT issue — responsive layout never triggered in shadow DOM)

**Claim:** `container-type: inline-size` and `container-name: argos-card` are on
`.card-content`, NOT on `:host`. `:host` retains only `display: block`.

**Evidence from codebase:**

- `argos_translate-card.js:490-492` — `:host { display: block; }` — no `container-type`, no `container-name`
- `argos_translate-card.js:499-505` — `.card-content { padding: 0 16px 16px; flex: 1; overflow: auto; container-type: inline-size; container-name: argos-card; }`
- `container-type: inline-size` appears exactly once in the file (in `.card-content` only)
- `@container argos-card (min-width: 580px)` rule at lines 584-593 unchanged — still targets the same named container, now correctly resolved from `.content-area` (child of `.card-content`) inside shadow DOM

**Status: VERIFIED**

---

### Fix 4: Grid height reduced from 7 to 5 rows (UAT issue — card overflowed into adjacent dashboard section)

**Claim:** `getCardSize()` returns `5`; `getGridOptions()` returns `rows: 5, min_rows: 4`.

**Evidence from codebase:**

- `argos_translate-card.js:87-89` — `getCardSize() { return 5; }`
- `argos_translate-card.js:91-98` — `getGridOptions() { return { rows: 5, columns: 12, min_rows: 4, min_columns: 4 }; }`

**Status: VERIFIED**

---

### Fix 5: Textarea resize: none (UAT issue — users could drag textarea beyond card boundary)

**Claim:** `textarea` CSS rule has `resize: none`, not `resize: vertical`.

**Evidence from codebase:**

- `argos_translate-card.js:569` — `resize: none;` inside the `textarea { ... }` block
- `resize: vertical` does not appear anywhere in the file

**Status: VERIFIED**

---

### Version Bump

**Claim:** `CARD_VERSION = "0.5.1"`

**Evidence:** `argos_translate-card.js:14` — `const CARD_VERSION = "0.5.1";`

**Status: VERIFIED**

---

## Commit Verification

Both commits referenced in 05-04-SUMMARY.md exist and contain exactly the files claimed:

| Commit | Message | Files Changed |
|--------|---------|---------------|
| `5d0822b` | fix(05-04): trigger coordinator refresh on CannotConnectError | `services.py` (+6), `tests/test_services.py` (+6/-1) |
| `a758559` | feat(05-04): card v0.5.1 — swap guard, container query fix, grid height, resize removal | `argos_translate-card.js` (+19/-13) |

---

## Regression Check: Previously Verified Must-Haves

All 16 observable truths from the initial verification are spot-checked for regressions:

### Observable Truths (Full Set)

| # | Truth | Status | Regression Check |
|---|-------|--------|-----------------|
| 1 | Service accepts source='auto' without ServiceValidationError | VERIFIED | `services.py:65` guard unchanged |
| 2 | Service returns translated_text + detected_language + detection_confidence | VERIFIED | `services.py:97-104` response dict unchanged |
| 3 | Uninstalled detected language returns uninstalled_detected_language warning | VERIFIED | `services.py:107-110` unchanged |
| 4 | /detect endpoint returns candidates array | VERIFIED | `api.py` not modified in plan 04 |
| 5 | HA detect service callable from card | VERIFIED | `services.py:148-154` registration unchanged |
| 6 | Card shows 4-category error discrimination | VERIFIED | `argos_translate-card.js:292-311` unchanged |
| 7 | Disabled translate button shows hint text | VERIFIED | `_getDisabledReason()` at lines 317-325 unchanged; hint IIFE at 475-478 unchanged |
| 8 | All 5 interactive controls have aria-label | VERIFIED | Lines 386, 414-415, 442, 453 unchanged |
| 9 | CSS container query responds to card width | VERIFIED | Fix 3 above — now correctly on .card-content, not :host |
| 10 | Layout config override (auto/horizontal/vertical) works | VERIFIED | `argos_translate-card.js:373-374, 594-603` unchanged |
| 11 | Auto-detect is first option and constructor default | VERIFIED | `constructor:41 this._source = "auto"`; option at line 390 unchanged |
| 12 | Target dropdown shows all languages when source is auto | VERIFIED | `_getTargetsForSource("auto")` at line 114 unchanged |
| 13 | Source dropdown label updates to Auto (Language) after detection | VERIFIED | `argos_translate-card.js:391-393` unchanged |
| 14 | Detection candidates above 50% shown as auto:XX options | VERIFIED | Filter at line 280; render at lines 395-401 unchanged |
| 15 | Selecting candidate re-translates with fixed source | VERIFIED | `_sourceChanged` at lines 159-187 unchanged |
| 16 | Swap button blocks swap when source is auto | VERIFIED | `argos_translate-card.js:200` `if (this._source === "auto") return;` present |

**Score: 16/16 truths verified — 0 regressions**

---

## Required Artifacts

| Artifact | Provides | Exists | Substantive | Wired | Status |
|----------|----------|--------|-------------|-------|--------|
| `custom_components/argos_translate/services.py` | async_request_refresh in both CannotConnectError handlers | Yes | Yes — 155 lines, both handlers patched | Called by HA service dispatch | VERIFIED |
| `custom_components/argos_translate/frontend/argos_translate-card.js` | Pre-swap guard, container query fix, grid reduction, resize removal, v0.5.1 | Yes | Yes — 785 lines, all 4 card fixes present, version bumped | Loaded by HA Lovelace | VERIFIED |
| `tests/test_services.py` | async_request_refresh AsyncMock + assert_called_once in test_translate_api_error | Yes | Yes — AsyncMock at line 37; assertion at line 119 | 8/8 tests pass | VERIFIED |

---

## Key Link Verification (Plan 05-04 Specific)

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `services.py _async_handle_translate catch` | `coordinator.async_request_refresh()` | CannotConnectError handler calls refresh before re-raise | WIRED | `services.py:92` — `await coordinator.async_request_refresh()` inside except block |
| `services.py _async_handle_detect catch` | `coordinator.async_request_refresh()` | CannotConnectError handler calls refresh before re-raise | WIRED | `services.py:141` — same pattern in detect handler |
| `.card-content CSS` | `@container argos-card` | container-type on .card-content enables shadow-DOM-local container query | WIRED | `.card-content:503-504` declares container; `@container argos-card (min-width: 580px)` at line 584 consumes it; `:host` block has no container-type |
| `_swapLanguages()` | `_getTargetsForSource(oldTarget)` | Pre-swap guard uses existing helper to check reversed pair | WIRED | `argos_translate-card.js:205` — `const reversedTargets = this._getTargetsForSource(oldTarget);` |

---

## Requirements Coverage

All 10 Phase 5 requirement IDs are accounted for. Plan 05-04 claims CPOL-04 and STAB-04.

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DTCT-01 | 05-03 | User can select "Auto" as source language | SATISFIED | `constructor:41`, option at line 390 |
| DTCT-02 | 05-01 | Service accepts source="auto", returns detected language info | SATISFIED | `services.py:65` bypass; `services.py:97-104` response |
| DTCT-03 | 05-01 | detected_language + detection_confidence in response | SATISFIED | `services.py:103-104`; test assertion at line 153-155 |
| DTCT-04 | 05-03 | All target languages shown when source is Auto | SATISFIED | `_getTargetsForSource("auto"):114-116` |
| DTCT-05 | 05-03 | Card displays detected language after auto-translate | SATISFIED | `.detection-info` div at lines 458-463 |
| DTCT-06 | 05-01 | Uninstalled detected language shows user warning | SATISFIED | Backend: `services.py:107-110`; Frontend: `argos_translate-card.js:261-263` |
| CPOL-01 | 05-02 | Specific error messages (connection, timeout, bad request) | SATISFIED | 4-branch catch at lines 292-311 |
| CPOL-02 | 05-02 | Translate button disabled with explanation | SATISFIED | `_getDisabledReason()` lines 317-325; hint div lines 475-478 |
| CPOL-03 | 05-02 | ARIA labels on all form controls | SATISFIED | Lines 386 (source), 415 (target), 442 (input textarea), 453 (output textarea), 414 (swap button) |
| CPOL-04 | 05-02 + 05-04 | Card layout stacks on narrow screens | SATISFIED | `flex-wrap: wrap` at line 547; container query fix now correctly fires inside shadow DOM |
| STAB-04 | 05-04 | Bugs found during manual testing fixed and tests updated | SATISFIED | 5 UAT bugs fixed in commits 5d0822b + a758559; `test_translate_api_error` now asserts refresh called |

No orphaned requirements. REQUIREMENTS.md traceability table lists all 10 Phase 5 IDs as
Complete and STAB-04 is marked as satisfied by the plan 05-04 work.

---

## Anti-Patterns Found

No anti-patterns in either modified file.

Grep for `TODO|FIXME|XXX|HACK|PLACEHOLDER` in `services.py`: 0 matches.
Grep for `TODO|FIXME|XXX|HACK|PLACEHOLDER` in `argos_translate-card.js`: 0 matches.

The word "placeholder" appears only in HTML `placeholder` attributes on textarea elements
(legitimate UX hint text, not a stub indicator).

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

## Human Verification Required

The following items require a live browser and HA instance. None are newly introduced by
plan 05-04; items 1 and 2 are directly related to the gap-closure fixes.

### 1. Pre-swap error message renders on invalid pair

**Test:** Load card with "English" source and "Spanish" target. Change source to a
language that has no reverse pair to Spanish (e.g., "French" if fr->es is not installed).
Click the swap button.
**Expected:** An `ha-alert` appears with text like "Cannot swap — Spanish -> French
translation pair is not installed." Source and target dropdowns remain unchanged.
**Why human:** DOM state mutation and reactive re-render require a live browser.

### 2. Status dot turns red immediately on server failure

**Test:** Stop the LibreTranslate server. Click Translate from the card.
**Expected:** The status dot turns red (offline) within ~1 second of the translation
attempt failing, without waiting up to 5 minutes for the next poll cycle.
**Why human:** Requires live HA instance with running coordinator and actual network
failure to observe timing of binary_sensor state change.

### 3. Container query triggers responsive layout at 580px

**Test:** Place card in a narrow column (< 580px wide) and in a wide panel (> 580px wide).
**Expected:** Narrow: textareas stack vertically. Wide: textareas appear side by side.
**Why human:** CSS container query rendering inside a shadow DOM requires a live browser
to confirm the .card-content-scoped query fires correctly post-fix.

### 4. Grid height fits content without overflow

**Test:** Add card to a dashboard grid. Observe whether it overflows into the section below.
**Expected:** Card fills 5 grid rows and stops; no content bleeds into adjacent sections.
**Why human:** Dashboard layout and visual overflow require a live HA instance.

### 5. Textarea cannot be resized by user drag

**Test:** Hover over the bottom-right corner of either textarea. Attempt to drag-resize.
**Expected:** No resize handle cursor appears; textarea dimensions remain fixed.
**Why human:** Browser cursor and drag behavior require a live browser to confirm.

---

## Summary

All 5 UAT gap-closure fixes from plan 05-04 are confirmed present and correctly wired in
the actual codebase:

1. **Pre-swap guard** (`argos_translate-card.js:204-212`): `_getTargetsForSource(oldTarget)` called before state mutation; descriptive error set and early return on invalid pair.
2. **Coordinator refresh on failure** (`services.py:92, 141`): `await coordinator.async_request_refresh()` present in both CannotConnectError handlers; test asserts it is called once.
3. **Container query on .card-content** (`argos_translate-card.js:503-504`): `container-type: inline-size` and `container-name: argos-card` on `.card-content` only; `:host` block has only `display: block`.
4. **Grid height reduction** (`argos_translate-card.js:88, 93, 95`): `getCardSize()` returns 5; `getGridOptions()` returns `rows: 5, min_rows: 4`.
5. **Textarea resize: none** (`argos_translate-card.js:569`): `resize: none` confirmed; `resize: vertical` absent from file.

Card version confirmed at 0.5.1. Both commits (5d0822b, a758559) verified in git history
and match the file changes claimed in the SUMMARY. All 8 Python tests pass including
`test_translate_api_error` which now asserts `async_request_refresh` is called once on
failure. JS syntax check passes. No regressions on the 16 previously verified observable
truths. All 10 Phase 5 requirement IDs (DTCT-01 through DTCT-06, CPOL-01 through CPOL-04)
are satisfied and cross-referenced against REQUIREMENTS.md. STAB-04 satisfied.

Phase 5 goal is achieved. Five human verification items remain for live-browser
confirmation of visual and runtime behavior that cannot be asserted through static analysis.

---

_Verified: 2026-02-22T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification after: plan 05-04 gap closure (5 UAT fixes)_
