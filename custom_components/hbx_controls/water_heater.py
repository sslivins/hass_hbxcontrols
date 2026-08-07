"""Platform for water_heater integration (DHW — Domestic Hot Water)."""
from __future__ import annotations

import logging
from typing import Any

from pysensorlinx.sensorlinx import SensorlinxDevice, Temperature

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HBXControlsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

STATE_HEATING = "heating"
STATE_IDLE = "idle"

OPERATION_LIST = [STATE_HEATING, STATE_IDLE]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the water heater platform."""
    coordinator: HBXControlsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    _LOGGER.debug("Setting up water heater platform")

    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]

        for device_id, device in devices.items():
            device_parameters = device.get("parameters", {})
            building_id = device.get("building_id")

            if "dhw_enabled" in device_parameters:
                entities.append(
                    HBXDHWWaterHeater(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )

    _LOGGER.debug("Adding %d water heater entities", len(entities))
    async_add_entities(entities)


class HBXDHWWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Water heater entity for HBX DHW (Domestic Hot Water) control."""

    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_min_temp = 33
    _attr_max_temp = 180
    _attr_operation_list = OPERATION_LIST
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.ON_OFF
    )
    _attr_icon = "mdi:water-boiler"

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id

        self._attr_unique_id = f"{device_id}_dhw"
        self._attr_name = f"{device.get('name', device_id)} DHW"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def current_operation(self) -> str | None:
        """Return the current DHW operation (heating or idle)."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        dhw_state = parameters.get("dhw_state")
        if not dhw_state:
            return None
        return STATE_HEATING if dhw_state.get("activated") else STATE_IDLE

    @property
    def target_temperature(self) -> float | None:
        """Return the DHW target temperature."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        temp = parameters.get("dhw_target_temp")
        if temp is None:
            return None
        return temp.value if hasattr(temp, "value") else temp

    @property
    def is_on(self) -> bool | None:
        """Return true if DHW is enabled."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return parameters.get("dhw_enabled")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the DHW target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(temperature, "F")
        await device_helper.set_dhw_target_temp(temp)
        self.coordinator.set_parameter_override(
            self._device_id, {"dhw_target_temp": temp}
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on DHW."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_dhw_enabled(True)
        self.coordinator.set_parameter_override(
            self._device_id, {"dhw_enabled": True}
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off DHW."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_dhw_enabled(False)
        self.coordinator.set_parameter_override(
            self._device_id, {"dhw_enabled": False}
        )
        await self.coordinator.async_request_refresh()
