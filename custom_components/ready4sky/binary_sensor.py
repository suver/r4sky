"""Platform for sensor integration."""
import logging
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import (
    BinarySensorEntity
)
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    sensors = []
    for device in hass.data[DOMAIN]:
        sensors.append(R4SkyKettleBinarySensor(hass.data[DOMAIN][device], device))
    if len(sensors) > 0:
        add_entities(sensors)


class R4SkyKettleBinarySensor(BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(self, config, device):
        """Initialize the sensor."""
        self._state = None
        self._config = config
        self._device = device
        self._name = ' '.join(['Binary', 'Sensor', self._config['name']])
        self._connect = self._config['instance']
        # self._connect = self._config['class'].getInstance(self._config['mac'], self._config['password'])
        print('BinarySensor Kettle', self._name, self._connect)

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
        return self._state

    def update(self):
        print('Update Sensor')
        print('Instance update', self._connect)
        info = self._connect.mode()
        if info:
            self._state = True if info['status'] == 'on' else False

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self.update()