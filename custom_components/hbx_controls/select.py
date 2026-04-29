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
            
            # HVAC Mode Priority — ECO/HHB-only concept (writes the ``prior``
            # field).  THM/ZON parameter dicts also expose ``hvac_mode`` but
            # mean a different thing (the THM's own changeover mode), and
            # routing those through ``set_hvac_mode_priority`` writes a field
            # the THM ignores.  Whitelist ECO explicitly: the coordinator's
            # ECO extractor is also the fallback for unknown device types, so
            # a blacklist would re-leak this entity onto any new HBX device
            # class that happens to expose ``hvac_mode`` for a different
            # purpose.
            device_type = (device_parameters.get("device_type") or "").upper()
            if "hvac_mode" in device_parameters and device_type == "ECO":
                entities.append(
                    HvacModePrioritySelect(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )

            # THM humidity mode select (writes ``useHum`` field).
            if "humidity_mode" in device_parameters and building_id:
                entities.append(
                    ThmHumidityModeSelect(
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


class ThmHumidityModeSelect(CoordinatorEntity, SelectEntity):
    """
    Select entity backing the THM ``useHum`` field (humidity mode).

    Three options:

    * ``off`` (``useHum`` = 0): humidity control is disabled.
    * ``on`` (``useHum`` = 1): runs continuously toward the humidity target.
    * ``auto`` (``useHum`` = 2): THM picks based on conditions.

    Field mapping confirmed via paired before/after THM-0600 dumps on
    2026-04-28.
    """

    _attr_options = ["off", "on", "auto"]
    _attr_icon = "mdi:water-percent"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the THM humidity mode select."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        self._pending: str | None = None

        self._attr_unique_id = f"{device_id}_thm_humidity_mode"
        self._attr_name = f"{device.get('name', device_id)} Humidity Mode"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    def _params(self) -> dict | None:
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        return device.get("parameters") or {}

    @property
    def available(self) -> bool:
        """Available when coordinator data carries a humidity_mode value."""
        if not self.coordinator.last_update_success:
            return False
        params = self._params()
        return params is not None and "humidity_mode" in params

    @property
    def current_option(self) -> str | None:
        """Return the currently selected humidity mode."""
        params = self._params()
        actual = params.get("humidity_mode") if params else None
        if self._pending is not None:
            if actual is not None and actual == self._pending:
                self._pending = None
                return actual
            return self._pending
        return actual

    async def async_select_option(self, option: str) -> None:
        """Write the new humidity mode to the THM."""
        from pysensorlinx.sensorlinx import ThmDevice

        helper = ThmDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        try:
            await helper.set_humidity_mode(option)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error(
                "Failed to set THM humidity mode on %s: %s",
                self._device_id, exc,
            )
            return
        self._pending = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
