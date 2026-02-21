# HBX Controls Integration — TODO

## Done

- [x] **pysensorlinx min/max swap fix** — `dbt`=max, `mbt`=min, `dst`=max, `mst`=min (published as 0.1.9)
- [x] **requirements.txt** — bumped to `pysensorlinx==0.1.9`
- [x] **climate.py: current_temperature** — changed from `temperature_hot_tank` to `temperature_tank`
- [x] **climate.py: target_temperature** — always reads `target_temperature_tank` (the controller's computed target) regardless of HVAC mode
- [x] **climate.py: entity creation gate** — removed device type check (`thermostat`/`heat_pump`), now gates on `temperature_tank` or `target_temperature_tank` presence
- [x] **number.py: HotTankTargetTemperature.native_value** — reads `target_temperature_tank` instead of `hot_tank_min_temp`
- [x] **Domain rename** — merged `hbxcontrols` → `hbx_controls` from main
- [x] **Coordinator rename** — `SensorLinxDataUpdateCoordinator` → `HBXControlsDataUpdateCoordinator`
- [x] **Version bump** — 2.2.0 in manifest.json and pyproject.toml
- [x] **Hassfest fixes** — removed `description` keys from entity definitions in strings.json and translations/en.json
- [x] **WidePriorityDifferentialSwitch bug fix** — `is_on` used `bool(value)` which returned `True` for `"off"`; fixed to `value != "off"` pattern
- [x] **Integration tests** — 220 tests across 9 files covering all entity platforms and core logic
- [x] **CI pipeline** — GitHub Actions workflow runs tests on PRs against Python 3.11 and 3.12
- [x] **README badges** — Tests, Hassfest, HACS Validation, HACS Custom, License
- [x] **LICENSE** — MIT license file added

## Still Open

- [ ] **climate.py: set_temperature when outdoor reset is on** — currently calls `set_hot_tank_target_temp()` which only sets the min end of the outdoor reset curve. Options:
  - **Option A**: Make target temperature read-only when outdoor reset is on
  - **Option B**: Disable set_temperature entirely when outdoor reset is on
  - **Option C**: Adjust both min and max proportionally
- [ ] **ColdTankTargetTemperature.native_value** — still reads `cold_tank_min_temp`; may need `target_temperature_cold_tank` equivalent if a cold tank temperature exists in the API
- [ ] **const.py cleanup** — `DEVICE_TYPE_THERMOSTAT` and `DEVICE_TYPE_HEAT_PUMP` are defined but no longer imported anywhere; consider removing
