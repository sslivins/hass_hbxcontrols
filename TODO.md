# Climate Entity: Outdoor Reset Target Temperature Issue

## Summary

When **outdoor reset is enabled**, the climate entity's target temperature behavior is incorrect for writes. It reads the correct calculated target but sets the wrong parameter.

## Current Behavior

### Reading (correct)
- The climate entity displays the **calculated target** from `temperatures[0].target` in the API response.
- This is the live value the controller computes from the outdoor reset curve based on current outdoor temp, min tank temp, max tank temp, and design outdoor temp.
- This works correctly.

### Writing (incorrect)
- When a user adjusts the target temperature on the climate entity, it calls `set_hot_tank_target_temp()`.
- In pysensorlinx, `set_hot_tank_target_temp()` is an alias for `set_hot_tank_min_temp()` — it only changes the **min** end of the outdoor reset curve.
- The user thinks they're setting the actual target, but they're really moving one end of the curve.
- When outdoor reset is **off**, this is fine — min and max are set to the same value (flat target). The `HotTankTargetTemperature` number entity already does this correctly by setting both min and max.

## What Needs to Change

When outdoor reset is enabled:
1. The climate entity's `set_temperature` should either be **disabled/read-only**, or it should clearly indicate it's not a direct setpoint.
2. The `HotTankMinTemperature` and `HotTankMaxTemperature` number entities are the proper controls when outdoor reset is on — these already work correctly and are only available when outdoor reset is enabled.

### Options to Consider
- **Option A**: Make the climate entity's target temperature **read-only** when outdoor reset is on (show the calculated target but don't allow setting it).
- **Option B**: Disable the climate entity entirely when outdoor reset is on and rely solely on the number entities.
- **Option C**: Keep it writable but change the behavior — e.g., adjust both min and max proportionally.

## Related: pysensorlinx Min/Max Swap Bug (FIXED)

The `HOT_TANK_MIN_TEMP` and `HOT_TANK_MAX_TEMP` constants in pysensorlinx were mapped to the wrong API keys. This has been fixed in the local pysensorlinx repo (branch TBD) but needs to be published:

- `dbt` = Design Boiler Temperature = **max** (was incorrectly mapped as min)
- `mbt` = Minimum Boiler Temperature = **min** (was incorrectly mapped as max)
- Same issue for cold tank: `dst` = max, `mst` = min

Once a new pysensorlinx version is published with this fix, update `requirements.txt` in this repo to use the new version. No code changes needed in this repo for that fix.

## Files to Modify
- `custom_components/hbxcontrols/climate.py` — `async_set_temperature()` and possibly `target_temperature` property
- `requirements.txt` — bump pysensorlinx version after the library fix is published
