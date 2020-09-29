"""Platform for light integration."""
import logging
import homeassistant.util.color as color_util
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    TEMP_CELSIUS,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_OPERATION_MODE,
    SUPPORT_AWAY_MODE,
    STATE_ELECTRIC,
    STATE_OFF,
    ATTR_TEMPERATURE,
    ATTR_OPERATION_MODE
)
from . import DOMAIN
from .kettle_entity import KettleEntity

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    water_heateres = []
    for device in hass.data[DOMAIN]:
        water_heateres.append(R4SkyKettleWaterHeater(hass.data[DOMAIN][device]))
    if len(water_heateres) > 0:
        add_entities(water_heateres)


class R4SkyKettleWaterHeater(WaterHeaterEntity, KettleEntity):
    """Representation of an Awesome Light."""

    # The minimum temperature that can be set.
    _min_temp = 40
    # The maximum temperature that can be set.
    _max_temp = 95
    _current_temperature = 0
    _target_temperature = 0
    _temperature_unit = TEMP_CELSIUS
    _current_operation = STATE_OFF

    async def async_added_to_hass(self):
        self._handle_update()
        self.async_on_remove(async_dispatcher_connect(self.hass, 'ready4sky_update', self._handle_update))

    def _handle_update(self):
        self._state = self._connect._state_heat
        self._current_temperature = self._connect._current_temperature
        self._target_temperature = self._connect._target_temperature
        self.schedule_update_ha_state()

    @property
    def icon(self):
        """Icon is a lightning bolt."""
        return "mdi:kettle-steam" if self._state else "mdi:kettle"

    @property
    def available(self):
        return True

    @property
    def name(self):
        """Return the display name of this light."""
        return f"{self._name}"

    @property
    def operation_list(self):
        ''' List of possible operation modes. '''
        return [STATE_ELECTRIC, STATE_OFF]

    @property
    def supported_features(self):
        ''' List of supported features. '''
        return (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE)
        # return (SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE | SUPPORT_AWAY_MODE)

    @property
    def current_operation(self):
        ''' The current operation mode. '''
        # return self._current_operation
        return STATE_ELECTRIC if self._state else STATE_OFF

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def device_state_attributes(self):
        data = {"target_temp_step": 5}
        return data

    @property
    def temperature_unit(self):
        ''' One of TEMP_CELSIUS, TEMP_FAHRENHEIT, or TEMP_KELVIN. '''
        return self._temperature_unit

    @property
    def min_temp(self):
        ''' The minimum temperature that can be set. '''
        return self._min_temp

    @property
    def max_temp(self):
        ''' The maximum temperature that can be set. '''
        return self._max_temp

    @property
    def current_temperature(self):
        ''' The current temperature. '''
        return self._current_temperature

    def set_operation_modeor(self, **kwargs):
        '''Sets the operation mode of the water heater. Must be in the operation_list.'''
        self._state = kwargs.get(ATTR_OPERATION_MODE)
        if self._state:
            self._connect.onModeHeat(temperature=self._target_temperature)
        elif not self._state:
            self._connect.offModeHeat()

    def async_set_operation_mode(self, **kwargs):
        self.set_operation_modeor(**kwargs)

    def set_temperature(self, **kwargs):
        '''Sets the temperature the water heater should heat water to.'''
        self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        if self._state:
            self._connect.offModeHeat()
            self._connect.onModeHeat(temperature=self._target_temperature)

    async def async_set_temperature(self, **kwargs):
        self.set_temperature(**kwargs)

    def turn_away_mode_on(self):
        '''Set the water heater to away mode'''
        if not self._target_temperature:
            self._target_temperature = 95
        self._connect.onModeHeat(temperature=self._target_temperature)

    async def async_turn_away_mode_on(self):
        self.turn_away_mode_on()

    def turn_away_mode_off(self):
        '''Set the water heater back to the previous operation mode. Turn off away mode'''
        if not self._target_temperature:
            self._target_temperature = 95
        self._connect.offModeHeat()

    async def async_turn_away_mode_off(self):
        self.turn_away_mode_off()

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self.turn_away_mode_on()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.turn_on()

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self.turn_away_mode_off()

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
