"""Constants for the Argos Translate integration."""

DOMAIN = "argos_translate"

# Config keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_API_KEY = "api_key"
CONF_SOURCE_LANG = "source_lang"
CONF_TARGET_LANG = "target_lang"

# Defaults
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5000
DEFAULT_SCAN_INTERVAL = 60

# Service
SERVICE_TRANSLATE = "translate"
ATTR_TEXT = "text"
ATTR_SOURCE = "source"
ATTR_TARGET = "target"

FRONTEND_SCRIPT_URL = f"/hacsfiles/{DOMAIN}/{DOMAIN}-card.js"
