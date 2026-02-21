# HBX Controls Integration — TODO

## Done (this branch)

- [x] **pysensorlinx min/max swap fix** — `dbt`=max, `mbt`=min, `dst`=max, `mst`=min (published as 0.1.9)
- [x] **requirements.txt** — bumped to `pysensorlinx==0.1.9`
- [x] **climate.py: current_temperature** — changed from `temperature_hot_tank` to `temperature_tank`
- [x] **climate.py: target_temperature** — always reads `target_temperature_tank` (the controller's computed target) regardless of HVAC mode
- [x] **climate.py: entity creation gate** — removed device type check (`thermostat`/`heat_pump`), now gates on `temperature_tank` or `target_temperature_tank` presence
- [x] **number.py: HotTankTargetTemperature.native_value** — reads `target_temperature_tank` instead of `hot_tank_min_temp`
- [x] **Domain rename** — merged `hbxcontrols` → `hbx_controls` from main

## Still Open (this branch)

- [ ] **climate.py: set_temperature when outdoor reset is on** — currently calls `set_hot_tank_target_temp()` which only sets the min end of the outdoor reset curve. Options:
  - **Option A**: Make target temperature read-only when outdoor reset is on
  - **Option B**: Disable set_temperature entirely when outdoor reset is on
  - **Option C**: Adjust both min and max proportionally
- [ ] **ColdTankTargetTemperature.native_value** — still reads `cold_tank_min_temp`; may need `target_temperature_cold_tank` equivalent if a cold tank temperature exists in the API
- [ ] **const.py cleanup** — `DEVICE_TYPE_THERMOSTAT` and `DEVICE_TYPE_HEAT_PUMP` are defined but no longer imported anywhere; consider removing

## Future (separate branches)

- [ ] **Integration tests** — add `pytest` + `pytest-homeassistant-custom-component` tests:
  - `conftest.py` — shared fixtures (mock coordinator, mock config entry, `make_coordinator_data()` helper)
  - `test_climate.py` — entity creation gating, `current_temperature`, `target_temperature`, `hvac_mode`, `hvac_action`, availability
  - `test_number.py` — `HotTankTargetTemperature` value/availability, min/max entities, outdoor reset interaction
  - `test_sensor.py` — sensor entity creation and value reading
  - `test_switch.py` — switch entity state and toggle actions
- [ ] **CI pipeline** — GitHub Actions to run tests on PR
