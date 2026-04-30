"""Tests for the THM climate entity (2.5.0b9)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.climate import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.climate import (
    HBXControlsThmClimate,
    async_setup_entry,
)
from custom_components.hbx_controls.const import DOMAIN

from .conftest import MOCK_BUILDING_ID, MOCK_DEVICE_ID, make_coordinator_data, make_device


THM_DEVICE_ID = "THM-001"


def _thm_params(**overrides):
    """Build a minimal set of THM parameters."""
    params = {
        "device_type": "THM",
        "temperature_room": 71.5,
        # Legacy single-target — coordinator still emits it but the
        # entity prefers heat_setpoint/cool_setpoint going forward.
        "target_temperature_room": 70.0,
        "heat_setpoint": 70.0,
        "cool_setpoint": 78.0,
        "humidity": 42.0,
        "hvac_mode": "heat",
        "fan_mode": "off",
        "thm_mode": "Air",
        "is_off": False,
        "active_demands": ["heating"],
        "away_mode_activated": False,
    }
    params.update(overrides)
    return params


def _make_thm_device(**overrides):
    return make_device(
        device_id=THM_DEVICE_ID,
        name="Hallway",
        device_type="THM",
        parameters=_thm_params(**overrides),
    )


def _coordinator_with_thm(mock_coordinator, **overrides):
    device = _make_thm_device(**overrides)
    mock_coordinator.data = make_coordinator_data(devices={THM_DEVICE_ID: device})
    return device


# ---------------------------------------------------------------------------
# Setup entry
# ---------------------------------------------------------------------------


async def test_setup_entry_creates_thm_climate(hass, mock_coordinator, mock_config_entry):
    _coordinator_with_thm(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    assert any(isinstance(e, HBXControlsThmClimate) for e in entities)


async def test_setup_entry_skips_eco_for_thm_class(hass, mock_coordinator, mock_config_entry):
    """ECO devices must NOT get a THM climate entity."""
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator
    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)
    assert not any(isinstance(e, HBXControlsThmClimate) for e in entities)


# ---------------------------------------------------------------------------
# Read-side properties
# ---------------------------------------------------------------------------


@pytest.fixture
def thm_climate(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator)
    return HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)


def test_current_temperature(thm_climate):
    assert thm_climate.current_temperature == 71.5


def test_target_temperature(thm_climate):
    """In HEAT mode, target_temperature surfaces the heat setpoint."""
    assert thm_climate.target_temperature == 70.0


def test_target_temperature_in_cool_mode(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator, hvac_mode="cool")
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.target_temperature == 78.0


def test_target_temperature_none_in_heat_cool(mock_coordinator):
    """HEAT_COOL uses target_temperature_low/high, not target_temperature."""
    device = _coordinator_with_thm(mock_coordinator, hvac_mode="auto")
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.target_temperature is None


def test_target_temperature_low_high_in_heat_cool(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator, hvac_mode="auto")
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.target_temperature_low == 70.0
    assert ent.target_temperature_high == 78.0


def test_target_temperature_low_high_none_outside_heat_cool(mock_coordinator):
    """HEAT/COOL/OFF modes report None for the low/high pair."""
    device = _coordinator_with_thm(mock_coordinator, hvac_mode="heat")
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.target_temperature_low is None
    assert ent.target_temperature_high is None


def test_current_humidity(thm_climate):
    assert thm_climate.current_humidity == 42


def test_hvac_mode_mapping(mock_coordinator):
    for raw, expected in [
        ("off", HVACMode.OFF),
        ("heat", HVACMode.HEAT),
        ("cool", HVACMode.COOL),
        ("auto", HVACMode.HEAT_COOL),
    ]:
        device = _coordinator_with_thm(mock_coordinator, hvac_mode=raw)
        ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
        assert ent.hvac_mode == expected


def test_hvac_action_off_via_mode(mock_coordinator):
    """Mode==off forces HVACAction.OFF even if active_demands is empty."""
    device = _coordinator_with_thm(
        mock_coordinator, hvac_mode="off", active_demands=[],
    )
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.hvac_action == HVACAction.OFF


def test_hvac_action_off_via_is_off_flag(mock_coordinator):
    """Legacy is_off flag still respected for back-compat."""
    device = _coordinator_with_thm(
        mock_coordinator, is_off=True, active_demands=["heating"],
    )
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    # is_off should win for safety even though demands say heating.
    # Our hvac_mode is still "heat" so OFF only fires via the flag.
    assert ent.hvac_action == HVACAction.OFF


def test_hvac_action_heating(thm_climate):
    """heating bit set in active_demands -> HEATING."""
    assert thm_climate.hvac_action == HVACAction.HEATING


def test_hvac_action_cooling(mock_coordinator):
    device = _coordinator_with_thm(
        mock_coordinator,
        hvac_mode="cool",
        active_demands=["cooling"],
    )
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.hvac_action == HVACAction.COOLING


def test_hvac_action_idle_when_no_demand(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator, active_demands=[])
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.hvac_action == HVACAction.IDLE


def test_hvac_action_fan_only_is_idle(mock_coordinator):
    """Hydronic systems treat fan-only as idle (no thermal demand)."""
    device = _coordinator_with_thm(mock_coordinator, active_demands=["fan"])
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.hvac_action == HVACAction.IDLE


def test_hvac_action_cooling_priority(mock_coordinator):
    """Defensive: if both heating and cooling bits are set, cooling wins."""
    device = _coordinator_with_thm(
        mock_coordinator, active_demands=["heating", "cooling"],
    )
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.hvac_action == HVACAction.COOLING


def test_fan_mode(thm_climate):
    assert thm_climate.fan_mode == "off"


def test_preset_away(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator, away_mode_activated=True)
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    assert ent.preset_mode == "away"


def test_preset_none(thm_climate):
    assert thm_climate.preset_mode == "none"


# ---------------------------------------------------------------------------
# Write-side methods (mock the ThmDevice helper)
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_thm():
    with patch("custom_components.hbx_controls.climate.ThmDevice") as cls:
        instance = MagicMock()
        instance.set_hvac_mode = AsyncMock()
        instance.set_fan_mode = AsyncMock()
        instance.set_away_mode = AsyncMock()
        instance.set_heat_setpoint = AsyncMock()
        instance.set_cool_setpoint = AsyncMock()
        instance.set_heat_cool_setpoints = AsyncMock()
        cls.return_value = instance
        yield instance


async def test_async_set_hvac_mode_writes_lib_str(thm_climate, patched_thm):
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_set_hvac_mode(HVACMode.COOL)
    patched_thm.set_hvac_mode.assert_awaited_once_with("cool")
    thm_climate.coordinator.async_request_refresh.assert_awaited()


async def test_async_set_hvac_mode_heat_cool_maps_to_auto(thm_climate, patched_thm):
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_set_hvac_mode(HVACMode.HEAT_COOL)
    patched_thm.set_hvac_mode.assert_awaited_once_with("auto")


async def test_async_set_fan_mode(thm_climate, patched_thm):
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_set_fan_mode("intermittent")
    patched_thm.set_fan_mode.assert_awaited_once_with("intermittent")


async def test_async_set_fan_mode_rejects_unknown(thm_climate, patched_thm):
    await thm_climate.async_set_fan_mode("turbo")
    patched_thm.set_fan_mode.assert_not_awaited()


async def test_async_set_preset_away(thm_climate, patched_thm):
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_set_preset_mode("away")
    patched_thm.set_away_mode.assert_awaited_once_with(True)


async def test_async_set_preset_none(thm_climate, patched_thm):
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_set_preset_mode("none")
    patched_thm.set_away_mode.assert_awaited_once_with(False)


async def test_async_set_temperature_in_heat_mode(thm_climate, patched_thm):
    """Single-setpoint write in HEAT routes to set_heat_setpoint."""
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_set_temperature(**{ATTR_TEMPERATURE: 72})
    patched_thm.set_heat_setpoint.assert_awaited_once()
    patched_thm.set_cool_setpoint.assert_not_awaited()
    temp = patched_thm.set_heat_setpoint.await_args.args[0]
    assert temp.to_fahrenheit() == 72


async def test_async_set_temperature_in_cool_mode(mock_coordinator, patched_thm):
    """Single-setpoint write in COOL routes to set_cool_setpoint."""
    device = _coordinator_with_thm(mock_coordinator, hvac_mode="cool")
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    ent.coordinator.async_request_refresh = AsyncMock()
    await ent.async_set_temperature(**{ATTR_TEMPERATURE: 78})
    patched_thm.set_cool_setpoint.assert_awaited_once()
    patched_thm.set_heat_setpoint.assert_not_awaited()
    temp = patched_thm.set_cool_setpoint.await_args.args[0]
    assert temp.to_fahrenheit() == 78


async def test_async_set_temperature_heat_cool_low_high(mock_coordinator, patched_thm):
    """HEAT_COOL writes both setpoints atomically via set_heat_cool_setpoints."""
    device = _coordinator_with_thm(mock_coordinator, hvac_mode="auto")
    ent = HBXControlsThmClimate(mock_coordinator, THM_DEVICE_ID, device)
    ent.coordinator.async_request_refresh = AsyncMock()
    await ent.async_set_temperature(**{
        ATTR_TARGET_TEMP_LOW: 67,
        ATTR_TARGET_TEMP_HIGH: 79,
    })
    patched_thm.set_heat_cool_setpoints.assert_awaited_once()
    args = patched_thm.set_heat_cool_setpoints.await_args.args
    assert args[0].to_fahrenheit() == 67
    assert args[1].to_fahrenheit() == 79
    # Single atomic call — must NOT have called the individual setters.
    patched_thm.set_heat_setpoint.assert_not_awaited()
    patched_thm.set_cool_setpoint.assert_not_awaited()


async def test_async_set_temperature_no_kwargs_is_noop(thm_climate, patched_thm):
    await thm_climate.async_set_temperature()
    patched_thm.set_heat_setpoint.assert_not_awaited()
    patched_thm.set_cool_setpoint.assert_not_awaited()
    patched_thm.set_heat_cool_setpoints.assert_not_awaited()


async def test_async_turn_on_off(thm_climate, patched_thm):
    """turn_on switches to HEAT_COOL ("auto"); turn_off to OFF."""
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_turn_off()
    await thm_climate.async_turn_on()
    calls = [c.args[0] for c in patched_thm.set_hvac_mode.await_args_list]
    assert calls == ["off", "auto"]


async def test_write_swallows_setter_failure(thm_climate, patched_thm, caplog):
    """A failing setter should log, not raise."""
    patched_thm.set_hvac_mode.side_effect = RuntimeError("boom")
    thm_climate.coordinator.async_request_refresh = AsyncMock()
    await thm_climate.async_set_hvac_mode(HVACMode.HEAT)  # must not raise
    assert "Failed to set THM HVAC mode" in caplog.text
