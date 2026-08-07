"""Platform for climate integration."""
from __future__ import annotations

import logging
from typing import Any

from pysensorlinx import DEVICE_TYPE_THM
from pysensorlinx.sensorlinx import Temperature, ThmDevice

from homeassistant.components.climate import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HBXControlsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


# Map between HA HVACMode values and the strings :py:meth:`ThmDevice.set_hvac_mode`
# accepts. ``ThmDevice.set_hvac_mode`` writes the matching ``cngOvr`` integer.
# Note: HA's HEAT_COOL maps to the device's ``auto`` (cngOvr=0). The cloud
# library still names that enum value ``"auto"``; the public-facing terminology
# in HA is HEAT_COOL because dual setpoints are advertised in that mode.
_THM_HVAC_TO_LIB = {
    HVACMode.OFF: "off",
    HVACMode.HEAT: "heat",
    HVACMode.COOL: "cool",
    HVACMode.HEAT_COOL: "auto",
}

# Friendly names HA shows for fan modes; mapped to library values when writing.
_THM_FAN_OFF = "off"
_THM_FAN_ON = "on"
_THM_FAN_INTERMITTENT = "intermittent"
_THM_FAN_MODES = [_THM_FAN_OFF, _THM_FAN_ON, _THM_FAN_INTERMITTENT]

_THM_PRESET_NONE = "none"
_THM_PRESET_AWAY = "away"
_THM_PRESET_MODES = [_THM_PRESET_NONE, _THM_PRESET_AWAY]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    coordinator: HBXControlsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    if coordinator.data and "devices" in coordinator.data:
        for device_id, device in coordinator.data["devices"].items():
            parameters = device.get("parameters", {})
            dtype = (parameters.get("device_type") or device.get("deviceType") or "").upper()

            if dtype == DEVICE_TYPE_THM:
                # THM thermostats have room/floor temps and the climate write
                # surfaces backed by ``ThmDevice`` setters added in
                # pysensorlinx 0.4.0.
                entities.append(
                    HBXControlsThmClimate(
                        coordinator,
                        device_id,
                        device,
                    )
                )
                continue

            # Existing ECO heat-pump climate entity (preserved verbatim).
            if "target_temperature_tank" in parameters or "temperature_tank" in parameters:
                entities.append(
                    HBXControlsClimate(
                        coordinator,
                        device_id,
                        device,
                    )
                )
    
    async_add_entities(entities)


class HBXControlsClimate(CoordinatorEntity, ClimateEntity):
    """Implementation of an HBX Controls climate entity."""

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        
        self._attr_unique_id = f"{device_id}_climate"
        self._attr_name = f"{device.get('name', device_id)} Climate"
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        
        # Supported features
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        
        # Supported HVAC modes
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.AUTO,
        ]
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("type", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        # Get the tank temperature from the temperatures array (searched by title)
        temp = parameters.get("temperature_tank")
        return temp

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        # Use the computed target from the temperatures array regardless of mode
        return parameters.get("target_temperature_tank")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        mode = parameters.get("hvac_mode", "").lower()
        
        if mode == "off":
            return HVACMode.OFF
        elif mode == "heat":
            return HVACMode.HEAT
        elif mode == "cool":
            return HVACMode.COOL
        elif mode == "auto":
            return HVACMode.AUTO
        
        return HVACMode.AUTO  # Default to auto

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
            
        parameters = device.get("parameters", {})
        
        # Check demand states
        if parameters.get("permanent_heat_demand", False):
            return HVACAction.HEATING
        elif parameters.get("permanent_cool_demand", False):
            return HVACAction.COOLING
        elif self.hvac_mode != HVACMode.OFF:
            return HVACAction.IDLE
        
        return HVACAction.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
            
        try:
            # Get building info from coordinator data
            if not self.coordinator.data or "devices" not in self.coordinator.data:
                _LOGGER.error("No coordinator data available")
                return
                
            device = self.coordinator.data["devices"].get(self._device_id)
            if not device:
                _LOGGER.error("Device %s not found in coordinator data", self._device_id)
                return
            
            # Find the building ID for this device
            building_id = None
            for building in self.coordinator.data.get("buildings", []):
                # You'll need to implement logic to find which building this device belongs to
                # For now, use the first building
                building_id = building.get("id")
                break
                
            if not building_id:
                _LOGGER.error("No building ID found for device %s", self._device_id)
                return
            
            # Create device helper and set temperature based on current mode
            from pysensorlinx.sensorlinx import SensorlinxDevice, Temperature
            device_helper = SensorlinxDevice(self.coordinator.sensorlinx, building_id, self._device_id)
            
            # Convert temperature to Fahrenheit (HBX Controls uses Fahrenheit)
            temp_f = Temperature(temperature, "C").to_fahrenheit() if self.temperature_unit == UnitOfTemperature.CELSIUS else temperature
            temp_obj = Temperature(temp_f, "F")
            
            hvac_mode = self.hvac_mode
            if hvac_mode == HVACMode.HEAT:
                await device_helper.set_hot_tank_target_temp(temp_obj)
            elif hvac_mode == HVACMode.COOL:
                await device_helper.set_cold_tank_target_temp(temp_obj)
            else:
                # Auto mode - set both hot and cool tank targets
                await device_helper.set_hot_tank_target_temp(temp_obj)
            
            self.coordinator.set_parameter_override(
                self._device_id, {"target_temperature_tank": temp_f}
            )
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            _LOGGER.error("Failed to set temperature for %s: %s", self._device_id, exc)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        try:
            # Get building info from coordinator data
            if not self.coordinator.data or "devices" not in self.coordinator.data:
                _LOGGER.error("No coordinator data available")
                return
                
            device = self.coordinator.data["devices"].get(self._device_id)
            if not device:
                _LOGGER.error("Device %s not found in coordinator data", self._device_id)
                return
            
            # Find the building ID for this device
            building_id = None
            for building in self.coordinator.data.get("buildings", []):
                building_id = building.get("id")
                break
                
            if not building_id:
                _LOGGER.error("No building ID found for device %s", self._device_id)
                return
            
            # Create device helper and set HVAC mode
            from pysensorlinx.sensorlinx import SensorlinxDevice
            device_helper = SensorlinxDevice(self.coordinator.sensorlinx, building_id, self._device_id)
            
            await device_helper.set_hvac_mode_priority(hvac_mode.value)
            self.coordinator.set_parameter_override(
                self._device_id, {"hvac_mode": hvac_mode.value}
            )
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            _LOGGER.error("Failed to set HVAC mode for %s: %s", self._device_id, exc)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )


class HBXControlsThmClimate(CoordinatorEntity, ClimateEntity):
    """
    Climate entity for THM-style thermostats (e.g. THM-0600).

    Backed by :class:`pysensorlinx.sensorlinx.ThmDevice`.

    * HVAC mode      -> ``cngOvr`` (auto/heat/cool/off)
    * Fan mode       -> ``fnMode`` (off/on/intermittent)
    * Heat setpoint  -> ``rmT`` (°F int)
    * Cool setpoint  -> ``rmCT`` (°F int)
    * Away preset    -> ``away`` (0/1)

    Heat-cool dual-setpoint support arrived in pysensorlinx 0.5.2 once
    we determined that ``rmT`` and ``rmCT`` always reflect the heat
    target and cool target respectively, even in Auto changeover.
    The previously-used single-target ``set_target_temperature``
    inferred the active side from ``target.type``, which is biased to
    heat in Auto and so cannot drive HEAT_COOL mode correctly.

    Reads come from the parameter dict the coordinator extracts via
    :func:`coordinator._extract_thm_parameters`.
    """

    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_min_temp = 35
    _attr_max_temp = 99
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
    ]
    _attr_fan_modes = _THM_FAN_MODES
    _attr_preset_modes = _THM_PRESET_MODES

    def __init__(
        self,
        coordinator: HBXControlsDataUpdateCoordinator,
        device_id: str,
        device: dict[str, Any],
    ) -> None:
        """Initialize the THM climate entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device
        self._building_id = device.get("building_id")

        self._attr_unique_id = f"{device_id}_thm_climate"
        self._attr_name = f"{device.get('name', device_id)} Climate"

        # We advertise BOTH single-setpoint and range features. HA picks
        # which UI to show based on ``hvac_mode``: HEAT/COOL use the
        # single setpoint, HEAT_COOL uses target_temperature_low/high.
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device.get("name", device_id),
            "manufacturer": "HBX Controls",
            "model": device.get("deviceType", "Unknown"),
            "sw_version": device.get("firmware_version"),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _params(self) -> dict[str, Any] | None:
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
        device = self.coordinator.data["devices"].get(self._device_id)
        if not device:
            return None
        return device.get("parameters") or {}

    def _device_helper(self) -> ThmDevice:
        return ThmDevice(
            self.coordinator.sensorlinx,
            self._building_id,
            self._device_id,
        )

    # ------------------------------------------------------------------
    # Read-side properties
    # ------------------------------------------------------------------

    @property
    def current_temperature(self) -> float | None:
        """Return the current room temperature."""
        params = self._params()
        if not params:
            return None
        return params.get("temperature_room")

    @property
    def current_humidity(self) -> int | None:
        """Return the current relative humidity."""
        params = self._params()
        if not params:
            return None
        humidity = params.get("humidity")
        try:
            return int(round(humidity)) if humidity is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def target_temperature(self) -> float | None:
        """Return the active single-setpoint target.

        Returned for HEAT (heat setpoint) and COOL (cool setpoint).
        ``None`` for HEAT_COOL/OFF — those use the low/high pair.

        When the Away preset is active and an away setpoint is published
        by the device, we return the away value instead so HA's UI
        reflects what the device is actually targeting.
        """
        params = self._params()
        if not params:
            return None
        mode = self.hvac_mode
        away = self.preset_mode == _THM_PRESET_AWAY
        if mode == HVACMode.HEAT:
            if away and params.get("away_heat_setpoint") is not None:
                return params.get("away_heat_setpoint")
            return params.get("heat_setpoint")
        if mode == HVACMode.COOL:
            if away and params.get("away_cool_setpoint") is not None:
                return params.get("away_cool_setpoint")
            return params.get("cool_setpoint")
        return None

    @property
    def target_temperature_low(self) -> float | None:
        """Heat-side setpoint when in HEAT_COOL mode."""
        if self.hvac_mode != HVACMode.HEAT_COOL:
            return None
        params = self._params()
        if not params:
            return None
        if (
            self.preset_mode == _THM_PRESET_AWAY
            and params.get("away_heat_setpoint") is not None
        ):
            return params.get("away_heat_setpoint")
        return params.get("heat_setpoint")

    @property
    def target_temperature_high(self) -> float | None:
        """Cool-side setpoint when in HEAT_COOL mode."""
        if self.hvac_mode != HVACMode.HEAT_COOL:
            return None
        params = self._params()
        if not params:
            return None
        if (
            self.preset_mode == _THM_PRESET_AWAY
            and params.get("away_cool_setpoint") is not None
        ):
            return params.get("away_cool_setpoint")
        return params.get("cool_setpoint")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current HVAC mode."""
        params = self._params()
        if not params:
            return None
        mode = (params.get("hvac_mode") or "").lower()
        if mode == "off":
            return HVACMode.OFF
        if mode == "heat":
            return HVACMode.HEAT
        if mode == "cool":
            return HVACMode.COOL
        if mode == "auto":
            return HVACMode.HEAT_COOL
        return None

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return current HVAC action (heating/cooling/idle/off).

        Derived from the ``active_demands`` list (decoded from the
        ``dmd`` bitfield) — that's the only reliable signal. The
        cloud's ``isCooling`` flag is broken (always false even with
        an active cool call). Cooling takes priority over heating in
        the unlikely event both bits are set; fan-only renders as
        idle for hydronic systems.
        """
        params = self._params()
        if not params:
            return None
        if self.hvac_mode == HVACMode.OFF or params.get("is_off"):
            return HVACAction.OFF
        demands = params.get("active_demands") or []
        if "cooling" in demands:
            return HVACAction.COOLING
        if "heating" in demands:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def fan_mode(self) -> str | None:
        """Return current fan mode."""
        params = self._params()
        if not params:
            return None
        mode = (params.get("fan_mode") or "").lower()
        if mode in _THM_FAN_MODES:
            return mode
        return None

    @property
    def preset_mode(self) -> str | None:
        """Return current preset mode (away/none)."""
        params = self._params()
        if not params:
            return None
        if params.get("away_mode_activated"):
            return _THM_PRESET_AWAY
        return _THM_PRESET_NONE

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "devices" in self.coordinator.data
            and self._device_id in self.coordinator.data["devices"]
        )

    # ------------------------------------------------------------------
    # Write-side methods
    # ------------------------------------------------------------------

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Send the new changeover state to the device."""
        lib_mode = _THM_HVAC_TO_LIB.get(hvac_mode)
        if lib_mode is None:
            _LOGGER.error(
                "Unsupported THM HVAC mode requested: %s", hvac_mode
            )
            return
        try:
            await self._device_helper().set_hvac_mode(lib_mode)
            self.coordinator.set_parameter_override(
                self._device_id, {"hvac_mode": lib_mode}
            )
            await self.coordinator.async_request_refresh()
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error(
                "Failed to set THM HVAC mode for %s: %s", self._device_id, exc
            )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Send the new fan mode to the device."""
        if fan_mode not in _THM_FAN_MODES:
            _LOGGER.error("Unsupported THM fan mode requested: %s", fan_mode)
            return
        try:
            await self._device_helper().set_fan_mode(fan_mode)
            self.coordinator.set_parameter_override(
                self._device_id, {"fan_mode": fan_mode}
            )
            await self.coordinator.async_request_refresh()
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error(
                "Failed to set THM fan mode for %s: %s", self._device_id, exc
            )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Toggle the THM Away preset based on requested preset."""
        if preset_mode not in _THM_PRESET_MODES:
            _LOGGER.error(
                "Unsupported THM preset mode requested: %s", preset_mode
            )
            return
        try:
            await self._device_helper().set_away_mode(
                preset_mode == _THM_PRESET_AWAY
            )
            self.coordinator.set_parameter_override(
                self._device_id,
                {"away_mode_activated": preset_mode == _THM_PRESET_AWAY},
            )
            await self.coordinator.async_request_refresh()
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error(
                "Failed to set THM preset mode for %s: %s",
                self._device_id, exc,
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Send setpoint(s) to the THM device.

        Three call shapes:

        * HEAT_COOL: HA passes ``target_temp_low`` (heat) and
          ``target_temp_high`` (cool). We write both with a single
          atomic ``set_heat_cool_setpoints`` PATCH.
        * HEAT: HA passes ``temperature``; we write ``rmT``.
        * COOL: HA passes ``temperature``; we write ``rmCT``.

        When the Away preset is active, writes are routed to the
        ``awayMode.heatTarget``/``awayMode.coolTarget`` nested fields
        via the matching ``set_away_*`` methods on pysensorlinx 0.5.3+.
        On older pysensorlinx the away-routing branch falls back to
        the home-mode writes (which the cloud silently ignores while
        away is active — this matches pre-0.5.3 behaviour).
        """
        low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        temperature = kwargs.get(ATTR_TEMPERATURE)

        helper = self._device_helper()
        away = self.preset_mode == _THM_PRESET_AWAY
        try:
            if low is not None and high is not None:
                if away and hasattr(helper, "set_away_heat_cool_setpoints"):
                    await helper.set_away_heat_cool_setpoints(
                        Temperature(low, "F"),
                        Temperature(high, "F"),
                    )
                    self.coordinator.set_parameter_override(
                        self._device_id,
                        {"away_heat_setpoint": low, "away_cool_setpoint": high},
                    )
                else:
                    await helper.set_heat_cool_setpoints(
                        Temperature(low, "F"),
                        Temperature(high, "F"),
                    )
                    self.coordinator.set_parameter_override(
                        self._device_id,
                        {"heat_setpoint": low, "cool_setpoint": high},
                    )
            elif temperature is not None:
                mode = self.hvac_mode
                if mode == HVACMode.COOL:
                    if away and hasattr(helper, "set_away_cool_setpoint"):
                        await helper.set_away_cool_setpoint(
                            Temperature(temperature, "F")
                        )
                        self.coordinator.set_parameter_override(
                            self._device_id, {"away_cool_setpoint": temperature}
                        )
                    else:
                        await helper.set_cool_setpoint(Temperature(temperature, "F"))
                        self.coordinator.set_parameter_override(
                            self._device_id, {"cool_setpoint": temperature}
                        )
                else:
                    # Default to heat for HEAT (and any unknown) — matches
                    # the HBX app's behaviour.
                    if away and hasattr(helper, "set_away_heat_setpoint"):
                        await helper.set_away_heat_setpoint(
                            Temperature(temperature, "F")
                        )
                        self.coordinator.set_parameter_override(
                            self._device_id, {"away_heat_setpoint": temperature}
                        )
                    else:
                        await helper.set_heat_setpoint(Temperature(temperature, "F"))
                        self.coordinator.set_parameter_override(
                            self._device_id, {"heat_setpoint": temperature}
                        )
            else:
                return
            await self.coordinator.async_request_refresh()
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error(
                "Failed to set THM target temperature for %s: %s",
                self._device_id, exc,
            )

    async def async_turn_on(self) -> None:
        """Turn the thermostat on (resume HEAT_COOL changeover)."""
        await self.async_set_hvac_mode(HVACMode.HEAT_COOL)

    async def async_turn_off(self) -> None:
        """Turn the thermostat off (changeover -> Off)."""
        await self.async_set_hvac_mode(HVACMode.OFF)
