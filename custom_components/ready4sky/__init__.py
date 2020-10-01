from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from datetime import timedelta

from homeassistant.helpers.event import async_track_time_interval
from .const import (
    DOMAIN,
    DEFAULT_INTERFACE,
    DEFAULT_SCAN_INTERVAL,
    CONF_BLUETOOTH_FACE_NAME,
    CONF_BLUETOOTH_FACE_INDEX,
    CONF_MODEL,
    CONF_MANUFACTURER,
    CONF_NAME,
    CONF_TEMPERATURE_LIGHT,
    CONF_UNIQUE_ID,
    STRING_HEX_SYMBOLS
)

from homeassistant.const import (
    CONF_DEVICE,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL
)

from .const import DOMAIN, SUPPORTED_PLATFORMS
from .lib import RedmondKettle
import logging
_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = vol.Schema(
    {vol.Optional(CONF_SCAN_INTERVAL, default=300): cv.positive_int}
)


async def async_setup(hass, config):
    _LOGGER.info(f"Start async_setup")
    return True

async def async_remove_entry(hass, entry):
    try:
        for platform in SUPPORTED_PLATFORMS:
            await hass.config_entries.async_forward_entry_unload(entry, platform)
    except ValueError as e:
        _LOGGER.error(f"ValueError {e}")

async def async_setup_entry(hass, config_entry):
    hass.data[DOMAIN] = {}

    config = config_entry.data

    mac = config.get(CONF_MAC)
    uniqueId = config.get(CONF_UNIQUE_ID)
    iface_name = config.get(CONF_BLUETOOTH_FACE_NAME)
    iface_index = config.get(CONF_BLUETOOTH_FACE_INDEX)
    device = config.get(CONF_DEVICE)
    password = config.get(CONF_PASSWORD)
    model = config.get(CONF_MODEL)
    manufacturer = config.get(CONF_MANUFACTURER)
    name = config.get(CONF_NAME)
    temperatureLight = config.get(CONF_TEMPERATURE_LIGHT, True)
    scan_delta = timedelta(seconds=config.get(CONF_SCAN_INTERVAL))

    _LOGGER.info(f"Start ready4sky[{name}] uniqueId:{uniqueId} mac:{mac} iface_index:{iface_index} password:{password}")

    # hass.states.async_set("r4sky.name", "SkyKettle RK-G210S")

    hass.data[DOMAIN] = {
        mac: {
            'name': name,
            'model': model,
            'manufacturer': manufacturer,
            'iface': iface_index,
            'mac': mac,
            'password': password,
            'instance': None,
            'temperature': 0,
            'temperatureLight': temperatureLight,
        },
    }

    # Data that you want to share with your platforms
    kettle = RedmondKettle(
        hass.data[DOMAIN][mac]['mac'],
        hass.data[DOMAIN][mac]['password'],
        iface=hass.data[DOMAIN][mac]['iface'],
        hass=hass
    )

    hass.data[DOMAIN][mac]['instance'] = kettle

    async_track_time_interval(hass, kettle.update, scan_delta)

    for platform in SUPPORTED_PLATFORMS:
        hass.helpers.discovery.load_platform(platform, DOMAIN, {}, hass.data[DOMAIN][mac])

    return True