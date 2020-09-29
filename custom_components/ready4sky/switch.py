"""Platform for light integration."""
import logging
import homeassistant.util.color as color_util
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.switch import (
    SwitchEntity
)
from . import DOMAIN
from .kettle_entity import KettleEntity

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    switches = []
    for device in hass.data[DOMAIN]:
        switches.append(R4SkyKettleSwitch(hass.data[DOMAIN][device]))
    if len(switches) > 0:
        add_entities(switches)


class R4SkyKettleSwitch(SwitchEntity, KettleEntity):
    """Representation of an Awesome Light."""

    # def __init__(self, config, device):
    #     """Initialize an AwesomeLight."""
    #     self._state = None
    #     # self._current_power_w = None
    #     self._today_energy_kwh = None
    #     self._is_standby = None
    #     self._config = config
    #     self._device = device
    #     self._brightness = None
    #     self._name = ' '.join(['Switch', self._config['name']])
    #     self._info = {}
    #     self._connect = self._config['instance']
    #     print('Switch Kettle', self._name, self._connect)

    _energy_kwh = 0
    _started_count = 0

    async def async_added_to_hass(self):
        self._handle_update()
        self.async_on_remove(async_dispatcher_connect(self.hass, 'r4sky_update', self._handle_update))

    def _handle_update(self):
        print('R4SkyKettleSwitch _handle_update', self._connect._state_boil)
        self._state = self._connect._state_boil
        self._started_count = self._connect._started_count
        self.schedule_update_ha_state()

    @property
    def icon(self):
        """Icon is a lightning bolt."""
        return "mdi:kettle-steam" if self.is_on else "mdi:kettle"

    def rgbhex_to_hs(self, rgbhex):
        rgb = color_util.rgb_hex_to_rgb_list(rgbhex)
        return color_util.color_RGB_to_hs(*rgb)

    def hs_to_rgbhex(self, hs):
        rgb = color_util.color_hs_to_RGB(*hs)
        return color_util.color_rgb_to_hex(*rgb)

    @property
    def available(self):
        return True

    @property
    def name(self):
        """Return the display name of this light."""
        return f"{self._name}"

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def is_standby(self):
        """Return true if light is on."""
        return self._is_standby

    @property
    def energy_kwh(self):
        """Return true if light is on."""
        return self._energy_kwh

    @property
    def _current_power_w(self):
        """Return true if light is on."""
        return self.__current_power_w

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        print('Instance turn_on', self._connect)
        print('kwargs', kwargs)
        self._connect.onModeBoil()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.turn_on()

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        print('Instance turn_off', self._connect)
        print('kwargs', kwargs)
        self._connect.off()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.turn_off()

    def toggle(self, **kwargs):
        """Toggle the entity."""
        print('Instance toggle', self._connect)
        print('kwargs', kwargs)
        if self._state:
            self._connect.off()
        else:
            self._connect.on()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        self.toggle()

    # async def async_update(self):
    #     """Fetch new state data for this light.
    #     This is the only method that should fetch new data for Home Assistant.
    #     """
    #     print('Update Switch')
    #     print('Instance update', self._connect)
    #     try:
    #         self._is_standby = True
    #         info = self._connect.mode()
    #         if info:
    #             self._state = True if (info['mode'] == 'boil' or info['mode'] == 'heat') and info['status'] == 'on' else False
    #         stat = self._connect.stat()
    #         if stat:
    #             self._today_energy_kwh = stat['energy_kwh'] / 1000
    #
    #     except:
    #         self._is_standby = False