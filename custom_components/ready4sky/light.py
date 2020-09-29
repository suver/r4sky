"""Platform for light integration."""
import logging
import homeassistant.util.color as color_util
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.light import (
    ATTR_RGB_COLOR,
    ATTR_HS_COLOR,
    SUPPORT_COLOR,
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA,
    LightEntity
)
from .kettle_entity import KettleEntity
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    illuminators = []
    for device in hass.data[DOMAIN]:
        illuminators.append(R4SkyKettleLight(hass.data[DOMAIN][device]))
        if hass.data[DOMAIN][device]['temperatureLight']:
            illuminators.append(R4SkyKettleWaterTemperatureLight(hass.data[DOMAIN][device]))
    if len(illuminators) > 0:
        add_entities(illuminators)


class R4SkyKettleLight(LightEntity, KettleEntity):
    """Representation of an Awesome Light."""

    _brightness = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._handle_update()
        self.async_on_remove(async_dispatcher_connect(self.hass, 'r4sky_update', self._handle_update))

    def _handle_update(self):
        print('R4SkyKettleLight _handle_update', self._connect._light_state)
        self._state = self._connect._light_state
        self.schedule_update_ha_state()

    @property
    def icon(self):
        """Icon is a lightning bolt."""
        return "mdi:lightbulb" if self.is_on else "mdi:lightbulb-outline"

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
    def supported_features(self):
        return SUPPORT_COLOR

    @property
    def name(self):
        """Return the display name of this light."""
        return f"Light {self._name}"

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

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        print('Instance turn_on', self._connect)
        print('kwargs', kwargs)
        color = '27FF00'
        if ATTR_HS_COLOR in kwargs:
            _hs = kwargs[ATTR_HS_COLOR]
            print('_hs', self.hs_to_rgbhex(_hs))
            color = self.hs_to_rgbhex(_hs)
        self._connect.onLight(rgb1=color, rgb2=color, rgb3=color)

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        print('Instance turn_off', self._connect)
        print('kwargs', kwargs)
        color = '27FF00'
        if ATTR_HS_COLOR in kwargs:
            _hs = kwargs[ATTR_HS_COLOR]
            print('_hs', self.hs_to_rgbhex(_hs))
            color = self.hs_to_rgbhex(_hs)
        self._connect.offLight(rgb1=color, rgb2=color, rgb3=color)


class R4SkyKettleWaterTemperatureLight(LightEntity, KettleEntity):
    """Representation of an Awesome Light."""

    _brightness = None

    async def async_added_to_hass(self):
        self._handle_update()
        self.async_on_remove(async_dispatcher_connect(self.hass, 'r4sky_update', self._handle_update))

    def _handle_update(self):
        self._state = self._connect._water_temperature_light_state
        self.schedule_update_ha_state()

    @property
    def icon(self):
        """Icon is a lightning bolt."""
        return "mdi:lightbulb-on" if self.is_on else "mdi:lightbulb-on-outline"

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    # def rgbhex_to_hs(self, rgbhex):
    #     rgb = color_util.rgb_hex_to_rgb_list(rgbhex)
    #     return color_util.color_RGB_to_hs(*rgb)
    #
    # def hs_to_rgbhex(self, hs):
    #     rgb = color_util.color_hs_to_RGB(*hs)
    #     return color_util.color_rgb_to_hex(*rgb)

    @property
    def available(self):
        return True

    @property
    def supported_features(self):
        return SUPPORT_COLOR

    @property
    def name(self):
        """Return the display name of this light."""
        return f"Water Temperature Light {self._name}"

    # @property
    # def brightness(self):
    #     """Return the brightness of the light.
    #     This method is optional. Removing it indicates to Home Assistant
    #     that brightness is not supported for this light.
    #     """
    #     return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        print('Instance turn_on', self._connect)
        print('kwargs', kwargs)
        if self._connect.onTemperatureToLight():
            self._state = True

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        # connect = self._connect.connect()
        print('Instance turn_off', self._connect)
        print('kwargs', kwargs)
        if self._connect.offTemperatureToLight():
            self._state = False