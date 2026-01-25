"""Platform for binary sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SensorLinxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="permanent_heat_demand",
        name="Permanent Heat Demand",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    BinarySensorEntityDescription(
        key="permanent_cool_demand", 
        name="Permanent Cool Demand",
        device_class=BinarySensorDeviceClass.COLD,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: SensorLinxDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    _LOGGER.debug("Setting up binary sensor platform")
    _LOGGER.debug("Coordinator data: %s", coordinator.data)
    
    if coordinator.data and "devices" in coordinator.data:
        devices = coordinator.data["devices"]
        _LOGGER.debug("Found %d devices in coordinator data", len(devices))
        
        for device_id, device in devices.items():
            _LOGGER.debug("Processing device %s: %s", device_id, device)
            device_parameters = device.get("parameters", {})
            _LOGGER.debug("Device %s parameters: %s", device_id, device_parameters)
            
            for description in BINARY_SENSOR_DESCRIPTIONS:
                if description.key in device_parameters:
                    _LOGGER.debug("Creating binary sensor %s for device %s", description.key, device_id)
                    entities.append(
                        SensorLinxBinarySensor(
                            coordinator,
                            description,
                            device_id,
                            device,
                        )
                    )
                else:
                    _LOGGER.debug("Device %s does not have parameter %s", device_id, description.key)
            
            # Create heat pump stage binary sensors
            heatpump_stages = device_parameters.get("heatpump_stages", [])
            for stage in heatpump_stages:
                stage_title = stage.get("title", "Stage")
                
                _LOGGER.debug("Creating heat pump stage binary sensors for device %s stage %s", 
                             device_id, stage_title)
                
                # Running sensor
                entities.append(
                    HeatPumpStageBinarySensor(
                        coordinator,
                        device_id,
                        device,
                        stage_title,
                        "running",
                        "activated",
                        "Running",
                    )
                )
                
                # Enabled sensor
                entities.append(
                    HeatPumpStageBinarySensor(
                        coordinator,
                        device_id,
                        device,
                        stage_title,
                        "enabled",
                        "enabled",
                        "Enabled",
                    )
                )
            
            # Create backup heater binary sensors
            backup_state = device_parameters.get("backup_state")
            if backup_state:
                backup_title = backup_state.get("title", "Backup")
                
                _LOGGER.debug("Creating backup binary sensors for device %s", device_id)
                
                # Running sensor
                entities.append(
                    BackupBinarySensor(
                        coordinator,
                        device_id,
                        device,
                        backup_title,
                        "running",
                        "activated",
                        "Running",
                    )
                )
                
                # Enabled sensor
                entities.append(
                    BackupBinarySensor(
                        coordinator,
                        device_id,
                        device,
                        backup_title,
                        "enabled",
                        "enabled",
                        "Enabled",
                    )
                )
    else:
        _LOGGER.debug("No coordinator data or devices found")
    
    _LOGGER.debug("Adding %d binary sensor entities", len(entities))
    async_add_entities(entities)


class SensorLinxBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of a SensorLinx binary sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        description: BinarySensorEntityDescription,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
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
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        value = parameters.get(self.entity_description.key)
        
        if value is None:
            return None
        
        # Handle different parameter types
        if self.entity_description.key in ["permanent_heat_demand", "permanent_cool_demand"]:
            # These are boolean values from the API
            return bool(value)
        
        # Default handling
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value > 0
        elif isinstance(value, str):
            return value.lower() in ("true", "on", "1", "yes", "active")
        
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )


class HeatPumpStageBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of a Heat Pump Stage binary sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        stage_title: str,
        sensor_type: str,  # "running" or "enabled"
        data_key: str,  # "activated" or "enabled"
        name_suffix: str,  # "Running" or "Enabled"
    ) -> None:
        """Initialize the heat pump stage binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._stage_title = stage_title
        self._sensor_type = sensor_type
        self._data_key = data_key
        
        # Create a safe key from title for unique_id (e.g., "Stage 1" -> "stage_1")
        safe_title = stage_title.lower().replace(" ", "_")
        
        self._attr_unique_id = f"{device_id}_hp_{safe_title}_{sensor_type}"
        self._attr_name = f"{device.get('name', device_id)} HP {stage_title} {name_suffix}"
        
        if sensor_type == "running":
            self._attr_icon = "mdi:heat-pump"
        else:
            self._attr_icon = "mdi:toggle-switch"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the heat pump stage is running/enabled."""
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
                value = stage.get(self._data_key)
                return bool(value) if value is not None else None
        
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


class BackupBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of a Backup Heater binary sensor."""

    def __init__(
        self,
        coordinator: SensorLinxDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        backup_title: str,
        sensor_type: str,  # "running" or "enabled"
        data_key: str,  # "activated" or "enabled"
        name_suffix: str,  # "Running" or "Enabled"
    ) -> None:
        """Initialize the backup heater binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._backup_title = backup_title
        self._sensor_type = sensor_type
        self._data_key = data_key
        
        self._attr_unique_id = f"{device_id}_backup_{sensor_type}"
        self._attr_name = f"{device.get('name', device_id)} {backup_title} {name_suffix}"
        
        if sensor_type == "running":
            self._attr_icon = "mdi:fire"
        else:
            self._attr_icon = "mdi:toggle-switch"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "SensorLinx",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the backup heater is running/enabled."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        backup_state = parameters.get("backup_state")
        
        if not backup_state:
            return None
        
        value = backup_state.get(self._data_key)
        return bool(value) if value is not None else None

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
