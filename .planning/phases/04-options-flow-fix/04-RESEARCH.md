# Phase 4: Options Flow Fix - Research

**Researched:** 2026-02-21
**Domain:** Home Assistant config entry options flow, coordinator reload pattern
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Connection validation**
- Test connection before saving (same as initial config flow)
- Reuse the existing `_async_validate_connection` helper from the config flow — keep code DRY and behavior consistent
- Only commit the config change if the connection test passes
- Invalid settings show an error in the form; user can correct and retry

**Form design**
- Single page with all four fields: host, port, SSL toggle, API key
- All fields pre-filled with current saved values (including API key)
- No multi-step flow — matches the simplicity of initial setup

**Reload behavior**
- Auto-reload after saving: call `async_reload` so the integration reconnects with new settings immediately
- Standard HA options flow UX: form closes, integration reloads in background, HA shows normal success/error state
- Coordinator refetches languages from the new server immediately after reload — card updates right away
- If the new server has different languages installed, reset any selected source/target language that's no longer available

### Claude's Discretion

- Error message granularity (reuse existing errors vs. more specific connection/SSL/auth errors)
- Whether to auto-change port when SSL is toggled (e.g., 5000 vs 443)
- Whether to include integration name in the options flow or keep it connection-settings-only
- Handling of post-validation reload failures (save anyway vs. rollback)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OPTS-01 | User can reconfigure host, port, API key, and SSL toggle from the integration's options without removing and re-adding | Options flow form already exists with all four fields pre-filled; the form schema and translation strings are in place. No structural additions required. |
| OPTS-02 | Options flow triggers coordinator reload so changes take effect immediately (no HA restart required) | The missing `await self.hass.config_entries.async_reload(self.config_entry.entry_id)` call is the fix. Coordinator reads `entry.data` at `__init__` time; without reload it uses stale credentials indefinitely. Explicit reload forces `async_unload_entry` → `async_setup_entry` → new coordinator with new client. |
</phase_requirements>

---

## Summary

Phase 4 is a single-bug fix. The `OptionsFlowHandler` in `config_flow.py` already exists, validates the connection correctly, updates `entry.data`, and shows the form pre-filled with current values. The only missing piece is an explicit `await self.hass.config_entries.async_reload(self.config_entry.entry_id)` call after `async_update_entry` succeeds. Without it, the coordinator object created during `async_setup_entry` continues to hold a reference to the old `ArgosTranslateApiClient` (built with the old host/port/API key at `__init__` time). Translation and language polling silently continue using the old server — the user sees no error even though their new settings were "saved."

The fix is three lines of code in `config_flow.py`. Everything else — the form schema, the translation strings in `strings.json`/`en.json`, the validation logic, the data merge pattern — is already correct. The test for the options flow (`test_options_flow` in `test_config_flow.py`) exists but does not assert that `async_reload` is called. New tests must cover: (1) successful save triggers reload, (2) connection error does not save or reload, (3) auth error does not save or reload.

The STATE.md decision locks the approach: use an explicit `async_reload` call (not `OptionsFlowWithReload`), because `OptionsFlowWithReload` was introduced in HA 2025.8 and the project targets 2025.7+. The explicit pattern works on all supported HA versions.

**Primary recommendation:** Add `await self.hass.config_entries.async_reload(self.config_entry.entry_id)` immediately after `async_update_entry` in `OptionsFlowHandler.async_step_init`, then add test assertions that `async_reload` is called on success and not called on error.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `homeassistant.config_entries.OptionsFlow` | HA 2024.x+ | Base class for the options flow handler | Already in use; explicit `async_reload` works on all versions ≥ 2024 |
| `homeassistant.config_entries.ConfigEntries.async_reload` | HA 2024.x+ | Triggers full `async_unload_entry` → `async_setup_entry` cycle | Standard HA mechanism for forcing coordinator rebuild after credential changes |
| `homeassistant.config_entries.ConfigEntries.async_update_entry` | HA 2024.x+ | Writes merged credentials back to `entry.data` | Required because coordinator reads from `entry.data`, not `entry.options` |
| `voluptuous` | HA-bundled | Options form schema validation | Already used for the options form |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest-homeassistant-custom-component` | Test framework | Testing config and options flows in isolation | All options flow unit tests |
| `unittest.mock.AsyncMock` | stdlib | Mock `_async_validate_connection` and `async_reload` in tests | Prevents real HTTP calls and real HA reload during test |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Explicit `async_reload` | `OptionsFlowWithReload` base class | `OptionsFlowWithReload` is cleaner but requires HA 2025.8+; project targets 2025.7+. Use explicit `async_reload` for version safety. |
| Explicit `async_reload` | `entry.add_update_listener` in `__init__.py` | Listener pattern works but requires boilerplate listener function, cleanup registration, and cannot run pre-save validation. Explicit call in the flow is simpler and already co-located with validation. |
| Options flow for credential changes | `async_step_reconfigure` + `async_update_reload_and_abort` | The HA-idiomatic path for connection credential changes. However the existing options flow already works correctly for this integration; adding a duplicate reconfigure step would be redundant. Document the intentional choice. |

**Installation:** No new packages. All patterns are provided by HA itself.

---

## Architecture Patterns

### Recommended Project Structure

No structural changes. All edits are within existing files:

```
custom_components/argos_translate/
├── config_flow.py         # EDIT: add async_reload call in OptionsFlowHandler
└── (no other files change)

tests/
└── test_config_flow.py    # EDIT: add reload assertion and error path tests
```

### Pattern 1: Options Flow With Explicit Reload

**What:** After `async_update_entry` succeeds, immediately call `async_reload` with the entry ID before returning `async_create_entry(data={})`.

**When to use:** Any options flow that updates values read by a coordinator at `__init__` time. The coordinator holds a snapshot of `entry.data` — it does not re-read from the config entry on each poll. Only a full reload forces coordinator reconstruction with new values.

**Example (target state for `config_flow.py`):**
```python
# Source: HA community pattern confirmed in ARCHITECTURE.md research
else:
    self.hass.config_entries.async_update_entry(
        self.config_entry, data=merged
    )
    # Reload so coordinator rebuilds with new connection credentials.
    # async_reload triggers: async_unload_entry → async_setup_entry → new ArgosCoordinator
    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
    return self.async_create_entry(data={})
```

The `await` is required — `async_reload` is a coroutine. Calling it without `await` silently schedules the reload but the flow returns before it runs, making the result unpredictable.

### Pattern 2: Data vs Options — Keep Writing to `entry.data`

**What:** The options flow stores updated connection settings in `entry.data` (not `entry.options`) by calling `async_update_entry(config_entry, data=merged)` where `merged = {**self.config_entry.data, **user_input}`. This is the existing pattern in the codebase and it is correct for this integration.

**When to use:** When the coordinator reads from `entry.data` exclusively. The standard HA pattern would store options in `entry.options`, but this integration predates any options and stores all configuration in `entry.data`. Changing the storage location would require a migration.

**Why this must not change:** `ArgosCoordinator.__init__` reads `entry.data[CONF_HOST]`, `entry.data[CONF_PORT]`, etc. If new values land in `entry.options` instead, the coordinator rebuilds with the old data after reload.

```python
# coordinator.py — reads entry.data at construction time
self.client = ArgosTranslateApiClient(
    host=entry.data[CONF_HOST],      # captured at __init__; stale until reload
    port=entry.data[CONF_PORT],
    api_key=entry.data.get(CONF_API_KEY, ""),
    session=session,
    use_ssl=entry.data.get(CONF_USE_SSL, False),
)
```

### Pattern 3: Validate Before Save

**What:** Run the full `_async_validate_connection` test against the new values (merged with existing data to include `CONF_NAME`) before calling `async_update_entry`. Only on successful validation proceed to update + reload.

**When to use:** Any options flow that changes connection credentials. Without pre-save validation, a typo in the host field saves invalid credentials and leaves the integration broken until the user manually reconfigures again.

**Current implementation status:** Already implemented correctly. The merge logic correctly combines `self.config_entry.data` (which contains `CONF_NAME`) with `user_input` (which contains the four editable fields) before validation.

### Anti-Patterns to Avoid

- **No `await` on `async_reload`:** Silently schedules reload but flow returns before it executes; coordinator may not rebuild in time and the result is race-condition-dependent.
- **Writing to `entry.options` instead of `entry.data`:** The coordinator reads `entry.data` exclusively. Writing to `entry.options` and reloading produces a coordinator with the old credentials.
- **Calling `async_reload` on error path:** Must only reload on successful validation. Reloading when validation failed would unload a working integration.
- **Removing the merge with `self.config_entry.data`:** `user_input` from the options form does not include `CONF_NAME`. If the merge is dropped, `entry.data` loses the name field after save.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Coordinator rebuild with new credentials | Manual attribute mutation on coordinator or client | `async_reload` | Reload guarantees full teardown and reconstruction; mutation leaves stale state (update listeners, sensor references, etc.) |
| Integration restart after save | `hass.services.async_call("homeassistant", "reload_config_entry", ...)` | `hass.config_entries.async_reload(entry_id)` | Direct config_entries API is the correct internal path; service call adds unnecessary indirection |
| Pre-fill form with current values | Complex form state management | `vol.Optional(CONF_HOST, default=self.config_entry.data.get(CONF_HOST, ""))` | Voluptuous `default=` handles pre-fill natively in HA forms |

**Key insight:** The HA config_entries framework owns the lifecycle. Don't try to partially update a running coordinator — let reload handle teardown and reconstruction cleanly.

---

## Common Pitfalls

### Pitfall 1: Missing `await` on `async_reload`

**What goes wrong:** `async_reload` returns a coroutine. Without `await`, Python schedules it on the event loop but the options flow handler returns immediately. The reload may run later or not at all before the flow result is processed. The integration appears to save but the coordinator does not rebuild.

**Why it happens:** Python silently discards unawaited coroutines. HA will log a warning but it may not be obvious in the UI.

**How to avoid:** Always write `await self.hass.config_entries.async_reload(self.config_entry.entry_id)`.

**Warning signs:** Options form closes, but translation still uses old server. HA logs show no `async_setup_entry` call for the new host.

### Pitfall 2: Coordinator Uses Stale Credentials (the Core Bug)

**What goes wrong:** The existing options flow calls `async_update_entry` but does not call `async_reload`. The `ArgosCoordinator` continues using the `ArgosTranslateApiClient` instance built at the previous `async_setup_entry` call. Even though `entry.data` now contains the new host/port/key, the coordinator's `self.client` still points to the old server.

**Why it happens:** `async_update_entry` is a synchronous call that updates the in-memory config entry object and persists it to storage. It does not trigger any integration lifecycle callbacks. The coordinator, which holds a direct reference to the API client object, is unaffected.

**How to avoid:** Add `await self.hass.config_entries.async_reload(self.config_entry.entry_id)` after `async_update_entry`.

**Warning signs:** After saving a changed host address, translation continues to succeed (it should fail if the new host is unreachable). HA logs show the old host URL after reload.

### Pitfall 3: Writing Merged Data to `entry.options` Instead of `entry.data`

**What goes wrong:** If the options flow returns `async_create_entry(data=user_input)` without the prior `async_update_entry` call (the standard HA options pattern), the user_input ends up in `entry.options`. After reload, the coordinator reads `entry.data` and builds the client with the old credentials.

**Why it happens:** The standard HA options flow stores in `entry.options`. This integration intentionally deviates — all configuration is in `entry.data`. The deviation is intentional but fragile.

**How to avoid:** Preserve the existing pattern: `merged = {**self.config_entry.data, **user_input}`, then `async_update_entry(config_entry, data=merged)`, then reload, then `return self.async_create_entry(data={})` (empty options). Add a comment explaining this deviation so future maintainers do not "fix" it to the standard pattern.

**Warning signs:** After saving, `self.config_entry.data` still shows old host but `self.config_entry.options` shows new host.

### Pitfall 4: Reload Failure After Successful Validation

**What goes wrong:** Validation passes with the new server address. `async_update_entry` writes the new data. `async_reload` is called. During reload, `async_setup_entry` fails (e.g., the server became unreachable in the milliseconds between validation and reload). The integration enters a failed state with the new credentials saved.

**Why it happens:** There is an inherent race between the validation HTTP call and the coordinator's first refresh. This is a general HA issue, not specific to this integration.

**How to avoid (Claude's discretion area):** This is the "post-validation reload failure" discretion item from CONTEXT.md. Two options:
1. Accept the failure — HA will show the integration as "failed" and the user can reload or fix. The new credentials are saved; they just need a working server. This is the simplest path and matches standard HA behavior.
2. Rollback — re-write the old data before reload. Complex and non-standard; not recommended.
Recommendation: accept the failure. The new credentials are correct; the server was transiently unavailable. HA's retry / manual reload handles it.

### Pitfall 5: Existing `test_options_flow` Test Does Not Assert Reload

**What goes wrong:** The existing test (`test_options_flow`) verifies that `entry.data` is updated correctly but does not assert that `async_reload` is called. A plan that adds the reload call without also updating the test will pass the existing test suite — giving false confidence.

**Why it happens:** The test was written before the reload requirement was identified.

**How to avoid:** Add a `patch` for `hass.config_entries.async_reload` and assert it was called once with the correct `entry_id` on the success path. Assert it was NOT called on error paths.

---

## Code Examples

Verified patterns from the existing codebase and official HA patterns:

### Current `OptionsFlowHandler.async_step_init` (the bug — missing reload)

```python
# custom_components/argos_translate/config_flow.py (current state)
else:
    self.hass.config_entries.async_update_entry(
        self.config_entry, data=merged
    )
    return self.async_create_entry(data={})
    # BUG: coordinator still uses old entry.data values; no reload triggered
```

### Fixed `OptionsFlowHandler.async_step_init` (target state)

```python
# Source: HA community pattern; async_reload confirmed in official HA docs
else:
    self.hass.config_entries.async_update_entry(
        self.config_entry, data=merged
    )
    # Reload so coordinator rebuilds with new connection credentials.
    # Triggers: async_unload_entry → async_setup_entry → new ArgosCoordinator
    # with new ArgosTranslateApiClient constructed from updated entry.data.
    # Note: credentials are stored in entry.data (not entry.options) because
    # ArgosCoordinator.__init__ reads entry.data. This is intentional.
    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
    return self.async_create_entry(data={})
```

### Test Pattern — Assert Reload Called on Success

```python
# tests/test_config_flow.py — new test or extension of test_options_flow
async def test_options_flow_triggers_reload(hass: HomeAssistant) -> None:
    """Test that saving options triggers an integration reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "My LibreTranslate",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_USE_SSL: False,
            CONF_API_KEY: "old-key",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with (
        patch(
            "custom_components.argos_translate.config_flow._async_validate_connection",
            return_value=None,
        ),
        patch.object(
            hass.config_entries,
            "async_reload",
            return_value=True,
        ) as mock_reload,
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "new-key",
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    mock_reload.assert_called_once_with(entry.entry_id)
```

### Test Pattern — Assert Reload NOT Called on Error

```python
async def test_options_flow_no_reload_on_error(hass: HomeAssistant) -> None:
    """Test that a connection error does not trigger reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "My LibreTranslate",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_USE_SSL: False,
            CONF_API_KEY: "old-key",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with (
        patch(
            "custom_components.argos_translate.config_flow._async_validate_connection",
            side_effect=CannotConnect,
        ),
        patch.object(
            hass.config_entries,
            "async_reload",
        ) as mock_reload,
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "bad-host",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    mock_reload.assert_not_called()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `entry.add_update_listener` + separate reload function in `__init__.py` | `OptionsFlowWithReload` base class | HA 2025.8 | Eliminates boilerplate; but requires HA 2025.8+ |
| Manual `async_update_entry` + `async_reload` in options flow | Same pattern | Stable since HA 2024.x | Works on all versions; chosen for this integration |
| `async_step_reconfigure` + `async_update_reload_and_abort` | Alternative credential-change pattern | HA 2024.x | More idiomatic for non-optional config changes; not used here since the options flow already covers the use case |

**Deprecated/outdated:**
- Passing `config_entry` explicitly to `OptionsFlow.__init__`: deprecated in HA 2025.1; `self.config_entry` is now provided automatically by the framework. The existing codebase does not use the deprecated pattern.

---

## What Is Already Correct (Do Not Change)

The following aspects of the current implementation are working and must be preserved:

1. **Form schema** — `vol.Optional(CONF_HOST, default=self.config_entry.data.get(...))` correctly pre-fills all four fields from current `entry.data`.

2. **Merge pattern** — `merged = {**self.config_entry.data, **user_input}` correctly preserves `CONF_NAME` which is not in the options form.

3. **Validation** — Calls `_async_validate_connection(self.hass, merged)` with the full merged dict before saving. Errors map to existing translation strings (`cannot_connect`, `invalid_auth`, `no_languages`).

4. **Translation strings** — `strings.json` and `en.json` already contain the `options.step.init` section with correct field labels and error messages. No translation changes needed.

5. **`async_get_options_flow` registration** — `@staticmethod @callback` correctly returns `OptionsFlowHandler()` from `ArgosTranslateConfigFlow`. No changes needed.

---

## Open Questions

1. **Post-reload failure handling (Claude's discretion)**
   - What we know: Validation passes, data is saved, reload is called, `async_setup_entry` fails (transient server issue). Integration enters `ConfigEntryState.SETUP_ERROR`.
   - What's unclear: Should the phase add any UX for this case (e.g., log message, or attempt to restore old data)?
   - Recommendation: Accept HA's default behavior — integration shows as failed, user retries or reloads. The credentials are correct; the server was transiently unavailable. No rollback logic needed for this phase. Document in code comments.

2. **SSL toggle auto-port (Claude's discretion)**
   - What we know: When toggling SSL, 5000 (default LibreTranslate HTTP) vs 443 (HTTPS) would require JavaScript-level form interaction, which HA config flows do not support natively.
   - What's unclear: Whether auto-changing port is expected by users.
   - Recommendation: Do not implement auto-port change. The port field is always editable and pre-filled. Users who enable SSL and need port 443 can change the port field themselves. Keep the form simple.

3. **Integration name in options form (Claude's discretion)**
   - What we know: `CONF_NAME` is used as the device name and is not in the options form; it's preserved via the merge pattern.
   - What's unclear: Whether users who want to rename the integration can do so.
   - Recommendation: Do not add `CONF_NAME` to the options form. The phase is about connection settings. Renaming can be done via HA's built-in "rename" UI. Keep the options form focused.

---

## Sources

### Primary (HIGH confidence)
- Existing codebase — `config_flow.py`, `coordinator.py`, `api.py`, `__init__.py`, `strings.json`, `test_config_flow.py` — read directly during research
- `.planning/research/ARCHITECTURE.md` — options flow reload pattern with code examples; verified against HA patterns
- `.planning/research/SUMMARY.md` — `async_reload` decision and version compatibility analysis
- `.planning/research/STACK.md` — `OptionsFlowWithReload` version requirements (HA 2025.8+), explicit `async_reload` compatibility
- `.planning/research/PITFALLS.md` — Pitfall 1 (coordinator stale credentials), Pitfall 4 (data vs options storage)
- `.planning/STATE.md` — Decision: "Options flow uses explicit `async_reload` (not `OptionsFlowWithReload`) for HA 2025.7+ compatibility"
- [HA Options Flow Handler docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/) — `OptionsFlowWithReload` documentation and code examples

### Secondary (MEDIUM confidence)
- [HA community: ConfigFlowHandler and OptionsFlowHandler managing same parameter](https://community.home-assistant.io/t/configflowhandler-and-optionsflowhandler-managing-the-same-parameter/365582) — confirmed `async_update_entry` to `entry.data` + separate `async_reload` pattern
- [HA community: OptionsFlowHandler does not work as expected](https://community.home-assistant.io/t/optionsflowhandler-does-not-work-as-expected/547622) — confirmed coordinator stale credentials as common issue

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all patterns are HA framework internals confirmed in prior research and official docs
- Architecture: HIGH — three-line fix with clear before/after; coordinator read pattern confirmed by code inspection
- Pitfalls: HIGH — core bug (missing `async_reload`) is unambiguous from code inspection; test gap identified by reading existing test

**Research date:** 2026-02-21
**Valid until:** 2026-08-21 (stable HA patterns; no external dependencies)
