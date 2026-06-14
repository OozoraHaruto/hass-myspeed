"""Constants for the MySpeed integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "myspeed"

# Config entry keys
CONF_URL: Final = "url"
CONF_PASSWORD: Final = "password"
CONF_VERIFY_SSL: Final = "verify_ssl"

# Options
CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 300  # seconds
MIN_SCAN_INTERVAL: Final = 30

DEFAULT_PORT: Final = 5216
DEFAULT_TIMEOUT: Final = 15

UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# Manufacturer / model shown on the HA device page
MANUFACTURER: Final = "gnmyt"
MODEL: Final = "MySpeed"
