"""Tests for the ZON relay demand binary sensors (2.5.0b3)."""
from __future__ import annotations

import pytest

from custom_components.hbx_controls.binary_sensor import (
    ZonRelayDemandBinarySensor,
    async_setup_entry,
)
from custom_components.hbx_controls.const import DOMAIN

from .conftest import MOCK_BUILDING_ID, make_coordinator_data, make_device


ZON_DEVICE_ID = "ZON-001"


def _zon_params(**overrides):
    params = {
        "device_type": "ZON",
        "relays": [False] * 16,
        "relay_types": [1, 1, 1] + [0] * 13,
        "app_button_enabled": False,
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


async def test_setup_creates_one_entity_per_configured_relay(
    hass, mock_coordinator, mock_config_entry
):
    """Only slots with non-zero relay_type get entities."""
    _coordinator_with_zon(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    relay_entities = [e for e in entities if isinstance(e, ZonRelayDemandBinarySensor)]
    assert len(relay_entities) == 3
    # Indices 0..2 are configured.
    assert sorted(e._index for e in relay_entities) == [0, 1, 2]


async def test_setup_falls_back_to_all_slots_when_relay_types_missing(
    hass, mock_coordinator, mock_config_entry
):
    """When relay_types is empty/missing, expose every slot we have data for."""
    _coordinator_with_zon(mock_coordinator, relay_types=[])
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    relay_entities = [e for e in entities if isinstance(e, ZonRelayDemandBinarySensor)]
    assert len(relay_entities) == 16


async def test_setup_skips_when_relays_array_missing(
    hass, mock_coordinator, mock_config_entry
):
    """Devices without a relays array yield no relay sensors."""
    _coordinator_with_zon(mock_coordinator, relays=[])
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    assert not any(isinstance(e, ZonRelayDemandBinarySensor) for e in entities)


def test_is_on_reflects_relay_state(mock_coordinator):
    """is_on tracks the boolean at the entity's index in the relays array."""
    device = _coordinator_with_zon(
        mock_coordinator,
        relays=[True, False, True] + [False] * 13,
    )
    sw0 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 0)
    sw1 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 1)
    sw2 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 2)

    assert sw0.is_on is True
    assert sw1.is_on is False
    assert sw2.is_on is True


def test_is_on_handles_short_relay_array(mock_coordinator):
    """When relays is shorter than expected, is_on returns None for missing slots."""
    device = _coordinator_with_zon(
        mock_coordinator,
        relays=[True, False],
    )
    sw5 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 5)
    assert sw5.is_on is None


def test_unavailable_when_index_out_of_range(mock_coordinator):
    """Entities for indices that disappear from coordinator data go unavailable."""
    device = _coordinator_with_zon(mock_coordinator, relays=[True])
    sw5 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 5)
    mock_coordinator.last_update_success = True
    assert sw5.available is False


def test_naming_is_one_indexed(mock_coordinator):
    """Internal 0-indexed slots surface as 1-indexed names."""
    device = _coordinator_with_zon(mock_coordinator)
    sw = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 0)
    assert sw._attr_name.endswith("Zone 1")
    assert sw._attr_unique_id.endswith("_zon_relay_0")
