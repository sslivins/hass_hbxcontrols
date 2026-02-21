"""Constants for the HBX Controls integration."""

DOMAIN = "hbx_controls"

# Configuration keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_NAME = "HBX Controls"
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes
MIN_SCAN_INTERVAL = 60  # 1 minute minimum
MAX_SCAN_INTERVAL = 3600  # 1 hour maximum

# Device types
DEVICE_TYPE_SENSOR = "sensor"
DEVICE_TYPE_THERMOSTAT = "thermostat"
DEVICE_TYPE_HEAT_PUMP = "heat_pump"

# Sensor types
SENSOR_TEMPERATURE = "temperature"
SENSOR_HUMIDITY = "humidity"
SENSOR_PRESSURE = "pressure"
SENSOR_ENERGY = "energy"
SENSOR_POWER = "power"

# Error messages
ERROR_AUTH_FAILED = "auth_failed"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_UNKNOWN = "unknown"
