"""Tests for the HBX Controls coordinator."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.hbx_controls.coordinator import HBXControlsDataUpdateCoordinator

from .conftest import (
    MOCK_BUILDING_ID,
    MOCK_DEVICE_ID,
    MOCK_PASSWORD,
    MOCK_USERNAME,
    make_config_entry_data,
)


# ---------------------------------------------------------------------------
# Helper to build a mock SensorlinxDevice + Sensorlinx
# ---------------------------------------------------------------------------


def _make_mock_sensorlinx(
    profile: dict | None = None,
    buildings: list[dict] | None = None,
    devices: list[dict] | None = None,
):
    """Return a mocked Sensorlinx object for coordinator tests."""
    mock = AsyncMock()
    mock.login = AsyncMock()
    mock.get_profile = AsyncMock(
        return_value=profile if profile is not None else {"username": MOCK_USERNAME}
    )
    mock.get_buildings = AsyncMock(
        return_value=buildings if buildings is not None
        else [{"id": MOCK_BUILDING_ID, "name": "Test Building"}]
    )
    mock.get_devices = AsyncMock(
        return_value=devices if devices is not None
        else [
            {
                "id": MOCK_DEVICE_ID,
                "syncCode": MOCK_DEVICE_ID,
                "name": "Test ECO",
                "deviceType": "ECO",
            }
        ]
    )
    mock.close = AsyncMock()
    return mock


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


async def test_coordinator_init(hass: HomeAssistant, mock_config_entry):
    """Test coordinator initializes with correct scan interval."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    assert coordinator.update_interval.total_seconds() == 300


async def test_coordinator_custom_scan_interval(hass: HomeAssistant):
    """Test coordinator respects custom scan interval from config."""
    entry = MagicMock()
    entry.data = make_config_entry_data(scan_interval=120)
    entry.options = {}

    coordinator = HBXControlsDataUpdateCoordinator(hass, entry)
    assert coordinator.update_interval.total_seconds() == 120


# ---------------------------------------------------------------------------
# _async_update_data tests
# ---------------------------------------------------------------------------


async def test_update_data_success(hass: HomeAssistant, mock_config_entry):
    """Test a successful data update returns profile, buildings, and devices."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    mock_sl = _make_mock_sensorlinx()
    coordinator.sensorlinx = mock_sl

    # Mock SensorlinxDevice to return minimal parameter data
    mock_device_helper = AsyncMock()
    mock_device_helper.get_temperatures = AsyncMock(return_value={})
    mock_device_helper.get_permanent_heat_demand = AsyncMock(return_value=False)
    mock_device_helper.get_permanent_cool_demand = AsyncMock(return_value=False)
    mock_device_helper.get_hvac_mode_priority = AsyncMock(return_value=0)
    mock_device_helper.get_hot_tank_min_temp = AsyncMock(return_value=100.0)
    mock_device_helper.get_hot_tank_max_temp = AsyncMock(return_value=140.0)
    mock_device_helper.get_hot_tank_outdoor_reset = AsyncMock(return_value="off")
    mock_device_helper.get_cold_tank_min_temp = AsyncMock(return_value=40.0)
    mock_device_helper.get_cold_tank_max_temp = AsyncMock(return_value=55.0)
    mock_device_helper.get_cold_tank_outdoor_reset = AsyncMock(return_value="off")
    mock_device_helper.get_firmware_version = AsyncMock(return_value="1.0")
    mock_device_helper.get_device_type = AsyncMock(return_value="ECO")
    mock_device_helper.get_warm_weather_shutdown = AsyncMock(return_value="off")
    mock_device_helper.get_cold_weather_shutdown = AsyncMock(return_value="off")
    mock_device_helper.get_heatpump_stages_state = AsyncMock(return_value=[])
    mock_device_helper.get_backup_state = AsyncMock(return_value=None)
    mock_device_helper.get_stage_on_lag_time = AsyncMock(return_value=10)
    mock_device_helper.get_stage_off_lag_time = AsyncMock(return_value=30)
    mock_device_helper.get_rotate_cycles = AsyncMock(return_value="off")
    mock_device_helper.get_rotate_time = AsyncMock(return_value="off")
    mock_device_helper.get_off_staging = AsyncMock(return_value=False)
    mock_device_helper.get_backup_lag_time = AsyncMock(return_value="off")
    mock_device_helper.get_backup_differential = AsyncMock(return_value="off")
    mock_device_helper.get_hot_tank_differential = AsyncMock(return_value=4.0)
    mock_device_helper.get_cold_tank_differential = AsyncMock(return_value=4.0)
    mock_device_helper.get_backup_only_outdoor_temp = AsyncMock(return_value="off")
    mock_device_helper.get_number_of_stages = AsyncMock(return_value=2)
    mock_device_helper.get_backup_temp = AsyncMock(return_value="off")
    mock_device_helper.get_wide_priority_differential = AsyncMock(return_value="off")
    mock_device_helper.get_weather_shutdown_lag_time = AsyncMock(return_value=0)
    mock_device_helper.get_two_stage_heat_pump = AsyncMock(return_value=False)
    mock_device_helper.get_heat_cool_switch_delay = AsyncMock(return_value=60)
    mock_device_helper.get_backup_only_tank_temp = AsyncMock(return_value="off")

    with patch(
        "pysensorlinx.sensorlinx.SensorlinxDevice",
        return_value=mock_device_helper,
    ):
        result = await coordinator._async_update_data()

    assert "profile" in result
    assert "buildings" in result
    assert "devices" in result
    assert MOCK_DEVICE_ID in result["devices"]
    assert "parameters" in result["devices"][MOCK_DEVICE_ID]

    mock_sl.login.assert_called_once_with(MOCK_USERNAME, MOCK_PASSWORD)
    mock_sl.get_profile.assert_called_once()
    mock_sl.get_buildings.assert_called_once()


async def test_update_data_auth_failed(hass: HomeAssistant, mock_config_entry):
    """Test ConfigEntryAuthFailed is raised when profile is None."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    mock_sl = _make_mock_sensorlinx(profile=None)
    mock_sl.get_profile = AsyncMock(return_value=None)
    coordinator.sensorlinx = mock_sl

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_update_data_api_error(hass: HomeAssistant, mock_config_entry):
    """Test UpdateFailed is raised on API errors."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    mock_sl = _make_mock_sensorlinx()
    mock_sl.login = AsyncMock(side_effect=Exception("Connection refused"))
    coordinator.sensorlinx = mock_sl

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_update_data_no_buildings(hass: HomeAssistant, mock_config_entry):
    """Test update succeeds with no buildings (empty device list)."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    mock_sl = _make_mock_sensorlinx(buildings=[])
    coordinator.sensorlinx = mock_sl

    result = await coordinator._async_update_data()

    assert result["devices"] == {}
    assert result["buildings"] == []


async def test_update_data_no_devices_in_building(hass: HomeAssistant, mock_config_entry):
    """Test update handles buildings with no devices."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    mock_sl = _make_mock_sensorlinx(devices=[])
    mock_sl.get_devices = AsyncMock(return_value=[])
    coordinator.sensorlinx = mock_sl

    result = await coordinator._async_update_data()

    assert result["devices"] == {}


async def test_coordinator_shutdown(hass: HomeAssistant, mock_config_entry):
    """Test shutdown closes the sensorlinx connection."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    mock_sl = _make_mock_sensorlinx()
    coordinator.sensorlinx = mock_sl

    await coordinator.async_shutdown()

    mock_sl.close.assert_called_once()


async def test_update_data_device_uses_sync_code(hass: HomeAssistant, mock_config_entry):
    """Test that device_id prefers syncCode over id."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    devices = [{"id": "fallback_id", "syncCode": "SYNC123", "name": "Test"}]
    mock_sl = _make_mock_sensorlinx(devices=devices)
    coordinator.sensorlinx = mock_sl

    mock_device_helper = AsyncMock()
    mock_device_helper.get_temperatures = AsyncMock(return_value={})
    # Set all other methods to raise so they're silently skipped
    for attr in dir(mock_device_helper):
        if attr.startswith("get_") and attr != "get_temperatures":
            setattr(mock_device_helper, attr, AsyncMock(side_effect=Exception("skip")))

    with patch(
        "pysensorlinx.sensorlinx.SensorlinxDevice",
        return_value=mock_device_helper,
    ):
        result = await coordinator._async_update_data()

    # syncCode should be used as key
    assert "SYNC123" in result["devices"]
    assert "fallback_id" not in result["devices"]


async def test_update_data_device_falls_back_to_id(hass: HomeAssistant, mock_config_entry):
    """Test that device_id falls back to id when syncCode is missing."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    devices = [{"id": "device_99", "name": "Test"}]
    mock_sl = _make_mock_sensorlinx(devices=devices)
    coordinator.sensorlinx = mock_sl

    mock_device_helper = AsyncMock()
    mock_device_helper.get_temperatures = AsyncMock(return_value={})
    for attr in dir(mock_device_helper):
        if attr.startswith("get_") and attr != "get_temperatures":
            setattr(mock_device_helper, attr, AsyncMock(side_effect=Exception("skip")))

    with patch(
        "pysensorlinx.sensorlinx.SensorlinxDevice",
        return_value=mock_device_helper,
    ):
        result = await coordinator._async_update_data()

    assert "device_99" in result["devices"]
