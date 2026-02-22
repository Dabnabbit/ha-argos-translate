---
status: resolved
trigger: "After a translation fails due to server being unreachable, the error message shows correctly, but the status indicator (green circle = Online) doesn't update to show the server is offline."
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:00:00Z
---

## Current Focus

hypothesis: confirmed - status indicator is architecturally decoupled from service call failures
test: traced full data flow from service call -> coordinator -> entity state -> card render
expecting: N/A - root cause confirmed, no further testing needed
next_action: return diagnosis

## Symptoms

expected: After a translation service call fails because the server is unreachable, the status dot should switch from green (Online) to red (Offline).
actual: Status dot remains green (Online) even after a connection error during translation.
errors: Card shows "Cannot connect to LibreTranslate server. Check that it is running." correctly, but status indicator stays green.
reproduction: Trigger a translation while the LibreTranslate server is unreachable.
started: By design — status and translation share the coordinator but the service call failure does not update coordinator state.

## Eliminated

- hypothesis: _getStatus() reads local card state (_error) and fails to check the server
  evidence: _getStatus() (line 128-137) reads from hass.states[entity] — entirely separate from _error
  timestamp: 2026-02-22T00:00:00Z

- hypothesis: The coordinator is not polling at all
  evidence: Coordinator polls every DEFAULT_SCAN_INTERVAL = 300 seconds (5 min), confirmed in coordinator.py line 32
  timestamp: 2026-02-22T00:00:00Z

## Evidence

- timestamp: 2026-02-22T00:00:00Z
  checked: argos_translate-card.js _getStatus() lines 128-137
  found: Reads hass.states[this.config.entity].state — a binary_sensor entity. Returns {online: true} when state === "on".
  implication: The card has NO local awareness of connectivity — it only reflects what HA entity state says.

- timestamp: 2026-02-22T00:00:00Z
  checked: binary_sensor.py ArgosStatusSensor.is_on lines 53-56
  found: Returns coordinator.last_update_success — a DataUpdateCoordinator built-in boolean flag.
  implication: The sensor is only "on" or "off" based on whether the coordinator's last SCHEDULED POLL succeeded.

- timestamp: 2026-02-22T00:00:00Z
  checked: coordinator.py _async_update_data lines 44-54
  found: Polls async_get_languages() on a timer (DEFAULT_SCAN_INTERVAL = 300 seconds). Sets last_update_success=False if CannotConnectError is raised.
  implication: Status only changes on poll cycle — not on service call failures.

- timestamp: 2026-02-22T00:00:00Z
  checked: services.py _async_handle_translate lines 87-92
  found: Calls coordinator.async_translate() and catches CannotConnectError, re-raising as HomeAssistantError. Does NOT call coordinator.async_request_refresh() or mutate coordinator.last_update_success.
  implication: A service call failure is completely invisible to the coordinator's state tracking.

- timestamp: 2026-02-22T00:00:00Z
  checked: card.js _translate() catch block lines 286-308
  found: Card catches the HomeAssistantError, sets this._error. No action to trigger a status re-check.
  implication: The card correctly surfaces the error text but has no mechanism to force a status refresh.

- timestamp: 2026-02-22T00:00:00Z
  checked: coordinator.py async_translate lines 56-65
  found: A thin wrapper around client.async_translate — does not update last_update_success on failure.
  implication: The coordinator's DataUpdateCoordinator machinery only updates last_update_success inside _async_update_data (the scheduled poll). Errors from async_translate are entirely outside that mechanism.

## Resolution

root_cause: |
  The status indicator reads `binary_sensor.X.state` (via _getStatus(), card.js line 129), which reflects
  `ArgosStatusSensor.is_on` (binary_sensor.py line 56), which reflects `coordinator.last_update_success`
  (a DataUpdateCoordinator built-in). That flag is ONLY updated by the coordinator's scheduled polling
  method `_async_update_data` (coordinator.py lines 44-54, polling interval = 300 seconds via const.py
  DEFAULT_SCAN_INTERVAL). Service call failures in services.py catch CannotConnectError and raise
  HomeAssistantError but never touch coordinator state. The card catch block (card.js lines 286-308)
  sets _error text but has no path to refresh the entity. Result: up to 5 minutes can pass before the
  status dot turns red after the server goes offline.

fix: |
  Two complementary options, not mutually exclusive:

  OPTION A — Coordinator-side (services.py): After a CannotConnectError in _async_handle_translate,
  call `await coordinator.async_request_refresh()` before re-raising. This causes the coordinator to
  immediately run _async_update_data, which will also fail, setting last_update_success=False and
  pushing the updated binary_sensor state to HA. The card will pick it up on the next hass update push.
  This is the architecturally correct fix — the coordinator is the single source of truth.

  OPTION B — Card-side only (not recommended alone): The card cannot directly force a coordinator
  refresh; hass.callService() cannot trigger a coordinator poll. The card has no API to request
  coordinator.async_request_refresh() from the frontend. So a card-only fix is not possible.

  RECOMMENDATION: Fix in services.py. Card requires no changes.

verification: N/A — diagnosis-only mode
files_changed: []
