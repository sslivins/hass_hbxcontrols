"""Tests for the HBX Controls water_heater platform (DHW)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.water_heater import (
    HBXDHWWaterHeater,
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


def _make_water_heater(coordinator, device_id=MOCK_DEVICE_ID, device=None, building_id=MOCK_BUILDING_ID):
    """Create a water heater entity for testing."""
    if device is None:
        device = make_device(device_id=device_id)
    return HBXDHWWaterHeater(coordinator, device_id, device, building_id)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def test_setup_creates_water_heater(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that a water heater entity is created when DHW is present."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 1
    assert isinstance(entities[0], HBXDHWWaterHeater)


async def test_setup_no_dhw(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test that no water heater entity is created when DHW is absent."""
    params = make_full_parameters(
        dhw_enabled=None,
        dhw_target_temp=None,
        dhw_differential=None,
        dhw_state=None,
    )
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
    """Test no entities when coordinator has no data."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator_no_data

    entities = []
    await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

    assert len(entities) == 0


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


async def test_is_on_true(mock_coordinator):
    """Test is_on returns True when DHW is enabled."""
    params = make_full_parameters(dhw_enabled=True)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})

    entity = _make_water_heater(mock_coordinator)
    assert entity.is_on is True


async def test_is_on_false(mock_coordinator):
    """Test is_on returns False when DHW is disabled."""
    params = make_full_parameters(dhw_enabled=False)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})

    entity = _make_water_heater(mock_coordinator)
    assert entity.is_on is False


async def test_target_temperature(mock_coordinator):
    """Test target_temperature returns the DHW target temp value."""
    target = MagicMock()
    target.value = 140.0
    params = make_full_parameters(dhw_target_temp=target)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})

    entity = _make_water_heater(mock_coordinator)
    assert entity.target_temperature == 140.0


async def test_target_temperature_plain_float(mock_coordinator):
    """Test target_temperature works with a plain float (no .value attr)."""
    params = make_full_parameters(dhw_target_temp=135.0)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})

    entity = _make_water_heater(mock_coordinator)
    assert entity.target_temperature == 135.0


async def test_current_operation_heating(mock_coordinator):
    """Test current_operation returns 'heating' when DHW is activated."""
    params = make_full_parameters(
        dhw_state={"activated": True, "enabled": True, "title": "DHW"}
    )
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})

    entity = _make_water_heater(mock_coordinator)
    assert entity.current_operation == "heating"


async def test_current_operation_idle(mock_coordinator):
    """Test current_operation returns 'idle' when DHW is not activated."""
    params = make_full_parameters(
        dhw_state={"activated": False, "enabled": True, "title": "DHW"}
    )
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})

    entity = _make_water_heater(mock_coordinator)
    assert entity.current_operation == "idle"


async def test_current_operation_no_state(mock_coordinator):
    """Test current_operation returns None when dhw_state is absent."""
    params = make_full_parameters(dhw_state=None)
    device = make_device(parameters=params)
    mock_coordinator.data = make_coordinator_data(devices={MOCK_DEVICE_ID: device})

    entity = _make_water_heater(mock_coordinator)
    assert entity.current_operation is None


async def test_available(mock_coordinator):
    """Test available returns True with valid data."""
    entity = _make_water_heater(mock_coordinator)
    assert entity.available is True


async def test_unavailable_no_data(mock_coordinator):
    """Test available returns False when coordinator has no data."""
    mock_coordinator.data = None
    entity = _make_water_heater(mock_coordinator)
    assert entity.available is False


async def test_unique_id(mock_coordinator):
    """Test unique_id format."""
    entity = _make_water_heater(mock_coordinator)
    assert entity.unique_id == f"{MOCK_DEVICE_ID}_dhw"


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


async def test_turn_on(mock_coordinator):
    """Test turning on DHW calls the API."""
    mock_coordinator.async_request_refresh = AsyncMock()

    entity = _make_water_heater(mock_coordinator)

    with patch(
        "custom_components.hbx_controls.water_heater.SensorlinxDevice"
    ) as mock_device_cls:
        mock_device = MagicMock()
        mock_device.set_dhw_enabled = AsyncMock()
        mock_device_cls.return_value = mock_device

        await entity.async_turn_on()

        mock_device.set_dhw_enabled.assert_called_once_with(True)
        mock_coordinator.async_request_refresh.assert_called_once()


async def test_turn_off(mock_coordinator):
    """Test turning off DHW calls the API."""
    mock_coordinator.async_request_refresh = AsyncMock()

    entity = _make_water_heater(mock_coordinator)

    with patch(
        "custom_components.hbx_controls.water_heater.SensorlinxDevice"
    ) as mock_device_cls:
        mock_device = MagicMock()
        mock_device.set_dhw_enabled = AsyncMock()
        mock_device_cls.return_value = mock_device

        await entity.async_turn_off()

        mock_device.set_dhw_enabled.assert_called_once_with(False)
        mock_coordinator.async_request_refresh.assert_called_once()


async def test_set_temperature(mock_coordinator):
    """Test setting DHW target temperature calls the API."""
    mock_coordinator.async_request_refresh = AsyncMock()

    entity = _make_water_heater(mock_coordinator)

    with patch(
        "custom_components.hbx_controls.water_heater.SensorlinxDevice"
    ) as mock_device_cls, patch(
        "custom_components.hbx_controls.water_heater.Temperature"
    ) as mock_temp_cls:
        mock_device = MagicMock()
        mock_device.set_dhw_target_temp = AsyncMock()
        mock_device_cls.return_value = mock_device

        mock_temp_instance = MagicMock()
        mock_temp_cls.return_value = mock_temp_instance

        await entity.async_set_temperature(temperature=145.0)

        mock_temp_cls.assert_called_once_with(145.0, "F")
        mock_device.set_dhw_target_temp.assert_called_once_with(mock_temp_instance)
        mock_coordinator.async_request_refresh.assert_called_once()


async def test_set_temperature_no_value(mock_coordinator):
    """Test set_temperature does nothing when no temperature kwarg."""
    mock_coordinator.async_request_refresh = AsyncMock()

    entity = _make_water_heater(mock_coordinator)

    with patch(
        "custom_components.hbx_controls.water_heater.SensorlinxDevice"
    ) as mock_device_cls:
        await entity.async_set_temperature()
        mock_device_cls.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()
