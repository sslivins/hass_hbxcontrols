"""Tests for the coordinator optimistic-write override mechanism.

These guard the fix for the SensorLinx eventual-consistency race: a poll
that lands inside the cloud's write-propagation window must not revert a
value the user just set.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.coordinator import (
    HBXControlsDataUpdateCoordinator,
)
from custom_components.hbx_controls.number import StageOnLagTime
from custom_components.hbx_controls.switch import WarmWeatherShutdownSwitch

from .conftest import (
    MOCK_BUILDING_ID,
    MOCK_DEVICE_ID,
    make_coordinator_data,
    make_device,
    make_full_parameters,
)


class _FakeTemp:
    """Minimal Temperature stand-in exposing ``.value`` like pysensorlinx."""

    def __init__(self, value: float) -> None:
        self.value = value


# ---------------------------------------------------------------------------
# _values_match
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (_FakeTemp(12.8), _FakeTemp(12.83), True),   # within tolerance
        (_FakeTemp(12.8), 12.8, True),               # Temperature vs float
        (_FakeTemp(12.8), _FakeTemp(15.0), False),   # far apart
        (12.0, 12.05, True),                         # float tolerance
        ("off", "off", True),
        (_FakeTemp(60.0), "off", False),             # temp vs disabled sentinel
        (True, True, True),
        (True, False, False),
        ("heat", "cool", False),
        (10, 10, True),
        (None, None, True),
    ],
)
def test_values_match(a, b, expected):
    """The tolerant comparator behaves across types the extractor stores."""
    assert HBXControlsDataUpdateCoordinator._values_match(a, b) is expected


# ---------------------------------------------------------------------------
# set_parameter_override / _apply_overrides
# ---------------------------------------------------------------------------


def test_override_applies_immediately(mock_coordinator):
    """Setting an override mutates coordinator.data and pushes to listeners."""
    with patch.object(
        mock_coordinator, "async_set_updated_data"
    ) as push:
        mock_coordinator.set_parameter_override(
            MOCK_DEVICE_ID, {"stage_on_lag_time": 15}
        )

    params = mock_coordinator.data["devices"][MOCK_DEVICE_ID]["parameters"]
    assert params["stage_on_lag_time"] == 15
    push.assert_called_once()


def test_stale_poll_does_not_revert_within_ttl(mock_coordinator):
    """A fresh poll carrying the OLD value is overridden back to the new one."""
    mock_coordinator.set_parameter_override(
        MOCK_DEVICE_ID, {"stage_on_lag_time": 15}
    )

    # Simulate a fresh poll where the cloud still reports the old value.
    stale = make_coordinator_data(
        devices={
            MOCK_DEVICE_ID: make_device(
                parameters=make_full_parameters(stage_on_lag_time=10)
            )
        }
    )["devices"]

    mock_coordinator._apply_overrides(stale)

    assert stale[MOCK_DEVICE_ID]["parameters"]["stage_on_lag_time"] == 15
    # Override is still pending (not yet confirmed by the cloud).
    assert MOCK_DEVICE_ID in mock_coordinator._overrides


def test_override_clears_when_poll_confirms(mock_coordinator):
    """Once the cloud reports the written value, the override is dropped."""
    mock_coordinator.set_parameter_override(
        MOCK_DEVICE_ID, {"stage_on_lag_time": 15}
    )

    confirmed = make_coordinator_data(
        devices={
            MOCK_DEVICE_ID: make_device(
                parameters=make_full_parameters(stage_on_lag_time=15)
            )
        }
    )["devices"]

    mock_coordinator._apply_overrides(confirmed)

    assert confirmed[MOCK_DEVICE_ID]["parameters"]["stage_on_lag_time"] == 15
    assert MOCK_DEVICE_ID not in mock_coordinator._overrides


def test_override_expires_after_ttl(mock_coordinator):
    """After the TTL elapses the override yields to the polled value."""
    with patch(
        "custom_components.hbx_controls.coordinator.time.monotonic",
        return_value=1000.0,
    ):
        mock_coordinator.set_parameter_override(
            MOCK_DEVICE_ID, {"stage_on_lag_time": 15}, ttl=120
        )

    stale = make_coordinator_data(
        devices={
            MOCK_DEVICE_ID: make_device(
                parameters=make_full_parameters(stage_on_lag_time=10)
            )
        }
    )["devices"]

    # Jump past the TTL window.
    with patch(
        "custom_components.hbx_controls.coordinator.time.monotonic",
        return_value=1000.0 + 121,
    ):
        mock_coordinator._apply_overrides(stale)

    assert stale[MOCK_DEVICE_ID]["parameters"]["stage_on_lag_time"] == 10
    assert MOCK_DEVICE_ID not in mock_coordinator._overrides


def test_override_ttl_scales_with_scan_interval(hass, mock_config_entry):
    """TTL is at least two poll cycles and never below the 120s floor."""
    mock_config_entry.data = {**mock_config_entry.data, "scan_interval": 300}
    coord = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    assert coord.override_ttl == 600

    mock_config_entry.data = {**mock_config_entry.data, "scan_interval": 30}
    coord = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    assert coord.override_ttl == 120


def test_typed_override_survives_stale_temperature_poll(mock_coordinator):
    """A Temperature-typed override holds against a stale Temperature poll."""
    written = _FakeTemp(88.0)
    mock_coordinator.set_parameter_override(
        MOCK_DEVICE_ID, {"warm_weather_shutdown": written}
    )

    stale = make_coordinator_data(
        devices={
            MOCK_DEVICE_ID: make_device(
                parameters=make_full_parameters(warm_weather_shutdown="off")
            )
        }
    )["devices"]

    mock_coordinator._apply_overrides(stale)

    assert stale[MOCK_DEVICE_ID]["parameters"]["warm_weather_shutdown"] is written


# ---------------------------------------------------------------------------
# End-to-end: a platform setter registers the override
# ---------------------------------------------------------------------------


async def test_number_setter_registers_override(hass: HomeAssistant, mock_coordinator):
    """StageOnLagTime.async_set_native_value records the optimistic value."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = StageOnLagTime(
        mock_coordinator, MOCK_DEVICE_ID, make_device(), MOCK_BUILDING_ID
    )
    with patch(
        "custom_components.hbx_controls.number.SensorlinxDevice",
        return_value=AsyncMock(),
    ):
        await entity.async_set_native_value(15.0)

    params = mock_coordinator.data["devices"][MOCK_DEVICE_ID]["parameters"]
    assert params["stage_on_lag_time"] == 15
    assert entity.native_value == 15


async def test_switch_turn_on_off_register_override(
    hass: HomeAssistant, mock_coordinator
):
    """The warm-weather-shutdown switch overrides both on ('temp') and off."""
    mock_coordinator.async_request_refresh = AsyncMock()
    entity = WarmWeatherShutdownSwitch(
        mock_coordinator, MOCK_DEVICE_ID, make_device(), MOCK_BUILDING_ID
    )
    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=AsyncMock(),
    ):
        await entity.async_turn_on()
    assert entity.is_on is True  # override holds a Temperature (not "off")

    with patch(
        "custom_components.hbx_controls.switch.SensorlinxDevice",
        return_value=AsyncMock(),
    ):
        await entity.async_turn_off()
    params = mock_coordinator.data["devices"][MOCK_DEVICE_ID]["parameters"]
    assert params["warm_weather_shutdown"] == "off"
    assert entity.is_on is False
