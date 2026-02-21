# Copilot Instructions — HBX Controls Home Assistant Integration

## Project Overview

This is a **Home Assistant custom component** (HACS-compatible) that integrates HBX Controls HVAC devices via the SensorLinx cloud API. The integration domain is `hbx_controls`.

- **Repo**: `sslivins/hass_hbxcontrols`
- **Companion library**: `pysensorlinx` (PyPI) — source at `sslivins/pysensorlinx`
- **HA integration pattern**: cloud polling via `DataUpdateCoordinator`

## Architecture

```
custom_components/hbx_controls/
  __init__.py        — entry point, forwards platforms
  config_flow.py     — UI-based setup (username/password)
  const.py           — domain, config keys, constants
  coordinator.py     — DataUpdateCoordinator, fetches all API data
  climate.py         — ClimateEntity (thermostat card)
  number.py          — NumberEntity controls (tank temps, outdoor reset, weather shutdown)
  switch.py          — SwitchEntity toggles (outdoor reset on/off, demand, weather shutdown)
  sensor.py          — SensorEntity (tank temp, outdoor temp, firmware, device type)
  binary_sensor.py   — BinarySensorEntity (heat pump stages, backup heater)
  manifest.json      — HA integration manifest
  strings.json       — UI strings
  translations/en.json
```

## Key Concepts

### Data Flow
1. `coordinator.py` logs into SensorLinx via `pysensorlinx`, fetches buildings → devices → parameters
2. For each device, it calls `SensorlinxDevice` helper methods to extract parameters into a flat dict
3. All platform entities read from `coordinator.data["devices"][device_id]["parameters"]`

### Parameter Keys (coordinator data)
Temperature values from the API `get_temperatures()` are stored by title:
- `temperature_tank` — actual tank temperature (from `temperatures` array, title="TANK")
- `target_temperature_tank` — computed target the controller is actively using
- `temperature_outdoor` — outdoor sensor reading

Raw parameter values:
- `hot_tank_min_temp` / `hot_tank_max_temp` — the user-configured tank temp range (°F)
- `hot_tank_outdoor_reset` — `"off"` or a `Temperature` object (design outdoor temp)
- `cold_tank_min_temp` / `cold_tank_max_temp` — cold tank range
- `cold_tank_outdoor_reset` — same pattern
- `hvac_mode` — `"heat"`, `"cool"`, `"auto"`, `"off"`
- `permanent_heat_demand` / `permanent_cool_demand` — bool
- `warm_weather_shutdown` / `cold_weather_shutdown` — `"off"` or `Temperature`
- `heatpump_stages` — list of stage dicts with `title`, `activated`, `runTime`
- `backup_state` — dict with `title`, `activated`, `runTime`

### Outdoor Reset Curve
When outdoor reset is **on**, the controller computes a target temperature from an outdoor reset curve based on outdoor temp, min tank temp, max tank temp, and design outdoor temp. The computed result is `target_temperature_tank`.

When outdoor reset is **off**, min and max are set to the same value (flat setpoint). The `HotTankTargetTemperature` number entity sets both min and max together.

### SensorLinx API Key Mappings (pysensorlinx)
- `dbt` = Design Boiler Temperature = **hot tank MAX**
- `mbt` = Minimum Boiler Temperature = **hot tank MIN**
- `dst` = Design Supply Temperature = **cold tank MAX**
- `mst` = Minimum Supply Temperature = **cold tank MIN**

### Entity Availability Patterns
- Number entities for min/max temp: only available when outdoor reset is **on**
- `HotTankTargetTemperature`: only available when outdoor reset is **off**
- Climate entity: created for any device with `temperature_tank` or `target_temperature_tank`
- Switches: always available if the parameter exists

## Conventions

- All temperatures in the API and number entities use **Fahrenheit**
- The climate entity declares its unit as **Fahrenheit** (HA converts to the user's preferred display unit)
- Device IDs come from `device.syncCode` (falls back to `device.id`)
- Each device is identified in HA by `(DOMAIN, device_id)` identifiers
- Entity unique IDs follow pattern: `{device_id}_{entity_type}` e.g. `device_123_climate`

## Git Workflow

- **Never commit directly to `main`** — all new features and bug fixes should go into a feature/fix branch
- Branch naming: `feature/<short-description>` or `fix/<short-description>`
- Open a PR to merge into `main`

## Testing

- Framework: `pytest` + `pytest-homeassistant-custom-component`
- Existing test: `tests/test_config_flow.py`
- Mock the coordinator with fake data rather than hitting the real API
- Use `make_coordinator_data()` helper pattern to build test fixtures

## Common Pitfalls

- **Don't use `temperature_hot_tank`** — the correct key is `temperature_tank` (keyed by API title "TANK", not prefixed with hot/cold)
- **Don't gate climate entity on device type strings** — the API returns controller model names like `"ECO"`, not functional types like `"thermostat"`
- **`target_temperature_tank` is the live computed target** — always use this for display, not `hot_tank_min_temp`
- **`pysensorlinx.Temperature` objects** — some parameters arrive as `Temperature` objects with a `.value` property; check `isinstance(value, Temperature)` before using as float
