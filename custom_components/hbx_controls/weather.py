"""Platform for weather integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HBXControlsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _owm_id_to_ha_condition(weather_id: int | None) -> str | None:
    """Map an OpenWeatherMap condition ID to a Home Assistant condition string."""
    if weather_id is None:
        return None
    group = weather_id // 100
    if group == 2:
        return "lightning-rainy"
    if group == 3:
        return "rainy"
    if group == 5:
        if weather_id in (502, 503, 504, 522, 531):
            return "pouring"
        return "rainy"
    if group == 6:
        return "snowy"
    if group == 7:
        return "fog"
    if weather_id == 800:
        return "sunny"
    if weather_id == 801:
        return "partlycloudy"
    if weather_id in (802, 803, 804):
        return "cloudy"
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the weather platform."""
    coordinator: HBXControlsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[HBXWeather] = []

    if coordinator.data and "weather" in coordinator.data:
        buildings = coordinator.data.get("buildings", [])
        building_map = {b["id"]: b for b in buildings if "id" in b}

        for building_id, weather_data in coordinator.data["weather"].items():
            if "current" in weather_data:
                building = building_map.get(building_id, {})
                entities.append(
                    HBXWeather(
                        coordinator,
                        building_id,
                        building,
                    )
                )

    async_add_entities(entities)


class HBXWeather(CoordinatorEntity, WeatherEntity):
    """Representation of HBX Controls weather data for a building."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.MILES_PER_HOUR
    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        building_id: str,
        building: dict[str, Any],
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._building_id = building_id
        self._attr_unique_id = f"{building_id}_weather"
        self._attr_name = "Weather"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, building_id)},
            "name": building.get("name", building_id),
            "manufacturer": "HBX Controls",
        }

    @property
    def _weather_data(self) -> dict[str, Any]:
        """Return the current weather data dict for this building."""
        if self.coordinator.data and "weather" in self.coordinator.data:
            return self.coordinator.data["weather"].get(self._building_id, {})
        return {}

    @property
    def _current(self) -> dict[str, Any] | None:
        """Return the current conditions dict."""
        return self._weather_data.get("current")

    @property
    def available(self) -> bool:
        """Return True if weather data is available."""
        return super().available and self._current is not None

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        current = self._current
        if current and "temp" in current:
            temp = current["temp"]
            return temp.value if hasattr(temp, "value") else temp
        return None

    @property
    def native_apparent_temperature(self) -> float | None:
        """Return the feels-like temperature."""
        current = self._current
        if current and "feelsLike" in current:
            temp = current["feelsLike"]
            return temp.value if hasattr(temp, "value") else temp
        return None

    @property
    def humidity(self) -> int | None:
        """Return the humidity."""
        current = self._current
        if current:
            return current.get("humidity")
        return None

    @property
    def native_pressure(self) -> float | None:
        """Return the atmospheric pressure in hPa."""
        current = self._current
        if current:
            return current.get("pressure")
        return None

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        current = self._current
        if current:
            return current.get("wind")
        return None

    @property
    def wind_bearing(self) -> int | None:
        """Return the wind bearing in degrees."""
        current = self._current
        if current:
            return current.get("windDir")
        return None

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        current = self._current
        if current:
            return _owm_id_to_ha_condition(current.get("weatherId"))
        return None

    async def async_forecast_service_handler(
        self,
        service: str,
    ) -> list[Forecast] | None:
        """Return the hourly forecast."""
        return self._build_forecast()

    def _build_forecast(self) -> list[Forecast] | None:
        """Build the forecast list from coordinator data."""
        weather_data = self._weather_data
        forecast_data = weather_data.get("forecast")
        if not forecast_data:
            return None

        forecasts: list[Forecast] = []
        for period in forecast_data:
            temp = period.get("temp")
            temp_low = period.get("min")
            temp_high = period.get("max")
            fc_time = period.get("time")

            forecast: Forecast = {
                "datetime": fc_time.isoformat() if hasattr(fc_time, "isoformat") else str(fc_time),
                "native_temperature": temp.value if hasattr(temp, "value") else temp,
                "native_templow": temp_low.value if hasattr(temp_low, "value") else temp_low,
                "condition": _owm_id_to_ha_condition(period.get("weatherId")),
                "precipitation_probability": period.get("pop"),
            }
            forecasts.append(forecast)

        return forecasts
