"""Platform for sensor integration."""
import logging
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
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
        sensors.append(R4SkyKettleSensor(hass.data[DOMAIN][device]))
    if len(sensors) > 0:
        add_entities(sensors)

class R4SkyKettleSensor(KettleEntity):
    """Representation of a sensor."""

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

    async def async_added_to_hass(self):
        self._handle_update()
        self.async_on_remove(async_dispatcher_connect(self.hass, 'r4sky_update', self._handle_update))

    def _handle_update(self):
        print('R4SkyKettleSensor _handle_update', self._connect._current_temperature)
        self._state = self._connect._current_temperature
        self.schedule_update_ha_state()

    @property
    def icon(self):
        """Icon is a lightning bolt."""
        return "mdi:coolant-temperature"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Sensor {self._name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        print('self._connect', self._connect._current_temperature)
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS