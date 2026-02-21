"""Tests for the HBX Controls select platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.select import (
    HvacModePrioritySelect,
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


def _make_select(coordinator, device_id=MOCK_DEVICE_ID, device=None, building_id=MOCK_BUILDING_ID):
    """Create a HvacModePrioritySelect entity for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return HvacModePrioritySelect(coordinator, device_id, device, building_id)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def test_setup_creates_select(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test select entity created for device with hvac_mode parameter."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 1
    assert isinstance(entities[0], HvacModePrioritySelect)


async def test_setup_no_hvac_mode(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test no select entity created when hvac_mode parameter missing."""
    params = {"temperature_tank": 120.0}
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


async def test_setup_no_data(
    hass: HomeAssistant, mock_coordinator_no_data, mock_config_entry
):
    """Test no entities created when coordinator has no data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator_no_data

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


async def test_options(hass: HomeAssistant, mock_coordinator):
    """Test available options."""
    entity = _make_select(mock_coordinator)
    assert entity.options == ["heat", "cool", "auto"]


# ---------------------------------------------------------------------------
# current_option
# ---------------------------------------------------------------------------


async def test_current_option_heat(hass: HomeAssistant, mock_coordinator):
    """Test current_option returns hvac_mode from parameters."""
    entity = _make_select(mock_coordinator)
    assert entity.current_option == "heat"


@pytest.mark.parametrize("mode", ["heat", "cool", "auto"])
async def test_current_option_values(
    hass: HomeAssistant, mock_coordinator, mode
):
    """Test current_option for each valid mode."""
    params = make_full_parameters(hvac_mode=mode)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_select(mock_coordinator)
    assert entity.current_option == mode


async def test_current_option_no_data(hass: HomeAssistant, mock_coordinator):
    """Test current_option returns None when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_select(mock_coordinator)
    assert entity.current_option is None


async def test_current_option_device_missing(
    hass: HomeAssistant, mock_coordinator
):
    """Test current_option returns None when device is not in data."""
    mock_coordinator.data = make_coordinator_data(devices={})
    entity = _make_select(mock_coordinator)
    assert entity.current_option is None


# ---------------------------------------------------------------------------
# async_select_option
# ---------------------------------------------------------------------------


async def test_select_option(hass: HomeAssistant, mock_coordinator):
    """Test selecting an option calls SensorlinxDevice."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_select(mock_coordinator)

    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.select.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_select_option("cool")

    mock_helper.set_hvac_mode_priority.assert_called_once_with("cool")
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_select_option_auto(hass: HomeAssistant, mock_coordinator):
    """Test selecting auto mode."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = _make_select(mock_coordinator)

    mock_helper = AsyncMock()
    with patch(
        "custom_components.hbx_controls.select.SensorlinxDevice",
        return_value=mock_helper,
    ):
        await entity.async_select_option("auto")

    mock_helper.set_hvac_mode_priority.assert_called_once_with("auto")


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


async def test_available_true(hass: HomeAssistant, mock_coordinator):
    """Test entity available when data exists and has hvac_mode."""
    entity = _make_select(mock_coordinator)
    assert entity.available is True


async def test_available_false_no_data(hass: HomeAssistant, mock_coordinator):
    """Test entity unavailable when coordinator has no data."""
    mock_coordinator.data = None
    mock_coordinator.last_update_success = False
    entity = _make_select(mock_coordinator)
    assert entity.available is False


async def test_available_false_no_hvac_mode(
    hass: HomeAssistant, mock_coordinator
):
    """Test entity unavailable when device lacks hvac_mode parameter."""
    params = {"temperature_tank": 120.0}
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})
    entity = _make_select(mock_coordinator)
    assert entity.available is False


# ---------------------------------------------------------------------------
# Unique ID / device info
# ---------------------------------------------------------------------------


async def test_unique_id(hass: HomeAssistant, mock_coordinator):
    """Test unique ID follows expected pattern."""
    entity = _make_select(mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_hvac_mode_priority"


async def test_device_info(hass: HomeAssistant, mock_coordinator):
    """Test device info has correct identifiers."""
    entity = _make_select(mock_coordinator)
    info = entity.device_info
    assert (DOMAIN, MOCK_DEVICE_ID) in info["identifiers"]
