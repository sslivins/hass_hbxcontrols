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
from .coordinator import HBXControlsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator: HBXControlsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
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
            
            # Rotate Cycles switch
            if "rotate_cycles" in device_parameters:
                entities.append(
                    RotateCyclesSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Rotate Time switch
            if "rotate_time" in device_parameters:
                entities.append(
                    RotateTimeSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Synchronized Stage Off switch
            if "off_staging" in device_parameters:
                entities.append(
                    SynchronizedStageOffSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Lag Time switch
            if "backup_lag_time" in device_parameters:
                entities.append(
                    BackupLagTimeSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Differential switch
            if "backup_differential" in device_parameters:
                entities.append(
                    BackupDifferentialSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Only Outdoor Temp switch
            if "backup_only_outdoor_temp" in device_parameters:
                entities.append(
                    BackupOnlyOutdoorTempSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Temperature switch
            if "backup_temp" in device_parameters:
                entities.append(
                    BackupTempSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Wide Priority Differential switch
            if "wide_priority_differential" in device_parameters:
                entities.append(
                    WidePriorityDifferentialSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Two Stage Heat Pump switch (only available when number_of_stages is even)
            if "two_stage_heat_pump" in device_parameters:
                entities.append(
                    TwoStageHeatPumpSwitch(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Only Tank Temp switch
            if "backup_only_tank_temp" in device_parameters:
                entities.append(
                    BackupOnlyTankTempSwitch(
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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


class RotateCyclesSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Heat Pump Rotate Cycles."""

    _attr_icon = "mdi:rotate-3d-variant"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_rotate_cycles_enabled"
        self._attr_name = f"{device.get('name', device_id)} Rotate Cycles"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if rotate cycles is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("rotate_cycles")
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
        """Turn on rotate cycles with default 1 cycle."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 1 cycle
        await device_helper.set_rotate_cycles(1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off rotate cycles."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_rotate_cycles("off")
        await self.coordinator.async_request_refresh()


class RotateTimeSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Heat Pump Rotate Time."""

    _attr_icon = "mdi:clock-rotate"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_rotate_time_enabled"
        self._attr_name = f"{device.get('name', device_id)} Rotate Time"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if rotate time is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("rotate_time")
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
        """Turn on rotate time with default 1 hour."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 1 hour
        await device_helper.set_rotate_time(1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off rotate time."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_rotate_time("off")
        await self.coordinator.async_request_refresh()


class SynchronizedStageOffSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Synchronized Stage Off.
    
    When OFF: Heat pumps stage off normally based on tank temperature,
              differential settings, or Stage OFF Lagtime settings.
    When ON: All heat pumps stage off at the same time based on tank
             temperature and differential settings.
    """

    _attr_icon = "mdi:sync"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_synchronized_stage_off"
        self._attr_name = f"{device.get('name', device_id)} Synchronized Stage Off"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if synchronized stage off is enabled."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return bool(parameters.get("off_staging", False))

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
        """Turn on synchronized stage off."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_off_staging(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off synchronized stage off (normal staging)."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_off_staging(False)
        await self.coordinator.async_request_refresh()


class BackupLagTimeSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Backup Lag Time.
    
    Minimum lag time between heat pump stages and the backup boiler.
    """

    _attr_icon = "mdi:timer-pause"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_lag_time_enabled"
        self._attr_name = f"{device.get('name', device_id)} Backup Lag Time"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if backup lag time is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_lag_time")
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
        """Turn on backup lag time with default 10 minutes."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 10 minutes
        await device_helper.set_backup_lag_time(10)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off backup lag time."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_backup_lag_time("off")
        await self.coordinator.async_request_refresh()


class BackupDifferentialSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Backup Differential.
    
    Tank temperature difference below target at which backup boiler activates,
    overriding backup time if needed.
    """

    _attr_icon = "mdi:thermometer-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_differential_enabled"
        self._attr_name = f"{device.get('name', device_id)} Backup Differential"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if backup differential is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_differential")
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
        """Turn on backup differential with default 10°F."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 10°F
        temp = Temperature(10, "F")
        await device_helper.set_backup_differential(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off backup differential."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_backup_differential("off")
        await self.coordinator.async_request_refresh()


class BackupOnlyOutdoorTempSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Backup Only Outdoor Temperature.
    
    The outdoor temperature below which only the backup will run.
    """

    _attr_icon = "mdi:snowflake-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_only_outdoor_temp_enabled"
        self._attr_name = f"{device.get('name', device_id)} Backup Only Outdoor Temp"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if backup only outdoor temp is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_only_outdoor_temp")
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
        """Turn on backup only outdoor temp with default -13°F."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to -13°F
        temp = Temperature(-13, "F")
        await device_helper.set_backup_only_outdoor_temp(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off backup only outdoor temp."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_backup_only_outdoor_temp("off")
        await self.coordinator.async_request_refresh()


class BackupTempSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Backup Temperature.
    
    The temperature threshold at which the backup activates.
    """

    _attr_icon = "mdi:fire-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_temp_enabled"
        self._attr_name = f"{device.get('name', device_id)} Backup Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if backup temp is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_temp")
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
        """Turn on backup temp with default 50°F."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 50°F (middle of range)
        temp = Temperature(50, "F")
        await device_helper.set_backup_temp(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off backup temp."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_backup_temp("off")
        await self.coordinator.async_request_refresh()


class WidePriorityDifferentialSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Wide Priority Differential.
    
    When enabled, the tank target will exceed the setpoint by the configured
    differential before switching between heat and cool demands if both are present.
    When disabled, the tank target switches as soon as the setpoint is satisfied.
    This should not be used for single tank systems.
    """

    _attr_icon = "mdi:swap-horizontal-bold"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "wide_priority_differential"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_wide_priority_differential"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if wide priority differential is enabled."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("wide_priority_differential")
        return bool(value) if value is not None else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "wide_priority_differential" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on wide priority differential."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_wide_priority_differential(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off wide priority differential."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_wide_priority_differential(False)
        await self.coordinator.async_request_refresh()


class TwoStageHeatPumpSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Two Stage Heat Pump mode.
    
    This setting appears when the Number of Stages is set to an even value (2 or 4).
    It can be utilized when using dual stage heat pumps or pumps with 2 compressors per unit.
    """

    _attr_icon = "mdi:heat-pump"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "two_stage_heat_pump"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_two_stage_heat_pump"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if two stage heat pump mode is enabled."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("two_stage_heat_pump")
        return bool(value) if value is not None else None

    @property
    def available(self) -> bool:
        """Return if entity is available.
        
        Only available when number_of_stages is an even value (2 or 4).
        """
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        parameters = self.coordinator.data["devices"][self._device_id].get("parameters", {})
        
        # Must have the parameter
        if "two_stage_heat_pump" not in parameters:
            return False
        
        # Only available when number_of_stages is even (2 or 4)
        num_stages = parameters.get("number_of_stages")
        if num_stages is None:
            return True  # If we can't determine stages, show entity anyway
        return num_stages in (2, 4)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on two stage heat pump mode."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_two_stage_heat_pump(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off two stage heat pump mode."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_two_stage_heat_pump(False)
        await self.coordinator.async_request_refresh()


class BackupOnlyTankTempSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable Backup Only Tank Temperature.
    
    When enabled, if the tank temperature exceeds this threshold, only the 
    backup will heat the tank to the target temperature (heat pumps disabled).
    """

    _attr_icon = "mdi:thermometer-alert"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "backup_only_tank_temp"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_only_tank_temp_enabled"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if backup only tank temp is enabled (not 'off')."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_only_tank_temp")
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
        """Turn on backup only tank temp with default 120°F."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Default to 120°F (typical hot water setting)
        temp = Temperature(120, "F")
        await device_helper.set_backup_only_tank_temp(temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off backup only tank temp."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_backup_only_tank_temp("off")
        await self.coordinator.async_request_refresh()
