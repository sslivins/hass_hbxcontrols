"""Tests for the ZON aux setpoint number entity (2.5.0b1)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.number import (
    ZonAuxSetpointNumber,
    async_setup_entry,
)

from .conftest import MOCK_BUILDING_ID, make_coordinator_data, make_device


ZON_DEVICE_ID = "ZON-001"


def _zon_params(**overrides):
    params = {
        "device_type": "ZON",
        "app_button_enabled": True,
        "app_button_activated": False,
        "aux_setpoint_target": 120,
    }
    params.update(overrides)
    return params


def _coordinator_with_zon(mock_coordinator, **overrides):
    device = make_device(
        device_id=ZON_DEVICE_ID,
        name="Zone Ctrl",
        device_type="ZON",
        parameters=_zon_params(**overrides),
    )
    mock_coordinator.data = make_coordinator_data(devices={ZON_DEVICE_ID: device})
    return device


async def test_setup_entry_creates_aux_setpoint(hass, mock_coordinator, mock_config_entry):
    _coordinator_with_zon(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)
    assert any(isinstance(e, ZonAuxSetpointNumber) for e in entities)


async def test_setup_entry_skips_when_no_aux(hass, mock_coordinator, mock_config_entry):
    device = make_device(
        device_id=ZON_DEVICE_ID,
        device_type="ZON",
        parameters={"device_type": "ZON", "app_button_enabled": False},
    )
    mock_coordinator.data = make_coordinator_data(devices={ZON_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)
    assert not any(isinstance(e, ZonAuxSetpointNumber) for e in entities)


@pytest.fixture
def aux_number(mock_coordinator):
    device = _coordinator_with_zon(mock_coordinator)
    return ZonAuxSetpointNumber(
        mock_coordinator, ZON_DEVICE_ID, device, MOCK_BUILDING_ID
    )


def test_native_value_int(aux_number):
    assert aux_number.native_value == 120.0


def test_native_value_temperature_object(mock_coordinator):
    temp = MagicMock()
    temp.to_fahrenheit = lambda: 122.0
    device = _coordinator_with_zon(mock_coordinator, aux_setpoint_target=temp)
    ent = ZonAuxSetpointNumber(mock_coordinator, ZON_DEVICE_ID, device, MOCK_BUILDING_ID)
    assert ent.native_value == 122.0


def test_native_value_value_attr(mock_coordinator):
    fake = type("T", (), {"value": 118})()  # has .value but no .to_fahrenheit
    device = _coordinator_with_zon(mock_coordinator, aux_setpoint_target=fake)
    ent = ZonAuxSetpointNumber(mock_coordinator, ZON_DEVICE_ID, device, MOCK_BUILDING_ID)
    assert ent.native_value == 118.0


def test_native_value_none(mock_coordinator):
    device = _coordinator_with_zon(mock_coordinator, aux_setpoint_target=None)
    ent = ZonAuxSetpointNumber(mock_coordinator, ZON_DEVICE_ID, device, MOCK_BUILDING_ID)
    assert ent.native_value is None


def test_attributes(aux_number):
    assert aux_number.native_min_value == 33
    assert aux_number.native_max_value == 180
    assert aux_number.native_step == 1


@pytest.fixture
def patched_zon():
    with patch("pysensorlinx.sensorlinx.ZonDevice") as cls:
        instance = MagicMock()
        instance.set_aux_setpoint = AsyncMock()
        cls.return_value = instance
        yield instance


async def test_set_native_value_calls_setter_with_temperature(aux_number, patched_zon):
    aux_number.coordinator.async_request_refresh = AsyncMock()
    await aux_number.async_set_native_value(125)
    patched_zon.set_aux_setpoint.assert_awaited_once()
    arg = patched_zon.set_aux_setpoint.await_args.args[0]
    assert arg.to_fahrenheit() == 125
    aux_number.coordinator.async_request_refresh.assert_awaited()


async def test_set_native_value_swallows_error(aux_number, patched_zon, caplog):
    patched_zon.set_aux_setpoint.side_effect = RuntimeError("oops")
    await aux_number.async_set_native_value(125)
    assert "Failed to set ZON aux setpoint" in caplog.text
