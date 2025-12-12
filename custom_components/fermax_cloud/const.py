"""Constants for the Fermax Cloud integration."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    PERCENTAGE,
)
from homeassistant.helpers.entity import EntityCategory

DOMAIN = "fermax_cloud"

# Configuration
CONF_UPDATE_INTERVAL = "update_interval"

# API Endpoints
FERMAX_OAUTH_BASE = "https://oauth-pro-duoxme.fermax.io"
FERMAX_API_BASE = "https://pro-duoxme.fermax.io"

# OAuth Client Credentials (from Fermax Blue app)
# ============================================================================
# IMPORTANT: These credentials are extracted from the official Fermax Blue
# mobile app and are the same for ALL users. They are required for OAuth2
# authentication with Fermax Cloud API.
#
# Security Note:
# - These are PUBLIC credentials (included in the mobile app)
# - They identify the "client application", not individual users
# - User credentials (email/password) remain private and secure
# - This is standard practice for mobile apps using OAuth2 ROPC flow
#
# Why are they here?
# - Fermax's API requires these credentials for authentication
# - They are hardcoded in the official mobile app
# - There is no alternative authentication method available
# - All third-party integrations must use the same credentials
#
# If Fermax changes these credentials:
# - The mobile app will be updated with new credentials
# - This integration will need to be updated accordingly
# - Users will need to update to the new version
# ============================================================================

import base64


def _get_client_credentials():
    """Get OAuth client credentials (obfuscated).
    
    Returns:
        tuple: (client_id, client_secret)
    
    Note:
        Credentials are base64 encoded to avoid easy scraping by bots,
        but this is NOT real security. Anyone can decode them.
    """
    # Format: base64(client_id:client_secret)
    encoded = "ZHB2N2lxejZlZTVtYXptMWlxOWR3MWQ0MnNseXV0NDhrajBtcDVmdm81OGo1aWg6Yzd5bGtxcHVqd2FoODV5aG5wcnYwd2R2eXp1dGxjbmt3NHN6OTBidWxkYnVsazE="
    decoded = base64.b64decode(encoded).decode()
    client_id, client_secret = decoded.split(":", 1)
    return client_id, client_secret


FERMAX_CLIENT_ID, FERMAX_CLIENT_SECRET = _get_client_credentials()

# Mobile App Headers
MOBILE_HEADERS = {
    "app-version": "4.2.5",
    "Accept-Language": "es-ES;q=1.0",
    "Accept": "*/*",
    "phone-os": "26.1",
    "User-Agent": "Blue/4.2.5 (com.fermax.bluefermax; build:2; iOS 26.1.0) Alamofire/5.10.2",
    "phone-model": "iPhone 15 Pro",
    "app-build": "2",
}

# Defaults
DEFAULT_UPDATE_INTERVAL = 60  # seconds

# Timeouts
TIMEOUT_CONNECTION = 10  # seconds
TIMEOUT_READ = 30  # seconds
TIMEOUT_TOTAL = 60  # seconds

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds

# Door keys
DOOR_KEY_ZERO = "ZERO"
DOOR_KEY_ONE = "ONE"
DOOR_KEY_GENERAL = "GENERAL"

# Door names mapping
DOOR_NAMES = {
    DOOR_KEY_ZERO: "Puerta Principal",
    DOOR_KEY_ONE: "Puerta 1",
    DOOR_KEY_GENERAL: "Puerta General",
}

# Sensor configuration keys
CONF_DEVICE_CLASS = "device_class"
CONF_STATE_CLASS = "state_class"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"
CONF_ICON = "icon"
CONF_ENTITY_CATEGORY = "entity_category"
CONF_TRANSLATION_KEY = "translation_key"
CONF_ENABLED_DEFAULT = "enabled_default"

# Sensor mapping for Fermax devices
SENSOR_MAPPING = {
    "connectionState": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:connection",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "connection_state",
        CONF_ENABLED_DEFAULT: True,
    },
    "status": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:information-outline",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "device_status",
        CONF_ENABLED_DEFAULT: True,
    },
    "type": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:devices",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "device_type",
        CONF_ENABLED_DEFAULT: True,
    },
    "wirelessSignal": {
        CONF_DEVICE_CLASS: None,
        CONF_STATE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None,
        CONF_ICON: "mdi:wifi",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "wireless_signal",
        CONF_ENABLED_DEFAULT: True,
    },
}

# Binary sensor mapping
BINARY_SENSOR_MAPPING = {
    "connected": {
        CONF_DEVICE_CLASS: BinarySensorDeviceClass.CONNECTIVITY,
        CONF_ICON: "mdi:lan-connect",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "connected",
        CONF_ENABLED_DEFAULT: True,
    },
    "activated": {
        CONF_DEVICE_CLASS: None,
        CONF_ICON: "mdi:check-circle-outline",
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        CONF_TRANSLATION_KEY: "activated",
        CONF_ENABLED_DEFAULT: True,
    },
}
