DOMAIN = "polster_akku"
PLATFORMS = ["sensor"]

STORAGE_KEY = "polster_akku_ignored"
STORAGE_VERSION = 1

CONF_THRESHOLD = "threshold"
CONF_NOTIFY = "notify_service"
DEFAULT_THRESHOLD = 20

SKIP_SUFFIXES = (
    "_battery_plus",
    "_battery_state",
    "_battery_low",
    "_battery_voltage",
)

ATTR_LISTE = "liste"
ATTR_GERAETE = "geraete"
ATTR_IGNORIERT = "ignoriert"
