"""Platform for sensor integration."""
import logging
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.binary_sensor import (
    BinarySensorEntity
)
from . import DOMAIN
from .kettle_entity import KettleEntity

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    sensors = []
    for device in hass.data[DOMAIN]:
        sensors.append(R4SkyKettleBinarySensor(hass.data[DOMAIN][device]))
    if len(sensors) > 0:
        add_entities(sensors)


class R4SkyKettleBinarySensor(BinarySensorEntity, KettleEntity):
    """Representation of a sensor."""

    async def async_added_to_hass(self):
        self._handle_update()
        self.async_on_remove(async_dispatcher_connect(self.hass, 'ready4sky_update', self._handle_update))

    def _handle_update(self):
        # print('R4SkyKettleBinarySensor _handle_update', self._connect._current_temperature)
        self._state = self._connect._current_temperature
        self.schedule_update_ha_state()

    @property
    def icon(self):
        """Icon is a lightning bolt."""
        return "mdi:lightbulb-on"

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return True if self._connect._state_boil or self._connect._state_heat else False

    def update(self):
        info = self._connect.mode()
        if info:
            self._state = True if info['status'] == 'on' else False

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.update()