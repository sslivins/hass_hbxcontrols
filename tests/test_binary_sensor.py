"""Tests for the HBX Controls binary sensor platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.binary_sensor import (
    BackupBinarySensor,
    HeatPumpStageBinarySensor,
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


async def test_setup_creates_binary_sensors(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that binary sensor entities are created for a fully-populated device."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    # 2 heat pump stage running sensors + 1 backup running sensor = 3
    assert len(entities) == 3


async def test_setup_no_data(
    hass: HomeAssistant, mock_coordinator_no_data, mock_config_entry
):
    """Test no binary sensor entities when coordinator has no data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator_no_data

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


async def test_setup_no_stages_no_backup(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test no binary sensors created when no stages or backup."""
    params = make_full_parameters(heatpump_stages=[], backup_state=None)
    # Must explicitly remove backup_state to avoid it being included
    params["backup_state"] = None
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    # No stages + backup_state is falsy (None) = 0 sensors
    assert len(entities) == 0


# ---------------------------------------------------------------------------
# HeatPumpStageBinarySensor
# ---------------------------------------------------------------------------


def _make_hp_binary(
    coordinator,
    stage_title="Stage 1",
    sensor_type="running",
    data_key="activated",
    name_suffix="Running",
    device_id=MOCK_DEVICE_ID,
    device=None,
):
    """Create a HeatPumpStageBinarySensor for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return HeatPumpStageBinarySensor(
        coordinator, device_id, device, stage_title, sensor_type, data_key, name_suffix
    )


async def test_hp_stage_is_on_activated(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns True when stage is activated."""
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    assert entity.is_on is True


async def test_hp_stage_is_off(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False when stage is not activated."""
    entity = _make_hp_binary(mock_coordinator, "Stage 2")
    assert entity.is_on is False


async def test_hp_stage_missing_returns_none(
    hass: HomeAssistant, mock_coordinator
):
    """Test is_on returns None when stage is not found."""
    entity = _make_hp_binary(mock_coordinator, "Stage 99")
    assert entity.is_on is None


async def test_hp_stage_no_data(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    assert entity.is_on is None


async def test_hp_stage_device_missing(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns None when device not in data."""
    mock_coordinator.data = make_coordinator_data(devices={})
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    assert entity.is_on is None


# ---------------------------------------------------------------------------
# HeatPumpStageBinarySensor metadata
# ---------------------------------------------------------------------------


async def test_hp_stage_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique ID follows pattern."""
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_hp_stage_1_running"


async def test_hp_stage_name(hass: HomeAssistant, mock_coordinator):
    """Test entity name includes device name, stage, and suffix."""
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    assert "Test ECO" in entity.name
    assert "Stage 1" in entity.name
    assert "Running" in entity.name


async def test_hp_stage_device_info(hass: HomeAssistant, mock_coordinator):
    """Test device info for HP stage binary sensor."""
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    info = entity.device_info
    assert (DOMAIN, MOCK_DEVICE_ID) in info["identifiers"]


# ---------------------------------------------------------------------------
# HeatPumpStageBinarySensor availability
# ---------------------------------------------------------------------------


async def test_hp_stage_available(hass: HomeAssistant, mock_coordinator):
    """Test HP stage available when stage exists in data."""
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    assert entity.available is True


async def test_hp_stage_unavailable_missing_stage(
    hass: HomeAssistant, mock_coordinator
):
    """Test HP stage unavailable when stage no longer exists."""
    entity = _make_hp_binary(mock_coordinator, "Stage 99")
    assert entity.available is False


async def test_hp_stage_unavailable_no_data(
    hass: HomeAssistant, mock_coordinator
):
    """Test HP stage unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    entity = _make_hp_binary(mock_coordinator, "Stage 1")
    assert entity.available is False


# ---------------------------------------------------------------------------
# BackupBinarySensor
# ---------------------------------------------------------------------------


def _make_backup_binary(
    coordinator,
    backup_title="Backup",
    sensor_type="running",
    data_key="activated",
    name_suffix="Running",
    device_id=MOCK_DEVICE_ID,
    device=None,
):
    """Create a BackupBinarySensor for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return BackupBinarySensor(
        coordinator, device_id, device, backup_title, sensor_type, data_key, name_suffix
    )


async def test_backup_is_off(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False when backup is not activated."""
    entity = _make_backup_binary(mock_coordinator)
    assert entity.is_on is False


async def test_backup_is_on(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns True when backup is activated."""
    params = make_full_parameters(
        backup_state={"title": "Backup", "activated": True, "runTime": "10:00:00"}
    )
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_backup_binary(mock_coordinator)
    assert entity.is_on is True


async def test_backup_no_backup_state(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns None when backup_state is missing."""
    params = make_full_parameters()
    params["backup_state"] = None
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_backup_binary(mock_coordinator)
    assert entity.is_on is None


async def test_backup_no_data(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_backup_binary(mock_coordinator)
    assert entity.is_on is None


# ---------------------------------------------------------------------------
# BackupBinarySensor metadata
# ---------------------------------------------------------------------------


async def test_backup_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique ID for backup binary sensor."""
    entity = _make_backup_binary(mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_backup_running"


async def test_backup_name(hass: HomeAssistant, mock_coordinator):
    """Test backup binary sensor name."""
    entity = _make_backup_binary(mock_coordinator)
    assert "Test ECO" in entity.name
    assert "Backup" in entity.name
    assert "Running" in entity.name


# ---------------------------------------------------------------------------
# BackupBinarySensor availability
# ---------------------------------------------------------------------------


async def test_backup_available(hass: HomeAssistant, mock_coordinator):
    """Test backup available when backup_state exists."""
    entity = _make_backup_binary(mock_coordinator)
    assert entity.available is True


async def test_backup_unavailable_no_backup_state(
    hass: HomeAssistant, mock_coordinator
):
    """Test backup unavailable when backup_state is None."""
    params = make_full_parameters()
    params["backup_state"] = None
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_backup_binary(mock_coordinator)
    assert entity.available is False


async def test_backup_unavailable_no_data(
    hass: HomeAssistant, mock_coordinator
):
    """Test backup unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    entity = _make_backup_binary(mock_coordinator)
    assert entity.available is False
