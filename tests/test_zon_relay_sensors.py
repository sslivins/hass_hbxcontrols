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


async def test_setup_uses_relay_types_length_when_relays_is_superset(
    hass, mock_coordinator, mock_config_entry
):
    """
    Real-hardware regression (issue #12): the HBX cloud API returns a
    16-element ``relays`` array on every ZON regardless of physical zone
    count. ``relType`` (HBX) -> ``relay_types`` (our coordinator) is the
    authoritative source of zone count and per-slot wiring state. A
    4-zone ZON-0224 with 3 zones wired must yield 3 entities, not 15.
    """
    _coordinator_with_zon(
        mock_coordinator,
        relays=[False] * 16,
        relay_types=[1, 1, 1, 0],  # eelton's AZON-0224
    )
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    relay_entities = [e for e in entities if isinstance(e, ZonRelayDemandBinarySensor)]
    assert len(relay_entities) == 3
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


async def test_setup_skips_when_relays_and_relay_types_both_missing(
    hass, mock_coordinator, mock_config_entry
):
    """Devices without any relay info at all yield no relay sensors."""
    _coordinator_with_zon(mock_coordinator, relays=[], relay_types=[])
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


# ---------------------------------------------------------------------------
# Sequence-aware zone numbering (issue #12, hbxtesting3.docx).
# The HBX mobile app numbers zones by absolute wired position across
# stacked ZON controllers: a Secondary at sequence=1 calls its slots
# Zone 5/6/7. Friendly names mirror that; unique_ids stay raw-index.
# ---------------------------------------------------------------------------


def test_naming_primary_sequence_zero(mock_coordinator):
    """sequence=0 (Primary) names slots Zone 1/2/3 — regression guard."""
    device = _coordinator_with_zon(mock_coordinator)
    sw0 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 0, 0)
    sw1 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 1, 0)
    sw2 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 2, 0)
    assert sw0._attr_name.endswith("Zone 1")
    assert sw1._attr_name.endswith("Zone 2")
    assert sw2._attr_name.endswith("Zone 3")


def test_naming_secondary_sequence_one_yields_zones_5_6_7(mock_coordinator):
    """sequence=1 + relType=[1,1,1,0] -> Zone 5/6/7 (hbxtesting3 dump #1)."""
    device = _coordinator_with_zon(mock_coordinator)
    sw0 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 0, 1)
    sw1 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 1, 1)
    sw2 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 2, 1)
    assert sw0._attr_name.endswith("Zone 5")
    assert sw1._attr_name.endswith("Zone 6")
    assert sw2._attr_name.endswith("Zone 7")


def test_naming_secondary_sequence_two_yields_zones_9_10_11(mock_coordinator):
    """sequence=2 + relType=[1,1,1,0] -> Zone 9/10/11 (hbxtesting3 dump #2)."""
    device = _coordinator_with_zon(mock_coordinator)
    sw0 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 0, 2)
    sw1 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 1, 2)
    sw2 = ZonRelayDemandBinarySensor(mock_coordinator, ZON_DEVICE_ID, device, 2, 2)
    assert sw0._attr_name.endswith("Zone 9")
    assert sw1._attr_name.endswith("Zone 10")
    assert sw2._attr_name.endswith("Zone 11")


def test_unique_id_does_not_change_with_sequence(mock_coordinator):
    """unique_id MUST stay raw-index so registry survives sequence relabels."""
    device = _coordinator_with_zon(mock_coordinator)
    sw_primary = ZonRelayDemandBinarySensor(
        mock_coordinator, ZON_DEVICE_ID, device, 0, 0
    )
    sw_secondary = ZonRelayDemandBinarySensor(
        mock_coordinator, ZON_DEVICE_ID, device, 0, 2
    )
    assert sw_primary._attr_unique_id == sw_secondary._attr_unique_id
    assert sw_primary._attr_unique_id.endswith("_zon_relay_0")


async def test_setup_propagates_zone_sequence_to_entity_names(
    hass, mock_coordinator, mock_config_entry
):
    """async_setup_entry reads zone_sequence and offsets entity names."""
    _coordinator_with_zon(mock_coordinator, zone_sequence=1)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    relay_entities = [
        e for e in entities if isinstance(e, ZonRelayDemandBinarySensor)
    ]
    assert len(relay_entities) == 3
    names = sorted(e._attr_name for e in relay_entities)
    assert names[0].endswith("Zone 5")
    assert names[1].endswith("Zone 6")
    assert names[2].endswith("Zone 7")


async def test_setup_handles_missing_zone_sequence(
    hass, mock_coordinator, mock_config_entry
):
    """When zone_sequence is missing, default to Primary numbering (1/2/3)."""
    _coordinator_with_zon(mock_coordinator)  # no zone_sequence set
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    relay_entities = [
        e for e in entities if isinstance(e, ZonRelayDemandBinarySensor)
    ]
    names = sorted(e._attr_name for e in relay_entities)
    assert names[0].endswith("Zone 1")
    assert names[1].endswith("Zone 2")
    assert names[2].endswith("Zone 3")


# ---------------------------------------------------------------------------
# Stale-entity cleanup migration (issue #12 followup).
# Pre-2.5.0b5 installs created up to 16 zone entities per ZON; b5+ trims
# the list using relType. The registry remembers everything, so users
# upgrading see zones 5-16 lingering as "unavailable". On setup, we walk
# the registry and prune <device>_zon_relay_<n> entries not in the
# active set built this run. Strict scope: only _zon_relay_<n>.
# ---------------------------------------------------------------------------


async def test_setup_purges_stale_zon_zone_registry_entries(
    hass, mock_coordinator, mock_config_entry
):
    """Stale zon_relay registry entries are removed on setup."""
    from homeassistant.helpers import entity_registry as er

    # Bootstrap a real entity registry on the mock hass.
    registry = er.EntityRegistry(hass)
    await registry.async_load()
    hass.data[er.DATA_REGISTRY] = registry
    mock_config_entry.pref_disable_new_entities = False

    _coordinator_with_zon(mock_coordinator)  # active: idx 0/1/2 (3 zones)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    # Simulate a pre-b5 install: zones 0-15 all have registry entries
    # under this config entry. b5+ only re-creates 0/1/2.
    stale_entity_ids = []
    for idx in range(16):
        entry = registry.async_get_or_create(
            "binary_sensor",
            DOMAIN,
            f"{ZON_DEVICE_ID}_zon_relay_{idx}",
            config_entry=mock_config_entry,
            suggested_object_id=f"zone_ctrl_zone_{idx + 1}",
        )
        if idx >= 3:
            stale_entity_ids.append(entry.entity_id)

    # Sanity: also create a non-zone entity that must NOT be touched.
    other = registry.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        f"{ZON_DEVICE_ID}_some_other_thing",
        config_entry=mock_config_entry,
        suggested_object_id="zone_ctrl_other",
    )

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    # Stale ones (idx 3..15) should be gone.
    for entity_id in stale_entity_ids:
        assert registry.async_get(entity_id) is None, (
            f"Stale entity {entity_id} should have been purged"
        )

    # Active ones (idx 0..2) and the non-zone entity must remain.
    assert registry.async_get(other.entity_id) is not None
    assert (
        registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{ZON_DEVICE_ID}_zon_relay_0"
        )
        is not None
    )


async def test_setup_purge_does_not_touch_other_unique_id_patterns(
    hass, mock_coordinator, mock_config_entry
):
    """Cleanup only matches '_zon_relay_'; other patterns are preserved."""
    from homeassistant.helpers import entity_registry as er

    registry = er.EntityRegistry(hass)
    await registry.async_load()
    hass.data[er.DATA_REGISTRY] = registry
    mock_config_entry.pref_disable_new_entities = False

    _coordinator_with_zon(mock_coordinator)
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = mock_coordinator

    survivors = []
    for unique_id in (
        f"{ZON_DEVICE_ID}_running",
        f"{ZON_DEVICE_ID}_pump_1",
        f"{ZON_DEVICE_ID}_demand_HD",
        "OTHER_DEVICE_thermostat_running",
    ):
        entry = registry.async_get_or_create(
            "binary_sensor",
            DOMAIN,
            unique_id,
            config_entry=mock_config_entry,
            suggested_object_id=unique_id.lower(),
        )
        survivors.append(entry.entity_id)

    entities = []
    await async_setup_entry(hass, mock_config_entry, entities.extend)

    for entity_id in survivors:
        assert registry.async_get(entity_id) is not None, (
            f"{entity_id} should not have been touched by zon_relay cleanup"
        )
