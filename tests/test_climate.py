"""Tests for the HBX Controls climate platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.climate import (
    HVACAction,
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.climate import (
    HBXControlsClimate,
    async_setup_entry,
)
from custom_components.hbx_controls.const import DOMAIN

from .conftest import (
    MOCK_BUILDING_ID,
    MOCK_DEVICE_ID,
    make_coordinator_data,
    make_device,
    make_full_parameters,
)


# ---------------------------------------------------------------------------
# Helper to build a climate entity with coordinator data
# ---------------------------------------------------------------------------


def _make_climate_entity(
    coordinator,
    device_id=MOCK_DEVICE_ID,
    device=None,
):
    """Create an HBXControlsClimate entity for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return HBXControlsClimate(coordinator, device_id, device)


# ---------------------------------------------------------------------------
# Platform setup tests
# ---------------------------------------------------------------------------


async def test_async_setup_entry_creates_entities(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that climate entities are created for devices with temperature data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    async_add_entities = lambda ents: entities.extend(ents)

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    assert len(entities) == 1
    assert isinstance(entities[0], HBXControlsClimate)


async def test_async_setup_entry_skips_devices_without_temp(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that devices without temperature parameters get no climate entity."""
    params = make_full_parameters()
    del params["temperature_tank"]
    del params["target_temperature_tank"]
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(
        devices={MOCK_DEVICE_ID: device}
    )
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


async def test_async_setup_entry_no_data(
    hass: HomeAssistant, mock_coordinator_no_data, mock_config_entry
):
    """Test platform setup with no coordinator data creates no entities."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator_no_data

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


# ---------------------------------------------------------------------------
# Entity attribute tests
# ---------------------------------------------------------------------------


async def test_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique_id follows expected pattern."""
    entity = _make_climate_entity(mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_climate"


async def test_name(hass: HomeAssistant, mock_coordinator):
    """Test entity name includes device name."""
    entity = _make_climate_entity(mock_coordinator)
    assert "Test ECO" in entity.name
    assert "Climate" in entity.name


async def test_temperature_unit(hass: HomeAssistant, mock_coordinator):
    """Test temperature unit is Fahrenheit."""
    entity = _make_climate_entity(mock_coordinator)
    assert entity.temperature_unit == UnitOfTemperature.FAHRENHEIT


async def test_supported_features(hass: HomeAssistant, mock_coordinator):
    """Test supported features include target temperature and on/off."""
    entity = _make_climate_entity(mock_coordinator)
    features = entity.supported_features
    assert features & ClimateEntityFeature.TARGET_TEMPERATURE
    assert features & ClimateEntityFeature.TURN_ON
    assert features & ClimateEntityFeature.TURN_OFF


async def test_hvac_modes(hass: HomeAssistant, mock_coordinator):
    """Test available HVAC modes."""
    entity = _make_climate_entity(mock_coordinator)
    assert HVACMode.OFF in entity.hvac_modes
    assert HVACMode.HEAT in entity.hvac_modes
    assert HVACMode.COOL in entity.hvac_modes
    assert HVACMode.AUTO in entity.hvac_modes


async def test_device_info(hass: HomeAssistant, mock_coordinator):
    """Test device info is set correctly."""
    entity = _make_climate_entity(mock_coordinator)
    info = entity.device_info
    assert (DOMAIN, MOCK_DEVICE_ID) in info["identifiers"]
    assert info["manufacturer"] == "HBX Controls"


# ---------------------------------------------------------------------------
# Property tests (reading coordinator data)
# ---------------------------------------------------------------------------


async def test_current_temperature(hass: HomeAssistant, mock_coordinator):
    """Test current_temperature reads temperature_tank from coordinator."""
    entity = _make_climate_entity(mock_coordinator)
    assert entity.current_temperature == 120.0


async def test_current_temperature_no_data(
    hass: HomeAssistant, mock_coordinator
):
    """Test current_temperature returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_climate_entity(mock_coordinator)
    assert entity.current_temperature is None


async def test_current_temperature_device_missing(
    hass: HomeAssistant, mock_coordinator
):
    """Test current_temperature returns None when device is missing."""
    mock_coordinator.data = make_coordinator_data(devices={})
    entity = _make_climate_entity(mock_coordinator)
    assert entity.current_temperature is None


async def test_target_temperature(hass: HomeAssistant, mock_coordinator):
    """Test target_temperature reads target_temperature_tank from coordinator."""
    entity = _make_climate_entity(mock_coordinator)
    assert entity.target_temperature == 125.0


async def test_target_temperature_no_data(
    hass: HomeAssistant, mock_coordinator
):
    """Test target_temperature returns None when coordinator data is None."""
    mock_coordinator.data = None
    entity = _make_climate_entity(mock_coordinator)
    assert entity.target_temperature is None


# ---------------------------------------------------------------------------
# HVAC mode property tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mode_str,expected",
    [
        ("heat", HVACMode.HEAT),
        ("cool", HVACMode.COOL),
        ("auto", HVACMode.AUTO),
        ("off", HVACMode.OFF),
        ("HEAT", HVACMode.HEAT),
        ("Heat", HVACMode.HEAT),
    ],
)
async def test_hvac_mode_mapping(
    hass: HomeAssistant, mock_coordinator, mode_str, expected
):
    """Test hvac_mode maps parameter string to HVACMode correctly."""
    params = make_full_parameters(hvac_mode=mode_str)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(
        devices={MOCK_DEVICE_ID: device}
    )
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_mode == expected


async def test_hvac_mode_unknown_defaults_auto(
    hass: HomeAssistant, mock_coordinator
):
    """Test unknown hvac_mode string defaults to AUTO."""
    params = make_full_parameters(hvac_mode="unknown")
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(
        devices={MOCK_DEVICE_ID: device}
    )
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_mode == HVACMode.AUTO


async def test_hvac_mode_no_data(hass: HomeAssistant, mock_coordinator):
    """Test hvac_mode returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_mode is None


# ---------------------------------------------------------------------------
# HVAC action tests
# ---------------------------------------------------------------------------


async def test_hvac_action_heating(hass: HomeAssistant, mock_coordinator):
    """Test hvac_action returns HEATING when permanent_heat_demand is True."""
    params = make_full_parameters(permanent_heat_demand=True)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(
        devices={MOCK_DEVICE_ID: device}
    )
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_action == HVACAction.HEATING


async def test_hvac_action_cooling(hass: HomeAssistant, mock_coordinator):
    """Test hvac_action returns COOLING when permanent_cool_demand is True."""
    params = make_full_parameters(permanent_cool_demand=True)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(
        devices={MOCK_DEVICE_ID: device}
    )
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_action == HVACAction.COOLING


async def test_hvac_action_idle(hass: HomeAssistant, mock_coordinator):
    """Test hvac_action returns IDLE when mode is not off and no demand."""
    params = make_full_parameters(
        hvac_mode="heat", permanent_heat_demand=False, permanent_cool_demand=False
    )
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(
        devices={MOCK_DEVICE_ID: device}
    )
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_action == HVACAction.IDLE


async def test_hvac_action_off(hass: HomeAssistant, mock_coordinator):
    """Test hvac_action returns OFF when hvac_mode is off."""
    params = make_full_parameters(
        hvac_mode="off", permanent_heat_demand=False, permanent_cool_demand=False
    )
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(
        devices={MOCK_DEVICE_ID: device}
    )
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_action == HVACAction.OFF


async def test_hvac_action_no_data(hass: HomeAssistant, mock_coordinator):
    """Test hvac_action returns None when coordinator data is None."""
    mock_coordinator.data = None
    entity = _make_climate_entity(mock_coordinator)
    assert entity.hvac_action is None


# ---------------------------------------------------------------------------
# set_temperature tests
# ---------------------------------------------------------------------------


async def test_set_temperature_heat_mode(hass: HomeAssistant, mock_coordinator):
    """Test set_temperature calls SensorlinxDevice when in heat mode."""
    mock_coordinator.data = make_coordinator_data()
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_climate_entity(mock_coordinator)

    mock_device_helper = AsyncMock()

    with patch(
        "pysensorlinx.sensorlinx.SensorlinxDevice",
        return_value=mock_device_helper,
    ), patch(
        "pysensorlinx.sensorlinx.Temperature",
    ) as mock_temp:
        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 130.0})

    mock_device_helper.set_hot_tank_target_temp.assert_called_once()
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_set_temperature_no_temp_kwarg(
    hass: HomeAssistant, mock_coordinator
):
    """Test set_temperature does nothing if no temperature is provided."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_climate_entity(mock_coordinator)
    await entity.async_set_temperature()
    mock_coordinator.async_request_refresh.assert_not_called()


async def test_set_temperature_no_data(hass: HomeAssistant, mock_coordinator):
    """Test set_temperature handles missing coordinator data gracefully."""
    mock_coordinator.data = None
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_climate_entity(mock_coordinator)
    await entity.async_set_temperature(**{ATTR_TEMPERATURE: 130.0})
    mock_coordinator.async_request_refresh.assert_not_called()


# ---------------------------------------------------------------------------
# set_hvac_mode tests
# ---------------------------------------------------------------------------


async def test_set_hvac_mode(hass: HomeAssistant, mock_coordinator):
    """Test set_hvac_mode calls SensorlinxDevice."""
    mock_coordinator.data = make_coordinator_data()
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_climate_entity(mock_coordinator)

    mock_device_helper = AsyncMock()

    with patch(
        "pysensorlinx.sensorlinx.SensorlinxDevice",
        return_value=mock_device_helper,
    ):
        await entity.async_set_hvac_mode(HVACMode.COOL)

    mock_device_helper.set_hvac_mode_priority.assert_called_once_with("cool")
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_set_hvac_mode_no_data(hass: HomeAssistant, mock_coordinator):
    """Test set_hvac_mode handles missing data gracefully."""
    mock_coordinator.data = None
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_climate_entity(mock_coordinator)
    await entity.async_set_hvac_mode(HVACMode.HEAT)
    mock_coordinator.async_request_refresh.assert_not_called()


async def test_set_hvac_mode_exception_handled(
    hass: HomeAssistant, mock_coordinator
):
    """Test set_hvac_mode logs error on exception instead of raising."""
    mock_coordinator.data = make_coordinator_data()
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_climate_entity(mock_coordinator)

    with patch(
        "pysensorlinx.sensorlinx.SensorlinxDevice",
        side_effect=Exception("API error"),
    ):
        # Should not raise
        await entity.async_set_hvac_mode(HVACMode.COOL)


# ---------------------------------------------------------------------------
# Availability tests
# ---------------------------------------------------------------------------


async def test_available_true(hass: HomeAssistant, mock_coordinator):
    """Test entity reports available when data exists."""
    entity = _make_climate_entity(mock_coordinator)
    assert entity.available is True


async def test_available_false_no_data(hass: HomeAssistant, mock_coordinator):
    """Test entity reports unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    entity = _make_climate_entity(mock_coordinator)
    assert entity.available is False
