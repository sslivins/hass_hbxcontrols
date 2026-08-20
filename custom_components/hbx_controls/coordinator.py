"""DataUpdateCoordinator for HBX Controls."""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from pysensorlinx import (
    InvalidCredentialsError,
    LoginError,
    LoginTimeoutError,
    Sensorlinx,
    DEVICE_TYPE_ECO,
    DEVICE_TYPE_THM,
    DEVICE_TYPE_ZON,
    device_for,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _extract_eco_parameters(device_helper, device: dict) -> dict[str, Any]:
    """
    Extract the historical ECO-shaped parameter set.

    All calls are wrapped in try/except so a single missing field never
    breaks the whole update. Behaviour preserved verbatim from prior
    versions of the coordinator to keep existing ECO installs identical.
    """
    parameters: dict[str, Any] = {}

    # Temperature data
    try:
        temps = await device_helper.get_temperatures(device_info=device)
        if temps:
            for temp_name, temp_data in temps.items():
                if temp_data.get("actual"):
                    parameters[
                        f"temperature_{temp_name.lower().replace(' ', '_')}"
                    ] = temp_data["actual"].value
                if temp_data.get("target"):
                    parameters[
                        f"target_temperature_{temp_name.lower().replace(' ', '_')}"
                    ] = temp_data["target"].value
    except Exception:  # noqa: BLE001
        pass

    async def _grab(key: str, fn, *, default_log: bool = False, transform=None):
        try:
            value = await fn(device_info=device)
            if transform is not None:
                value = transform(value)
            if value is not None or not default_log:
                parameters[key] = value
        except Exception as exc:  # noqa: BLE001
            if default_log:
                _LOGGER.debug("Failed to get %s: %s", key, exc)

    await _grab("permanent_heat_demand", device_helper.get_permanent_heat_demand)
    await _grab("permanent_cool_demand", device_helper.get_permanent_cool_demand)
    try:
        hvac_mode = await device_helper.get_hvac_mode_priority(device_info=device)
        mode_map = {0: "heat", 1: "cool", 2: "auto"}
        parameters["hvac_mode"] = mode_map.get(hvac_mode, "auto")
    except Exception:  # noqa: BLE001
        pass
    await _grab("hot_tank_min_temp", device_helper.get_hot_tank_min_temp)
    await _grab("hot_tank_max_temp", device_helper.get_hot_tank_max_temp)
    await _grab("hot_tank_outdoor_reset", device_helper.get_hot_tank_outdoor_reset)
    await _grab("cold_tank_min_temp", device_helper.get_cold_tank_min_temp)
    await _grab("cold_tank_max_temp", device_helper.get_cold_tank_max_temp)
    await _grab("cold_tank_outdoor_reset", device_helper.get_cold_tank_outdoor_reset)
    await _grab("warm_weather_shutdown", device_helper.get_warm_weather_shutdown)
    await _grab("cold_weather_shutdown", device_helper.get_cold_weather_shutdown)

    try:
        heatpump_stages = await device_helper.get_heatpump_stages_state(device_info=device)
        if heatpump_stages:
            parameters["heatpump_stages"] = heatpump_stages
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Failed to get heatpump_stages: %s", exc)

    try:
        backup_state = await device_helper.get_backup_state(device_info=device)
        if backup_state:
            parameters["backup_state"] = backup_state
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Failed to get backup_state: %s", exc)

    await _grab("stage_on_lag_time", device_helper.get_stage_on_lag_time)
    await _grab("stage_off_lag_time", device_helper.get_stage_off_lag_time)
    await _grab("rotate_cycles", device_helper.get_rotate_cycles)
    await _grab("rotate_time", device_helper.get_rotate_time)
    await _grab("off_staging", device_helper.get_off_staging)
    await _grab("backup_lag_time", device_helper.get_backup_lag_time)
    await _grab("backup_differential", device_helper.get_backup_differential)
    await _grab("hot_tank_differential", device_helper.get_hot_tank_differential)
    await _grab("cold_tank_differential", device_helper.get_cold_tank_differential)
    await _grab("backup_only_outdoor_temp", device_helper.get_backup_only_outdoor_temp)
    await _grab("number_of_stages", device_helper.get_number_of_stages)
    await _grab("backup_temp", device_helper.get_backup_temp)
    await _grab("wide_priority_differential", device_helper.get_wide_priority_differential)
    await _grab("weather_shutdown_lag_time", device_helper.get_weather_shutdown_lag_time)
    await _grab("two_stage_heat_pump", device_helper.get_two_stage_heat_pump)
    await _grab("heat_cool_switch_delay", device_helper.get_heat_cool_switch_delay)
    await _grab("backup_only_tank_temp", device_helper.get_backup_only_tank_temp)
    await _grab("dhw_enabled", device_helper.get_dhw_enabled)
    await _grab("dhw_target_temp", device_helper.get_dhw_target_temp)
    await _grab("dhw_differential", device_helper.get_dhw_differential)

    try:
        dhw_state = await device_helper.get_dhw_state(device_info=device)
        if dhw_state:
            parameters["dhw_state"] = dhw_state
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Failed to get dhw_state: %s", exc)

    return parameters


async def _extract_thm_parameters(device_helper, device: dict) -> dict[str, Any]:
    """Extract THM-specific parameters into a flat dict."""
    parameters: dict[str, Any] = {}

    async def _grab(key: str, coro):
        try:
            value = await coro
            if value is not None:
                parameters[key] = value
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Failed to get %s: %s", key, exc)

    # Temperatures arrive as Temperature objects; flatten to °F floats so
    # they slot into the existing sensor descriptions in sensor.py.
    try:
        room = await device_helper.get_room_temperature(device)
        if room is not None:
            parameters["temperature_room"] = room.value
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("THM room temp: %s", exc)

    try:
        floor = await device_helper.get_floor_temperature(device)
        if floor is not None:
            parameters["temperature_floor"] = floor.value
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("THM floor temp: %s", exc)

    try:
        target = await device_helper.get_target_temperature(device)
        if target is not None:
            parameters["target_temperature_room"] = target.value
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("THM target temp: %s", exc)

    # Dual heat/cool setpoints — pysensorlinx 0.5.2+. Both fields exist
    # at all times in the device payload regardless of changeover mode;
    # rmT = heat target, rmCT = cool target.
    try:
        heat_setpoint = await device_helper.get_heat_setpoint(device)
        if heat_setpoint is not None:
            parameters["heat_setpoint"] = heat_setpoint.value
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("THM heat setpoint: %s", exc)

    try:
        cool_setpoint = await device_helper.get_cool_setpoint(device)
        if cool_setpoint is not None:
            parameters["cool_setpoint"] = cool_setpoint.value
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("THM cool setpoint: %s", exc)

    # Active demand bitfield decoder — pysensorlinx 0.5.2+. Returns a
    # list (subset of {heating, cooling, fan}) that the climate entity
    # uses for hvac_action; the cloud's isCooling flag is unreliable.
    if hasattr(device_helper, "get_active_demands"):
        try:
            demands = await device_helper.get_active_demands(device)
            if demands is not None:
                parameters["active_demands"] = list(demands)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("THM active demands: %s", exc)

    await _grab("humidity", device_helper.get_humidity(device))
    await _grab("hvac_mode", device_helper.get_hvac_mode(device))
    await _grab("fan_mode", device_helper.get_fan_mode(device))
    await _grab("thm_mode", device_helper.get_thm_mode(device))
    await _grab("target_type", device_helper.get_target_type(device))
    try:
        parameters["is_off"] = bool(await device_helper.is_off(device))
        parameters["is_heating"] = bool(await device_helper.is_heating(device))
        parameters["is_cooling"] = bool(await device_helper.is_cooling(device))
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("THM activity flags: %s", exc)

    try:
        away = await device_helper.get_away_mode(device)
        if isinstance(away, dict):
            parameters["away_mode_activated"] = bool(away.get("activated"))
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("THM away mode: %s", exc)

    # Away-mode setpoints — pysensorlinx 0.5.3+. The Away preset reads
    # from a separate nested object (awayMode.heatTarget/coolTarget) and
    # the home setpoints (rmT/rmCT) are silently ignored while away is
    # active. Guarded with hasattr for older pysensorlinx versions.
    if hasattr(device_helper, "get_away_heat_setpoint"):
        try:
            away_heat = await device_helper.get_away_heat_setpoint(device)
            if away_heat is not None:
                parameters["away_heat_setpoint"] = away_heat.value
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("THM away heat setpoint: %s", exc)

    if hasattr(device_helper, "get_away_cool_setpoint"):
        try:
            away_cool = await device_helper.get_away_cool_setpoint(device)
            if away_cool is not None:
                parameters["away_cool_setpoint"] = away_cool.value
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("THM away cool setpoint: %s", exc)

    # Schedule + humidity raw fields. pysensorlinx 0.5.0 added setters
    # for these but no getters yet, so we read them straight from the
    # device dict. Field names confirmed from THM-0600 dumps 2026-04-28.
    if "pgmble" in device:
        parameters["schedule_enabled"] = bool(device.get("pgmble"))
    if "useHum" in device:
        humidity_mode = {0: "off", 1: "on", 2: "auto"}.get(device.get("useHum"))
        if humidity_mode is not None:
            parameters["humidity_mode"] = humidity_mode
    if "hmT" in device:
        try:
            parameters["humidity_target"] = int(device.get("hmT"))
        except (TypeError, ValueError):
            _LOGGER.debug("THM humidity target not an int: %r", device.get("hmT"))

    return parameters


async def _extract_zon_parameters(device_helper, device: dict) -> dict[str, Any]:
    """Extract ZON-specific parameters and the linked THM sync codes."""
    parameters: dict[str, Any] = {}

    async def _grab(key: str, coro):
        try:
            value = await coro
            if value is not None:
                parameters[key] = value
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Failed to get %s: %s", key, exc)

    await _grab("relays", device_helper.get_relays(device))
    await _grab("relay_types", device_helper.get_relay_types(device))
    await _grab("zone_id", device_helper.get_zone_id(device))
    # `get_sequence` was added in pysensorlinx 0.4.0+. Guard the attribute
    # lookup so older library versions or test mocks without this method
    # don't break extraction of the rest of the ZON parameters.
    if hasattr(device_helper, "get_sequence"):
        await _grab("zone_sequence", device_helper.get_sequence(device))
    try:
        codes = await device_helper.get_thermostat_sync_codes(device)
        # Stored under a stable key the next platform PR can iterate on.
        parameters["thermostat_sync_codes"] = list(codes or [])
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("ZON thermostat sync codes: %s", exc)

    try:
        btn = await device_helper.get_app_button(device)
        if isinstance(btn, dict):
            parameters["app_button_enabled"] = bool(btn.get("enabled"))
            parameters["app_button_activated"] = bool(btn.get("activated"))
            if btn.get("text"):
                parameters["app_button_text"] = btn["text"]
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("ZON app button: %s", exc)

    try:
        aux = await device_helper.get_aux_setpoint(device)
        if isinstance(aux, dict):
            if aux.get("target") is not None:
                parameters["aux_setpoint_target"] = aux["target"]
            mode = aux.get("mode") or {}
            if isinstance(mode, dict) and mode.get("title"):
                parameters["aux_setpoint_mode"] = mode["title"]
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("ZON aux setpoint: %s", exc)

    return parameters


def _wire_via_device_links(devices: dict[str, dict[str, Any]]) -> None:
    """
    Walk the device map and stamp ``via_device_id`` onto each child THM.

    Reads the ``thermostat_sync_codes`` list off every ZON device and
    points back at it from each matching THM device, so HA's device
    registry nests child thermostats under their parent zone controller.
    """
    parent_for_thm: dict[str, str] = {}
    for zon_id, zon_device in devices.items():
        dtype = (zon_device.get("deviceType") or "").upper()
        if dtype != DEVICE_TYPE_ZON:
            continue
        parameters = zon_device.get("parameters") or {}
        for thm_sync in parameters.get("thermostat_sync_codes", []) or []:
            parent_for_thm[str(thm_sync)] = zon_id

    for thm_id, thm_device in devices.items():
        dtype = (thm_device.get("deviceType") or "").upper()
        if dtype != DEVICE_TYPE_THM:
            continue
        parent = parent_for_thm.get(str(thm_id))
        if parent is not None:
            thm_device["via_device_id"] = parent


class HBXControlsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the SensorLinx API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.sensorlinx = Sensorlinx()
        self.entry = entry

        # scan_interval moved to entry.options; fall back to entry.data for
        # entries created before that change.
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        self._scan_interval = scan_interval

        # Optimistic write overrides: device_id -> {param_key: (value, expires)}.
        # The SensorLinx cloud is eventually consistent, so a poll that races a
        # just-written value re-reads the *old* value and reverts the entity.
        # We hold each written value locally for a short grace window until the
        # cloud confirms it (poll matches) or the window (TTL) expires.
        self._overrides: dict[str, dict[str, tuple[Any, float]]] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def override_ttl(self) -> float:
        """Grace window (seconds) to hold an optimistic write.

        At least two poll cycles so the cloud has time to become consistent,
        never shorter than 120s for fast scan intervals.
        """
        return max(2 * self._scan_interval, 120)

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Reduce Temperature/TemperatureDelta wrappers to their scalar value.

        pysensorlinx getters return typed Temperature objects for some params
        and plain scalars for others; comparisons must work across both.
        """
        return getattr(value, "value", value)

    @classmethod
    def _values_match(cls, a: Any, b: Any) -> bool:
        """Compare an override value against a freshly polled value."""
        na, nb = cls._normalize_value(a), cls._normalize_value(b)
        num = (int, float)
        if (
            isinstance(na, num)
            and not isinstance(na, bool)
            and isinstance(nb, num)
            and not isinstance(nb, bool)
        ):
            return abs(float(na) - float(nb)) <= 0.1
        return na == nb

    def set_parameter_override(
        self, device_id: str, updates: dict[str, Any], ttl: float | None = None
    ) -> None:
        """Optimistically hold just-written parameter values.

        Call this from a platform setter *after* the pysensorlinx write
        succeeds, passing the coordinator-data param key(s) the entity reads
        and the value(s) written (in the same representation the extractor
        stores — e.g. a Temperature object, "off", a bool or an int). The
        values are reflected in ``self.data`` immediately (instant UI) and
        re-applied over subsequent stale polls until the cloud confirms them
        or ``ttl`` elapses.
        """
        if ttl is None:
            ttl = self.override_ttl
        expires = time.monotonic() + ttl
        dev = self._overrides.setdefault(device_id, {})
        for key, value in updates.items():
            dev[key] = (value, expires)

        # Reflect immediately in the current snapshot and push to entities.
        data = self.data
        if data:
            devices = data.get("devices")
            if devices and device_id in devices:
                params = devices[device_id].get("parameters")
                if params is not None:
                    for key, value in updates.items():
                        params[key] = value
                    self.async_set_updated_data(data)

    def _apply_overrides(self, devices: dict[str, dict[str, Any]]) -> None:
        """Re-apply un-expired overrides over freshly polled parameters.

        An override is cleared when the poll confirms it (cloud caught up) or
        when its TTL expires (defer to the cloud so genuine external changes or
        controller-rejected writes are not masked forever).
        """
        now = time.monotonic()
        for device_id in list(self._overrides.keys()):
            keys = self._overrides[device_id]
            dev = devices.get(device_id)
            params = dev.get("parameters") if dev else None
            for key in list(keys.keys()):
                value, expires = keys[key]
                if now >= expires:
                    del keys[key]
                    continue
                if params is None:
                    continue
                if self._values_match(value, params.get(key)):
                    del keys[key]
                    continue
                params[key] = value
            if not keys:
                del self._overrides[device_id]

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        _LOGGER.debug("Starting HBX Controls data update")
        try:
            # Lazy login: pysensorlinx>=0.2.3 owns session lifecycle and is
            # idempotent when already authenticated. Skipping the call when
            # we already hold a valid session avoids a pointless POST every
            # poll cycle.
            if not self.sensorlinx.is_logged_in:
                _LOGGER.debug("Logging in as user: %s", self.entry.data[CONF_USERNAME])
                await self.sensorlinx.login(
                    self.entry.data[CONF_USERNAME],
                    self.entry.data[CONF_PASSWORD],
                )

            _LOGGER.debug("Fetching user profile")
            profile = await self.sensorlinx.get_profile()
            if not profile:
                # `pysensorlinx.get_profile()` returns None on transient failures
                # (timeouts, 5xx, network blips) — InvalidCredentialsError is
                # raised explicitly. So a None response means "try again later",
                # NOT "credentials are bad". Forcing reauth here boots users out
                # of the integration on every blip. Surface as UpdateFailed so
                # HA retries on the next poll cycle.
                _LOGGER.debug("No profile returned from HBX Controls (transient)")
                raise UpdateFailed("Failed to get user profile (transient)")

            _LOGGER.debug("Fetching buildings")
            buildings = await self.sensorlinx.get_buildings()
            if not buildings:
                buildings = []

            devices: dict[str, dict[str, Any]] = {}
            for building in buildings:
                building_id = building.get("id")
                _LOGGER.debug("Fetching devices for building: %s", building_id)
                try:
                    building_devices = await self.sensorlinx.get_devices(building_id)
                except Exception as building_exc:  # noqa: BLE001
                    _LOGGER.warning(
                        "Failed to get devices for building %s: %s",
                        building_id, building_exc,
                    )
                    continue
                if not building_devices:
                    continue

                for device in building_devices:
                    device_id = device.get("syncCode") or device.get("id")
                    if not device_id:
                        continue

                    dtype = (device.get("deviceType") or "").upper()
                    device_helper = device_for(self.sensorlinx, building_id, device)

                    parameters: dict[str, Any] = {}
                    # Always populate the diagnostic fields so HA registers
                    # the device regardless of type.
                    try:
                        parameters["firmware_version"] = await device_helper.get_firmware_version(
                            device_info=device
                        )
                    except Exception:  # noqa: BLE001
                        pass
                    parameters["device_type"] = dtype or "Unknown"

                    try:
                        if dtype == DEVICE_TYPE_THM:
                            parameters.update(await _extract_thm_parameters(device_helper, device))
                        elif dtype == DEVICE_TYPE_ZON:
                            parameters.update(await _extract_zon_parameters(device_helper, device))
                        else:
                            # ECO or unknown — preserve the historical full extract.
                            parameters.update(await _extract_eco_parameters(device_helper, device))
                    except Exception as param_exc:  # noqa: BLE001
                        _LOGGER.warning(
                            "Failed to extract parameters for device %s: %s",
                            device_id, param_exc,
                        )

                    device["parameters"] = parameters
                    device["building_id"] = building_id
                    devices[device_id] = device

            _wire_via_device_links(devices)

            # Re-apply optimistic overrides so a poll that races the
            # eventually-consistent cloud doesn't revert a just-written value.
            self._apply_overrides(devices)

            # Get weather data for each building (building-level, not device-level)
            weather: dict[str, Any] = {}
            for building in buildings:
                building_id = building.get("id")
                try:
                    from pysensorlinx.sensorlinx import SensorlinxDevice as _SD
                    weather_helper = _SD(self.sensorlinx, building_id, "")
                    building_weather: dict[str, Any] = {}
                    try:
                        current = await weather_helper.get_current_weather(building_info=building)
                        if current:
                            building_weather["current"] = current
                    except Exception as exc:  # noqa: BLE001
                        _LOGGER.debug("No current weather for building %s: %s", building_id, exc)
                    try:
                        forecast = await weather_helper.get_forecast(building_info=building)
                        if forecast:
                            building_weather["forecast"] = forecast
                    except Exception as exc:  # noqa: BLE001
                        _LOGGER.debug("No forecast for building %s: %s", building_id, exc)
                    if building_weather:
                        weather[building_id] = building_weather
                except Exception as weather_exc:  # noqa: BLE001
                    _LOGGER.debug(
                        "Failed to get weather for building %s: %s",
                        building_id, weather_exc,
                    )

            _LOGGER.debug(
                "Data update complete: profile=%s, buildings=%d, devices=%d, weather=%d",
                bool(profile), len(buildings), len(devices), len(weather),
            )
            return {
                "profile": profile,
                "buildings": buildings,
                "devices": devices,
                "weather": weather,
            }

        except ConfigEntryAuthFailed:
            _LOGGER.debug("Authentication failed during data update")
            raise
        except InvalidCredentialsError as exc:
            _LOGGER.warning("Invalid credentials for SensorLinx: %s", exc)
            raise ConfigEntryAuthFailed(str(exc)) from exc
        except (LoginTimeoutError, LoginError) as exc:
            _LOGGER.warning("Transient SensorLinx login failure: %s", exc)
            try:
                await self.sensorlinx.close()
            except Exception:  # pylint: disable=broad-except
                pass
            raise UpdateFailed(f"SensorLinx login failed: {exc}") from exc
        except Exception as exc:
            _LOGGER.error("Error communicating with SensorLinx API: %s", exc)
            raise UpdateFailed(f"Error communicating with API: {exc}") from exc

    async def async_shutdown(self) -> None:
        """Close the HBX Controls connection."""
        if self.sensorlinx:
            await self.sensorlinx.close()
