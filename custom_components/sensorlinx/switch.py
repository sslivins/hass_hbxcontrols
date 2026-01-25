"""Platform for switch integration."""
from __future__ import annotations

import logging
from typing import Any

from pysensorlinx.sensorlinx import SensorlinxDevice, Temperature

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up switch platform")
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        
        for device_id, device in devices.items():
            device_parameters = device.get("parameters", {})
            building_id = device.get("building_id")
            
            # Hot Tank Outdoor Reset switch
            if "hot_tank_outdoor_reset" in device_parameters:
                entities.append(
                    HotTankOutdoorResetSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Tank Outdoor Reset switch
            if "cold_tank_outdoor_reset" in device_parameters:
                entities.append(
                    ColdTankOutdoorResetSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Permanent Heat Demand switch
            if "permanent_heat_demand" in device_parameters:
                entities.append(
                    PermanentHeatDemandSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Permanent Cool Demand switch
            if "permanent_cool_demand" in device_parameters:
                entities.append(
                    PermanentCoolDemandSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Warm Weather Shutdown switch
            if "warm_weather_shutdown" in device_parameters:
                entities.append(
                    WarmWeatherShutdownSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Weather Shutdown switch
            if "cold_weather_shutdown" in device_parameters:
                entities.append(
                    ColdWeatherShutdownSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
    
    _LOGGER.debug("Adding %d switch entities", len(entities))
    async_add_entities(entities)


class HotTankOutdoorResetSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Hot Tank Outdoor Reset."""

    _attr_icon = "mdi:sun-thermometer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_hot_tank_outdoor_reset_enabled"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Outdoor Reset"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if outdoor reset is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("hot_tank_outdoor_reset")
        return value != "off" and value is not None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on outdoor reset with default 0°F design temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 0°F (common design outdoor temperature)
        temp = Temperature(0, "F")
        await device_helper.set_hot_tank_outdoor_reset(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off outdoor reset."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_hot_tank_outdoor_reset("off")
        await self.coordinator.async_request_refresh()


class PermanentHeatDemandSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Permanent Heat Demand."""

    _attr_icon = "mdi:fire"

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_permanent_heat_demand"
        self._attr_name = f"{device.get('name', device_id)} Permanent Heat Demand"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if permanent heat demand is enabled."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return bool(parameters.get("permanent_heat_demand", False))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on permanent heat demand."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_permanent_hd(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off permanent heat demand."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_permanent_hd(False)
        await self.coordinator.async_request_refresh()


class PermanentCoolDemandSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Permanent Cool Demand."""

    _attr_icon = "mdi:snowflake"

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_permanent_cool_demand"
        self._attr_name = f"{device.get('name', device_id)} Permanent Cool Demand"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if permanent cool demand is enabled."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return bool(parameters.get("permanent_cool_demand", False))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on permanent cool demand."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_permanent_cd(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off permanent cool demand."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_permanent_cd(False)
        await self.coordinator.async_request_refresh()


class ColdTankOutdoorResetSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Cold Tank Outdoor Reset."""

    _attr_icon = "mdi:snowflake-thermometer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_tank_outdoor_reset_enabled"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Outdoor Reset"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if outdoor reset is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_tank_outdoor_reset")
        return value != "off" and value is not None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on outdoor reset with default 0°F design temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 0°F (common design outdoor temperature)
        temp = Temperature(0, "F")
        await device_helper.set_cold_tank_outdoor_reset(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off outdoor reset."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_cold_tank_outdoor_reset("off")
        await self.coordinator.async_request_refresh()


class WarmWeatherShutdownSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Warm Weather Shutdown."""

    _attr_icon = "mdi:weather-sunny-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_warm_weather_shutdown_enabled"
        self._attr_name = f"{device.get('name', device_id)} Warm Weather Shutdown"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if warm weather shutdown is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("warm_weather_shutdown")
        return value != "off" and value is not None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on warm weather shutdown with default 88°F temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 88°F
        temp = Temperature(88, "F")
        await device_helper.set_warm_weather_shutdown(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off warm weather shutdown."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_warm_weather_shutdown("off")
        await self.coordinator.async_request_refresh()


class ColdWeatherShutdownSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Cold Weather Shutdown."""

    _attr_icon = "mdi:weather-snowy-heavy"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_weather_shutdown_enabled"
        self._attr_name = f"{device.get('name', device_id)} Cold Weather Shutdown"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if cold weather shutdown is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_weather_shutdown")
        return value != "off" and value is not None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on cold weather shutdown with default 41°F temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 41°F
        temp = Temperature(41, "F")
        await device_helper.set_cold_weather_shutdown(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off cold weather shutdown."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_cold_weather_shutdown("off")
        await self.coordinator.async_request_refresh()
