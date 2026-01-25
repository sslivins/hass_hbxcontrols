"""Platform for number integration."""
from __future__ import annotations

import logging
from typing import Any

from pysensorlinx.sensorlinx import SensorlinxDevice, Temperature

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
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
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
    
    _LOGGER.debug("Adding %d number entities", len(entities))
    async_add_entities(entities)


class HotTankTargetTemperature(CoordinatorEntity, NumberEntity):
    """Hot Tank Target Temperature control (used when outdoor reset is off)."""

    _attr_native_min_value = 35
    _attr_native_max_value = 200
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.AUTO
    _attr_icon = "mdi:thermometer"

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
        
        self._attr_unique_id = f"{device_id}_hot_tank_target_temp"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Target Temperature"
        
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
        value = parameters.get("hot_tank_min_temp")
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-low"
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
        
        self._attr_unique_id = f"{device_id}_hot_tank_min_temp"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Min Temperature"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-high"
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
        
        self._attr_unique_id = f"{device_id}_hot_tank_max_temp"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Max Temperature"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:sun-thermometer"
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
        
        self._attr_unique_id = f"{device_id}_hot_tank_outdoor_reset"
        self._attr_name = f"{device.get('name', device_id)} Hot Tank Outdoor Reset"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.AUTO
    _attr_icon = "mdi:thermometer"

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
        
        self._attr_unique_id = f"{device_id}_cold_tank_target_temp"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Target Temperature"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-low"
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
        
        self._attr_unique_id = f"{device_id}_cold_tank_min_temp"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Min Temperature"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-high"
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
        
        self._attr_unique_id = f"{device_id}_cold_tank_max_temp"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Max Temperature"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:snowflake-thermometer"
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
        
        self._attr_unique_id = f"{device_id}_cold_tank_outdoor_reset"
        self._attr_name = f"{device.get('name', device_id)} Cold Tank Outdoor Reset"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.AUTO
    _attr_icon = "mdi:weather-sunny-alert"
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
        
        self._attr_unique_id = f"{device_id}_warm_weather_shutdown"
        self._attr_name = f"{device.get('name', device_id)} Warm Weather Shutdown Temperature"
        
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
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.AUTO
    _attr_icon = "mdi:weather-snowy-heavy"
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
        
        self._attr_unique_id = f"{device_id}_cold_weather_shutdown"
        self._attr_name = f"{device.get('name', device_id)} Cold Weather Shutdown Temperature"
        
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
