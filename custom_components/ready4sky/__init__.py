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


PLATFORM_SCHEMA = vol.Schema(
    {vol.Optional(CONF_SCAN_INTERVAL, default=300): cv.positive_int}
)


async def async_setup(hass, config):
    print("Setup: SkyKettle RK-G210S")
    print('config', config)
    return True

async def async_remove_entry(hass, entry):
    try:
        for platform in SUPPORTED_PLATFORMS:
            await hass.config_entries.async_forward_entry_unload(entry, platform)
    except ValueError as e:
        print('ValueError', e)

async def async_setup_entry(hass, config_entry):
    hass.data[DOMAIN] = {}

    config = config_entry.data
    print('config', config)

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
    print('mac', mac)
    print('device', device)
    print('uniqueId', uniqueId)
    print('iface_name', iface_name)
    print('iface_index', iface_index)
    print('password', password)
    print('scan_delta', scan_delta)

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
        # hass.async_create_task(
        #     hass.config_entries.async_forward_entry_setup(hass.data[DOMAIN][mac], domain)
        # )

    # hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    # hass.helpers.discovery.load_platform('light', DOMAIN, {}, config)
    # hass.helpers.discovery.load_platform('switch', DOMAIN, {}, config)
    # hass.helpers.discovery.load_platform('binary_sensor', DOMAIN, {}, config)
    # hass.helpers.discovery.load_platform('water_heater', DOMAIN, {}, config)

    return True


    # mac = config.get(CONF_MAC)
    # device = config.get(CONF_DEVICE)
    # password = config.get(CONF_PASSWORD)
    # scan_delta = timedelta(seconds=config.get(CONF_SCAN_INTERVAL))
    # backlight = config.get(CONF_USE_BACKLIGHT)
    #
    # device_registry = await dr.async_get_registry(hass)
    # device_registry.async_get_or_create(
    #     config_entry_id=config_entry.entry_id,
    #     connections={(dr.CONNECTION_NETWORK_MAC, mac)},
    #     name="ReadyForSky",
    #     model="ReadyForSky",
    #     manufacturer="Redmond"
    # )
    #
    # kettler = hass.data[DOMAIN]["kettler"] = RedmondKettler(
    #     hass,
    #     mac,
    #     password,
    #     device,
    #     backlight
    # )
    #
    # try:
    #     await kettler.async_firstConnect()
    # except:
    #     _LOGGER.error("Connect to Kettler %s through device %s failed", mac, device)
    #     return False
    #
    # async_track_time_interval(hass, kettler.async_update, scan_delta)
    #
    # for domain in SUPPORTED_DOMAINS:
    #     hass.async_create_task(
    #         hass.config_entries.async_forward_entry_setup(config_entry, domain)
    #     )
    #
    # return True


# async def async_setup_entry(hass, config_entry):
#     print('config_entry', config_entry)
#
#     device_registry = await dr.async_get_registry(hass)
#     print('device_registry', device_registry)
#     # device_registry.async_get_or_create(
#     #     config_entry_id=config_entry.entry_id,
#     #     connections={(dr.CONNECTION_NETWORK_MAC, mac)},
#     #     name="ReadyForSky",
#     #     model="ReadyForSky",
#     #     manufacturer="Redmond"
#     # )
#     # print('device_registry', device_registry)
#
#     print('hass.data[DOMAIN]', hass.data[DOMAIN])
#
#
#
#     # async_track_time_interval(hass, kettler.async_update, scan_delta)
#     #
#     for domain in SUPPORTED_DOMAINS:
#         hass.async_create_task(
#             hass.config_entries.async_forward_entry_setup(config_entry, domain)
#         )
#     #
#     # return True
#
#
# async def async_remove_entry(hass, entry):
#     try:
#         for domain in SUPPORTED_DOMAINS:
#             await hass.config_entries.async_forward_entry_unload(entry, domain)
#     except ValueError:
#         pass

