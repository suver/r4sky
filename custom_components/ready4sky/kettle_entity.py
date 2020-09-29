import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from typing import Any, Awaitable, Dict, Iterable, List, Optional
from homeassistant.helpers.typing import StateType
from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_PICTURE,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_SUPPORTED_FEATURES,
    ATTR_UNIT_OF_MEASUREMENT,
    DEVICE_DEFAULT_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from .const import (
    DOMAIN,
)


class KettleEntity(Entity):

    VERSION = 1

    __instance = {}

    def __init__(self, config):
        self._config = config
        self._mac = self._config['mac']
        self._manufacturer = self._config['manufacturer']
        self._model = self._config['model']
        self._password = self._config['password']
        self._iface = self._config['iface']
        self._connect = self._config['instance']
        self._name = self._config['name']
        self._state = None

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state.

        False if entity pushes its state to HA.
        """
        return False

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return f"{self._mac}-{self.name}"

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
            "manufacturer": self._manufacturer,
            "model": self._model,
            "version": self.VERSION,
        }

    @property
    def state(self) -> StateType:
        """Return the state of the entity."""
        return STATE_UNKNOWN

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement of this entity, if any."""
        return None

    @property
    def icon(self) -> Optional[str]:
        """Return the icon to use in the frontend, if any."""
        return None

    # @property
    # def enabled(self):
    #     return True

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    @property
    def force_update(self) -> bool:
        """Return True if state updates should be forced.

        If True, a state change will be triggered anytime the state property is
        updated, not just when the value changes.
        """
        return False

    @property
    def supported_features(self) -> Optional[int]:
        """Flag supported features."""
        return None



class KettleToggleEntity(KettleEntity):
    """An abstract class for entities that can be turned on and off."""

    @property
    def state(self) -> str:
        """Return the state."""
        return STATE_ON if self.is_on else STATE_OFF

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        raise NotImplementedError()

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        raise NotImplementedError()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        assert self.hass is not None
        await self.hass.async_add_executor_job(ft.partial(self.turn_on, **kwargs))

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        raise NotImplementedError()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        assert self.hass is not None
        await self.hass.async_add_executor_job(ft.partial(self.turn_off, **kwargs))

    def toggle(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        if self.is_on:
            self.turn_off(**kwargs)
        else:
            self.turn_on(**kwargs)

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off(**kwargs)
        else:
            await self.async_turn_on(**kwargs)