# Phase 3: Polish + Validation - Research

**Researched:** 2026-02-21
**Domain:** HA custom component testing, CI validation (hassfest + hacs/action), README documentation
**Confidence:** HIGH

## Summary

Phase 3 is a validation and documentation phase — no new features. It has three parallel workstreams: (1) fix stale template tests and add new test files for LibreTranslate-specific logic, (2) ensure CI passes (hassfest and hacs/action), and (3) write a comprehensive README.

The existing tests contain hard template artifacts — `TemplateCoordinator`, `ApiClient.async_get_data` — that must be replaced with actual class names (`ArgosCoordinator`, `ArgosTranslateApiClient.async_get_languages`). The config flow tests use port 8080 (the old template default) instead of 5000, and they are missing coverage for `InvalidAuth`, `NoLanguages`, and the `CONF_NAME` field added in Phase 1. New test files for services and binary_sensor are entirely absent.

CI is already wired correctly — `validate.yml` runs both `hassfest` and `hacs/action` on push to main. The `hacs/action` already uses `ignore: brands` which skips the only check this integration cannot yet satisfy. The manifest.json is complete and well-formed. The release workflow is correct for HACS distribution. No CI config changes are needed.

**Primary recommendation:** Fix the broken template tests first (they will fail immediately), then add new test files covering services and binary_sensor, then write the README. Run each test file incrementally to confirm they pass with the `pytest-homeassistant-custom-component` framework already configured in `pyproject.toml`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**README content:**
- Comprehensive documentation: installation, prerequisites, config flow walkthrough, card usage, service call examples, automation examples
- Include brief LibreTranslate setup section: docker-compose snippet + link to LibreTranslate docs (not a full setup guide)
- Include 2-3 automation examples showing practical use cases (e.g., translate notification text, template sensor, etc.)
- Describe the UI visually (what users will see) but no actual screenshots — text descriptions of card and config flow
- Document service call interface with YAML examples for Developer Tools

**Test coverage:**
- Plain pytest with unittest.mock (match existing test approach, no pytest-homeassistant-custom-component NEW patterns — it is already installed)
- Update existing tests: conftest.py, test_config_flow.py, test_coordinator.py for LibreTranslate-specific logic
- Add new test files: test_services.py (translate service), test_sensor.py (sensor states and attributes)
- Config flow tests: happy path, connection refused, invalid API key, empty language list
- Coordinator tests: successful poll, failed poll, data shape validation
- Service tests: successful translation, invalid language pair, server error/timeout
- Sensor tests: status sensor online/error states, language count with attributes
- No frontend JS tests — manual testing covers the card at v1

**Quality gate:**
- CI must pass: hassfest and hacs/action validation
- All pytest tests must pass
- Real device testing: install on actual HA instance, test against running LibreTranslate server
- Validation covers: config flow, sensor creation, service call from Developer Tools, card rendering and interaction

### Claude's Discretion
- Whether to create a separate TESTING.md checklist or keep validation steps in the plan
- Whether release.yml workflow needs verification or is fine from template
- Exact test fixture structure and mock patterns
- Test file organization

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DIST-01 | HACS-compatible (hacs.json, manifest.json, correct file structure) | Already satisfied by template. hacs.json has correct `name`, `homeassistant`, `render_readme` fields. manifest.json has all required fields. File structure is correct. hacs/action CI is already wired and uses `ignore: brands`. No changes needed. |
| DIST-03 | CI passes hassfest and hacs/action validation | validate.yml already wired for both. Hassfest runs via `home-assistant/actions/hassfest`. hacs/action runs via `hacs/action@22.5.0`. Both trigger on push to main. The `ignore: brands` in validate.yml handles the only check we can't satisfy pre-HACS-submission. No workflow changes needed — just make sure the code itself passes. |
</phase_requirements>

## Standard Stack

### Core (Already in Use)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest-homeassistant-custom-component | latest (pyproject.toml) | HA test fixtures: `hass`, `MockConfigEntry`, `enable_custom_integrations` | The only supported way to run HA integration tests in custom components |
| unittest.mock | stdlib | `AsyncMock`, `patch` | Standard Python mocking, already used in all existing tests |
| pytest | latest | Test runner | Standard |
| pytest-asyncio | latest (bundled via phcc) | `asyncio_mode = auto` already set in pyproject.toml | Required for async test functions |

### No Additional Libraries Needed

The test stack is already fully configured. `pyproject.toml` already has `asyncio_mode = "auto"` and `testpaths = ["tests"]`. No new packages are required.

## Architecture Patterns

### Pattern 1: Existing Test Structure (What to Match)

The existing tests use `pytest-homeassistant-custom-component` fixtures directly (the `hass` fixture is injected automatically) combined with `unittest.mock.patch`. All tests are `async def` functions.

**Config flow test pattern (from existing test_config_flow.py):**
```python
from unittest.mock import AsyncMock, patch
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.argos_translate.config_flow import CannotConnect
from custom_components.argos_translate.const import DOMAIN

async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.1.100", CONF_PORT: 5000, CONF_API_KEY: ""},
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
```

### Pattern 2: Coordinator Test Pattern

The existing `test_coordinator.py` patches at the method level. The CRITICAL fix: replace `TemplateCoordinator` with `ArgosCoordinator` and `ApiClient.async_get_data` with `ArgosTranslateApiClient.async_get_languages`.

**Correct coordinator test pattern:**
```python
from custom_components.argos_translate.coordinator import ArgosCoordinator
from custom_components.argos_translate.api import CannotConnectError

async def test_coordinator_update(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 5000, CONF_API_KEY: ""},
    )
    entry.add_to_hass(hass)

    mock_languages = [
        {"code": "en", "name": "English", "targets": ["es", "fr"]},
        {"code": "es", "name": "Spanish", "targets": ["en"]},
    ]

    with patch(
        "custom_components.argos_translate.coordinator.ArgosTranslateApiClient.async_get_languages",
        new_callable=AsyncMock,
        return_value=mock_languages,
    ):
        coordinator = ArgosCoordinator(hass, entry)
        await coordinator.async_refresh()

    assert coordinator.data == {
        "languages": mock_languages,
        "language_count": 2,
    }
```

### Pattern 3: Service Test Pattern

Services are tested by calling `hass.services.async_call` with `return_response=True` (required for `SupportsResponse.ONLY` services). The integration must be set up first via `async_setup_component` or by manually adding a config entry with runtime_data.

The cleanest approach for service tests is to patch the coordinator and set up `entry.runtime_data` manually, avoiding full HA startup:

```python
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
import pytest

async def test_translate_service_success(hass: HomeAssistant) -> None:
    """Test successful translation via service call."""
    # Set up a mock coordinator in runtime_data
    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "languages": [{"code": "en", "name": "English", "targets": ["es"]}],
        "language_count": 1,
    }
    mock_coordinator.async_translate = AsyncMock(return_value="Hola mundo")

    mock_runtime_data = MagicMock()
    mock_runtime_data.coordinator = mock_coordinator

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 5000},
    )
    entry.add_to_hass(hass)
    entry.runtime_data = mock_runtime_data

    # Register the service (async_setup does this)
    from custom_components.argos_translate.services import async_register_services
    async_register_services(hass)

    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "Hello world", "source": "en", "target": "es"},
        blocking=True,
        return_response=True,
    )

    assert result == {"translated_text": "Hola mundo"}
```

**Testing ServiceValidationError:**
```python
async def test_translate_invalid_source(hass: HomeAssistant) -> None:
    # ... setup same as above ...
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "xx", "target": "es"},
            blocking=True,
            return_response=True,
        )
```

### Pattern 4: Sensor/Binary Sensor Test Pattern

Test sensors by setting up a coordinator with mock data and then checking `hass.states`:

```python
from homeassistant.setup import async_setup_component
from custom_components.argos_translate.sensor import ArgosLanguageCountSensor
from custom_components.argos_translate.coordinator import ArgosCoordinator

async def test_language_count_sensor(hass: HomeAssistant) -> None:
    mock_languages = [
        {"code": "en", "name": "English", "targets": ["es"]},
        {"code": "es", "name": "Spanish", "targets": ["en"]},
    ]

    with patch(
        "custom_components.argos_translate.coordinator.ArgosTranslateApiClient.async_get_languages",
        new_callable=AsyncMock,
        return_value=mock_languages,
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_HOST: "192.168.1.100", CONF_PORT: 5000, CONF_API_KEY: ""},
            title="Test LibreTranslate",
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Language count sensor is disabled by default, check via coordinator instead
    # Or enable it first, then check state
    state = hass.states.get("sensor.test_libretranslate_language_count")
    # Note: sensor is disabled by default (_attr_entity_registry_enabled_default = False)
    # Must test the entity directly or enable it before checking hass.states
```

**Key gotcha:** `ArgosLanguageCountSensor` has `_attr_entity_registry_enabled_default = False`. Testing via `hass.states` will show nothing because disabled entities are not in the state machine. Test the entity class directly or mock-enable it.

**Alternative: test sensor methods directly:**
```python
async def test_language_count_sensor_value(hass: HomeAssistant) -> None:
    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "languages": [
            {"code": "en", "name": "English", "targets": ["es"]},
        ],
        "language_count": 1,
    }
    entry = MockConfigEntry(domain=DOMAIN, data={...}, entry_id="test123")
    sensor = ArgosLanguageCountSensor(mock_coordinator, entry)
    assert sensor.native_value == 1
    attrs = sensor.extra_state_attributes
    assert attrs["language_codes"] == ["en"]
```

### Anti-Patterns to Avoid

- **Using template class names:** `TemplateCoordinator` and `ApiClient.async_get_data` are gone. Using them causes `ImportError`.
- **Port 8080 in tests:** Real default is 5000. Using 8080 won't cause failures but is misleading and could mask unique_id bugs.
- **Testing disabled sensors via hass.states:** Will always return None. Test entity methods directly.
- **Missing `CONF_NAME` in config flow tests:** The new config flow has `vol.Required(CONF_NAME)`. Tests that omit it will fail schema validation.
- **Calling SupportsResponse.ONLY service without return_response=True:** HA raises `ServiceValidationError` with message about requiring `return_response=True`. Must always pass `return_response=True` when testing the translate service.
- **Patching at wrong path:** Always patch at the import location, not the definition location. The coordinator imports `ArgosTranslateApiClient` from `.api`, so patch at `custom_components.argos_translate.coordinator.ArgosTranslateApiClient.async_get_languages`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HA test instance setup | Custom HA startup code | `hass` fixture from pytest-homeassistant-custom-component | Handles all setup/teardown correctly |
| Config entry mocking | Custom entry objects | `MockConfigEntry` from `pytest_homeassistant_custom_component.common` | Handles HA internals |
| Service error assertion | Try/except in test | `pytest.raises(ServiceValidationError)` | Standard pytest pattern |
| Async mock creation | `Mock(return_value=coroutine(...))` | `AsyncMock` from `unittest.mock` | stdlib, correct for async |

## Common Pitfalls

### Pitfall 1: Stale Template References in Existing Tests

**What goes wrong:** `test_coordinator.py` imports `TemplateCoordinator` and patches `ApiClient.async_get_data` — both are template artifacts that no longer exist. The test will fail with `ImportError` immediately.

**Why it happens:** Template tests were never updated after Phase 1 customization.

**How to avoid:** Fix these files first before running any tests. Replace:
- `TemplateCoordinator` → `ArgosCoordinator`
- `ApiClient.async_get_data` → `ArgosTranslateApiClient.async_get_languages`
- Port `8080` → `5000`
- `mock_data = {"sensor_value": 42, "status": "ok"}` → actual shape `{"languages": [...], "language_count": N}`

**Warning signs:** `ImportError: cannot import name 'TemplateCoordinator'` on first test run.

### Pitfall 2: Config Flow Tests Missing CONF_NAME

**What goes wrong:** The existing `test_form` passes `{CONF_HOST, CONF_PORT, CONF_API_KEY}` but `STEP_USER_DATA_SCHEMA` now has `vol.Required(CONF_NAME)`. Voluptuous will raise a validation error.

**Why it happens:** Phase 1 added the name field; config flow tests were not updated.

**How to avoid:** Add `CONF_NAME: "My LibreTranslate"` to every config flow test's `user_input` dict.

### Pitfall 3: Config Flow Tests Missing Coverage for New Error States

**What goes wrong:** Phase 1 added `InvalidAuth` and `NoLanguages` errors. The existing tests only cover `CannotConnect`. hassfest and code review would flag untested error paths.

**How to avoid:** Add tests for `InvalidAuth` → `errors["base"] == "invalid_auth"` and `NoLanguages` → `errors["base"] == "no_languages"`.

### Pitfall 4: Testing the Translate Service Setup

**What goes wrong:** The translate service is registered in `async_setup` (domain-level), not `async_setup_entry`. If you call `hass.config_entries.async_setup(entry.entry_id)` without first calling `async_setup`, the service won't be registered.

**Why it happens:** `async_setup` → registers service, `async_setup_entry` → creates coordinator. They're separate.

**How to avoid:** Either (a) call `async_register_services(hass)` directly in the test before calling the service, or (b) use `async_setup_component(hass, DOMAIN, {})` to trigger full setup. Option (a) is simpler for isolated service tests.

### Pitfall 5: HACS 'images' Validation Check

**What goes wrong:** hacs/action validates that the README (information file) has images. Our README has none, and we've decided not to add screenshots.

**Why it happens:** HACS considers images part of good documentation quality.

**How to avoid:** The `validate.yml` already does NOT ignore `images`. Check if this causes CI failure. If it does, add `ignore: brands images` to the `with:` block. **Verify this against actual CI run** — if CI is currently green without images, it passes as-is.

### Pitfall 6: Coordinator Options Flow Test Data Shape

**What goes wrong:** `test_options_flow` passes `{CONF_HOST, CONF_PORT, CONF_API_KEY}` to options flow but options flow validates connection. If the connection mock isn't patched, it will try to make a real network call.

**How to avoid:** The existing test doesn't patch `_async_validate_connection` for options flow — check if this works (it may because options flow patches differently) or add the patch.

### Pitfall 7: Disabled Sensor Not in State Machine

**What goes wrong:** `ArgosLanguageCountSensor` has `_attr_entity_registry_enabled_default = False`. After full integration setup, `hass.states.get("sensor.X_language_count")` returns `None`.

**How to avoid:** Test sensor `native_value` and `extra_state_attributes` by instantiating the entity class directly with a mock coordinator, rather than going through the state machine.

## Code Examples

### conftest.py — Updated Fixture

The current `conftest.py` provides `mock_setup_entry`. No changes needed to the existing fixture, but consider adding a `mock_config_entry` fixture for reuse:

```python
# Source: existing tests/conftest.py pattern
@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a standard MockConfigEntry for tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test LibreTranslate",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_API_KEY: "",
        },
    )

MOCK_LANGUAGES = [
    {"code": "en", "name": "English", "targets": ["es", "fr"]},
    {"code": "es", "name": "Spanish", "targets": ["en"]},
    {"code": "fr", "name": "French", "targets": ["en", "es"]},
]
```

### test_coordinator.py — Corrected Patterns

```python
# Correct: use actual class names
from custom_components.argos_translate.coordinator import ArgosCoordinator
from custom_components.argos_translate.api import CannotConnectError

# Correct patch target
with patch(
    "custom_components.argos_translate.coordinator.ArgosTranslateApiClient.async_get_languages",
    new_callable=AsyncMock,
    return_value=mock_languages,
):
    coordinator = ArgosCoordinator(hass, entry)
    await coordinator.async_refresh()

# Correct data shape assertion
assert coordinator.data["language_count"] == 2
assert len(coordinator.data["languages"]) == 2
```

### test_services.py — New File Pattern

```python
"""Tests for Argos Translate translate service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from custom_components.argos_translate.const import DOMAIN
from custom_components.argos_translate.services import async_register_services

MOCK_LANGUAGES = [{"code": "en", "name": "English", "targets": ["es"]}]

async def _setup_service(hass, mock_translated="Hello"):
    """Set up service with a mock coordinator entry."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"languages": MOCK_LANGUAGES, "language_count": 1}
    mock_coordinator.async_translate = AsyncMock(return_value=mock_translated)

    mock_data = MagicMock()
    mock_data.coordinator = mock_coordinator

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "localhost", CONF_PORT: 5000})
    entry.add_to_hass(hass)
    entry.runtime_data = mock_data
    async_register_services(hass)
    return entry


async def test_translate_success(hass: HomeAssistant) -> None:
    await _setup_service(hass, mock_translated="Hola")
    result = await hass.services.async_call(
        DOMAIN, "translate",
        {"text": "Hello", "source": "en", "target": "es"},
        blocking=True, return_response=True,
    )
    assert result == {"translated_text": "Hola"}


async def test_translate_invalid_source(hass: HomeAssistant) -> None:
    await _setup_service(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "translate",
            {"text": "Hello", "source": "xx", "target": "es"},
            blocking=True, return_response=True,
        )


async def test_translate_invalid_target(hass: HomeAssistant) -> None:
    await _setup_service(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "translate",
            {"text": "Hello", "source": "en", "target": "xx"},
            blocking=True, return_response=True,
        )


async def test_translate_api_error(hass: HomeAssistant) -> None:
    from homeassistant.exceptions import HomeAssistantError
    from custom_components.argos_translate.api import CannotConnectError
    entry = await _setup_service(hass)
    entry.runtime_data.coordinator.async_translate = AsyncMock(
        side_effect=CannotConnectError("timeout")
    )
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN, "translate",
            {"text": "Hello", "source": "en", "target": "es"},
            blocking=True, return_response=True,
        )
```

### test_sensor.py — New File Pattern (Direct Entity Test)

```python
"""Tests for Argos Translate sensor entities."""
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.argos_translate.const import DOMAIN
from custom_components.argos_translate.sensor import ArgosLanguageCountSensor
from custom_components.argos_translate.binary_sensor import ArgosStatusSensor

MOCK_LANGUAGES = [
    {"code": "en", "name": "English", "targets": ["es"]},
    {"code": "es", "name": "Spanish", "targets": ["en"]},
]


def make_coordinator(languages=None, success=True):
    """Return a mock coordinator with controlled data."""
    coordinator = MagicMock()
    coordinator.data = (
        {"languages": languages or MOCK_LANGUAGES, "language_count": len(languages or MOCK_LANGUAGES)}
        if success else None
    )
    coordinator.last_update_success = success
    return coordinator


async def test_language_count_value(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="test_lc")
    coordinator = make_coordinator()
    sensor = ArgosLanguageCountSensor(coordinator, entry)
    assert sensor.native_value == 2


async def test_language_count_attributes(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="test_lc2")
    coordinator = make_coordinator()
    sensor = ArgosLanguageCountSensor(coordinator, entry)
    attrs = sensor.extra_state_attributes
    assert "en" in attrs["language_codes"]
    assert "language_targets" in attrs


async def test_language_count_none_when_no_data(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="test_lc3")
    coordinator = make_coordinator(success=False)
    sensor = ArgosLanguageCountSensor(coordinator, entry)
    assert sensor.native_value is None
    assert sensor.extra_state_attributes is None


async def test_status_sensor_online(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="test_ss1")
    coordinator = make_coordinator(success=True)
    sensor = ArgosStatusSensor(coordinator, entry)
    assert sensor.is_on is True


async def test_status_sensor_offline(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="test_ss2")
    coordinator = make_coordinator(success=False)
    sensor = ArgosStatusSensor(coordinator, entry)
    assert sensor.is_on is False
```

## CI and Validation Details

### Hassfest

**Confidence: HIGH** — based on official HA docs and current manifest.json state.

Hassfest validates:
- `manifest.json` fields: all required fields present (`domain`, `name`, `codeowners`, `dependencies`, `documentation`, `integration_type`, `iot_class`, `requirements`, `version`)
- `strings.json` / `translations/en.json`: checked for consistency with each other (strings.json takes priority for custom integrations when present)
- `services.yaml`: field definitions must be valid
- Python imports: no broken imports in integration files

**Current state:** The manifest.json is complete and correct. `strings.json` and `translations/en.json` are in sync (identical content). `services.yaml` is valid. No hassfest issues are expected — this should pass as-is on the current code.

**Risk area:** If Phase 1 or 2 introduced any import errors or broke the manifest, hassfest will catch it. Run CI to confirm.

### HACS Action (hacs/action)

**Confidence: HIGH** — based on official HACS action docs.

Eight checks run; `validate.yml` ignores `brands` only. The other 7 checks:
- **archived**: repo is not archived — passes
- **description**: GitHub repo needs a description set — **must verify** this is set on GitHub
- **hacsjson**: hacs.json exists with correct structure — passes (has `name`, `homeassistant`, `render_readme`)
- **images**: README must have images — **potential failure point** (no images in README)
- **information**: repo has an information file (README.md) — passes
- **issues**: GitHub issues must be enabled — **must verify** this is enabled on repo settings
- **topics**: repo must have GitHub topics set — **must verify** at least one topic is set

**Action for `images` check:** The current `validate.yml` does NOT ignore `images`. Since no screenshots are being added (user decision), if hacs/action fails on `images`, add `images` to the ignore list: `ignore: brands images`. This is the expected approach for v1 pre-HACS-submission.

### Release Workflow

`release.yml` is correct as-is. It:
- Triggers on published GitHub release
- Adjusts version in `manifest.json` from tag (strips `v` prefix)
- Zips `custom_components/argos_translate/` into `release.zip`
- Uploads as release asset

No changes needed. Claude's discretion: treat it as verified and note it in the plan.

## README Structure (Per Locked Decisions)

The current README.md is a stub. Full replacement is needed. Required sections:

```
# Argos Translate

[Badges: HACS, HA version]

Brief description: local privacy-respecting translation via self-hosted LibreTranslate.

## Prerequisites
- Home Assistant 2025.7+
- LibreTranslate server (self-hosted)
- [LibreTranslate docker-compose snippet]
- [Link to LibreTranslate docs]

## Installation
### Via HACS (Recommended)
[Steps]
### Manual Installation
[Steps]

## Configuration
### Adding the Integration
[Config flow walkthrough: name, host, port, SSL toggle, optional API key]
[What each field means]
[Error states: connection refused, invalid API key, no languages installed]

## The Translation Card
### Adding the Card
[How to add custom:argos-translate-card to dashboard]
[Visual description of what users will see]
### Card Configuration
[entity picker, title, default source/target language]
### Using the Card
[Text input area, language dropdowns, swap button, translate button, status indicator]

## Service: argos_translate.translate
[Developer Tools usage with YAML examples]
[Fields: text, source, target]
[Response format: translated_text]

## Automation Examples
[Example 1: translate notification text]
[Example 2: template sensor for translated value]
[Example 3: translate input_text entity on button press]

## Sensors
[Status binary sensor: connectivity device class, online/offline]
[Language count sensor: disabled by default, enable to see count + language list]

## Troubleshooting
[Common issues: connection refused, no languages, card not showing]

## License
MIT
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Template class names (`TemplateCoordinator`, `ApiClient`) | Actual class names (`ArgosCoordinator`, `ArgosTranslateApiClient`) | Phase 1 completion | Tests will `ImportError` if not updated |
| Port 8080 | Port 5000 (LibreTranslate default) | Phase 1 | Tests using 8080 are misleading |
| Single sensor | Binary sensor (status) + sensor (language count, disabled by default) | Phase 1 | test_sensor.py must cover both; binary sensor is in binary_sensor.py |
| No service | translate service (SupportsResponse.ONLY) | Phase 2 | test_services.py is a new file |
| Stub README | Comprehensive README | Phase 3 | Full rewrite |

## Open Questions

1. **HACS `images` check — will it fail CI?**
   - What we know: hacs/action checks for images in the README. No images will be added (user decision). The current `validate.yml` does not ignore `images`.
   - What's unclear: Whether hacs/action currently passes without images (some repos pass without them, HACS may have made this non-fatal recently).
   - Recommendation: Push to CI and observe. If it fails, add `images` to the ignore list in validate.yml.

2. **GitHub repo metadata (description, topics, issues)**
   - What we know: hacs/action checks description, topics, and issues are enabled.
   - What's unclear: Current state of the GitHub repo settings.
   - Recommendation: Verify and set a description and at least one topic (e.g., `home-assistant`, `hacs`, `libretranslate`) on GitHub before considering CI complete.

3. **Options flow test connection validation**
   - What we know: `test_options_flow` passes without patching `_async_validate_connection`. This means options flow may be calling the real validator.
   - What's unclear: Does the existing options flow test actually pass, or does it silently skip validation?
   - Recommendation: Add `_async_validate_connection` patch to options flow tests to be safe and explicit.

## Sources

### Primary (HIGH confidence)
- Official HACS Action docs (https://www.hacs.xyz/docs/publish/action/) — complete list of 8 validation checks and ignore options
- HACS Integration docs (https://www.hacs.xyz/docs/publish/integration/) — required manifest.json fields and repo structure
- HA Integration Manifest docs (https://developers.home-assistant.io/docs/creating_integration_manifest/) — all manifest fields and validation rules
- Direct codebase inspection — all existing test files, integration source files, CI workflows

### Secondary (MEDIUM confidence)
- HA Developer Docs testing page (https://developers.home-assistant.io/docs/development_testing/) — service testing patterns
- HA conversation component test file (https://github.com/home-assistant/core/blob/dev/tests/components/conversation/test_init.py) — `return_response=True` pattern confirmed
- WebSearch results confirming `hass.services.async_call(return_response=True, blocking=True)` for SupportsResponse.ONLY services

### Tertiary (LOW confidence)
- None — all critical findings verified against code or official docs

## Metadata

**Confidence breakdown:**
- Existing test issues (template names, missing CONF_NAME): HIGH — confirmed by direct code inspection
- Service test pattern (return_response=True): HIGH — confirmed by HA conversation tests and official docs
- Sensor test pattern (test disabled entity directly): HIGH — confirmed by sensor code inspection
- hassfest validation: HIGH — manifest/strings confirmed valid by inspection
- HACS action checks: HIGH — confirmed by official hacs.xyz docs
- HACS images check outcome: LOW — depends on current hacs/action behavior, must verify by running CI

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable domain — HA test patterns and HACS requirements change slowly)
