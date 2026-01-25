"""Platform for sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # Temperature sensors - these will be dynamically created based on available temperature sensors
    SensorEntityDescription(
        key="temperature_tank",
        name="Tank Temperature",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature_outdoor",
        name="Outdoor Temperature", 
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="device_type",
        name="Device Type",
        device_class=SensorDeviceClass.ENUM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up sensor platform")
    _LOGGER.debug("Coordinator data: %s", coordinator.data)
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        _LOGGER.debug("Found %d devices in coordinator data", len(devices))
        
        for device_id, device in devices.items():
            _LOGGER.debug("Processing device %s: %s", device_id, device)
            device_parameters = device.get("parameters", {})
            _LOGGER.debug("Device %s parameters: %s", device_id, device_parameters)
            
            for description in SENSOR_DESCRIPTIONS:
                if description.key in device_parameters:
                    _LOGGER.debug("Creating sensor %s for device %s", description.key, device_id)
                    entities.append(
                        SensorLinxSensor(
                            coordinator,
                            description,
                            device_id,
                            device,
                        )
                    )
                else:
                    _LOGGER.debug("Device %s does not have parameter %s", device_id, description.key)
            
            # Create heat pump stage sensors
            heatpump_stages = device_parameters.get("heatpump_stages", [])
            for stage in heatpump_stages:
                stage_title = stage.get("title", "Stage")
                
                _LOGGER.debug("Creating heat pump stage runtime sensor for device %s stage %s", 
                             device_id, stage_title)
                
                # Runtime sensor
                entities.append(
                    HeatPumpStageRuntimeSensor(
                        coordinator,
                        device_id,
                        device,
                        stage_title,
                    )
                )
            
            # Create backup heater sensors
            backup_state = device_parameters.get("backup_state")
            if backup_state:
                backup_title = backup_state.get("title", "Backup")
                
                _LOGGER.debug("Creating backup runtime sensor for device %s", device_id)
                
                # Runtime sensor
                entities.append(
                    BackupRuntimeSensor(
                        coordinator,
                        device_id,
                        device,
                        backup_title,
                    )
                )
    else:
        _LOGGER.debug("No coordinator data or devices found")
    
    _LOGGER.debug("Adding %d sensor entities", len(entities))
    async_add_entities(entities)


class SensorLinxSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a SensorLinx sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        description: SensorEntityDescription,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._device = device
        
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_name = f"{device.get('name', device_id)} {description.name}"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("type", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> str | int | float | None:
        """Return the native value of the sensor."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        return parameters.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )


class HeatPumpStageRuntimeSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a Heat Pump Stage Runtime sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        stage_title: str,
    ) -> None:
        """Initialize the heat pump stage runtime sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._stage_title = stage_title
        
        # Create a safe key from title for unique_id
        safe_title = stage_title.lower().replace(" ", "_")
        
        self._attr_unique_id = f"{device_id}_hp_{safe_title}_runtime"
        self._attr_name = f"{device.get('name', device_id)} HP {stage_title} Runtime"
        self._attr_icon = "mdi:timer-outline"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("type", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> str | None:
        """Return the runtime of the heat pump stage."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        heatpump_stages = parameters.get("heatpump_stages", [])
        
        # Find the stage by title
        for stage in heatpump_stages:
            if stage.get("title") == self._stage_title:
                return stage.get("runTime")
        
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Check if the stage still exists
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
            
        parameters = device.get("parameters", {})
        heatpump_stages = parameters.get("heatpump_stages", [])
        
        return any(stage.get("title") == self._stage_title for stage in heatpump_stages)


class BackupRuntimeSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a Backup Heater Runtime sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        backup_title: str,
    ) -> None:
        """Initialize the backup heater runtime sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._backup_title = backup_title
        
        self._attr_unique_id = f"{device_id}_backup_runtime"
        self._attr_name = f"{device.get('name', device_id)} {backup_title} Runtime"
        self._attr_icon = "mdi:timer-outline"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("type", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def native_value(self) -> str | None:
        """Return the runtime of the backup heater."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        backup_state = parameters.get("backup_state")
        
        if not backup_state:
            return None
        
        return backup_state.get("runTime")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        ):
            return False
        
        # Check if backup state exists
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return False
            
        parameters = device.get("parameters", {})
        return parameters.get("backup_state") is not None
