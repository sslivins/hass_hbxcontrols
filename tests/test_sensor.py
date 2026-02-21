"""Tests for the HBX Controls sensor platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.sensor import (
    SENSOR_DESCRIPTIONS,
    BackupRuntimeSensor,
    HBXControlsSensor,
    HeatPumpStageRuntimeSensor,
    async_setup_entry,
)

from .conftest import (
    MOCK_BUILDING_ID,
    MOCK_DEVICE_ID,
    make_coordinator_data,
    make_device,
    make_full_parameters,
)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def test_setup_creates_all_sensors(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that sensor entities are created for a fully-populated device."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    # 5 SENSOR_DESCRIPTIONS (tank temp, target temp, outdoor temp, firmware, device type)
    # + 2 heat pump stage runtime sensors
    # + 1 backup runtime sensor
    assert len(entities) == 8


async def test_setup_no_data(
    hass: HomeAssistant, mock_coordinator_no_data, mock_config_entry
):
    """Test no sensor entities when coordinator has no data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator_no_data

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


async def test_setup_no_heatpump_stages(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test setup with device that has no heat pump stages."""
    params = make_full_parameters(heatpump_stages=[], backup_state=None)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    # Only the 5 basic SENSOR_DESCRIPTIONS
    assert len(entities) == 5


# ---------------------------------------------------------------------------
# HBXControlsSensor (description-based sensors)
# ---------------------------------------------------------------------------


def _make_sensor(coordinator, description, device_id=MOCK_DEVICE_ID, device=None):
    """Create an HBXControlsSensor for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return HBXControlsSensor(coordinator, description, device_id, device)


async def test_tank_temperature_value(hass: HomeAssistant, mock_coordinator):
    """Test tank temperature sensor returns correct value."""
    desc = SENSOR_DESCRIPTIONS[0]  # temperature_tank
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.native_value == 120.0


async def test_target_temperature_value(hass: HomeAssistant, mock_coordinator):
    """Test target temperature sensor returns correct value."""
    desc = SENSOR_DESCRIPTIONS[1]  # target_temperature_tank
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.native_value == 125.0


async def test_outdoor_temperature_value(hass: HomeAssistant, mock_coordinator):
    """Test outdoor temperature sensor returns correct value."""
    desc = SENSOR_DESCRIPTIONS[2]  # temperature_outdoor
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.native_value == 35.0


async def test_firmware_version_value(hass: HomeAssistant, mock_coordinator):
    """Test firmware version sensor returns correct value."""
    desc = SENSOR_DESCRIPTIONS[3]  # firmware_version
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.native_value == "1.2.3"


async def test_device_type_value(hass: HomeAssistant, mock_coordinator):
    """Test device type sensor returns correct value."""
    desc = SENSOR_DESCRIPTIONS[4]  # device_type
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.native_value == "ECO"


async def test_sensor_value_no_data(hass: HomeAssistant, mock_coordinator):
    """Test sensor returns None when coordinator has no data."""
    mock_coordinator.data = None
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.native_value is None


async def test_sensor_value_device_missing(
    hass: HomeAssistant, mock_coordinator
):
    """Test sensor returns None when device is missing from data."""
    mock_coordinator.data = make_coordinator_data(devices={})
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.native_value is None


# ---------------------------------------------------------------------------
# Sensor unique IDs and metadata
# ---------------------------------------------------------------------------


async def test_sensor_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique ID follows pattern device_id_key."""
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_temperature_tank"


async def test_sensor_name(hass: HomeAssistant, mock_coordinator):
    """Test sensor name includes device name and description name."""
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    assert "Test ECO" in entity.name
    assert "Tank Temperature" in entity.name


async def test_sensor_device_info(hass: HomeAssistant, mock_coordinator):
    """Test sensor device info."""
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    info = entity.device_info
    assert (DOMAIN, MOCK_DEVICE_ID) in info["identifiers"]
    assert info["manufacturer"] == "HBX Controls"


# ---------------------------------------------------------------------------
# Sensor availability
# ---------------------------------------------------------------------------


async def test_sensor_available(hass: HomeAssistant, mock_coordinator):
    """Test sensor available when coordinator data exists."""
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.available is True


async def test_sensor_unavailable_no_data(
    hass: HomeAssistant, mock_coordinator
):
    """Test sensor unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.available is False


async def test_sensor_unavailable_device_missing(
    hass: HomeAssistant, mock_coordinator
):
    """Test sensor unavailable when device is not in coordinator data."""
    mock_coordinator.data = make_coordinator_data(devices={})
    desc = SENSOR_DESCRIPTIONS[0]
    entity = _make_sensor(mock_coordinator, desc)
    assert entity.available is False


# ---------------------------------------------------------------------------
# HeatPumpStageRuntimeSensor
# ---------------------------------------------------------------------------


def _make_hp_runtime(coordinator, stage_title="Stage 1", device_id=MOCK_DEVICE_ID, device=None):
    """Create a HeatPumpStageRuntimeSensor for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return HeatPumpStageRuntimeSensor(coordinator, device_id, device, stage_title)


async def test_hp_runtime_value(hass: HomeAssistant, mock_coordinator):
    """Test heat pump stage runtime returns the runTime string."""
    entity = _make_hp_runtime(mock_coordinator, "Stage 1")
    assert entity.native_value == "100:05:30"


async def test_hp_runtime_stage2(hass: HomeAssistant, mock_coordinator):
    """Test runtime for stage 2."""
    entity = _make_hp_runtime(mock_coordinator, "Stage 2")
    assert entity.native_value == "50:10:00"


async def test_hp_runtime_missing_stage(hass: HomeAssistant, mock_coordinator):
    """Test runtime returns None for non-existent stage."""
    entity = _make_hp_runtime(mock_coordinator, "Stage 99")
    assert entity.native_value is None


async def test_hp_runtime_no_data(hass: HomeAssistant, mock_coordinator):
    """Test runtime returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_hp_runtime(mock_coordinator, "Stage 1")
    assert entity.native_value is None


async def test_hp_runtime_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique ID for heat pump runtime sensor."""
    entity = _make_hp_runtime(mock_coordinator, "Stage 1")
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_hp_stage_1_runtime"


async def test_hp_runtime_available(hass: HomeAssistant, mock_coordinator):
    """Test availability when stage exists."""
    entity = _make_hp_runtime(mock_coordinator, "Stage 1")
    assert entity.available is True


async def test_hp_runtime_unavailable_missing_stage(
    hass: HomeAssistant, mock_coordinator
):
    """Test unavailable when stage no longer exists."""
    entity = _make_hp_runtime(mock_coordinator, "Stage 99")
    assert entity.available is False


async def test_hp_runtime_unavailable_no_data(
    hass: HomeAssistant, mock_coordinator
):
    """Test unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    entity = _make_hp_runtime(mock_coordinator, "Stage 1")
    assert entity.available is False


# ---------------------------------------------------------------------------
# BackupRuntimeSensor
# ---------------------------------------------------------------------------


def _make_backup_runtime(coordinator, backup_title="Backup", device_id=MOCK_DEVICE_ID, device=None):
    """Create a BackupRuntimeSensor for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return BackupRuntimeSensor(coordinator, device_id, device, backup_title)


async def test_backup_runtime_value(hass: HomeAssistant, mock_coordinator):
    """Test backup runtime returns the runTime string."""
    entity = _make_backup_runtime(mock_coordinator)
    assert entity.native_value == "10:00:00"


async def test_backup_runtime_no_backup_state(
    hass: HomeAssistant, mock_coordinator
):
    """Test backup runtime returns None when backup_state is missing."""
    params = make_full_parameters(backup_state=None)
    # Need to include backup_state key but set it to None
    params["backup_state"] = None
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_backup_runtime(mock_coordinator)
    assert entity.native_value is None


async def test_backup_runtime_no_data(hass: HomeAssistant, mock_coordinator):
    """Test backup runtime returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_backup_runtime(mock_coordinator)
    assert entity.native_value is None


async def test_backup_runtime_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique ID for backup runtime sensor."""
    entity = _make_backup_runtime(mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_backup_runtime"


async def test_backup_runtime_available(hass: HomeAssistant, mock_coordinator):
    """Test availability when backup_state exists."""
    entity = _make_backup_runtime(mock_coordinator)
    assert entity.available is True


async def test_backup_runtime_unavailable_no_backup(
    hass: HomeAssistant, mock_coordinator
):
    """Test unavailable when backup_state is None."""
    params = make_full_parameters()
    params["backup_state"] = None
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_backup_runtime(mock_coordinator)
    assert entity.available is False
