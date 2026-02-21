# Phase 4: Options Flow Fix - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can reconfigure host, port, API key, and SSL toggle from the integration's options without removing and re-adding. Changes trigger a coordinator reload so they take effect immediately (no HA restart required). This phase covers the options flow form, connection validation, and reload behavior only.

</domain>

<decisions>
## Implementation Decisions

### Connection validation
- Test connection before saving (same as initial config flow)
- Reuse the existing `_test_connection` helper from the config flow — keep code DRY and behavior consistent
- Only commit the config change if the connection test passes
- Invalid settings show an error in the form; user can correct and retry

### Form design
- Single page with all four fields: host, port, SSL toggle, API key
- All fields pre-filled with current saved values (including API key)
- No multi-step flow — matches the simplicity of initial setup

### Reload behavior
- Auto-reload after saving: call `async_reload` so the integration reconnects with new settings immediately
- Standard HA options flow UX: form closes, integration reloads in background, HA shows normal success/error state
- Coordinator refetches languages from the new server immediately after reload — card updates right away
- If the new server has different languages installed, reset any selected source/target language that's no longer available

### Claude's Discretion
- Error message granularity (reuse existing errors vs. more specific connection/SSL/auth errors)
- Whether to auto-change port when SSL is toggled (e.g., 5000 vs 443)
- Whether to include integration name in the options flow or keep it connection-settings-only
- Handling of post-validation reload failures (save anyway vs. rollback)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard HA integration patterns. The existing config flow already validates connections, so the options flow should feel like a natural extension of the same setup experience.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-options-flow-fix*
*Context gathered: 2026-02-21*
