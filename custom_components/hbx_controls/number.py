"""Platform for number integration."""
from __future__ import annotations

import logging
from typing import Any

from pysensorlinx.sensorlinx import SensorlinxDevice, Temperature, TemperatureDelta

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
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
    """Set up the number platform."""
    coordinator: HBXControlsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up number platform")
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        
        for device_id, device in devices.items():
            device_parameters = device.get("parameters", {})
            building_id = device.get("building_id")
            
            # Hot Tank Target Temperature (used when outdoor reset is off)
            if "hot_tank_min_temp" in device_parameters:
                entities.append(
                    HotTankTargetTemperature(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Hot Tank Min Temperature (used when outdoor reset is on)
            if "hot_tank_min_temp" in device_parameters:
                entities.append(
                    HotTankMinTemperature(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Hot Tank Max Temperature (used when outdoor reset is on)
            if "hot_tank_max_temp" in device_parameters:
                entities.append(
                    HotTankMaxTemperature(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Hot Tank Outdoor Reset
            if "hot_tank_outdoor_reset" in device_parameters:
                entities.append(
                    HotTankOutdoorReset(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Tank Target Temperature (used when outdoor reset is off)
            if "cold_tank_min_temp" in device_parameters:
                entities.append(
                    ColdTankTargetTemperature(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Tank Min Temperature (used when outdoor reset is on)
            if "cold_tank_min_temp" in device_parameters:
                entities.append(
                    ColdTankMinTemperature(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Tank Max Temperature (used when outdoor reset is on)
            if "cold_tank_max_temp" in device_parameters:
                entities.append(
                    ColdTankMaxTemperature(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Tank Outdoor Reset
            if "cold_tank_outdoor_reset" in device_parameters:
                entities.append(
                    ColdTankOutdoorReset(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Warm Weather Shutdown
            if "warm_weather_shutdown" in device_parameters:
                entities.append(
                    WarmWeatherShutdown(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Weather Shutdown
            if "cold_weather_shutdown" in device_parameters:
                entities.append(
                    ColdWeatherShutdown(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Stage On Lag Time
            if "stage_on_lag_time" in device_parameters:
                entities.append(
                    StageOnLagTime(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Stage Off Lag Time
            if "stage_off_lag_time" in device_parameters:
                entities.append(
                    StageOffLagTime(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Rotate Cycles
            if "rotate_cycles" in device_parameters:
                entities.append(
                    RotateCycles(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Rotate Time
            if "rotate_time" in device_parameters:
                entities.append(
                    RotateTime(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Lag Time
            if "backup_lag_time" in device_parameters:
                entities.append(
                    BackupLagTime(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Differential
            if "backup_differential" in device_parameters:
                entities.append(
                    BackupDifferential(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Hot Tank Differential
            if "hot_tank_differential" in device_parameters:
                entities.append(
                    HotTankDifferential(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Cold Tank Differential
            if "cold_tank_differential" in device_parameters:
                entities.append(
                    ColdTankDifferential(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Only Outdoor Temp
            if "backup_only_outdoor_temp" in device_parameters:
                entities.append(
                    BackupOnlyOutdoorTemp(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Number of Heat Pump Stages
            if "number_of_stages" in device_parameters:
                entities.append(
                    NumberOfStages(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Temperature
            if "backup_temp" in device_parameters:
                entities.append(
                    BackupTemp(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Weather Shutdown Lag Time
            if "weather_shutdown_lag_time" in device_parameters:
                entities.append(
                    WeatherShutdownLagTime(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Heat/Cool Switch Delay
            if "heat_cool_switch_delay" in device_parameters:
                entities.append(
                    HeatCoolSwitchDelay(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
            
            # Backup Only Tank Temp
            if "backup_only_tank_temp" in device_parameters:
                entities.append(
                    BackupOnlyTankTemp(
                        coordinator,
                        device_id,
                        device,
                        building_id,
                    )
                )
    
    _LOGGER.debug("Adding %d number entities", len(entities))
    async_add_entities(entities)


class HotTankTargetTemperature(CoordinatorEntity, NumberEntity):
    """Hot Tank Target Temperature control (used when outdoor reset is off)."""

    _attr_native_min_value = 35
    _attr_native_max_value = 200
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_hot_tank_target_temp"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Target Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value (computed target from the temperatures array)."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return parameters.get("target_temperature_tank")

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is off)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        outdoor_reset = parameters.get("hot_tank_outdoor_reset")
        return outdoor_reset == "off" or outdoor_reset is None

    async def async_set_native_value(self, value: float) -> None:
        """Set the target temperature (sets both min and max to same value)."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        # When outdoor reset is off, min and max must be the same
        await device_helper.set_hot_tank_min_temp(temp)
        await device_helper.set_hot_tank_max_temp(temp)
        await self.coordinator.async_request_refresh()


class HotTankMinTemperature(CoordinatorEntity, NumberEntity):
    """Hot Tank Min Temperature control (used when outdoor reset is on)."""

    _attr_native_min_value = 35
    _attr_native_max_value = 200
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-low"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_hot_tank_min_temp"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Min Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("hot_tank_min_temp")
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is on)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        outdoor_reset = parameters.get("hot_tank_outdoor_reset")
        return outdoor_reset != "off" and outdoor_reset is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the min temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_hot_tank_min_temp(temp)
        await self.coordinator.async_request_refresh()


class HotTankMaxTemperature(CoordinatorEntity, NumberEntity):
    """Hot Tank Max Temperature control (used when outdoor reset is on)."""

    _attr_native_min_value = 35
    _attr_native_max_value = 200
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-high"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_hot_tank_max_temp"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Max Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("hot_tank_max_temp")
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is on)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        outdoor_reset = parameters.get("hot_tank_outdoor_reset")
        return outdoor_reset != "off" and outdoor_reset is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the max temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_hot_tank_max_temp(temp)
        await self.coordinator.async_request_refresh()


class HotTankOutdoorReset(CoordinatorEntity, NumberEntity):
    """Hot Tank Outdoor Reset control (design outdoor temperature or off)."""

    _attr_native_min_value = -40
    _attr_native_max_value = 127
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:sun-thermometer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_hot_tank_outdoor_reset"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Outdoor Reset"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("hot_tank_outdoor_reset")
        if value == "off":
            return None
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("hot_tank_outdoor_reset")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the outdoor reset temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_hot_tank_outdoor_reset(temp)
        await self.coordinator.async_request_refresh()


class ColdTankTargetTemperature(CoordinatorEntity, NumberEntity):
    """Cold Tank Target Temperature control (used when outdoor reset is off)."""

    _attr_native_min_value = 35
    _attr_native_max_value = 200
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_tank_target_temp"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Target Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_tank_min_temp")
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is off)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        outdoor_reset = parameters.get("cold_tank_outdoor_reset")
        return outdoor_reset == "off" or outdoor_reset is None

    async def async_set_native_value(self, value: float) -> None:
        """Set the target temperature (sets both min and max to same value)."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        # When outdoor reset is off, min and max must be the same
        await device_helper.set_cold_tank_min_temp(temp)
        await device_helper.set_cold_tank_max_temp(temp)
        await self.coordinator.async_request_refresh()


class ColdTankMinTemperature(CoordinatorEntity, NumberEntity):
    """Cold Tank Min Temperature control (used when outdoor reset is on)."""

    _attr_native_min_value = 35
    _attr_native_max_value = 200
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-low"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_tank_min_temp"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Min Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_tank_min_temp")
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is on)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        outdoor_reset = parameters.get("cold_tank_outdoor_reset")
        return outdoor_reset != "off" and outdoor_reset is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the min temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_cold_tank_min_temp(temp)
        await self.coordinator.async_request_refresh()


class ColdTankMaxTemperature(CoordinatorEntity, NumberEntity):
    """Cold Tank Max Temperature control (used when outdoor reset is on)."""

    _attr_native_min_value = 35
    _attr_native_max_value = 200
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-high"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_tank_max_temp"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Max Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_tank_max_temp")
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is on)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        outdoor_reset = parameters.get("cold_tank_outdoor_reset")
        return outdoor_reset != "off" and outdoor_reset is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the max temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_cold_tank_max_temp(temp)
        await self.coordinator.async_request_refresh()


class ColdTankOutdoorReset(CoordinatorEntity, NumberEntity):
    """Cold Tank Outdoor Reset control (design outdoor temperature or off)."""

    _attr_native_min_value = -40
    _attr_native_max_value = 127
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:snowflake-thermometer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_tank_outdoor_reset"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Outdoor Reset"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_tank_outdoor_reset")
        if value == "off":
            return None
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when outdoor reset is enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when outdoor reset is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("cold_tank_outdoor_reset")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the outdoor reset temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_cold_tank_outdoor_reset(temp)
        await self.coordinator.async_request_refresh()


class WarmWeatherShutdown(CoordinatorEntity, NumberEntity):
    """Warm Weather Shutdown temperature control."""

    _attr_native_min_value = 34
    _attr_native_max_value = 180
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:weather-sunny-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_warm_weather_shutdown"
        self._attr_name = f"{device.get('name', device_id)} Warm Weather Shutdown Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("warm_weather_shutdown")
        if value == "off":
            return None
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when warm weather shutdown is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("warm_weather_shutdown")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the warm weather shutdown temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_warm_weather_shutdown(temp)
        await self.coordinator.async_request_refresh()


class ColdWeatherShutdown(CoordinatorEntity, NumberEntity):
    """Cold Weather Shutdown temperature control."""

    _attr_native_min_value = 33
    _attr_native_max_value = 119
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:weather-snowy-heavy"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_weather_shutdown"
        self._attr_name = f"{device.get('name', device_id)} Cold Weather Shutdown Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_weather_shutdown")
        if value == "off":
            return None
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when cold weather shutdown is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("cold_weather_shutdown")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the cold weather shutdown temperature."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_cold_weather_shutdown(temp)
        await self.coordinator.async_request_refresh()


class StageOnLagTime(CoordinatorEntity, NumberEntity):
    """Stage On Lag Time control."""

    _attr_native_min_value = 1
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-plus"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_stage_on_lag_time"
        self._attr_name = f"{device.get('name', device_id)} Stage On Lag Time"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return parameters.get("stage_on_lag_time")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "stage_on_lag_time" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the stage on lag time."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_stage_on_lag_time(int(value))
        await self.coordinator.async_request_refresh()


class StageOffLagTime(CoordinatorEntity, NumberEntity):
    """Stage Off Lag Time control."""

    _attr_native_min_value = 1
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-minus"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_stage_off_lag_time"
        self._attr_name = f"{device.get('name', device_id)} Stage Off Lag Time"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        return parameters.get("stage_off_lag_time")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "stage_off_lag_time" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the stage off lag time."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_stage_off_lag_time(int(value))
        await self.coordinator.async_request_refresh()


class RotateCycles(CoordinatorEntity, NumberEntity):
    """Rotate Cycles control - number of cycles to rotate heat pumps."""

    _attr_native_min_value = 1
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "cycles"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:rotate-3d-variant"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_rotate_cycles"
        self._attr_name = f"{device.get('name', device_id)} Rotate Cycles"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("rotate_cycles")
        if value == "off":
            return None
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when rotate cycles is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("rotate_cycles")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the rotate cycles value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_rotate_cycles(int(value))
        await self.coordinator.async_request_refresh()


class RotateTime(CoordinatorEntity, NumberEntity):
    """Rotate Time control - time of rotation between heat pumps in hours."""

    _attr_native_min_value = 1
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:clock-rotate"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_rotate_time"
        self._attr_name = f"{device.get('name', device_id)} Rotate Time"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("rotate_time")
        if value == "off":
            return None
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when rotate time is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("rotate_time")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the rotate time value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_rotate_time(int(value))
        await self.coordinator.async_request_refresh()


class BackupLagTime(CoordinatorEntity, NumberEntity):
    """Backup Lag Time control - minimum lag time between HP stages and backup boiler."""

    _attr_native_min_value = 1
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-pause"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_lag_time"
        self._attr_name = f"{device.get('name', device_id)} Backup Lag Time"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_lag_time")
        if value == "off":
            return None
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when backup lag time is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("backup_lag_time")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the backup lag time value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_backup_lag_time(int(value))
        await self.coordinator.async_request_refresh()


class BackupDifferential(CoordinatorEntity, NumberEntity):
    """Backup Differential control - temp difference below target to activate backup."""

    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_differential"
        self._attr_name = f"{device.get('name', device_id)} Backup Differential"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1  # Round to nearest 0.5 for Celsius
        return 1

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement based on HA config."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def native_min_value(self) -> float:
        """Return minimum value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 1.0  # 2°F ≈ 1.1°C, rounded to 1.0
        return 2

    @property
    def native_max_value(self) -> float:
        """Return maximum value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 55.5  # 100°F ≈ 55.6°C, rounded to 55.5
        return 100

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_differential")
        if value == "off":
            return None
        if isinstance(value, TemperatureDelta):
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
                # Round to nearest 0.5 to match step
                return round(value.to_celsius() * 2) / 2
            return value.to_fahrenheit()
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when backup differential is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("backup_differential")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the backup differential value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Convert from user's unit system
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            delta = TemperatureDelta(value, "C")
        else:
            delta = TemperatureDelta(value, "F")
        await device_helper.set_backup_differential(delta)
        await self.coordinator.async_request_refresh()


class HotTankDifferential(CoordinatorEntity, NumberEntity):
    """Hot Tank Differential control.
    
    Sets the desired hot tank differential. For example, a differential of 4°F
    will allow for 2 degrees above and/or 2 degrees below the desired temperature
    before a demand is present.
    """

    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-plus"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_hot_tank_differential"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Differential"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1  # Round to nearest 0.5 for Celsius
        return 1

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement based on HA config."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def native_min_value(self) -> float:
        """Return minimum value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 1.0  # 2°F ≈ 1.1°C, rounded to 1.0
        return 2

    @property
    def native_max_value(self) -> float:
        """Return maximum value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 55.5  # 100°F ≈ 55.6°C, rounded to 55.5
        return 100

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("hot_tank_differential")
        if isinstance(value, TemperatureDelta):
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
                # Round to nearest 0.5 to match step
                return round(value.to_celsius() * 2) / 2
            return value.to_fahrenheit()
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "hot_tank_differential" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the hot tank differential value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Convert from user's unit system
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            delta = TemperatureDelta(value, "C")
        else:
            delta = TemperatureDelta(value, "F")
        await device_helper.set_hot_tank_differential(delta)
        await self.coordinator.async_request_refresh()


class ColdTankDifferential(CoordinatorEntity, NumberEntity):
    """Cold Tank Differential control.
    
    Sets the desired cold tank differential. For example, a differential of 4°F
    will allow for 2 degrees above and/or 2 degrees below the desired temperature
    before a demand is present.
    """

    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-minus"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_cold_tank_differential"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Differential"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1  # Round to nearest 0.5 for Celsius
        return 1

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement based on HA config."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def native_min_value(self) -> float:
        """Return minimum value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 1.0  # 2°F ≈ 1.1°C, rounded to 1.0
        return 2

    @property
    def native_max_value(self) -> float:
        """Return maximum value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 55.5  # 100°F ≈ 55.6°C, rounded to 55.5
        return 100

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("cold_tank_differential")
        if isinstance(value, TemperatureDelta):
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
                # Round to nearest 0.5 to match step
                return round(value.to_celsius() * 2) / 2
            return value.to_fahrenheit()
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "cold_tank_differential" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the cold tank differential value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        # Convert from user's unit system
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            delta = TemperatureDelta(value, "C")
        else:
            delta = TemperatureDelta(value, "F")
        await device_helper.set_cold_tank_differential(delta)
        await self.coordinator.async_request_refresh()


class BackupOnlyOutdoorTemp(CoordinatorEntity, NumberEntity):
    """Backup Only Outdoor Temperature control.
    
    The outdoor temperature below which only the backup will run.
    """

    _attr_native_min_value = -40
    _attr_native_max_value = 127
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:snowflake-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_only_outdoor_temp"
        self._attr_name = f"{device.get('name', device_id)} Backup Only Outdoor Temp"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_only_outdoor_temp")
        if value == "off":
            return None
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when backup only outdoor temp is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("backup_only_outdoor_temp")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the backup only outdoor temp value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_backup_only_outdoor_temp(temp)
        await self.coordinator.async_request_refresh()


class NumberOfStages(CoordinatorEntity, NumberEntity):
    """Number of Heat Pump Stages configuration.
    
    Sets the number of heat pump stages for the device.
    Valid values are 1 through 4.
    """

    _attr_native_min_value = 1
    _attr_native_max_value = 4
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:heat-pump-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_number_of_stages"
        self._attr_name = f"{device.get('name', device_id)} Number of HP Stages"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> int | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("number_of_stages")
        if value is None:
            return 1  # Default to 1 if not set
        return int(value)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "number_of_stages" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the number of heat pump stages."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_number_of_stages(int(value))
        await self.coordinator.async_request_refresh()


class BackupTemp(CoordinatorEntity, NumberEntity):
    """Backup Temperature control.
    
    The temperature threshold at which the backup activates.
    Valid range: 2°F to 100°F.
    """

    _attr_native_min_value = 2
    _attr_native_max_value = 100
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:fire-alert"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_temp"
        self._attr_name = f"{device.get('name', device_id)} Backup Temperature"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_temp")
        if value == "off":
            return None
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when backup temp is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("backup_temp")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the backup temperature value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_backup_temp(temp)
        await self.coordinator.async_request_refresh()


class WeatherShutdownLagTime(CoordinatorEntity, NumberEntity):
    """Weather Shutdown Lag Time control.
    
    Sets the lag time (in hours) for Warm Weather Shutdown (WWSD) or 
    Cold Weather Shutdown (CWSD). This is how long to wait after the 
    temperature threshold is met before entering shutdown mode.
    """

    _attr_native_min_value = 0
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "weather_shutdown_lag_time"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_weather_shutdown_lag_time"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> int | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("weather_shutdown_lag_time")
        if value is None:
            return 0
        return int(value)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "weather_shutdown_lag_time" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the weather shutdown lag time."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_weather_shutdown_lag_time(int(value))
        await self.coordinator.async_request_refresh()


class HeatCoolSwitchDelay(CoordinatorEntity, NumberEntity):
    """Heat/Cool Switch Delay control.
    
    Sets the delay (in seconds) between the control switching between 
    heat and cool calls. Range: 30 to 600 seconds.
    """

    _attr_native_min_value = 30
    _attr_native_max_value = 600
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-sync-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "heat_cool_switch_delay"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_heat_cool_switch_delay"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> int | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("heat_cool_switch_delay")
        if value is None:
            return None
        return int(value)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
            and "heat_cool_switch_delay" in self.coordinator.data["devices"][self._device_id].get("parameters", {})
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the heat/cool switch delay."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        await device_helper.set_heat_cool_switch_delay(int(value))
        await self.coordinator.async_request_refresh()


class BackupOnlyTankTemp(CoordinatorEntity, NumberEntity):
    """Backup Only Tank Temperature control.
    
    When the tank temperature exceeds this value, only the backup will heat 
    the tank to the target temperature (heat pumps disabled).
    Valid range: 33°F to 200°F.
    """

    _attr_native_min_value = 33
    _attr_native_max_value = 200
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-alert"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "backup_only_tank_temp"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        building_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = building_id
        
        self._attr_unique_id = f"{device_id}_backup_only_tank_temp"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_step(self) -> float:
        """Return step value based on unit system."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 0.1
        return 1


    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        parameters = device.get("parameters", {})
        value = parameters.get("backup_only_tank_temp")
        if value == "off":
            return None
        if isinstance(value, Temperature):
            return value.value
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available (only when enabled)."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Only available when backup only tank temp is NOT off
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
        parameters = device.get("parameters", {})
        value = parameters.get("backup_only_tank_temp")
        return value != "off" and value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Set the backup only tank temperature value."""
        device_helper = SensorlinxDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )
        temp = Temperature(value, "F")
        await device_helper.set_backup_only_tank_temp(temp)
        await self.coordinator.async_request_refresh()
