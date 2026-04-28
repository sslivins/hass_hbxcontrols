"""Tests for THM schedule + humidity entities (2.5.0b4)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.hbx_controls.const import DOMAIN
from custom_components.hbx_controls.number import (
    ThmHumidityTargetNumber,
    async_setup_entry as number_async_setup_entry,
)
from custom_components.hbx_controls.select import (
    ThmHumidityModeSelect,
    async_setup_entry as select_async_setup_entry,
)
from custom_components.hbx_controls.switch import (
    ThmScheduleEnableSwitch,
    async_setup_entry as switch_async_setup_entry,
)

from .conftest import MOCK_BUILDING_ID, make_coordinator_data, make_device


THM_DEVICE_ID = "THM-001"


def _thm_params(**overrides):
    params = {
        "device_type": "THM",
        "schedule_enabled": False,
        "humidity_mode": "off",
        "humidity_target": 40,
    }
    params.update(overrides)
    return params


def _make_thm_device(**overrides):
    return make_device(
        device_id=THM_DEVICE_ID,
        name="Living Room",
        device_type="THM",
        parameters=_thm_params(**overrides),
    )


def _coordinator_with_thm(mock_coordinator, **overrides):
    device = _make_thm_device(**overrides)
    mock_coordinator.data = make_coordinator_data(devices={THM_DEVICE_ID: device})
    return device


# ---------------------------------------------------------------------------
# Setup tests — entities are wired up when the right keys are present
# ---------------------------------------------------------------------------

async def test_setup_creates_schedule_switch(hass, mock_coordinator, mock_config_entry):
    _coordinator_with_thm(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await switch_async_setup_entry(hass, mock_config_entry, entities.extend)
    assert any(isinstance(e, ThmScheduleEnableSwitch) for e in entities)


async def test_setup_skips_schedule_switch_without_field(
    hass, mock_coordinator, mock_config_entry
):
    device = _make_thm_device()
    device["parameters"].pop("schedule_enabled")
    mock_coordinator.data = make_coordinator_data(devices={THM_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await switch_async_setup_entry(hass, mock_config_entry, entities.extend)
    assert not any(isinstance(e, ThmScheduleEnableSwitch) for e in entities)


async def test_setup_creates_humidity_mode_select(
    hass, mock_coordinator, mock_config_entry
):
    _coordinator_with_thm(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await select_async_setup_entry(hass, mock_config_entry, entities.extend)
    assert any(isinstance(e, ThmHumidityModeSelect) for e in entities)


async def test_setup_skips_humidity_mode_select_without_field(
    hass, mock_coordinator, mock_config_entry
):
    device = _make_thm_device()
    device["parameters"].pop("humidity_mode")
    mock_coordinator.data = make_coordinator_data(devices={THM_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await select_async_setup_entry(hass, mock_config_entry, entities.extend)
    assert not any(isinstance(e, ThmHumidityModeSelect) for e in entities)


async def test_setup_creates_humidity_target_number(
    hass, mock_coordinator, mock_config_entry
):
    _coordinator_with_thm(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await number_async_setup_entry(hass, mock_config_entry, entities.extend)
    assert any(isinstance(e, ThmHumidityTargetNumber) for e in entities)


async def test_setup_skips_humidity_target_number_without_field(
    hass, mock_coordinator, mock_config_entry
):
    device = _make_thm_device()
    device["parameters"].pop("humidity_target")
    mock_coordinator.data = make_coordinator_data(devices={THM_DEVICE_ID: device})
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await number_async_setup_entry(hass, mock_config_entry, entities.extend)
    assert not any(isinstance(e, ThmHumidityTargetNumber) for e in entities)


# ---------------------------------------------------------------------------
# Schedule switch
# ---------------------------------------------------------------------------

@pytest.fixture
def schedule_switch(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator)
    sw = ThmScheduleEnableSwitch(
        mock_coordinator, THM_DEVICE_ID, device, MOCK_BUILDING_ID
    )
    sw.async_write_ha_state = MagicMock()
    return sw


@pytest.fixture
def patched_thm():
    with patch("pysensorlinx.sensorlinx.ThmDevice") as cls:
        instance = MagicMock()
        instance.set_schedule_enabled = AsyncMock()
        instance.set_humidity_mode = AsyncMock()
        instance.set_humidity_target = AsyncMock()
        cls.return_value = instance
        yield instance


def test_schedule_is_on_reflects_field(schedule_switch):
    assert schedule_switch.is_on is False


def test_schedule_is_on_when_enabled(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator, schedule_enabled=True)
    sw = ThmScheduleEnableSwitch(
        mock_coordinator, THM_DEVICE_ID, device, MOCK_BUILDING_ID
    )
    assert sw.is_on is True


def test_schedule_unavailable_when_field_missing(mock_coordinator):
    device = _make_thm_device()
    device["parameters"].pop("schedule_enabled")
    mock_coordinator.data = make_coordinator_data(devices={THM_DEVICE_ID: device})
    sw = ThmScheduleEnableSwitch(
        mock_coordinator, THM_DEVICE_ID, device, MOCK_BUILDING_ID
    )
    mock_coordinator.last_update_success = True
    assert sw.available is False


async def test_schedule_turn_on_calls_setter(schedule_switch, patched_thm):
    schedule_switch.coordinator.async_request_refresh = AsyncMock()
    await schedule_switch.async_turn_on()
    patched_thm.set_schedule_enabled.assert_awaited_once_with(True)
    schedule_switch.coordinator.async_request_refresh.assert_awaited()


async def test_schedule_turn_off_calls_setter(schedule_switch, patched_thm):
    schedule_switch.coordinator.async_request_refresh = AsyncMock()
    await schedule_switch.async_turn_off()
    patched_thm.set_schedule_enabled.assert_awaited_once_with(False)


async def test_schedule_turn_on_swallows_error(schedule_switch, patched_thm, caplog):
    patched_thm.set_schedule_enabled.side_effect = RuntimeError("nope")
    await schedule_switch.async_turn_on()
    assert "Failed to enable THM schedule" in caplog.text


async def test_schedule_optimistic_state(schedule_switch, patched_thm, mock_coordinator):
    schedule_switch.coordinator.async_request_refresh = AsyncMock()
    assert schedule_switch.is_on is False

    await schedule_switch.async_turn_on()
    # Stale coordinator still says OFF; optimistic must report ON.
    assert schedule_switch.is_on is True

    # Coordinator catches up.
    _coordinator_with_thm(mock_coordinator, schedule_enabled=True)
    assert schedule_switch.is_on is True
    assert schedule_switch._pending is None


# ---------------------------------------------------------------------------
# Humidity mode select
# ---------------------------------------------------------------------------

@pytest.fixture
def humidity_mode_select(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator)
    sel = ThmHumidityModeSelect(
        mock_coordinator, THM_DEVICE_ID, device, MOCK_BUILDING_ID
    )
    sel.async_write_ha_state = MagicMock()
    return sel


def test_humidity_mode_options(humidity_mode_select):
    assert humidity_mode_select.options == ["off", "on", "auto"]


@pytest.mark.parametrize("mode", ["off", "on", "auto"])
def test_humidity_mode_current_option(mock_coordinator, mode):
    device = _coordinator_with_thm(mock_coordinator, humidity_mode=mode)
    sel = ThmHumidityModeSelect(
        mock_coordinator, THM_DEVICE_ID, device, MOCK_BUILDING_ID
    )
    assert sel.current_option == mode


@pytest.mark.parametrize("mode", ["off", "on", "auto"])
async def test_humidity_mode_select_calls_setter(
    humidity_mode_select, patched_thm, mode
):
    humidity_mode_select.coordinator.async_request_refresh = AsyncMock()
    await humidity_mode_select.async_select_option(mode)
    patched_thm.set_humidity_mode.assert_awaited_once_with(mode)


async def test_humidity_mode_select_swallows_error(
    humidity_mode_select, patched_thm, caplog
):
    patched_thm.set_humidity_mode.side_effect = RuntimeError("nope")
    await humidity_mode_select.async_select_option("auto")
    assert "Failed to set THM humidity mode" in caplog.text


async def test_humidity_mode_optimistic(
    humidity_mode_select, patched_thm, mock_coordinator
):
    humidity_mode_select.coordinator.async_request_refresh = AsyncMock()
    assert humidity_mode_select.current_option == "off"

    await humidity_mode_select.async_select_option("auto")
    assert humidity_mode_select.current_option == "auto"
    assert humidity_mode_select._pending == "auto"

    _coordinator_with_thm(mock_coordinator, humidity_mode="auto")
    assert humidity_mode_select.current_option == "auto"
    assert humidity_mode_select._pending is None


# ---------------------------------------------------------------------------
# Humidity target number
# ---------------------------------------------------------------------------

@pytest.fixture
def humidity_target_number(mock_coordinator):
    device = _coordinator_with_thm(mock_coordinator)
    num = ThmHumidityTargetNumber(
        mock_coordinator, THM_DEVICE_ID, device, MOCK_BUILDING_ID
    )
    num.async_write_ha_state = MagicMock()
    return num


def test_humidity_target_native_value(humidity_target_number):
    assert humidity_target_number.native_value == 40.0


def test_humidity_target_range_metadata(humidity_target_number):
    assert humidity_target_number._attr_native_min_value == 0
    assert humidity_target_number._attr_native_max_value == 100
    assert humidity_target_number._attr_native_step == 1
    assert humidity_target_number._attr_native_unit_of_measurement == "%"


async def test_humidity_target_set_calls_setter(humidity_target_number, patched_thm):
    humidity_target_number.coordinator.async_request_refresh = AsyncMock()
    await humidity_target_number.async_set_native_value(45)
    patched_thm.set_humidity_target.assert_awaited_once_with(45)
    humidity_target_number.coordinator.async_request_refresh.assert_awaited()


async def test_humidity_target_rounds_float_to_int(
    humidity_target_number, patched_thm
):
    humidity_target_number.coordinator.async_request_refresh = AsyncMock()
    await humidity_target_number.async_set_native_value(42.7)
    patched_thm.set_humidity_target.assert_awaited_once_with(43)


async def test_humidity_target_swallows_error(
    humidity_target_number, patched_thm, caplog
):
    patched_thm.set_humidity_target.side_effect = RuntimeError("nope")
    await humidity_target_number.async_set_native_value(50)
    assert "Failed to set THM humidity target" in caplog.text


async def test_humidity_target_optimistic(
    humidity_target_number, patched_thm, mock_coordinator
):
    humidity_target_number.coordinator.async_request_refresh = AsyncMock()
    assert humidity_target_number.native_value == 40.0

    await humidity_target_number.async_set_native_value(45)
    assert humidity_target_number.native_value == 45.0
    assert humidity_target_number._pending == 45

    _coordinator_with_thm(mock_coordinator, humidity_target=45)
    assert humidity_target_number.native_value == 45.0
    assert humidity_target_number._pending is None


# ---------------------------------------------------------------------------
# Coordinator extraction (raw device dict → parameters)
# ---------------------------------------------------------------------------

async def test_coordinator_extracts_pgmble_usehum_hmt():
    """``_extract_thm_parameters`` reads pgmble/useHum/hmT directly off the device."""
    from custom_components.hbx_controls.coordinator import _extract_thm_parameters

    device_helper = MagicMock()
    # All getters return None / raise so only the raw-field path matters.
    device_helper.get_device_info = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_setpoint = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_room_temperature = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_floor_temperature = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_humidity = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_changeover_mode = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_thm_mode = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_fan_mode = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_is_heating = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_is_cooling = AsyncMock(side_effect=Exception("unused"))
    device_helper.get_away_mode = AsyncMock(side_effect=Exception("unused"))

    device = {"pgmble": 1, "useHum": 2, "hmT": 45}
    params = await _extract_thm_parameters(device_helper, device)

    assert params["schedule_enabled"] is True
    assert params["humidity_mode"] == "auto"
    assert params["humidity_target"] == 45


async def test_coordinator_omits_thm_fields_when_absent():
    from custom_components.hbx_controls.coordinator import _extract_thm_parameters

    device_helper = MagicMock()
    for attr in (
        "get_device_info", "get_setpoint", "get_room_temperature",
        "get_floor_temperature", "get_humidity", "get_changeover_mode",
        "get_thm_mode", "get_fan_mode", "get_is_heating", "get_is_cooling",
        "get_away_mode",
    ):
        setattr(device_helper, attr, AsyncMock(side_effect=Exception("unused")))

    params = await _extract_thm_parameters(device_helper, {})
    assert "schedule_enabled" not in params
    assert "humidity_mode" not in params
    assert "humidity_target" not in params


@pytest.mark.parametrize(
    "use_hum,expected",
    [(0, "off"), (1, "on"), (2, "auto")],
)
async def test_coordinator_humidity_mode_mapping(use_hum, expected):
    from custom_components.hbx_controls.coordinator import _extract_thm_parameters

    device_helper = MagicMock()
    for attr in (
        "get_device_info", "get_setpoint", "get_room_temperature",
        "get_floor_temperature", "get_humidity", "get_changeover_mode",
        "get_thm_mode", "get_fan_mode", "get_is_heating", "get_is_cooling",
        "get_away_mode",
    ):
        setattr(device_helper, attr, AsyncMock(side_effect=Exception("unused")))

    params = await _extract_thm_parameters(device_helper, {"useHum": use_hum})
    assert params["humidity_mode"] == expected
