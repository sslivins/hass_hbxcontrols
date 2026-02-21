"""Platform for select integration."""
from __future__ import annotations

import logging
from typing import Any

from pysensorlinx.sensorlinx import SensorlinxDevice

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HBXControlsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator: HBXControlsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up select platform")
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        
        for device_id, device in devices.items():
            device_parameters = device.get("parameters", {})
            building_id = device.get("building_id")
            
            # HVAC Mode Priority
            if "hvac_mode" in device_parameters:
                entities.append(
                    HvacModePrioritySelect(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
    
    _LOGGER.debug("Adding %d select entities", len(entities))
    async_add_entities(entities)


class HvacModePrioritySelect(CoordinatorEntity, SelectEntity):
    """HVAC Mode Priority select entity.
    
    Sets the HVAC mode priority for the device.
    Options: heat, cool, auto.
    """

    _attr_options = ["heat", "cool", "auto"]
    _attr_icon = "mdi:hvac"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "hvac_mode_priority"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_hvac_mode_priority"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return parameters.get("hvac_mode")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "hvac_mode" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_select_option(self, option: str) -> None:
        """Set the HVAC mode priority."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_hvac_mode_priority(option)
        await self.coordinator.async_request_refresh()
