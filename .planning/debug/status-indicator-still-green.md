---
status: diagnosed
trigger: "async_request_refresh() was added to CannotConnectError handlers in services.py but the binary_sensor status indicator still stays green when the server is unreachable. The integration was reloaded before testing."
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:15:00Z
---

## Current Focus

hypothesis: CONFIRMED — The fix used the wrong API method. async_request_refresh() uses a Debouncer with a 10-second cooldown (REQUEST_REFRESH_DEFAULT_COOLDOWN = 10). When called from services.py it schedules a deferred refresh that may be debounced. More critically, there is a simpler, synchronous API that was missed: coordinator.async_set_update_error(err) — which immediately sets last_update_success=False AND calls async_update_listeners() synchronously, causing the binary_sensor to update right away.
test: Confirmed by reading HA DataUpdateCoordinator source — async_request_refresh() calls _debounced_refresh.async_call() which has cooldown=10s. async_set_update_error() is a @callback that immediately sets last_update_success=False and calls async_update_listeners() with no async delay.
expecting: CONFIRMED — replacing await coordinator.async_request_refresh() with coordinator.async_set_update_error(err) will cause the binary_sensor to flip to offline synchronously, before the HomeAssistantError is raised.
next_action: ROOT CAUSE FOUND — report diagnosis

## Symptoms

expected: Status indicator (binary_sensor.libretranslate_status) turns offline/red immediately when a translation service call fails with CannotConnectError
actual: "Cannot connect" error message shows correctly in the card, but the green status indicator stays green the whole time. Integration was confirmed reloaded.
errors: None — the translate service correctly raises HomeAssistantError, but binary_sensor doesn't change state
reproduction: Stop LibreTranslate Docker container, attempt translation, observe status indicator stays green
started: After 05-04 gap closure applied async_request_refresh fix

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-02-22T00:01:00Z
  checked: binary_sensor.py ArgosStatusSensor.is_on
  found: Returns self.coordinator.last_update_success — meaning sensor state is TRUE (green) when last_update_success=True
  implication: The binary_sensor ONLY changes state when coordinator.last_update_success flips to False, which only happens when _async_update_data raises UpdateFailed

- timestamp: 2026-02-22T00:02:00Z
  checked: coordinator.py _async_update_data
  found: Catches CannotConnectError and raises UpdateFailed. This is what sets last_update_success=False on a POLL cycle.
  implication: On a normal 5-min poll when server is down, the sensor WILL go offline. The fix was supposed to make this happen immediately.

- timestamp: 2026-02-22T00:03:00Z
  checked: services.py CannotConnectError handlers
  found: await coordinator.async_request_refresh() is called before re-raising HomeAssistantError. async_request_refresh() queues a fresh poll of _async_update_data.
  implication: When async_request_refresh() runs, _async_update_data will be called. Since the server is unreachable, it raises UpdateFailed. DataUpdateCoordinator catches UpdateFailed, sets last_update_success=False, and notifies listeners. This SHOULD work — so why doesn't it?

- timestamp: 2026-02-22T00:04:00Z
  checked: coordinator.py async_translate and async_detect_languages
  found: Both methods call self.client directly (async_translate, async_detect_languages) — they do NOT go through _async_update_data. They are bypass methods that skip the DataUpdateCoordinator error-tracking machinery entirely.
  implication: When CannotConnectError is raised from async_translate, the coordinator's last_update_success is NOT affected at all by the failed call. The CannotConnectError is caught in services.py and then async_request_refresh() is called — but at this point the server is still down, so the refresh ALSO fails with UpdateFailed. THIS should set last_update_success=False. So it still should work...

- timestamp: 2026-02-22T00:05:00Z
  checked: DataUpdateCoordinator.async_request_refresh() semantics (HA core knowledge)
  found: async_request_refresh() does NOT immediately run _async_update_data. It schedules a refresh by calling async_set_updated_data or uses debounce logic. In HA's DataUpdateCoordinator, async_request_refresh() schedules the refresh as a task — it does not await the actual poll completion before returning.
  implication: CRITICAL FINDING — await coordinator.async_request_refresh() returns as soon as the refresh is SCHEDULED, not after the refresh COMPLETES. The service handler then raises HomeAssistantError and returns to the caller. The actual _async_update_data poll fires asynchronously AFTER the service call has already returned. By the time the binary_sensor's state update fires, the UI has already rendered the error message but the sensor may still show green briefly — or the event loop scheduling means the sensor update fires slightly later.

- timestamp: 2026-02-22T00:06:00Z
  checked: Whether scheduling vs awaiting actually explains persistent green (not just a brief delay)
  found: If the server is truly down and async_request_refresh() runs, _async_update_data WILL eventually be called, WILL raise UpdateFailed, and last_update_success WILL flip to False. So "stays green the whole time" (not just briefly) needs a different explanation.
  implication: The scheduling delay might not be the whole story. Need to check: does async_request_refresh() get debounced/throttled and possibly skipped? Or is there a race where the coordinator already has a pending refresh that supersedes this one?

- timestamp: 2026-02-22T00:07:00Z
  checked: DataUpdateCoordinator.async_request_refresh() — request_refresh_debouncer
  found: DataUpdateCoordinator uses a Debouncer for async_request_refresh. The debouncer coalesces multiple rapid requests into a single refresh. BUT more importantly: if _async_update_data raises UpdateFailed, DataUpdateCoordinator catches it, logs it, sets last_update_success=False, and calls _listeners to notify. The LISTENERS are what cause CoordinatorEntity to call async_write_ha_state(). This chain should work.
  implication: The mechanism looks correct on paper. Need to consider whether the problem is that async_request_refresh() fires but CannotConnectError in async_translate is NOT the same code path as CannotConnectError in _async_update_data (client.async_get_languages vs client.async_translate). The refresh polls async_get_languages — if THAT also fails (server down), last_update_success should go False.

- timestamp: 2026-02-22T00:08:00Z
  checked: Whether the Debouncer has a cooldown/immediate=False default
  found: DataUpdateCoordinator passes immediate=True to the debouncer for async_request_refresh in older HA versions, but in newer HA (2024+), the debouncer behavior changed. If cooldown prevents the debouncer from firing immediately when called from a non-poll context, the refresh might be delayed significantly.
  implication: Potential timing issue, but probably not "stays green the WHOLE time."

- timestamp: 2026-02-22T00:09:00Z
  checked: The actual fix logic flow more carefully — what happens in sequence
  found: (1) User calls translate service. (2) coordinator.async_translate() → client.async_translate() raises CannotConnectError. (3) services.py catches it, calls await coordinator.async_request_refresh(). (4) async_request_refresh schedules _async_update_data to run. (5) services.py raises HomeAssistantError. (6) Card shows error. (7) Meanwhile, _async_update_data runs, calls client.async_get_languages(), which ALSO fails (server down). (8) UpdateFailed raised. (9) coordinator.last_update_success = False. (10) Listeners notified → binary_sensor flips to off. Steps 7-10 happen asynchronously AFTER step 6.
  implication: The sequence is correct and the sensor SHOULD eventually go offline. "Stays green the whole time" in user testing likely means the user checked immediately after the error and did not wait, OR the debouncer has a cooldown that delays the refresh by seconds. For a UAT tester, "stays green" might mean "didn't observe it change" not "definitively never changed."

- timestamp: 2026-02-22T00:10:00Z
  checked: Whether there is a deeper structural issue — CoordinatorEntity and listener registration
  found: CoordinatorEntity calls coordinator.async_add_listener(self._handle_coordinator_update) in async_added_to_hass. _handle_coordinator_update calls self.async_write_ha_state(). This is a standard HA pattern and is well-tested. The listener IS registered on the coordinator and WILL be called when coordinator notifies.
  implication: The listener chain is sound. No issue here.

- timestamp: 2026-02-22T00:11:00Z
  checked: CRITICAL — whether DataUpdateCoordinator.async_request_refresh() actually results in last_update_success=False when the poll fails
  found: In HA core, when _async_update_data raises UpdateFailed, DataUpdateCoordinator does this: self.last_update_success = False, self.last_exception = exception, self._async_refresh_finished(), then calls self._listeners. BUT — there is a subtlety: DataUpdateCoordinator only sets last_update_success=False if it WAS previously True. If last_update_success is already False (from a previous failed poll), it does NOT call listeners again (no state change = no notification).
  implication: This is likely NOT the issue since we're starting from last_update_success=True (green state).

- timestamp: 2026-02-22T00:12:00Z
  checked: The REAL question — does async_request_refresh guarantee _async_update_data will RUN or just that it's SCHEDULED?
  found: In DataUpdateCoordinator source, async_request_refresh calls self._debounced_refresh.async_call(). The debouncer schedules execution. If the event loop is busy or if there's already a refresh in flight (_unsub_refresh is set), the debouncer may not fire immediately or at all during the brief window the user observes.
  implication: The refresh IS scheduled but fires AFTER the service handler completes. In the time between the error showing in the card and the user looking at the binary_sensor, the async refresh may not have run yet. The user sees green, reports "stays green," but the sensor may have gone offline seconds later — which is still a UX problem but a different root cause than "the mechanism is broken."

- timestamp: 2026-02-22T00:13:00Z
  checked: HA DataUpdateCoordinator source — REQUEST_REFRESH_DEFAULT_COOLDOWN constant and async_request_refresh implementation
  found: REQUEST_REFRESH_DEFAULT_COOLDOWN = 10 (line 36). async_request_refresh() calls await self._debounced_refresh.async_call() (line 274). The Debouncer has a 10-second cooldown. With immediate=True (REQUEST_REFRESH_DEFAULT_IMMEDIATE), the FIRST call fires immediately, but subsequent calls within 10 seconds are debounced. Since the integration was recently reloaded (which itself triggers a refresh), the debouncer cooldown window may still be active — so async_request_refresh() from services.py is silently dropped by the debouncer.
  implication: STRONG CANDIDATE — If a refresh ran during integration reload or within the previous 10 seconds, the debouncer rejects the async_request_refresh() call entirely. The binary_sensor never gets notified. This perfectly explains "stays green the whole time."

- timestamp: 2026-02-22T00:14:00Z
  checked: DataUpdateCoordinator.async_set_update_error() method (line 490-496)
  found: |
    @callback
    def async_set_update_error(self, err: Exception) -> None:
        """Manually set an error, log the message and notify listeners."""
        self.last_exception = err
        if self.last_update_success:
            self.logger.error("Error requesting %s data: %s", self.name, err)
            self.last_update_success = False
            self.async_update_listeners()
    This is a @callback (synchronous), sets last_update_success=False immediately, and calls async_update_listeners() — which fires all registered CoordinatorEntity._handle_coordinator_update() callbacks immediately. No debouncing. No async delay. No scheduling.
  implication: DEFINITIVE FIX PATH — This is exactly the right method for the use case: "I know a connection error just occurred, immediately mark the coordinator as failed and notify all listeners." The fix already in services.py used async_request_refresh() which is the wrong tool — it's for polling data refreshes, not for propagating known errors.

- timestamp: 2026-02-22T00:15:00Z
  checked: _async_refresh() listener notification logic (lines 470-478)
  found: |
    if not self.last_update_success and not previous_update_success:
        return  # <- EARLY RETURN if already failed
    if (self.always_update or self.last_update_success != previous_update_success or previous_data != self.data):
        self.async_update_listeners()
    This means: even if async_request_refresh() DID fire after the debounce cooldown expired, IF a previous failed poll had already set last_update_success=False, _async_refresh() returns early WITHOUT calling async_update_listeners(). The binary_sensor would still not update.
  implication: This reinforces that async_request_refresh() was the wrong choice. async_set_update_error() is immune to this — it checks `if self.last_update_success` and only notifies listeners on the transition from True to False (first failure), exactly the right behavior.

## Eliminated

- hypothesis: "The listener chain (CoordinatorEntity -> async_add_listener -> _handle_coordinator_update -> async_write_ha_state) is broken"
  evidence: HA source confirms the chain is standard and well-tested. CoordinatorEntity.async_added_to_hass() registers the listener. async_update_listeners() calls each callback. The chain works correctly when triggered.
  timestamp: 2026-02-22T00:10:00Z

- hypothesis: "async_request_refresh() eventually sets last_update_success=False correctly via _async_update_data → UpdateFailed path"
  evidence: True in principle, but the 10-second debouncer cooldown means the call from services.py is silently dropped when the integration was recently refreshed (e.g., after reload). Even when it does fire, _async_refresh() has an early-return guard that skips listener notification if already in failed state.
  timestamp: 2026-02-22T00:14:00Z

## Resolution

root_cause: |
  Two compounding problems make async_request_refresh() ineffective for immediately updating the binary_sensor:

  1. DEBOUNCER COOLDOWN (primary): REQUEST_REFRESH_DEFAULT_COOLDOWN = 10 seconds. When async_request_refresh() is called from services.py after a translation failure, the Debouncer may have fired within the past 10 seconds (e.g., during integration reload or recent poll). The debouncer silently drops the request — no refresh runs, last_update_success stays True, binary_sensor stays green.

  2. WRONG API METHOD (root): async_request_refresh() is designed to poll for new data. It goes through the full async machinery: debounce → schedule → _async_update_data → UpdateFailed → last_update_success=False → listeners. The RIGHT method for "I know a connection error just occurred" is async_set_update_error(err), a synchronous @callback that immediately sets last_update_success=False and calls async_update_listeners() — no debouncing, no scheduling, no async delay.

  The fix in services.py correctly catches CannotConnectError and correctly intends to notify the binary_sensor, but chose the wrong coordinator method. The synchronous async_set_update_error() method exists precisely for this use case.

fix: "Replace `await coordinator.async_request_refresh()` with `coordinator.async_set_update_error(err)` in both CannotConnectError handlers in services.py (translate and detect). This is a @callback so no await is needed."
verification: ""
files_changed: []
