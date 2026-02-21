"""Tests for the HBX Controls number platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.number import (
    HotTankTargetTemperature,
    HotTankMinTemperature,
    HotTankMaxTemperature,
    HotTankOutdoorReset,
    ColdTankTargetTemperature,
    ColdTankMinTemperature,
    ColdTankMaxTemperature,
    ColdTankOutdoorReset,
    WarmWeatherShutdown,
    ColdWeatherShutdown,
    StageOnLagTime,
    StageOffLagTime,
    RotateCycles,
    RotateTime,
    BackupLagTime,
    BackupDifferential,
    HotTankDifferential,
    ColdTankDifferential,
    BackupOnlyOutdoorTemp,
    NumberOfStages,
    BackupTemp,
    WeatherShutdownLagTime,
    HeatCoolSwitchDelay,
    BackupOnlyTankTemp,
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


def _make_number(cls, coordinator, device_id=MOCK_DEVICE_ID, device=None, building_id=MOCK_BUILDING_ID):
    """Create a number entity for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return cls(coordinator, device_id, device, building_id)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def test_setup_creates_number_entities(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that number entities are created for a fully-populated device."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    # Full parameters should create 24 number entities
    # (hot target, hot min, hot max, hot outdoor reset,
    #  cold target, cold min, cold max, cold outdoor reset,
    #  warm shutdown, cold shutdown, stage on lag, stage off lag,
    #  rotate cycles, rotate time, backup lag, backup diff,
    #  hot tank diff, cold tank diff, backup only outdoor,
    #  num stages, backup temp, weather shutdown lag, heat/cool switch delay,
    #  backup only tank temp)
    assert len(entities) == 24


async def test_setup_no_data(
    hass: HomeAssistant, mock_coordinator_no_data, mock_config_entry
):
    """Test no number entities are created when coordinator has no data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator_no_data

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


async def test_setup_partial_parameters(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test only entities for present parameters are created."""
    params = {"hot_tank_min_temp": 100.0, "stage_on_lag_time": 10}
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    # hot_tank_min_temp creates HotTankTargetTemperature + HotTankMinTemperature
    # stage_on_lag_time creates StageOnLagTime
    assert len(entities) == 3


# ---------------------------------------------------------------------------
# HotTankTargetTemperature (available when outdoor reset is OFF)
# ---------------------------------------------------------------------------


async def test_hot_target_native_value(hass: HomeAssistant, mock_coordinator):
    """Test native_value reads target_temperature_tank."""
    entity = _make_number(HotTankTargetTemperature, mock_coordinator)
    assert entity.native_value == 125.0


async def test_hot_target_available_when_reset_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test entity is available when outdoor reset is 'off'."""
    entity = _make_number(HotTankTargetTemperature, mock_coordinator)
    assert entity.available is True


async def test_hot_target_unavailable_when_reset_on(
    hass: HomeAssistant, mock_coordinator
):
    """Test entity is unavailable when outdoor reset is enabled."""
    params = make_full_parameters(hot_tank_outdoor_reset=MagicMock())
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_number(HotTankTargetTemperature, mock_coordinator)
    assert entity.available is False


async def test_hot_target_set_value(hass: HomeAssistant, mock_coordinator):
    """Test setting target temp calls both min and max."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_number(HotTankTargetTemperature, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.number.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_set_native_value(130.0)

    mock_helper.set_hot_tank_min_temp.assert_called_once()
    mock_helper.set_hot_tank_max_temp.assert_called_once()
    mock_coordinator.async_request_refresh.assert_called_once()


# ---------------------------------------------------------------------------
# HotTankMinTemperature (available when outdoor reset is ON)
# ---------------------------------------------------------------------------


async def test_hot_min_native_value(hass: HomeAssistant, mock_coordinator):
    """Test native_value reads hot_tank_min_temp."""
    entity = _make_number(HotTankMinTemperature, mock_coordinator)
    assert entity.native_value == 100.0


async def test_hot_min_available_when_reset_on(
    hass: HomeAssistant, mock_coordinator
):
    """Test entity is available when outdoor reset is enabled."""
    params = make_full_parameters(hot_tank_outdoor_reset=MagicMock())
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_number(HotTankMinTemperature, mock_coordinator)
    assert entity.available is True


async def test_hot_min_unavailable_when_reset_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test entity is unavailable when outdoor reset is 'off'."""
    entity = _make_number(HotTankMinTemperature, mock_coordinator)
    assert entity.available is False


async def test_hot_min_set_value(hass: HomeAssistant, mock_coordinator):
    """Test setting min temp calls set_hot_tank_min_temp."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_number(HotTankMinTemperature, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.number.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_set_native_value(95.0)
    mock_helper.set_hot_tank_min_temp.assert_called_once()
    mock_coordinator.async_request_refresh.assert_called_once()


# ---------------------------------------------------------------------------
# HotTankMaxTemperature
# ---------------------------------------------------------------------------


async def test_hot_max_native_value(hass: HomeAssistant, mock_coordinator):
    """Test native_value reads hot_tank_max_temp."""
    entity = _make_number(HotTankMaxTemperature, mock_coordinator)
    assert entity.native_value == 140.0


async def test_hot_max_set_value(hass: HomeAssistant, mock_coordinator):
    """Test setting max temp calls set_hot_tank_max_temp."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_number(HotTankMaxTemperature, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.number.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_set_native_value(145.0)
    mock_helper.set_hot_tank_max_temp.assert_called_once()


# ---------------------------------------------------------------------------
# HotTankOutdoorReset (Temperature value)
# ---------------------------------------------------------------------------


async def test_hot_outdoor_reset_value_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test native_value returns None when outdoor reset is 'off'."""
    entity = _make_number(HotTankOutdoorReset, mock_coordinator)
    assert entity.native_value is None


async def test_hot_outdoor_reset_available_when_on(
    hass: HomeAssistant, mock_coordinator
):
    """Test entity is available when outdoor reset is enabled."""
    params = make_full_parameters(hot_tank_outdoor_reset=MagicMock(value=0))
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_number(HotTankOutdoorReset, mock_coordinator)
    assert entity.available is True


# ---------------------------------------------------------------------------
# ColdTankTargetTemperature
# ---------------------------------------------------------------------------


async def test_cold_target_native_value(hass: HomeAssistant, mock_coordinator):
    """Test cold tank target reads cold_tank_min_temp."""
    entity = _make_number(ColdTankTargetTemperature, mock_coordinator)
    # ColdTankTargetTemperature reads cold_tank_min_temp
    assert entity.native_value == 40.0


# ---------------------------------------------------------------------------
# NumberOfStages (always available, integer)
# ---------------------------------------------------------------------------


async def test_num_stages_native_value(hass: HomeAssistant, mock_coordinator):
    """Test NumberOfStages returns integer value."""
    entity = _make_number(NumberOfStages, mock_coordinator)
    assert entity.native_value == 2


async def test_num_stages_default_when_none(
    hass: HomeAssistant, mock_coordinator
):
    """Test NumberOfStages defaults to 1 when parameter is None."""
    params = make_full_parameters()
    params["number_of_stages"] = None
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_number(NumberOfStages, mock_coordinator)
    assert entity.native_value == 1


async def test_num_stages_available(hass: HomeAssistant, mock_coordinator):
    """Test availability check requires parameter presence."""
    entity = _make_number(NumberOfStages, mock_coordinator)
    assert entity.available is True


async def test_num_stages_set_value(hass: HomeAssistant, mock_coordinator):
    """Test set_native_value calls set_number_of_stages."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_number(NumberOfStages, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.number.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_set_native_value(3.0)
    mock_helper.set_number_of_stages.assert_called_once_with(3)


# ---------------------------------------------------------------------------
# StageOnLagTime / StageOffLagTime (always available, minutes)
# ---------------------------------------------------------------------------


async def test_stage_on_lag_native_value(hass: HomeAssistant, mock_coordinator):
    """Test StageOnLagTime reads stage_on_lag_time."""
    entity = _make_number(StageOnLagTime, mock_coordinator)
    assert entity.native_value == 10


async def test_stage_off_lag_native_value(hass: HomeAssistant, mock_coordinator):
    """Test StageOffLagTime reads stage_off_lag_time."""
    entity = _make_number(StageOffLagTime, mock_coordinator)
    assert entity.native_value == 30


async def test_stage_on_lag_set_value(hass: HomeAssistant, mock_coordinator):
    """Test setting stage on lag time."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_number(StageOnLagTime, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.number.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_set_native_value(15.0)
    mock_helper.set_stage_on_lag_time.assert_called_once_with(15)


# ---------------------------------------------------------------------------
# RotateCycles (available only when enabled / not "off")
# ---------------------------------------------------------------------------


async def test_rotate_cycles_value_when_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test RotateCycles returns None when parameter is 'off'."""
    entity = _make_number(RotateCycles, mock_coordinator)
    assert entity.native_value is None


async def test_rotate_cycles_value_when_on(
    hass: HomeAssistant, mock_coordinator
):
    """Test RotateCycles returns integer value when enabled."""
    params = make_full_parameters(rotate_cycles=5)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_number(RotateCycles, mock_coordinator)
    assert entity.native_value == 5


async def test_rotate_cycles_unavailable_when_off(
    hass: HomeAssistant, mock_coordinator
):
    """Test RotateCycles is unavailable when 'off'."""
    entity = _make_number(RotateCycles, mock_coordinator)
    assert entity.available is False


async def test_rotate_cycles_available_when_on(
    hass: HomeAssistant, mock_coordinator
):
    """Test RotateCycles is available when not 'off'."""
    params = make_full_parameters(rotate_cycles=5)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_number(RotateCycles, mock_coordinator)
    assert entity.available is True


async def test_rotate_cycles_set_value(hass: HomeAssistant, mock_coordinator):
    """Test setting rotate cycles."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_number(RotateCycles, mock_coordinator)
    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.number.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_set_native_value(10.0)
    mock_helper.set_rotate_cycles.assert_called_once_with(10)


# ---------------------------------------------------------------------------
# HotTankDifferential / ColdTankDifferential
# ---------------------------------------------------------------------------


async def test_hot_tank_differential_value(
    hass: HomeAssistant, mock_coordinator
):
    """Test hot tank differential reads correct parameter."""
    entity = _make_number(HotTankDifferential, mock_coordinator)
    assert entity.native_value == 4.0


async def test_cold_tank_differential_value(
    hass: HomeAssistant, mock_coordinator
):
    """Test cold tank differential reads correct parameter."""
    entity = _make_number(ColdTankDifferential, mock_coordinator)
    assert entity.native_value == 4.0


# ---------------------------------------------------------------------------
# WeatherShutdownLagTime / HeatCoolSwitchDelay
# ---------------------------------------------------------------------------


async def test_weather_shutdown_lag_value(
    hass: HomeAssistant, mock_coordinator
):
    """Test WeatherShutdownLagTime reads correct parameter."""
    entity = _make_number(WeatherShutdownLagTime, mock_coordinator)
    assert entity.native_value == 0


async def test_heat_cool_switch_delay_value(
    hass: HomeAssistant, mock_coordinator
):
    """Test HeatCoolSwitchDelay reads correct parameter."""
    entity = _make_number(HeatCoolSwitchDelay, mock_coordinator)
    assert entity.native_value == 60


# ---------------------------------------------------------------------------
# Common: no data returns None
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cls",
    [
        HotTankTargetTemperature,
        HotTankMinTemperature,
        NumberOfStages,
        StageOnLagTime,
        RotateCycles,
        HotTankDifferential,
    ],
)
async def test_native_value_no_data(
    hass: HomeAssistant, mock_coordinator, cls
):
    """Test native_value returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_number(cls, mock_coordinator)
    assert entity.native_value is None


@pytest.mark.parametrize(
    "cls",
    [
        HotTankTargetTemperature,
        HotTankMinTemperature,
        NumberOfStages,
        StageOnLagTime,
    ],
)
async def test_unavailable_no_data(
    hass: HomeAssistant, mock_coordinator, cls
):
    """Test entities report unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    entity = _make_number(cls, mock_coordinator)
    assert entity.available is False


# ---------------------------------------------------------------------------
# Unique IDs
# ---------------------------------------------------------------------------


async def test_hot_target_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test HotTankTargetTemperature unique ID."""
    entity = _make_number(HotTankTargetTemperature, mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_hot_tank_target_temp"


async def test_hot_min_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test HotTankMinTemperature unique ID."""
    entity = _make_number(HotTankMinTemperature, mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_hot_tank_min_temp"


async def test_num_stages_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test NumberOfStages unique ID."""
    entity = _make_number(NumberOfStages, mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_number_of_stages"


# ---------------------------------------------------------------------------
# Device info
# ---------------------------------------------------------------------------


async def test_number_device_info(hass: HomeAssistant, mock_coordinator):
    """Test device_info for number entities."""
    entity = _make_number(HotTankTargetTemperature, mock_coordinator)
    info = entity.device_info
    assert (DOMAIN, MOCK_DEVICE_ID) in info["identifiers"]
