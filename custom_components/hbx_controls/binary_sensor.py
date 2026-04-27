"""Platform for binary sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from pysensorlinx import DEVICE_TYPE_ZON

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
from .coordinator import HBXControlsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = ()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: HBXControlsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
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
                        HBXControlsBinarySensor(
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

            # Create per-zone demand binary sensors for ZON controllers.
            dtype = (device_parameters.get("device_type") or device.get("deviceType") or "").upper()
            if dtype == DEVICE_TYPE_ZON:
                relays = device_parameters.get("relays") or []
                relay_types = device_parameters.get("relay_types") or []
                # Best-effort: only create entities for slots that look
                # configured. Relay slots with relay_type == 0 are presumed
                # disabled / unwired; if relay_types is missing entirely,
                # fall back to all 16 slots so we don't silently skip
                # everything on devices that don't report the array.
                for idx in range(len(relays)):
                    rtype = relay_types[idx] if idx < len(relay_types) else None
                    if rtype is not None and rtype == 0:
                        continue
                    entities.append(
                        ZonRelayDemandBinarySensor(
                            coordinator,
                            device_id,
                            device,
                            idx,
                        )
                    )
    else:
        _LOGGER.debug("No coordinator data or devices found")
    
    _LOGGER.debug("Adding %d binary sensor entities", len(entities))
    async_add_entities(entities)


class HBXControlsBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Implementation of an HBX Controls binary sensor."""

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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
        coordinator: HBXControlsDataUpdateCoordinator,
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
            "manufacturer": "HBX Controls",
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


class ZonRelayDemandBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """
    Per-zone demand binary sensor for a ZON zone controller.

    Reads the boolean state of one slot in the ZON's ``relays`` array. A
    relay turning on reflects the controller energizing that zone's
    pump/valve in response to a thermostat demand.

    Slots are 0-indexed internally; entity names are 1-indexed for
    user-friendliness ("Zone 1" through "Zone 16").
    """

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:pipe-valve"

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        index: int,
    ) -> None:
        """Initialize the ZON relay demand binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._index = index

        self._attr_unique_id = f"{device_id}_zon_relay_{index}"
        self._attr_name = f"{device.get('name', device_id)} Zone {index + 1}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    def _relays(self) -> list[bool]:
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return []
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return []
        return device.get("parameters", {}).get("relays") or []

    @property
    def is_on(self) -> bool | None:
        """Return whether this zone's relay is currently energized."""
        relays = self._relays()
        if self._index >= len(relays):
            return None
        return bool(relays[self._index])

    @property
    def available(self) -> bool:
        """Available while the coordinator reports a relay slot for this index."""
        if not self.coordinator.last_update_success:
            return False
        return self._index < len(self._relays())
