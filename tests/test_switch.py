"""Tests for the HBX Controls switch platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.switch import (
    HotTankOutdoorResetSwitch,
    ColdTankOutdoorResetSwitch,
    PermanentHeatDemandSwitch,
    PermanentCoolDemandSwitch,
    WarmWeatherShutdownSwitch,
    ColdWeatherShutdownSwitch,
    RotateCyclesSwitch,
    RotateTimeSwitch,
    SynchronizedStageOffSwitch,
    BackupLagTimeSwitch,
    BackupDifferentialSwitch,
    BackupOnlyOutdoorTempSwitch,
    BackupTempSwitch,
    WidePriorityDifferentialSwitch,
    TwoStageHeatPumpSwitch,
    BackupOnlyTankTempSwitch,
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
# Helper
# ---------------------------------------------------------------------------


def _make_switch(cls, coordinator, device_id=MOCK_DEVICE_ID, device=None, building_id=MOCK_BUILDING_ID):
    """Create a switch entity for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return cls(coordinator, device_id, device, building_id)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def test_setup_creates_all_switches(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that all switch entities are created for a fully-populated device."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    # With full parameters we expect 16 switch types
    assert len(entities) == 16


async def test_setup_no_data(
    hass: HomeAssistant, mock_coordinator_no_data, mock_config_entry
):
    """Test no switch entities are created when coordinator has no data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator_no_data

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


async def test_setup_skips_missing_parameters(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test only switches for present parameters are created."""
    params = {"permanent_heat_demand": False, "hvac_mode": "heat"}
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 1
    assert isinstance(entities[0], PermanentHeatDemandSwitch)


# ---------------------------------------------------------------------------
# HotTankOutdoorResetSwitch tests  (off/value pattern)
# ---------------------------------------------------------------------------


async def test_hot_outdoor_reset_is_off_when_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test is_on returns False when hot_tank_outdoor_reset is 'off'."""
    entity = _make_switch(HotTankOutdoorResetSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_hot_outdoor_reset_is_on_when_value(
    hass: HomeAssistant, mock_coordinator
):
    """Test is_on returns True when outdoor reset is not 'off'."""
    params = make_full_parameters(hot_tank_outdoor_reset=MagicMock())
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_switch(HotTankOutdoorResetSwitch, mock_coordinator)
    assert entity.is_on is True


async def test_hot_outdoor_reset_turn_on(
    hass: HomeAssistant, mock_coordinator
):
    """Test turn_on calls set_hot_tank_outdoor_reset with a Temperature."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(HotTankOutdoorResetSwitch, mock_coordinator)

    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_on()

    mock_helper.set_hot_tank_outdoor_reset.assert_called_once()
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_hot_outdoor_reset_turn_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test turn_off calls set_hot_tank_outdoor_reset('off')."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(HotTankOutdoorResetSwitch, mock_coordinator)

    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_off()

    mock_helper.set_hot_tank_outdoor_reset.assert_called_once_with("off")
    mock_coordinator.async_request_refresh.assert_called_once()


# ---------------------------------------------------------------------------
# PermanentHeatDemandSwitch tests  (bool pattern)
# ---------------------------------------------------------------------------


async def test_heat_demand_is_on_true(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns True for permanent_heat_demand=True."""
    params = make_full_parameters(permanent_heat_demand=True)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    assert entity.is_on is True


async def test_heat_demand_is_on_false(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False for permanent_heat_demand=False."""
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_heat_demand_turn_on(hass: HomeAssistant, mock_coordinator):
    """Test turn_on calls set_permanent_hd(True)."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_on()
    mock_helper.set_permanent_hd.assert_called_once_with(True)


async def test_heat_demand_turn_off(hass: HomeAssistant, mock_coordinator):
    """Test turn_off calls set_permanent_hd(False)."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_off()
    mock_helper.set_permanent_hd.assert_called_once_with(False)


# ---------------------------------------------------------------------------
# PermanentCoolDemandSwitch tests
# ---------------------------------------------------------------------------


async def test_cool_demand_is_on(hass: HomeAssistant, mock_coordinator):
    """Test is_on for permanent_cool_demand."""
    params = make_full_parameters(permanent_cool_demand=True)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_switch(PermanentCoolDemandSwitch, mock_coordinator)
    assert entity.is_on is True


async def test_cool_demand_turn_on(hass: HomeAssistant, mock_coordinator):
    """Test turn_on calls set_permanent_cd(True)."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(PermanentCoolDemandSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_on()
    mock_helper.set_permanent_cd.assert_called_once_with(True)


# ---------------------------------------------------------------------------
# WarmWeatherShutdownSwitch tests  (off/Temperature pattern)
# ---------------------------------------------------------------------------


async def test_warm_weather_off(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False when warm_weather_shutdown is 'off'."""
    entity = _make_switch(WarmWeatherShutdownSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_warm_weather_on(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns True when not 'off'."""
    params = make_full_parameters(warm_weather_shutdown=MagicMock())
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_switch(WarmWeatherShutdownSwitch, mock_coordinator)
    assert entity.is_on is True


async def test_warm_weather_turn_on(hass: HomeAssistant, mock_coordinator):
    """Test turn_on sets warm weather shutdown to 88°F."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(WarmWeatherShutdownSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_on()
    mock_helper.set_warm_weather_shutdown.assert_called_once()


async def test_warm_weather_turn_off(hass: HomeAssistant, mock_coordinator):
    """Test turn_off sets warm weather shutdown to 'off'."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(WarmWeatherShutdownSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_off()
    mock_helper.set_warm_weather_shutdown.assert_called_once_with("off")


# ---------------------------------------------------------------------------
# ColdWeatherShutdownSwitch tests
# ---------------------------------------------------------------------------


async def test_cold_weather_off(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False when cold_weather_shutdown is 'off'."""
    entity = _make_switch(ColdWeatherShutdownSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_cold_weather_turn_on(hass: HomeAssistant, mock_coordinator):
    """Test turn_on calls set_cold_weather_shutdown."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(ColdWeatherShutdownSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_on()
    mock_helper.set_cold_weather_shutdown.assert_called_once()


# ---------------------------------------------------------------------------
# SynchronizedStageOffSwitch tests  (bool pattern)
# ---------------------------------------------------------------------------


async def test_sync_stage_off_false(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False when off_staging=False."""
    entity = _make_switch(SynchronizedStageOffSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_sync_stage_off_true(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns True when off_staging=True."""
    params = make_full_parameters(off_staging=True)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_switch(SynchronizedStageOffSwitch, mock_coordinator)
    assert entity.is_on is True


async def test_sync_stage_off_turn_on(hass: HomeAssistant, mock_coordinator):
    """Test turn_on calls set_off_staging(True)."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(SynchronizedStageOffSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_on()
    mock_helper.set_off_staging.assert_called_once_with(True)


async def test_sync_stage_off_turn_off(hass: HomeAssistant, mock_coordinator):
    """Test turn_off calls set_off_staging(False)."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(SynchronizedStageOffSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_off()
    mock_helper.set_off_staging.assert_called_once_with(False)


# ---------------------------------------------------------------------------
# BackupLagTimeSwitch tests  (off/value pattern)
# ---------------------------------------------------------------------------


async def test_backup_lag_off(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False when backup_lag_time is 'off'."""
    entity = _make_switch(BackupLagTimeSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_backup_lag_on(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns True when backup_lag_time has a value."""
    params = make_full_parameters(backup_lag_time=15)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_switch(BackupLagTimeSwitch, mock_coordinator)
    assert entity.is_on is True


# ---------------------------------------------------------------------------
# Availability tests (common pattern)
# ---------------------------------------------------------------------------


async def test_switch_available(hass: HomeAssistant, mock_coordinator):
    """Test switch reports available when coordinator has data."""
    entity = _make_switch(HotTankOutdoorResetSwitch, mock_coordinator)
    assert entity.available is True


async def test_switch_unavailable_no_data(
    hass: HomeAssistant, mock_coordinator
):
    """Test switch reports unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    entity = _make_switch(HotTankOutdoorResetSwitch, mock_coordinator)
    assert entity.available is False


async def test_switch_unavailable_device_missing(
    hass: HomeAssistant, mock_coordinator
):
    """Test switch reports unavailable when device is missing from data."""
    mock_coordinator.data = make_coordinator_data(devices={})
    entity = _make_switch(HotTankOutdoorResetSwitch, mock_coordinator)
    assert entity.available is False


# ---------------------------------------------------------------------------
# is_on with no data
# ---------------------------------------------------------------------------


async def test_is_on_no_data_returns_none(
    hass: HomeAssistant, mock_coordinator
):
    """Test is_on returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    assert entity.is_on is None


async def test_is_on_device_missing_returns_none(
    hass: HomeAssistant, mock_coordinator
):
    """Test is_on returns None when device not in coordinator data."""
    mock_coordinator.data = make_coordinator_data(devices={})
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    assert entity.is_on is None


# ---------------------------------------------------------------------------
# Unique ID / device info
# ---------------------------------------------------------------------------


async def test_switch_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique IDs follow the expected pattern."""
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_permanent_heat_demand"


async def test_switch_device_info(hass: HomeAssistant, mock_coordinator):
    """Test device_info contains correct identifiers."""
    entity = _make_switch(PermanentHeatDemandSwitch, mock_coordinator)
    info = entity.device_info
    assert (DOMAIN, MOCK_DEVICE_ID) in info["identifiers"]


# ---------------------------------------------------------------------------
# ColdTankOutdoorResetSwitch
# ---------------------------------------------------------------------------


async def test_cold_outdoor_reset_off(hass: HomeAssistant, mock_coordinator):
    """Test cold outdoor reset is_on False when 'off'."""
    entity = _make_switch(ColdTankOutdoorResetSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_cold_outdoor_reset_turn_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test turn_off calls set_cold_tank_outdoor_reset('off')."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_switch(ColdTankOutdoorResetSwitch, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_turn_off()
    mock_helper.set_cold_tank_outdoor_reset.assert_called_once_with("off")


# ---------------------------------------------------------------------------
# RotateCyclesSwitch / RotateTimeSwitch  (off/value pattern)
# ---------------------------------------------------------------------------


async def test_rotate_cycles_off(hass: HomeAssistant, mock_coordinator):
    """Test rotate_cycles is_on False when 'off'."""
    entity = _make_switch(RotateCyclesSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_rotate_time_off(hass: HomeAssistant, mock_coordinator):
    """Test rotate_time is_on False when 'off'."""
    entity = _make_switch(RotateTimeSwitch, mock_coordinator)
    assert entity.is_on is False


# ---------------------------------------------------------------------------
# TwoStageHeatPumpSwitch (bool pattern)
# ---------------------------------------------------------------------------


async def test_two_stage_hp_false(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns False when two_stage_heat_pump=False."""
    entity = _make_switch(TwoStageHeatPumpSwitch, mock_coordinator)
    assert entity.is_on is False


async def test_two_stage_hp_true(hass: HomeAssistant, mock_coordinator):
    """Test is_on returns True when two_stage_heat_pump=True."""
    params = make_full_parameters(two_stage_heat_pump=True)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_switch(TwoStageHeatPumpSwitch, mock_coordinator)
    assert entity.is_on is True


# ---------------------------------------------------------------------------
# BackupDifferentialSwitch / BackupOnlyOutdoorTempSwitch / BackupTempSwitch
# WidePriorityDifferentialSwitch / BackupOnlyTankTempSwitch (off/value)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cls,param_key",
    [
        (BackupDifferentialSwitch, "backup_differential"),
        (BackupOnlyOutdoorTempSwitch, "backup_only_outdoor_temp"),
        (BackupTempSwitch, "backup_temp"),
        (WidePriorityDifferentialSwitch, "wide_priority_differential"),
        (BackupOnlyTankTempSwitch, "backup_only_tank_temp"),
    ],
)
async def test_off_value_switches_off(
    hass: HomeAssistant, mock_coordinator, cls, param_key
):
    """Test various off/value pattern switches report is_on=False when 'off'."""
    entity = _make_switch(cls, mock_coordinator)
    assert entity.is_on is False
