"""Tests for the HBX Controls weather platform."""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest

from custom_components.hbx_controls.weather import (
    HBXWeather,
    _owm_id_to_ha_condition,
    async_setup_entry,
)

from .conftest import (
    MOCK_BUILDING_ID,
    make_coordinator_data,
    make_weather_data,
)


# ---------------------------------------------------------------------------
# OWM condition mapping tests
# ---------------------------------------------------------------------------


class TestOWMConditionMapping:
    """Tests for _owm_id_to_ha_condition."""

    @pytest.mark.parametrize(
        "weather_id, expected",
        [
            (200, "lightning-rainy"),
            (211, "lightning-rainy"),
            (232, "lightning-rainy"),
            (300, "rainy"),
            (321, "rainy"),
            (500, "rainy"),
            (501, "rainy"),
            (502, "pouring"),
            (503, "pouring"),
            (504, "pouring"),
            (522, "pouring"),
            (531, "pouring"),
            (600, "snowy"),
            (622, "snowy"),
            (701, "fog"),
            (741, "fog"),
            (781, "fog"),
            (800, "sunny"),
            (801, "partlycloudy"),
            (802, "cloudy"),
            (803, "cloudy"),
            (804, "cloudy"),
            (None, None),
            (999, None),
        ],
    )
    def test_owm_mapping(self, weather_id, expected):
        """Test OWM weather ID mapping to HA conditions."""
        assert _owm_id_to_ha_condition(weather_id) == expected


# ---------------------------------------------------------------------------
# Setup tests
# ---------------------------------------------------------------------------


class TestWeatherSetup:
    """Tests for weather platform setup."""

    @pytest.mark.asyncio
    async def test_setup_creates_weather_entity(
        self, hass, mock_coordinator
    ):
        """Test that a weather entity is created for a building with weather data."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        weather_entities = [e for e in entities if isinstance(e, HBXWeather)]
        assert len(weather_entities) == 1
        assert weather_entities[0]._building_id == MOCK_BUILDING_ID

    @pytest.mark.asyncio
    async def test_setup_no_weather_data(self, hass, mock_config_entry):
        """Test that no weather entities are created when weather data is absent."""
        from custom_components.hbx_controls.coordinator import HBXControlsDataUpdateCoordinator
        from custom_components.hbx_controls.const import DOMAIN

        coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
        coordinator.data = make_coordinator_data(weather={})
        coordinator.last_update_success = True
        coordinator.sensorlinx = MagicMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        entities = []
        await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

        weather_entities = [e for e in entities if isinstance(e, HBXWeather)]
        assert len(weather_entities) == 0

    @pytest.mark.asyncio
    async def test_setup_no_current_weather(self, hass, mock_config_entry):
        """Test no entity when building has forecast but no current conditions."""
        from custom_components.hbx_controls.coordinator import HBXControlsDataUpdateCoordinator
        from custom_components.hbx_controls.const import DOMAIN

        coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
        weather_no_current = {MOCK_BUILDING_ID: {"forecast": []}}
        coordinator.data = make_coordinator_data(weather=weather_no_current)
        coordinator.last_update_success = True
        coordinator.sensorlinx = MagicMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        entities = []
        await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

        weather_entities = [e for e in entities if isinstance(e, HBXWeather)]
        assert len(weather_entities) == 0


# ---------------------------------------------------------------------------
# Entity property tests
# ---------------------------------------------------------------------------


class TestWeatherProperties:
    """Tests for HBXWeather entity properties."""

    @pytest.mark.asyncio
    async def test_unique_id(self, hass, mock_coordinator):
        """Test the unique ID format."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.unique_id == f"{MOCK_BUILDING_ID}_weather"

    @pytest.mark.asyncio
    async def test_native_temperature(self, hass, mock_coordinator):
        """Test current temperature property."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.native_temperature == 72.0

    @pytest.mark.asyncio
    async def test_native_apparent_temperature(self, hass, mock_coordinator):
        """Test feels-like temperature property."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.native_apparent_temperature == 70.0

    @pytest.mark.asyncio
    async def test_humidity(self, hass, mock_coordinator):
        """Test humidity property."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.humidity == 55

    @pytest.mark.asyncio
    async def test_native_pressure(self, hass, mock_coordinator):
        """Test atmospheric pressure property."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.native_pressure == 1013

    @pytest.mark.asyncio
    async def test_native_wind_speed(self, hass, mock_coordinator):
        """Test wind speed property."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.native_wind_speed == 10.5

    @pytest.mark.asyncio
    async def test_wind_bearing(self, hass, mock_coordinator):
        """Test wind bearing property."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.wind_bearing == 180

    @pytest.mark.asyncio
    async def test_condition(self, hass, mock_coordinator):
        """Test weather condition mapping (802 → cloudy)."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.condition == "cloudy"

    @pytest.mark.asyncio
    async def test_available_with_data(self, hass, mock_coordinator):
        """Test entity is available when weather data is present."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.available is True

    @pytest.mark.asyncio
    async def test_device_info(self, hass, mock_coordinator):
        """Test device info references the building."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        info = entity.device_info
        assert (DOMAIN, MOCK_BUILDING_ID) in info["identifiers"]
        assert info["name"] == "Test Building"
        assert info["manufacturer"] == "HBX Controls"


# ---------------------------------------------------------------------------
# Forecast tests
# ---------------------------------------------------------------------------


class TestWeatherForecast:
    """Tests for weather forecast."""

    @pytest.mark.asyncio
    async def test_build_forecast(self, hass, mock_coordinator):
        """Test forecast list is built correctly."""
        entities = []
        await async_setup_entry(hass, MagicMock(), lambda e: entities.extend(e))

        entity = entities[0]
        forecast = entity._build_forecast()
        assert forecast is not None
        assert len(forecast) == 1

        fc = forecast[0]
        assert fc["native_temperature"] == 68.0
        assert fc["native_templow"] == 60.0
        assert fc["condition"] == "rainy"
        assert fc["precipitation_probability"] == 20
        assert "2025-01-15" in fc["datetime"]

    @pytest.mark.asyncio
    async def test_build_forecast_none_when_no_data(self, hass, mock_config_entry):
        """Test forecast returns None when no forecast data."""
        from custom_components.hbx_controls.coordinator import HBXControlsDataUpdateCoordinator
        from custom_components.hbx_controls.const import DOMAIN

        coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
        weather_no_forecast = {
            MOCK_BUILDING_ID: make_weather_data(forecast=None),
        }
        coordinator.data = make_coordinator_data(weather=weather_no_forecast)
        coordinator.last_update_success = True
        coordinator.sensorlinx = MagicMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        entities = []
        await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

        entity = entities[0]
        forecast = entity._build_forecast()
        assert forecast is None

    @pytest.mark.asyncio
    async def test_no_current_returns_none_properties(self, hass, mock_config_entry):
        """Test that properties return None when current data is removed."""
        from custom_components.hbx_controls.coordinator import HBXControlsDataUpdateCoordinator
        from custom_components.hbx_controls.const import DOMAIN

        coordinator = HBXControlsDataUpdateCoordinator(hass, mock_config_entry)
        coordinator.data = make_coordinator_data(
            weather={MOCK_BUILDING_ID: make_weather_data()}
        )
        coordinator.last_update_success = True
        coordinator.sensorlinx = MagicMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        entities = []
        await async_setup_entry(hass, mock_config_entry, lambda e: entities.extend(e))

        entity = entities[0]
        assert entity.native_temperature == 72.0

        # Remove current data and verify graceful handling
        coordinator.data["weather"][MOCK_BUILDING_ID].pop("current")
        assert entity.native_temperature is None
        assert entity.native_apparent_temperature is None
        assert entity.humidity is None
        assert entity.native_pressure is None
        assert entity.native_wind_speed is None
        assert entity.wind_bearing is None
        assert entity.condition is None
