"""DataUpdateCoordinator for HBX Controls."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from pysensorlinx import Sensorlinx

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class HBXControlsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the SensorLinx API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.sensorlinx = Sensorlinx()
        self.entry = entry
        
        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
      """Update data via library."""
      _LOGGER.debug("Starting HBX Controls data update")
      try:
        # Login
        _LOGGER.debug("Logging in as user: %s", self.entry.data[CONF_USERNAME])
        await self.sensorlinx.login(
          self.entry.data[CONF_USERNAME],
          self.entry.data[CONF_PASSWORD]
        )
        
        # Get user profile
        _LOGGER.debug("Fetching user profile")
        profile = await self.sensorlinx.get_profile()
        if not profile:
          _LOGGER.debug("No profile returned from HBX Controls")
          raise ConfigEntryAuthFailed("Failed to get user profile")
        _LOGGER.debug("User profile fetched: %s", profile)
        
        # Get buildings
        _LOGGER.debug("Fetching buildings")
        buildings = await self.sensorlinx.get_buildings()
        if not buildings:
          _LOGGER.debug("No buildings returned from HBX Controls")
          buildings = []
        else:
          _LOGGER.debug("Fetched %d buildings", len(buildings))
        
        # Get devices for each building
        devices = {}
        for building in buildings:
          building_id = building.get("id")
          _LOGGER.debug("Fetching devices for building: %s", building_id)
          try:
            building_devices = await self.sensorlinx.get_devices(building_id)
            if building_devices:
              _LOGGER.debug("Fetched %d devices for building %s", len(building_devices), building_id)
              for device in building_devices:
                device_id = device.get("syncCode") or device.get("id")
                _LOGGER.debug("Processing device: %s (ID: %s)", device.get("name"), device_id)
                
                # Create a SensorlinxDevice helper to extract parameters
                from pysensorlinx.sensorlinx import SensorlinxDevice
                device_helper = SensorlinxDevice(self.sensorlinx, building_id, device_id)
                
                # Extract parameters using the library methods
                parameters = {}
                try:
                  # Temperature data
                  temps = await device_helper.get_temperatures(device_info=device)
                  if temps:
                    for temp_name, temp_data in temps.items():
                      if temp_data.get("actual"):
                        parameters[f"temperature_{temp_name.lower().replace(' ', '_')}"] = temp_data["actual"].value
                      if temp_data.get("target"):
                        parameters[f"target_temperature_{temp_name.lower().replace(' ', '_')}"] = temp_data["target"].value
                  
                  # HVAC and demand states
                  try:
                    parameters["permanent_heat_demand"] = await device_helper.get_permanent_heat_demand(device_info=device)
                  except:
                    pass
                  
                  try:
                    parameters["permanent_cool_demand"] = await device_helper.get_permanent_cool_demand(device_info=device)
                  except:
                    pass
                    
                  try:
                    hvac_mode = await device_helper.get_hvac_mode_priority(device_info=device)
                    # Convert numeric to string
                    mode_map = {0: "heat", 1: "cool", 2: "auto"}
                    parameters["hvac_mode"] = mode_map.get(hvac_mode, "auto")
                  except:
                    pass
                  
                  # Tank temperatures
                  try:
                    parameters["hot_tank_min_temp"] = await device_helper.get_hot_tank_min_temp(device_info=device)
                  except:
                    pass
                    
                  try:
                    parameters["hot_tank_max_temp"] = await device_helper.get_hot_tank_max_temp(device_info=device)
                  except:
                    pass
                  
                  try:
                    parameters["hot_tank_outdoor_reset"] = await device_helper.get_hot_tank_outdoor_reset(device_info=device)
                  except:
                    pass
                    
                  try:
                    parameters["cold_tank_min_temp"] = await device_helper.get_cold_tank_min_temp(device_info=device)
                  except:
                    pass
                    
                  try:
                    parameters["cold_tank_max_temp"] = await device_helper.get_cold_tank_max_temp(device_info=device)
                  except:
                    pass
                  
                  try:
                    parameters["cold_tank_outdoor_reset"] = await device_helper.get_cold_tank_outdoor_reset(device_info=device)
                  except:
                    pass
                  
                  # Device info
                  try:
                    parameters["firmware_version"] = await device_helper.get_firmware_version(device_info=device)
                  except:
                    pass
                    
                  try:
                    parameters["device_type"] = await device_helper.get_device_type(device_info=device)
                  except:
                    pass
                  
                  # Weather shutdown states
                  try:
                    parameters["warm_weather_shutdown"] = await device_helper.get_warm_weather_shutdown(device_info=device)
                  except:
                    pass
                    
                  try:
                    parameters["cold_weather_shutdown"] = await device_helper.get_cold_weather_shutdown(device_info=device)
                  except:
                    pass
                  
                  # Heat pump stages
                  try:
                    heatpump_stages = await device_helper.get_heatpump_stages_state(device_info=device)
                    if heatpump_stages:
                      parameters["heatpump_stages"] = heatpump_stages
                      _LOGGER.debug("Device %s heatpump_stages: %s", device_id, heatpump_stages)
                  except Exception as e:
                    _LOGGER.debug("Failed to get heatpump_stages for device %s: %s", device_id, e)
                  
                  # Backup heater state
                  try:
                    backup_state = await device_helper.get_backup_state(device_info=device)
                    if backup_state:
                      parameters["backup_state"] = backup_state
                      _LOGGER.debug("Device %s backup_state: %s", device_id, backup_state)
                  except Exception as e:
                    _LOGGER.debug("Failed to get backup_state for device %s: %s", device_id, e)
                  
                except Exception as param_exc:
                  _LOGGER.warning("Failed to extract parameters for device %s: %s", device_id, param_exc)
                
                device["parameters"] = parameters
                device["building_id"] = building_id  # Store building_id for API calls
                _LOGGER.debug("Device %s parameters: %s", device_id, parameters)
                devices[device_id] = device
            else:
              _LOGGER.debug("No devices found for building %s", building_id)
          except Exception as building_exc:
            _LOGGER.warning("Failed to get devices for building %s: %s", building_id, building_exc)
        
        _LOGGER.debug("Data update complete: profile=%s, buildings=%d, devices=%d",
                bool(profile), len(buildings), len(devices))
        return {
          "profile": profile,
          "buildings": buildings,
          "devices": devices,
        }
        
      except ConfigEntryAuthFailed:
        _LOGGER.debug("Authentication failed during data update")
        raise
      except Exception as exc:
        _LOGGER.error("Error communicating with SensorLinx API: %s", exc)
        raise UpdateFailed(f"Error communicating with API: {exc}") from exc

    async def async_shutdown(self) -> None:
        """Close the HBX Controls connection."""
        if self.sensorlinx:
            await self.sensorlinx.close()
