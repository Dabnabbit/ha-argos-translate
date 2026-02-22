---
status: diagnosed
trigger: "Swapping languages when reversed pair doesn't exist causes both source and target to show the same language"
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:00:00Z
---

## Current Focus

hypothesis: _swapLanguages blindly commits the swap before checking pair validity, then the fallback silently overwrites _target with the first valid target for the new source — which is the same as the new source language when no reverse pair exists
test: trace execution of _swapLanguages when en→fr is swapped but fr→en pair doesn't exist
expecting: confirmed — _source becomes fr, _target becomes fr (first valid target for fr, which is fr or some other language that isn't en)
next_action: DONE — root cause confirmed, diagnosis returned

## Symptoms

expected: Swapping en→fr when fr→en doesn't exist should either block the swap, warn the user, or at minimum not produce fr→fr
actual: Both source and target show the same language (e.g., fr→fr) because _target is auto-corrected to validTargets[0] after the irreversible swap
errors: No error thrown or surfaced to user — silent degradation
reproduction: Have a language pair en→fr installed but NOT fr→en. Press the swap button.
started: Always (design gap, not regression)

## Eliminated

- hypothesis: Bug is in _targetChanged or the dropdown render
  evidence: _targetChanged is not involved — swap doesn't call it. Dropdown render correctly reflects _source and _target state.
  timestamp: 2026-02-22T00:00:00Z

- hypothesis: Bug is in _getTargetsForSource returning wrong data
  evidence: It returns correct data — the problem is that the swap commits before consulting it
  timestamp: 2026-02-22T00:00:00Z

## Evidence

- timestamp: 2026-02-22T00:00:00Z
  checked: _swapLanguages (lines 199–219)
  found: |
    Line 200: early return only for "auto" source — no check that the reversed pair exists.
    Lines 201–204: oldSource and oldTarget are saved, then _source = oldTarget and _target = oldSource — the swap is committed unconditionally.
    Lines 207–210: AFTER the irreversible commit, validTargets is fetched for the NEW _source. If _target (now oldSource) is not in validTargets, it is silently overwritten with validTargets[0].
    Lines 213–216: _outputText is moved to _inputText — also already committed.
  implication: |
    The "validity check" on lines 207–210 is a fallback corrector, not a guard. By the time it runs,
    _source is already the old target. If fr→en doesn't exist, validTargets for fr won't include en,
    so _target falls to validTargets[0] — often the first alphabetical target for fr, which could be
    fr itself (if fr is listed as its own target) or any other language that is NOT en. The result is
    a nonsensical or identical source/target pair with no feedback to the user.

- timestamp: 2026-02-22T00:00:00Z
  checked: _getTargetsForSource (lines 113–120)
  found: |
    Returns targets[sourceCode] from the language_targets attribute. This is the correct and complete
    list of valid targets for a given source. It is consulted AFTER the swap, not before.
  implication: The data needed to prevent the bad swap is available — it just isn't consulted pre-swap.

- timestamp: 2026-02-22T00:00:00Z
  checked: render() swap button (lines 406–412)
  found: |
    Button is only disabled when _source === 'auto'. There is no disabled state for "reverse pair
    doesn't exist", so the user can always click it even when the result will be degenerate.
  implication: No UI-level guard either — the bug is purely in _swapLanguages logic.

## Resolution

root_cause: |
  _swapLanguages commits the swap unconditionally (lines 201–204) and only checks pair validity
  AFTER the irreversible state mutation (lines 207–210). When the reversed pair doesn't exist,
  the post-swap fallback silently corrects _target to validTargets[0] — which may be the same
  language as the new _source or an unrelated language — producing a degenerate state with no
  user feedback. The swap button also has no pre-swap disabled state for this condition.

fix: |
  Pre-swap guard in _swapLanguages: before mutating any state, call
  _getTargetsForSource(oldTarget) and check whether oldSource is in that list.
  If not, either:
    Option A (block): return early without swapping; set _error to a user-friendly message
      like "Cannot swap — French → English translation is not installed."
    Option B (warn + block): same as A but with a visible ha-alert.
    Option C (partial): perform the swap but pick the closest valid target rather than [0],
      and surface a warning — still degrades but less silently.
  Recommended: Option A/B (block with error message). It is unambiguous and consistent with
  how auto-detect is blocked. The swap button could also be conditionally disabled by checking
  pair validity in render(), giving the user advance notice before they click.

files_changed: []
