<h1 align="center">
  <img src="custom_components/hbx_controls/brand/icon.png" width="96" alt="HBX Controls"><br>
  HBX Controls for Home Assistant
</h1>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/sslivins/hass_hbxcontrols/releases/latest"><img src="https://img.shields.io/github/v/release/sslivins/hass_hbxcontrols?display_name=tag&sort=semver" alt="GitHub release"></a>
  <a href="https://github.com/sslivins/hass_hbxcontrols/actions/workflows/hacs_validate.yml"><img src="https://github.com/sslivins/hass_hbxcontrols/actions/workflows/hacs_validate.yml/badge.svg" alt="HACS Validation"></a>
  <a href="https://github.com/sslivins/hass_hbxcontrols/actions/workflows/hassfest.yml"><img src="https://github.com/sslivins/hass_hbxcontrols/actions/workflows/hassfest.yml/badge.svg" alt="Hassfest"></a>
  <a href="https://github.com/sslivins/hass_hbxcontrols/actions/workflows/tests.yml"><img src="https://github.com/sslivins/hass_hbxcontrols/actions/workflows/tests.yml/badge.svg" alt="Unit Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/sslivins/hass_hbxcontrols" alt="License"></a>
</p>

<p align="center">
  Monitor and control your <a href="https://hbxcontrols.com">HBX Controls</a>
  hydronic heating / cooling controllers from Home Assistant —
  thermostats, heat pumps, tank temps, outdoor reset, weather shutdown,
  and all the staging knobs in one place.
</p>

---

## Features

- 🔌 **One-click install** via HACS (button below).
- 🌡️ **Climate per device** — current and target tank temperatures, HVAC mode, plus an HVAC-mode-priority selector for auto-mode tie-breaks.
- 📊 **Sensors** — temperature, humidity, pressure, energy, and power, mapped automatically from whatever the controller exposes.
- 🚨 **Binary sensors** — online, alarm, maintenance, heating, cooling.
- 🎛️ **Configuration entities** — outdoor reset, weather shutdown, tank differentials, heat-pump staging + rotation, backup boiler logic, and demand overrides as native HA switches / numbers / selects.
- 🏠 **Multi-building / multi-device** — every building and every device on your account is discovered automatically.

## Quick install

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sslivins&repository=hass_hbxcontrols&category=Integration)

Click the button above on a device that has access to your Home
Assistant. It takes you straight to the **Add custom repository**
dialog in HACS with everything pre-filled.

After it installs:

1. **Restart Home Assistant.**
2. Go to **Settings → Devices & Services → Add Integration**, search
   for **HBX Controls**.
3. Sign in with the same username + password you use on the HBX
   Controls portal / app.

## Requirements

- Home Assistant **2023.1** or newer
- [HACS](https://hacs.xyz) installed
- A working HBX Controls account
- At least one HBX-compatible device already paired with the account

## Manual install (without HACS)

If you don't run HACS:

1. Copy the entire `custom_components/hbx_controls/` directory into
   your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration from **Settings → Devices & Services**.

## How it works

The integration is a thin wrapper around
[`pysensorlinx`](https://pypi.org/project/pysensorlinx/), which talks
to the HBX Controls cloud on your behalf. It uses Home Assistant's
`DataUpdateCoordinator` to poll every device every 5 minutes and
surfaces whatever parameters the device actually reports — devices
without a given sensor simply won't get the corresponding entity.

## Configuration entities

The integration exposes a lot of switches / numbers / selects that
correspond directly to HBX controller settings. Below is what each
group does and the entities it produces.

### Climate

A **Climate** entity is created per device with tank temperature data.
You can set the HVAC mode (heat / cool / auto / off) and view current
and target tank temperatures.

**HVAC Mode Priority** (select): when the system is in Auto mode, this
determines whether heating or cooling takes precedence when both are
demanded.

### Outdoor reset

Outdoor reset automatically adjusts the tank target temperature based
on outdoor conditions, improving efficiency by only heating / cooling
water as much as needed.

When outdoor reset is **enabled**, the controller computes a target
temperature along a linear curve between two points:

| Outdoor temp | Tank target |
|---|---|
| Warm Weather Shutdown threshold | Min tank temp (least heating needed) |
| Design Outdoor Temp | Max tank temp (most heating needed) |

As the outdoor temperature drops from the warm end toward the design
temp, the tank target rises proportionally from min to max. Below the
design temp, the target clamps at max.

For **cooling**, the curve works in reverse — as outdoor temp rises
toward the cold-tank design temp, the target drops toward the
cold-tank min.

When outdoor reset is **off**, the system uses a flat setpoint
(Hot / Cold Tank Target Temperature) instead of min/max.

#### Entities

| Entity | Type | Description |
|---|---|---|
| Hot Tank Outdoor Reset | Switch | Enable/disable outdoor reset for heating |
| Cold Tank Outdoor Reset | Switch | Enable/disable outdoor reset for cooling |
| Hot Tank Target Temperature | Number | Flat setpoint when outdoor reset is **off** |
| Hot Tank Min Temperature | Number | Bottom of heat curve (only when outdoor reset is **on**) |
| Hot Tank Max Temperature | Number | Top of heat curve (only when outdoor reset is **on**) |
| Hot Tank Design Outdoor Temp | Number | Coldest expected outdoor temp for heat curve (-40 °F to 127 °F) |
| Cold Tank Target Temperature | Number | Flat setpoint when outdoor reset is **off** |
| Cold Tank Min Temperature | Number | Bottom of cooling curve (only when outdoor reset is **on**) |
| Cold Tank Max Temperature | Number | Top of cooling curve (only when outdoor reset is **on**) |
| Cold Tank Design Outdoor Temp | Number | Hottest expected outdoor temp for cooling curve (0 °F to 119 °F) |

#### Choosing a Design Outdoor Temperature

The **Design Outdoor Temperature** is the extreme outdoor temperature
your system is designed around. At this temperature, the controller
will target the max (heating) or min (cooling) tank temperature.

- **Set it to the coldest outdoor temperature you realistically expect**
  in your climate (e.g. if -20 °C / -4 °F is a typical cold snap, use that).
- **Setting it too low** stretches the curve — the system won't reach
  max tank temp on the coldest actual days, potentially under-heating.
- **Setting it too high** compresses the curve — the system hits max
  tank temp too early and runs hotter water than needed for most of
  the season, reducing efficiency.
- **If outdoor temp drops below the design temp**, the target simply
  clamps at max. The system runs at full capacity — nothing breaks,
  you just don't get extra benefit from the curve.

> **Tip:** use the coldest temperature that occurs with some regularity
> (a few days per year), not a once-in-a-decade extreme.

### Weather shutdown

| Entity | Type | Description |
|---|---|---|
| Warm Weather Shutdown | Switch | Enable/disable WWSD |
| Warm Weather Shutdown Temp | Number | Outdoor temp above which the system shuts off (34 °F–180 °F) |
| Cold Weather Shutdown | Switch | Enable/disable CWSD |
| Cold Weather Shutdown Temp | Number | Outdoor temp below which heat pumps shut off (33 °F–119 °F) |
| Weather Shutdown Lag Time | Number | Delay (hours) after threshold is met before entering shutdown (0–240 h) |

### Heat pump staging

| Entity | Type | Description |
|---|---|---|
| Number of Stages | Number | Number of heat pump stages (1–4) |
| Stage ON Lag Time | Number | Min delay (minutes) between stages turning on (1–240) |
| Stage OFF Lag Time | Number | Min delay (seconds) between stages turning off (1–240) |
| Synchronized Stage Off | Switch | When on, all stages turn off at the same time |
| Two Stage Heat Pump | Switch | Enable for dual-stage or 2-compressor units (even stage counts only) |

### Heat pump rotation

| Entity | Type | Description |
|---|---|---|
| Rotate by Cycles | Switch | Enable rotation based on on/off cycles |
| Rotate Cycles | Number | Number of cycles before rotation (1–240) |
| Rotate by Time | Switch | Enable rotation based on run time |
| Rotate Time | Number | Hours of run-time difference to trigger rotation (1–240) |

### Tank differentials

| Entity | Type | Description |
|---|---|---|
| Hot Tank Differential | Number | Temp range around target before demand triggers (2 °F–100 °F) |
| Cold Tank Differential | Number | Same for cold tank (2 °F–100 °F) |
| Heat/Cool Switch Delay | Number | Delay (seconds) between switching heat/cool modes (30–600) |
| Wide Priority Differential | Switch | Exceed setpoint by differential before switching demands (not for single-tank systems) |

### Backup boiler

| Entity | Type | Description |
|---|---|---|
| Backup Lag Time | Switch | Enable minimum delay before backup activates |
| Backup Lag Time | Number | Delay (minutes) between last heat pump stage and backup (1–240) |
| Backup Differential | Switch | Enable instant backup activation on large temp drops |
| Backup Differential | Number | Temp drop from target at which backup fires immediately (2 °F–100 °F) |
| Backup Temperature | Switch | Enable outdoor temp threshold for backup |
| Backup Temperature | Number | Outdoor temp below which backup is allowed (2 °F–100 °F) |
| Backup Only Outdoor Temp | Switch | Enable backup-only mode below a threshold |
| Backup Only Outdoor Temp | Number | Outdoor temp below which only backup runs (2 °F–100 °F) |
| Backup Only Tank Temp | Switch | Enable backup-only mode above a tank temp |
| Backup Only Tank Temp | Number | Tank temp above which only backup heats (33 °F–200 °F) |

### Demand overrides

| Entity | Type | Description |
|---|---|---|
| Permanent Heat Demand | Switch | Force continuous heating regardless of setpoints |
| Permanent Cool Demand | Switch | Force continuous cooling regardless of setpoints |

## Credentials

Your HBX Controls password is stored only in the Home Assistant config
entry (encrypted at rest like every other HA credential) and is never
written to logs by this integration.

## Troubleshooting

- **Authentication errors** — double-check your HBX Controls username
  and password and confirm the account has access to the devices.
- **Missing entities** — only entities for parameters the device
  actually reports are created. Different controller models expose
  different parameter sets.
- **No data updating** — check the HA logs for connection errors and
  confirm your HA instance has internet access.

## Development

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1     # Windows PowerShell
# or:  source .venv/bin/activate # macOS / Linux
pip install -e ".[tests]"

ruff check custom_components/hbx_controls tests
mypy custom_components/hbx_controls
pytest
```

> **Note:** running the full pytest suite locally on Windows fails
> because `pytest-homeassistant-custom-component` ultimately imports
> `fcntl`, which is Unix-only. Tests run cleanly on Linux CI.

## Contributing

Bug reports and PRs welcome on the
[issue tracker](https://github.com/sslivins/hass_hbxcontrols/issues).

For issues with the underlying API or your hardware, talk to HBX
Controls directly. For issues with the wrapping library, see
[`pysensorlinx`](https://github.com/sslivins/pysensorlinx).

## License

[MIT](LICENSE) © [sslivins](https://github.com/sslivins)
