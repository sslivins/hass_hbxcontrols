"""Tests for the ZON app button switch (2.5.0b1)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.switch import (
    ZonAppButtonSwitch,
    async_setup_entry,
)

from .conftest import MOCK_BUILDING_ID, make_coordinator_data, make_device


ZON_DEVICE_ID = "ZON-001"


def _zon_params(**overrides):
    params = {
        "device_type": "ZON",
        "app_button_enabled": True,
        "app_button_activated": False,
        "app_button_text": "Boost",
        "aux_setpoint_target": 120,
    }
    params.update(overrides)
    return params


def _make_zon_device(**overrides):
    return make_device(
        device_id=ZON_DEVICE_ID,
        name="Zone Ctrl",
        device_type="ZON",
        parameters=_zon_params(**overrides),
    )


def _coordinator_with_zon(mock_coordinator, **overrides):
    device = _make_zon_device(**overrides)
    mock_coordinator.data = make_coordinator_data(devices={ZON_DEVICE_ID: device})
    return device


async def test_setup_entry_creates_app_button(hass, mock_coordinator, mock_config_entry):
    _coordinator_with_zon(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)
    assert any(isinstance(e, ZonAppButtonSwitch) for e in entities)


async def test_setup_entry_skips_when_disabled(hass, mock_coordinator, mock_config_entry):
    _coordinator_with_zon(mock_coordinator, app_button_enabled=False)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)
    assert not any(isinstance(e, ZonAppButtonSwitch) for e in entities)


@pytest.fixture
def app_switch(mock_coordinator):
    device = _coordinator_with_zon(mock_coordinator)
    sw = ZonAppButtonSwitch(mock_coordinator, ZON_DEVICE_ID, device, MOCK_BUILDING_ID)
    # Bypass HA's `hass` requirement when invoking optimistic state writes.
    sw.async_write_ha_state = MagicMock()
    return sw


def test_is_on_reflects_activated(app_switch):
    assert app_switch.is_on is False


def test_is_on_when_activated(mock_coordinator):
    device = _coordinator_with_zon(mock_coordinator, app_button_activated=True)
    sw = ZonAppButtonSwitch(mock_coordinator, ZON_DEVICE_ID, device, MOCK_BUILDING_ID)
    assert sw.is_on is True


def test_unavailable_when_slot_disabled(mock_coordinator):
    device = _coordinator_with_zon(mock_coordinator, app_button_enabled=False)
    sw = ZonAppButtonSwitch(mock_coordinator, ZON_DEVICE_ID, device, MOCK_BUILDING_ID)
    mock_coordinator.last_update_success = True
    assert sw.available is False


@pytest.fixture
def patched_zon():
    with patch("pysensorlinx.sensorlinx.ZonDevice") as cls:
        instance = MagicMock()
        instance.set_app_button = AsyncMock()
        cls.return_value = instance
        yield instance


async def test_turn_on_calls_set_app_button_true(app_switch, patched_zon):
    app_switch.coordinator.async_request_refresh = AsyncMock()
    await app_switch.async_turn_on()
    patched_zon.set_app_button.assert_awaited_once_with(True)
    app_switch.coordinator.async_request_refresh.assert_awaited()


async def test_turn_off_calls_set_app_button_false(app_switch, patched_zon):
    app_switch.coordinator.async_request_refresh = AsyncMock()
    await app_switch.async_turn_off()
    patched_zon.set_app_button.assert_awaited_once_with(False)


async def test_turn_on_swallows_error(app_switch, patched_zon, caplog):
    patched_zon.set_app_button.side_effect = RuntimeError("nope")
    await app_switch.async_turn_on()
    assert "Failed to enable ZON app button" in caplog.text


async def test_optimistic_state_after_turn_on(app_switch, patched_zon, mock_coordinator):
    """is_on returns the requested state until coordinator confirms it."""
    app_switch.coordinator.async_request_refresh = AsyncMock()
    # Coordinator initially reports OFF (matching device fixture).
    assert app_switch.is_on is False

    await app_switch.async_turn_on()

    # Coordinator hasn't refreshed yet → still reports OFF, but is_on
    # should now return the optimistic ON to suppress the flicker.
    assert app_switch.is_on is True

    # Coordinator catches up → optimistic state clears, returns coordinator value.
    _coordinator_with_zon(mock_coordinator, app_button_activated=True)
    # Re-bind device pointer (coordinator data was replaced).
    assert app_switch.is_on is True
    assert app_switch._pending is None


async def test_optimistic_state_after_turn_off(app_switch, patched_zon, mock_coordinator):
    """Optimistic state survives a stale-on coordinator refresh."""
    _coordinator_with_zon(mock_coordinator, app_button_activated=True)
    app_switch.coordinator.async_request_refresh = AsyncMock()
    assert app_switch.is_on is True

    await app_switch.async_turn_off()

    # Stale coordinator data still says ON; is_on must report optimistic OFF.
    assert app_switch.is_on is False
    assert app_switch._pending is False

    # Coordinator catches up to OFF → optimistic clears.
    _coordinator_with_zon(mock_coordinator, app_button_activated=False)
    assert app_switch.is_on is False
    assert app_switch._pending is None
