---
status: investigating
trigger: "Auto-detect fails with HTTP 400 when detected language can't translate to selected target"
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:00:00Z
---

## Current Focus

hypothesis: "The HTTP 400 is raised as a CannotConnectError by api.py, masking the actual cause; the fix requires a two-phase approach: call /detect first, surface the detected language, then attempt /translate — if /translate fails with a non-auth HTTP error on auto source, catch it in services.py and return the detection result with a descriptive pair-not-available error instead of raising"
test: "Code trace complete — no actual test needed; the control flow is fully deterministic"
expecting: "Confirmed by code reading"
next_action: "Return ROOT CAUSE FOUND"

## Symptoms

expected: Auto-detect shows "Detected: [Language]" even when translation pair is unavailable, with a descriptive error about the pair
actual: HTTP 400 Bad Request shown — no detection result surfaced, no helpful error message about the pair
errors: HTTP 400 from LibreTranslate when detected language (e.g., fr) can't translate to target (e.g., en)
reproduction: Set source to Auto-detect, target to English, enter French text "Bonjour le monde", click Translate. Server detects French but fr→en pair doesn't exist, returns 400.
timeline: Discovered during Phase 5 re-test UAT

## Eliminated

- hypothesis: "The card frontend is catching the error before it can surface the detected language"
  evidence: "The card never receives a detected_language field because services.py raises HomeAssistantError before returning any response. The detection info is only available inside a successful result dict."
  timestamp: 2026-02-22T00:00:00Z

- hypothesis: "The validation in services.py blocks the request before even calling the API"
  evidence: "The source == AUTO_SOURCE guard at services.py line 65 explicitly bypasses validation for source='auto', so the call always reaches the API. The 400 is a server-side rejection of the auto-detect pair, not a pre-flight validation failure."
  timestamp: 2026-02-22T00:00:00Z

## Evidence

- timestamp: 2026-02-22T00:00:00Z
  checked: "api.py _request() method — HTTP error handling block (lines 67-70)"
  found: "Any response.status >= 400 (including 400 Bad Request) is raised as CannotConnectError with message 'Server returned HTTP 400: Bad Request'. This includes 401/403 which are also caught first as InvalidAuthError."
  implication: "A 400 from LibreTranslate when the auto-detected language can't translate to the target is indistinguishable from a network failure at the api.py layer. It always surfaces as CannotConnectError."

- timestamp: 2026-02-22T00:00:00Z
  checked: "services.py _async_handle_translate() — CannotConnectError handler (lines 89-95)"
  found: "CannotConnectError is caught and re-raised as HomeAssistantError('Translation failed: ...'). No detection result is available at this point because async_translate() raised before returning any data."
  implication: "The caller (card JS) receives only an error. The detected_language is never in the response because LibreTranslate returns 400 instead of the translated text + detectedLanguage object."

- timestamp: 2026-02-22T00:00:00Z
  checked: "services.py — result processing block (lines 97-111)"
  found: "detected_language is only extracted from result['detectedLanguage'] after a SUCCESSFUL translate call. If the call raises, this block is never reached."
  implication: "There is no path to surface the detected language when the translation itself fails with a 400."

- timestamp: 2026-02-22T00:00:00Z
  checked: "api.py async_detect_languages() — /detect endpoint (lines 110-119)"
  found: "A separate /detect endpoint exists and is already used in the card as a best-effort post-translation step. It returns [{language, confidence}, ...]."
  implication: "The fix can call /detect FIRST (or in addition to), then attempt /translate. If /translate fails with a bad pair, we still have the detection result from the /detect call."

- timestamp: 2026-02-22T00:00:00Z
  checked: "card JS _translate() method — post-success detection candidates block (lines 266-287)"
  found: "The card already calls argos_translate.detect as a best-effort step AFTER a successful translate call. This secondary call is completely skipped when translate raises."
  implication: "The detection-first logic needs to move into services.py (server side) so both detection result AND the pair-invalid error can be returned together in a single structured response, not as an exception."

- timestamp: 2026-02-22T00:00:00Z
  checked: "card JS catch block (lines 292-314)"
  found: "When services.py raises HomeAssistantError, the card receives err.code === 'home_assistant_error'. The message is checked for 'connection'/'timeout' patterns. 'Translation failed: Server returned HTTP 400: Bad Request' matches none of these patterns, so it falls through to the generic 'Translation error: {msg}' branch."
  implication: "Even if the error message were improved, the card has no path to show the detected language — it only gets an error string, not a result object."

## Resolution

root_cause: |
  Two layered failures combine to produce the symptom:

  LAYER 1 — api.py misclassifies HTTP 400 as a connection error:
    In api.py _request() (line 67-70), any HTTP status >= 400 is raised as
    CannotConnectError. A 400 from LibreTranslate when the auto-detected
    language has no translation path to the target is a semantic/validation
    error (the server understood the request but can't fulfill it), not a
    connection failure. By raising CannotConnectError, the 400 is treated
    identically to a network timeout or server unreachable error, losing the
    semantic distinction.

  LAYER 2 — services.py has no fallback detect-first path for auto source:
    When source='auto', services.py bypasses pair validation and calls
    async_translate() directly. If LibreTranslate returns 400 because the
    auto-detected language can't reach the target, the CannotConnectError
    is re-raised as HomeAssistantError with no detection data included.
    There is no two-phase logic: detect first → surface result → then
    attempt translate → if translate fails, return detection result + error.

  The result: The card receives only an error exception and never sees the
  detectedLanguage field, so _detectedLanguage stays null, the "Detected: X"
  display never renders, and the user sees a generic error with no context
  about what language was actually detected.

fix: |
  NOT APPLIED (goal: find_root_cause_only)

  Suggested fix direction:
    Option A (server-side, cleaner):
      In services.py _async_handle_translate(), when source == AUTO_SOURCE,
      call async_detect_languages() first to get the detected language code
      and confidence. Then attempt async_translate(). If translate raises a
      non-connection HTTP error (new exception type needed, e.g., ApiError),
      return a partial response: include detected_language + detection_confidence
      (from /detect) plus an error field indicating the pair is not available
      instead of raising HomeAssistantError. The card can then show the
      detection result and a descriptive error message.

    Option B (api.py fix only):
      In api.py _request(), distinguish HTTP 4xx client errors from connection
      failures by raising a new ApiRequestError (or similar) for 4xx that is
      NOT 401/403. In services.py, catch that new error type in the auto-source
      case, call /detect separately to get the language, and return detection
      result + error field. This is the same as Option A but with a cleaner
      exception hierarchy.

    Option A is preferred — it adds the detect-first logic in one place
    (services.py) without requiring a new api.py exception type, and it aligns
    with the existing pattern of calling /detect as a supplementary step.

verification: "N/A — diagnosis only"
files_changed: []
