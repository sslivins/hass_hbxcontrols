"""Fixtures for HBX Controls tests."""
from __future__ import annotations

import tempfile
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.hbx_controls.const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.hbx_controls.coordinator import HBXControlsDataUpdateCoordinator


# ---------------------------------------------------------------------------
# hass fixture (standalone, no pytest-homeassistant-custom-component needed)
# ---------------------------------------------------------------------------

@pytest.fixture
async def hass(tmp_path):
    """Create a Home Assistant instance for testing."""
    hass = HomeAssistant(str(tmp_path))
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries._entries = {}
    hass.config_entries._domain_index = {}
    hass.config_entries.async_reload = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.states = MagicMock()
    hass.bus = MagicMock()
    hass.bus.async_listen_once = MagicMock()
    hass.bus.async_fire = MagicMock()
    yield hass
    try:
        await hass.async_stop(force=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Reusable test data builders
# ---------------------------------------------------------------------------

MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "test_password"
MOCK_DEVICE_ID = "ABC123"
MOCK_BUILDING_ID = "building_1"


def make_config_entry_data(
    username: str = MOCK_USERNAME,
    password: str = MOCK_PASSWORD,
    scan_interval: int = DEFAULT_SCAN_INTERVAL,
) -> dict[str, Any]:
    """Build a config entry data dict."""
    return {
        CONF_USERNAME: username,
        CONF_PASSWORD: password,
        CONF_SCAN_INTERVAL: scan_interval,
    }


def make_device(
    device_id: str = MOCK_DEVICE_ID,
    name: str = "Test ECO",
    device_type: str = "ECO",
    building_id: str = MOCK_BUILDING_ID,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a fake device dict as returned by the coordinator."""
    if parameters is None:
        parameters = make_full_parameters()

    return {
        "id": device_id,
        "syncCode": device_id,
        "name": name,
        "deviceType": device_type,
        "type": device_type,
        "building_id": building_id,
        "parameters": parameters,
    }


_UNSET = object()  # sentinel for "use default"


def make_full_parameters(
    temperature_tank: float = 120.0,
    target_temperature_tank: float = 125.0,
    temperature_outdoor: float = 35.0,
    hot_tank_min_temp: float = 100.0,
    hot_tank_max_temp: float = 140.0,
    hot_tank_outdoor_reset: Any = "off",
    cold_tank_min_temp: float = 40.0,
    cold_tank_max_temp: float = 55.0,
    cold_tank_outdoor_reset: Any = "off",
    hvac_mode: str = "heat",
    permanent_heat_demand: bool = False,
    permanent_cool_demand: bool = False,
    warm_weather_shutdown: Any = "off",
    cold_weather_shutdown: Any = "off",
    firmware_version: str = "1.2.3",
    device_type: str = "ECO",
    heatpump_stages: list[dict] | None | object = _UNSET,
    backup_state: dict | None | object = _UNSET,
    stage_on_lag_time: int = 10,
    stage_off_lag_time: int = 30,
    rotate_cycles: Any = "off",
    rotate_time: Any = "off",
    off_staging: bool = False,
    backup_lag_time: Any = "off",
    backup_differential: Any = "off",
    hot_tank_differential: float = 4.0,
    cold_tank_differential: float = 4.0,
    backup_only_outdoor_temp: Any = "off",
    number_of_stages: int = 2,
    backup_temp: Any = "off",
    wide_priority_differential: Any = "off",
    weather_shutdown_lag_time: int = 0,
    two_stage_heat_pump: bool = False,
    heat_cool_switch_delay: int = 60,
    backup_only_tank_temp: Any = "off",
) -> dict[str, Any]:
    """Build a complete set of device parameters for testing."""
    if heatpump_stages is _UNSET:
        heatpump_stages = [
            {"title": "Stage 1", "activated": True, "runTime": "100:05:30"},
            {"title": "Stage 2", "activated": False, "runTime": "50:10:00"},
        ]

    if backup_state is _UNSET:
        backup_state = {"title": "Backup", "activated": False, "runTime": "10:00:00"}

    return {
        "temperature_tank": temperature_tank,
        "target_temperature_tank": target_temperature_tank,
        "temperature_outdoor": temperature_outdoor,
        "hot_tank_min_temp": hot_tank_min_temp,
        "hot_tank_max_temp": hot_tank_max_temp,
        "hot_tank_outdoor_reset": hot_tank_outdoor_reset,
        "cold_tank_min_temp": cold_tank_min_temp,
        "cold_tank_max_temp": cold_tank_max_temp,
        "cold_tank_outdoor_reset": cold_tank_outdoor_reset,
        "hvac_mode": hvac_mode,
        "permanent_heat_demand": permanent_heat_demand,
        "permanent_cool_demand": permanent_cool_demand,
        "warm_weather_shutdown": warm_weather_shutdown,
        "cold_weather_shutdown": cold_weather_shutdown,
        "firmware_version": firmware_version,
        "device_type": device_type,
        "heatpump_stages": heatpump_stages,
        "backup_state": backup_state,
        "stage_on_lag_time": stage_on_lag_time,
        "stage_off_lag_time": stage_off_lag_time,
        "rotate_cycles": rotate_cycles,
        "rotate_time": rotate_time,
        "off_staging": off_staging,
        "backup_lag_time": backup_lag_time,
        "backup_differential": backup_differential,
        "hot_tank_differential": hot_tank_differential,
        "cold_tank_differential": cold_tank_differential,
        "backup_only_outdoor_temp": backup_only_outdoor_temp,
        "number_of_stages": number_of_stages,
        "backup_temp": backup_temp,
        "wide_priority_differential": wide_priority_differential,
        "weather_shutdown_lag_time": weather_shutdown_lag_time,
        "two_stage_heat_pump": two_stage_heat_pump,
        "heat_cool_switch_delay": heat_cool_switch_delay,
        "backup_only_tank_temp": backup_only_tank_temp,
    }


def make_coordinator_data(
    devices: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """Build coordinator.data as returned by _async_update_data."""
    if devices is None:
        devices = {MOCK_DEVICE_ID: make_device()}

    return {
        "profile": {"username": MOCK_USERNAME},
        "buildings": [{"id": MOCK_BUILDING_ID, "name": "Test Building"}],
        "devices": devices,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> ConfigEntry:
    """Return a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.title = f"HBX Controls ({MOCK_USERNAME})"
    entry.data = make_config_entry_data()
    entry.options = {}
    entry.unique_id = f"HBX Controls ({MOCK_USERNAME})"
    entry.version = 1
    entry.minor_version = 1
    entry.source = "user"
    entry.state = MagicMock()
    return entry


@pytest.fixture
def mock_coordinator(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> HBXControlsDataUpdateCoordinator:
    """Return a coordinator with fake data already loaded."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.data = make_coordinator_data()
    coordinator.last_update_success = True
    # Replace sensorlinx with a mock so no real API calls happen
    coordinator.sensorlinx = MagicMock()
    return coordinator


@pytest.fixture
def mock_coordinator_no_data(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> HBXControlsDataUpdateCoordinator:
    """Return a coordinator with no data (simulating failed update)."""
    coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
    coordinator.data = None
    coordinator.last_update_success = False
    coordinator.sensorlinx = MagicMock()
    return coordinator


@pytest.fixture
def mock_setup_coordinator(mock_coordinator):
    """Patch the coordinator setup so platform tests can load entities."""
    with patch(
        "custom_components.hbx_controls.HBXControlsDataUpdateCoordinator",
        return_value=mock_coordinator,
    ), patch.object(
        mock_coordinator,
        "async_config_entry_first_refresh",
        new_callable=AsyncMock,
    ):
        yield mock_coordinator
