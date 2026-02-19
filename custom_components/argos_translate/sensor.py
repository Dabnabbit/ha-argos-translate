"""Sensor platform for Argos Translate."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ArgosTranslateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: ArgosTranslateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            ArgosStatusSensor(coordinator, entry),
            ArgosLanguageCountSensor(coordinator, entry),
        ]
    )


class ArgosStatusSensor(CoordinatorEntity[ArgosTranslateCoordinator], SensorEntity):
    """Sensor showing the translation service status."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:translate"

    def __init__(self, coordinator: ArgosTranslateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str | None:
        """Return the status."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("status")


class ArgosLanguageCountSensor(CoordinatorEntity[ArgosTranslateCoordinator], SensorEntity):
    """Sensor showing the number of available languages."""

    _attr_has_entity_name = True
    _attr_name = "Available Languages"
    _attr_icon = "mdi:earth"

    def __init__(self, coordinator: ArgosTranslateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_language_count"

    @property
    def native_value(self) -> int | None:
        """Return the language count."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("language_count")
