# Phase 3: Polish + Validation - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the integration ready for HACS distribution: update tests for LibreTranslate-specific logic, ensure CI passes (hassfest + hacs/action), and write comprehensive README documentation. No new features — this phase validates and documents what Phases 1 and 2 built.

</domain>

<decisions>
## Implementation Decisions

### README content
- Comprehensive documentation: installation, prerequisites, config flow walkthrough, card usage, service call examples, automation examples
- Include brief LibreTranslate setup section: docker-compose snippet + link to LibreTranslate docs (not a full setup guide)
- Include 2-3 automation examples showing practical use cases (e.g., translate notification text, template sensor, etc.)
- Describe the UI visually (what users will see) but no actual screenshots — text descriptions of card and config flow
- Document service call interface with YAML examples for Developer Tools

### Test coverage
- Plain pytest with unittest.mock (match existing test approach, no pytest-homeassistant-custom-component)
- Update existing tests: conftest.py, test_config_flow.py, test_coordinator.py for LibreTranslate-specific logic
- Add new test files: test_services.py (translate service), test_sensor.py (sensor states and attributes)
- Config flow tests: happy path, connection refused, invalid API key, empty language list
- Coordinator tests: successful poll, failed poll, data shape validation
- Service tests: successful translation, invalid language pair, server error/timeout
- Sensor tests: status sensor online/error states, language count with attributes
- No frontend JS tests — manual testing covers the card at v1

### Quality gate
- CI must pass: hassfest and hacs/action validation
- All pytest tests must pass
- Real device testing: install on actual HA instance, test against running LibreTranslate server (user has one available)
- Validation covers: config flow, sensor creation, service call from Developer Tools, card rendering and interaction

### Claude's Discretion
- Whether to create a separate TESTING.md checklist or keep validation steps in the plan
- Whether release.yml workflow needs verification or is fine from template
- Exact test fixture structure and mock patterns
- Test file organization

</decisions>

<specifics>
## Specific Ideas

- User wants the integration to feel polished enough for real HACS distribution, not just "works in dev"
- Real-device testing is part of the quality bar — CI green alone is not sufficient
- LibreTranslate server is already running and available for testing

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-polish-validation*
*Context gathered: 2026-02-21*
