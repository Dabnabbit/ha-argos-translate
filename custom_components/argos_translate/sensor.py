"""Sensor platform for Argos Translate."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ArgosTranslateConfigEntry
from .const import DOMAIN
from .coordinator import ArgosCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ArgosTranslateConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([ArgosLanguageCountSensor(coordinator, entry)])


class ArgosLanguageCountSensor(CoordinatorEntity[ArgosCoordinator], SensorEntity):
    """Sensor showing the number of installed languages on LibreTranslate."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:translate"
    _attr_name = "Language Count"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "languages"

    def __init__(
        self,
        coordinator: ArgosCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the language count sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_language_count"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry.title,
            manufacturer="LibreTranslate",
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of installed languages."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("language_count")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return language list as extra attributes."""
        if self.coordinator.data is None:
            return None
        languages = self.coordinator.data.get("languages", [])
        return {
            "languages": [lang["name"] for lang in languages],
            "language_codes": [lang["code"] for lang in languages],
        }
