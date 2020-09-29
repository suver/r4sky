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

    _energy_kwh = 0
    _started_count = 0

    async def async_added_to_hass(self):
        self._handle_update()
        self.async_on_remove(async_dispatcher_connect(self.hass, 'ready4sky_update', self._handle_update))

    def _handle_update(self):
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
        self.log('R4SkyKettleSwitch.turn_on')
        self._connect.onModeBoil()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.turn_on()

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self.log('R4SkyKettleSwitch.turn_off')
        self._connect.off()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.turn_off()

    def toggle(self, **kwargs):
        """Toggle the entity."""
        if self._state:
            self.turn_off()
        else:
            self.turn_on()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        self.toggle()