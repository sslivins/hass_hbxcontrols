# HBX Controls Home Assistant Integration

A custom Home Assistant integration for HBX Controls devices using the [pysensorlinx](https://pypi.org/project/pysensorlinx/) Python library.

## Features

- **Sensor Monitoring**: Monitor temperature, humidity, pressure, energy consumption, and power usage from your HBX Controls devices
- **Binary Sensors**: Track device connectivity, alarms, maintenance mode, and heating/cooling status
- **Climate Control**: Control thermostats and heat pumps with temperature setting and HVAC mode control
- **Real-time Updates**: Automatic polling of device data every 5 minutes
- **Multiple Buildings**: Support for multiple buildings and devices per account

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations" 
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Add"
6. Find "HBX Controls" in the integration list and click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `hbx_controls` folder to your `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI

## Configuration

1. In Home Assistant, go to **Configuration** > **Integrations**
2. Click the **+** button to add a new integration
3. Search for "HBX Controls"
4. Enter your HBX Controls username and password
5. Click **Submit**

The integration will automatically discover all your devices and create entities for:
- Temperature, humidity, pressure, energy, and power sensors
- Device connectivity and status binary sensors  
- Climate control entities for thermostats and heat pumps

## Supported Devices

This integration works with any HBX Controls-compatible device that provides:
- Sensor data (temperature, humidity, pressure, energy, power)
- Device status information
- Climate control capabilities (for thermostats/heat pumps)

## Device Parameters

The integration automatically maps HBX Controls device parameters to Home Assistant entities:

### Sensors
- `temperature` → Temperature sensor
- `humidity` → Humidity sensor  
- `pressure` → Pressure sensor
- `energy` → Energy sensor
- `power` → Power sensor

### Binary Sensors
- `online` → Connectivity status
- `alarm` → Alarm status
- `maintenance` → Maintenance mode
- `heating` → Heating status
- `cooling` → Cooling status

### Climate Controls
- `current_temperature` → Current temperature reading
- `target_temperature` → Target temperature setting
- `hvac_mode` → HVAC operation mode
- `heating`/`cooling` → Current HVAC action

## Troubleshooting

### Authentication Issues
- Verify your HBX Controls username and password are correct
- Check that your account has access to the devices you want to monitor

### Connection Issues  
- Ensure your Home Assistant instance has internet connectivity
- Check the Home Assistant logs for specific error messages

### Missing Entities
- Not all devices may support all sensor types
- Only devices with available parameters will create corresponding entities
- Check your device configuration in the HBX Controls app/portal

## Configuration Entities

This integration exposes a number of switches, number inputs, and selects that correspond to HBX controller settings. Below is an overview of how they work.

### Climate Control

The integration creates a **Climate** entity for each device with tank temperature data. You can set the HVAC mode (heat, cool, auto, off) and view the current and target tank temperatures.

**HVAC Mode Priority** (select): When the system is in Auto mode, this determines whether heating or cooling takes precedence when both are needed.

### Outdoor Reset

Outdoor reset automatically adjusts the tank target temperature based on outdoor conditions, improving efficiency by only heating/cooling water as much as needed.

#### How It Works

When outdoor reset is **enabled**, the controller computes a target temperature along a linear curve between two points:

| Outdoor Temp | Tank Target |
|---|---|
| Warm Weather Shutdown threshold | Min tank temp (least heating needed) |
| Design Outdoor Temp | Max tank temp (most heating needed) |

As the outdoor temperature drops from the warm end toward the design temp, the tank target rises proportionally from min to max. Below the design temp, the target clamps at max.

For **cooling**, the curve works in reverse — as outdoor temp rises toward the cold tank design temp, the target drops toward the cold tank min.

When outdoor reset is **off**, the system uses a flat setpoint (Hot/Cold Tank Target Temperature) instead of min/max.

#### Related Entities

| Entity | Type | Description |
|---|---|---|
| Hot Tank Outdoor Reset | Switch | Enable/disable outdoor reset for heating |
| Cold Tank Outdoor Reset | Switch | Enable/disable outdoor reset for cooling |
| Hot Tank Target Temperature | Number | Flat setpoint when outdoor reset is **off** |
| Hot Tank Min Temperature | Number | Bottom of heat curve (only when outdoor reset is **on**) |
| Hot Tank Max Temperature | Number | Top of heat curve (only when outdoor reset is **on**) |
| Hot Tank Design Outdoor Temp | Number | Coldest expected outdoor temp for heat curve (-40°F to 127°F) |
| Cold Tank Target Temperature | Number | Flat setpoint when outdoor reset is **off** |
| Cold Tank Min Temperature | Number | Bottom of cooling curve (only when outdoor reset is **on**) |
| Cold Tank Max Temperature | Number | Top of cooling curve (only when outdoor reset is **on**) |
| Cold Tank Design Outdoor Temp | Number | Hottest expected outdoor temp for cooling curve (0°F to 119°F) |

#### Design Outdoor Temperature — How to Choose

The **Design Outdoor Temperature** is the extreme outdoor temperature your system is designed around. At this temperature, the controller will target the max (heating) or min (cooling) tank temperature.

- **Set it to the coldest outdoor temperature you realistically expect** in your climate. For example, if -20°C (-4°F) is a common cold snap for your area, use that.
- **Setting it too low** (colder than reality) stretches the curve — your system won't reach max tank temp on the coldest actual days, potentially under-heating.
- **Setting it too high** (warmer than reality) compresses the curve — the system hits max tank temp too early and runs hotter water than needed for most of the season, reducing efficiency.
- **If outdoor temp drops below the design temp**, the target simply clamps at max. The system runs at full capacity — nothing breaks, you just don't get extra benefit from the curve.

**Tip**: Use the coldest temperature that occurs with some regularity (a few days per year), not a once-in-a-decade extreme.

### Weather Shutdown

| Entity | Type | Description |
|---|---|---|
| Warm Weather Shutdown | Switch | Enable/disable WWSD |
| Warm Weather Shutdown Temp | Number | Outdoor temp above which the system shuts off (34°F–180°F) |
| Cold Weather Shutdown | Switch | Enable/disable CWSD |
| Cold Weather Shutdown Temp | Number | Outdoor temp below which heat pumps shut off (33°F–119°F) |
| Weather Shutdown Lag Time | Number | Delay (hours) after threshold is met before entering shutdown (0–240h) |

### Heat Pump Staging

| Entity | Type | Description |
|---|---|---|
| Number of Stages | Number | Number of heat pump stages (1–4) |
| Stage ON Lag Time | Number | Min delay (minutes) between stages turning on (1–240) |
| Stage OFF Lag Time | Number | Min delay (seconds) between stages turning off (1–240) |
| Synchronized Stage Off | Switch | When on, all stages turn off at the same time |
| Two Stage Heat Pump | Switch | Enable for dual-stage or 2-compressor units (even stage counts only) |

### Heat Pump Rotation

| Entity | Type | Description |
|---|---|---|
| Rotate by Cycles | Switch | Enable rotation based on on/off cycles |
| Rotate Cycles | Number | Number of cycles before rotation (1–240) |
| Rotate by Time | Switch | Enable rotation based on run time |
| Rotate Time | Number | Hours of run time difference to trigger rotation (1–240) |

### Tank Differentials

| Entity | Type | Description |
|---|---|---|
| Hot Tank Differential | Number | Temp range around target before demand triggers (2°F–100°F) |
| Cold Tank Differential | Number | Same for cold tank (2°F–100°F) |
| Heat/Cool Switch Delay | Number | Delay (seconds) between switching heat/cool modes (30–600) |
| Wide Priority Differential | Switch | Exceed setpoint by differential before switching heat/cool demands (not for single-tank systems) |

### Backup Boiler

| Entity | Type | Description |
|---|---|---|
| Backup Lag Time | Switch | Enable minimum delay before backup activates |
| Backup Lag Time | Number | Delay (minutes) between last heat pump stage and backup (1–240) |
| Backup Differential | Switch | Enable instant backup activation on large temp drops |
| Backup Differential | Number | Temp drop from target at which backup fires immediately (2°F–100°F) |
| Backup Temperature | Switch | Enable outdoor temp threshold for backup |
| Backup Temperature | Number | Outdoor temp below which backup is allowed (2°F–100°F) |
| Backup Only Outdoor Temp | Switch | Enable backup-only mode below a threshold |
| Backup Only Outdoor Temp | Number | Outdoor temp below which only backup runs (2°F–100°F) |
| Backup Only Tank Temp | Switch | Enable backup-only mode above a tank temp |
| Backup Only Tank Temp | Number | Tank temp above which only backup heats (33°F–200°F) |

### Demand Overrides

| Entity | Type | Description |
|---|---|---|
| Permanent Heat Demand | Switch | Force continuous heating regardless of setpoints |
| Permanent Cool Demand | Switch | Force continuous cooling regardless of setpoints |

## Development

This integration is built using:
- [pysensorlinx](https://pypi.org/project/pysensorlinx/) - Python library for HBX Controls API
- Home Assistant's DataUpdateCoordinator for efficient data management
- Modern Home Assistant integration patterns and best practices

## Support

For issues related to:
- **Integration functionality**: Open an issue in this repository
- **HBX Controls API/devices**: Contact HBX Controls support
- **pysensorlinx library**: Check the [library repository](https://github.com/sslivins/pysensorlinx)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
