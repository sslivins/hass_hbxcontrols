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
from homeassistant.helpers import entity_registry as er
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
                # ``relay_types`` (HBX ``relType``) is the authoritative
                # zone-count signal: its length tells us how many zone
                # slots this physical ZON exposes (4 on a ZON-0224, 8 on
                # ZON-08xx, etc.) and a value of 0 marks a slot as unwired.
                # ``relays`` (HBX ``relays``) is always 16 entries on the
                # wire — a superset that includes things beyond zones —
                # so iterating over it produced phantom "Zone 5..16"
                # sensors on a 4-zone box (issue #12).
                #
                # Strategy: trust ``relay_types`` length when present and
                # skip slots where ``relay_types[i] == 0``. Only fall back
                # to ``len(relays)`` when ``relay_types`` is missing
                # entirely so devices that don't report it still get
                # something rather than nothing.
                if relay_types:
                    zone_count = len(relay_types)
                else:
                    zone_count = len(relays)
                # The HBX mobile app numbers zones by absolute wired
                # position across stacked ZON controllers, not by local
                # slot. A Secondary controller at sequence=1 occupies
                # zones 5-8, so its first three wired slots show up as
                # Zone 5/6/7 in the app. We mirror that for parity:
                # zone_number = sequence_value * 4 + idx + 1.
                # Default to 0 (Primary, zones 1-4) when the field is
                # missing so legacy fixtures keep their existing names.
                sequence_value = device_parameters.get("zone_sequence", 0) or 0
                for idx in range(zone_count):
                    if relay_types and relay_types[idx] == 0:
                        continue
                    entities.append(
                        ZonRelayDemandBinarySensor(
                            coordinator,
                            device_id,
                            device,
                            idx,
                            sequence_value,
                        )
                    )
    else:
        _LOGGER.debug("No coordinator data or devices found")

    _purge_stale_zon_zone_entities(hass, config_entry, entities)

    _LOGGER.debug("Adding %d binary sensor entities", len(entities))
    async_add_entities(entities)


def _purge_stale_zon_zone_entities(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    active_entities: list,
) -> None:
    """
    Remove ZON zone-relay entries left behind in the entity registry.

    Earlier integration versions (<= 2.5.0b4) created up to 16 binary
    sensors per ZON controller regardless of how many slots were
    actually wired. After issue #12 we trust ``relType`` to bound the
    list, but the registry persists everything created in the past —
    so users upgrading from a pre-b5 install see zones 5-16 lingering
    as "unavailable" forever.

    On every setup we walk the entity registry, scope to the entries
    this config entry owns, and remove any ``<device>_zon_relay_<n>``
    unique_id that is *not* in the active set the platform just built.

    Strict scope: only ``_zon_relay_<n>`` is touched. Other binary
    sensors (running flags, future per-device entities) are untouched.
    """
    try:
        registry = er.async_get(hass)
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Entity registry not available for cleanup: %s", exc)
        return

    active_uids = {
        getattr(e, "_attr_unique_id", None)
        for e in active_entities
        if isinstance(e, ZonRelayDemandBinarySensor)
    }

    try:
        entries = er.async_entries_for_config_entry(
            registry, config_entry.entry_id
        )
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Failed to enumerate registry entries: %s", exc)
        return

    for entry in entries:
        uid = entry.unique_id or ""
        # Match any device's "<device_id>_zon_relay_<n>" pattern.
        if "_zon_relay_" not in uid:
            continue
        if uid in active_uids:
            continue
        _LOGGER.info(
            "Removing stale ZON zone entity %s (unique_id=%s) — "
            "no longer reported by the controller",
            entry.entity_id,
            uid,
        )
        try:
            registry.async_remove(entry.entity_id)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Failed to remove %s: %s", entry.entity_id, exc)


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
    user-friendliness and offset by the controller's sequence value
    so stacked installs match the HBX app numbering. A Secondary
    controller at sequence=1 with relays at idx 0/1/2 produces
    "Zone 5/6/7" — same as what the mobile app shows for the physical
    wiring (see issue #12 hbxtesting3.docx).

    The unique_id stays raw-index ``<device>_zon_relay_<idx>`` so the
    entity registry survives an installer relabelling a controller's
    sequence; only the friendly name reflects the offset.
    """

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:pipe-valve"

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
        index: int,
        sequence_value: int = 0,
    ) -> None:
        """Initialize the ZON relay demand binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._index = index
        self._sequence_value = int(sequence_value or 0)

        zone_number = self._sequence_value * 4 + index + 1
        self._attr_unique_id = f"{device_id}_zon_relay_{index}"
        self._attr_name = f"{device.get('name', device_id)} Zone {zone_number}"

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
