"""Constants for the CFMOTO RIDE integration."""
from datetime import timedelta

DOMAIN = "cfmoto"

CONF_AREA = "area"
CONF_BASE_URL = "base_url"

DEFAULT_BASE_URL = "https://tapi.cfmoto-oversea.com/v1.0"
DEFAULT_AREA = "PT"
SCAN_INTERVAL = timedelta(minutes=5)
