"""Binary sensor platform for Argos Translate."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ArgosTranslateConfigEntry
from .const import DOMAIN
from .coordinator import ArgosCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ArgosTranslateConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([ArgosStatusSensor(coordinator, entry)])


class ArgosStatusSensor(CoordinatorEntity[ArgosCoordinator], BinarySensorEntity):
    """Binary sensor showing LibreTranslate server connectivity."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Status"
    _attr_icon = "mdi:server"

    def __init__(
        self,
        coordinator: ArgosCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry.title,
            manufacturer="LibreTranslate",
        )

    @property
    def is_on(self) -> bool:
        """Return True if the server is reachable."""
        return self.coordinator.last_update_success
