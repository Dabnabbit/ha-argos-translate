"""Tests for Argos Translate sensor and binary sensor entities."""

from unittest.mock import MagicMock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argos_translate.binary_sensor import ArgosStatusSensor
from custom_components.argos_translate.const import DOMAIN
from custom_components.argos_translate.sensor import ArgosLanguageCountSensor

MOCK_LANGUAGES = [
    {"code": "en", "name": "English", "targets": ["es"]},
    {"code": "es", "name": "Spanish", "targets": ["en"]},
]


def _make_coordinator(languages=None, success=True):
    """Create a mock coordinator with the given language data."""
    if languages is None:
        languages = MOCK_LANGUAGES

    coordinator = MagicMock()
    coordinator.last_update_success = success

    if success:
        coordinator.data = {
            "languages": languages,
            "language_count": len(languages),
        }
    else:
        coordinator.data = None

    return coordinator


def _make_entry(entry_id="test_entry_123"):
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        entry_id=entry_id,
    )


# --- ArgosLanguageCountSensor tests ---


def test_language_count_value():
    """Test language count sensor returns correct count."""
    coordinator = _make_coordinator()
    entry = _make_entry()
    sensor = ArgosLanguageCountSensor(coordinator, entry)

    assert sensor.native_value == 2


def test_language_count_attributes():
    """Test language count sensor returns language details as attributes."""
    coordinator = _make_coordinator()
    entry = _make_entry()
    sensor = ArgosLanguageCountSensor(coordinator, entry)

    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert attrs["languages"] == ["English", "Spanish"]
    assert attrs["language_codes"] == ["en", "es"]
    assert attrs["language_targets"] == {"en": ["es"], "es": ["en"]}


def test_language_count_no_data():
    """Test language count sensor handles missing data gracefully."""
    coordinator = _make_coordinator(success=False)
    entry = _make_entry()
    sensor = ArgosLanguageCountSensor(coordinator, entry)

    assert sensor.native_value is None
    assert sensor.extra_state_attributes is None


def test_language_count_unique_id():
    """Test language count sensor unique_id format."""
    coordinator = _make_coordinator()
    entry = _make_entry(entry_id="test_entry_123")
    sensor = ArgosLanguageCountSensor(coordinator, entry)

    assert sensor.unique_id == "test_entry_123_language_count"


def test_language_count_disabled_by_default():
    """Test language count sensor is disabled by default."""
    coordinator = _make_coordinator()
    entry = _make_entry()
    sensor = ArgosLanguageCountSensor(coordinator, entry)

    assert sensor._attr_entity_registry_enabled_default is False


# --- ArgosStatusSensor tests ---


def test_status_sensor_online():
    """Test status binary sensor shows on when server is reachable."""
    coordinator = _make_coordinator(success=True)
    entry = _make_entry()
    sensor = ArgosStatusSensor(coordinator, entry)

    assert sensor.is_on is True


def test_status_sensor_offline():
    """Test status binary sensor shows off when server is unreachable."""
    coordinator = _make_coordinator(success=False)
    entry = _make_entry()
    sensor = ArgosStatusSensor(coordinator, entry)

    assert sensor.is_on is False


def test_status_sensor_unique_id():
    """Test status binary sensor unique_id format."""
    coordinator = _make_coordinator()
    entry = _make_entry(entry_id="test_entry_123")
    sensor = ArgosStatusSensor(coordinator, entry)

    assert sensor.unique_id == "test_entry_123_status"


def test_status_sensor_device_class():
    """Test status binary sensor has connectivity device class."""
    coordinator = _make_coordinator()
    entry = _make_entry()
    sensor = ArgosStatusSensor(coordinator, entry)

    assert sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY
