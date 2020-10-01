from bluepy.btle import BTLEDisconnectError
from homeassistant.helpers.dispatcher import async_dispatcher_send
import traceback
import time
from datetime import datetime
from .kettle_controller import RedmondKettleController
from .exception import RedmondKettleConnectException
from .tool import iteration_decorator
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)


class RedmondKettle():

    __instance = {}
    _mac = None
    _password = None

    def __init__(self, mac=None, password=None, iface=None, hass=None):
        self._connect = None
        self._hass = hass
        self._mac = mac
        self._password = password
        self._iface = iface
        self._touch_time = 0
        self._self_reconnect = 0
        self.init_activate = False

        # The current temperature.
        self._current_temperature = 0
        # The temperature we are trying to reach.
        self._target_temperature = 0
        # self._current_power_w = None
        self._energy_kwh = None
        self._started_count = 0
        self._mode = None
        self._state = None
        self._light_state = None
        self._state_boil = None
        self._state_heat = None
        self._water_temperature_light_state = None

    @classmethod
    def getInstance(cls, mac=None, password=None):
        if not cls.__instance.get(cls._mac, None):
            cls.__instance[cls._mac] = RedmondKettle(mac=mac, password=password)
        return cls.__instance.get(cls._mac, None)

    def disconnect(self):
        try:
            self.log('Disconnected device')
            self._connect = None
            self._connect.disconnect()
        except:
            pass

    # @iteration_decorator
    def connect(self):
        self._self_reconnect = self._self_reconnect + 1
        if self._self_reconnect > 10:
            self.disconnect()
            self.log('Maximum limit to connect to device', self._mac, self._password, self._iface)
            self._self_reconnect = 0
            raise Exception('Maximum limit to connect to device', self._mac, self._password, self._iface)

        self.log('Connect to device with', self._mac, self._password, self._iface, self._connect)
        if not self._connect:
            try:
                self._connect = RedmondKettleController(self._mac, self._password, iface=self._iface)
                self._connect.withDebug()
                self.log('Kettle Connected', self._mac, self._password)
                if not self._connect.auth():
                    raise Exception('bte.auth() error')
                if not self.init_activate:
                    if not self._connect.sync():
                        raise Exception('bte.sync() error')
                    self.init_activate = True
            except RedmondKettleConnectException as e:
                self.log('Kettle Connected RedmondKettleConnectException', e, error=True)
                time.sleep(3)
                self.disconnect()
                self.connect()
            except BTLEDisconnectError as e:
                self.log('Kettle Connected BTLEDisconnectError', e, error=True)
                time.sleep(3)
                self.disconnect()
                self.connect()

        self._self_reconnect = 0
        return self._connect

    def log(self, *args, msg='', level=1, error=False, log=False, debug=False):
        if error:
            _LOGGER.error(' '.join([str(a) for a in args]) + "\n" + traceback.format_exc())
        if log:
            _LOGGER.log(level, msg, args, traceback=traceback.format_exc())
        if debug:
            _LOGGER.debug(level, msg, args, traceback=traceback.format_exc())
        else:
            _LOGGER.info(' '.join([str(a) for a in args]))

    # @iteration_decorator
    def paring(self):
        try:
            bte = self.connect()
            mode = bte.mode()
            self.log('Kettle Paring', mode)
            return mode
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Paring Error', e)

    # @iteration_decorator
    def mode(self):
        try:
            bte = self.connect()
            mode = bte.mode()
            self._update_data_mode(mode)
            self.log('Kettle MODE', mode)
            return mode
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle MODE Error', e)

    # @iteration_decorator
    def stat(self):
        try:
            self.log('CHeck stat')
            bte = self.connect()
            stat = bte.stat()
            self.log('Kettle STAT', stat)
            return stat
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle STAT Error', e)

    # @iteration_decorator
    def on(self):
        try:
            bte = self.connect()
            if self._light_state:
                self.offLight()
            bte.on()
            self._state_boil = True
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self.log('Kettle ON')
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle ON Error', e)

    # @iteration_decorator
    def off(self):
        try:
            bte = self.connect()
            bte.off()
            self._state_boil = False
            self._state_heat = False
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self.log('Kettle OFF')
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle OFF Error', e)

    # @iteration_decorator
    def onTemperatureToLight(self):
        try:
            bte = self.connect()
            bte.onTemperatureToLight()
            self.log('Kettle Temperature Light ON')
            self._water_temperature_light_state = True
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            return True
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Temperature Light ON Error', e)

    # @iteration_decorator
    def offTemperatureToLight(self):
        try:
            bte = self.connect()
            bte.offTemperatureToLight()
            self.log('Kettle Temperature Light OFF')
            self._water_temperature_light_state = False
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            return True
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Temperature Light OFF Error', e)

    # @iteration_decorator
    def onModeHeat(self, temperature=80):
        try:
            bte = self.connect()
            if self._light_state:
                self.offLight()
            bte.sendMode(mode='heat', temperature=temperature, howMuchBoil=80)
            bte.onMode()
            self._state_heat = True
            mode = bte.mode()
            self._update_data_mode(mode)
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self.log('Kettle Heat ON')
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Heat ON Error', e)

    # @iteration_decorator
    def offModeHeat(self):
        try:
            bte = self.connect()
            bte.offMode()
            self._state_heat = False
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self.log('Kettle Heat OFF')
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Heat OFF Error', e)

    # @iteration_decorator
    def onModeBoil(self):
        try:
            bte = self.connect()
            if self._light_state:
                self.offLight()
            bte.sendMode(mode='boil', temperature=100, howMuchBoil=50)
            bte.onMode()
            bte.onTemperatureToLight()
            self._state_boil = True
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self.log('Kettle Boil ON')
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Boil ON Error', e)

    # @iteration_decorator
    def onLight(self, rgb1='27FF00', rgb2='00FFEC', rgb3='000FFF'):
        try:
            bte = self.connect()
            if self._state_boil or self._state_heat:
                bte.offMode()
            bte.sendRGBLight('light', rgb1=rgb1, rgb2=rgb2, rgb3=rgb3)
            bte.sendMode(mode='light')
            bte.onMode()
            self._light_state = True
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self.log('Kettle Light ON', rgb1, rgb2, rgb3)
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Light ON Error', e)

    # @iteration_decorator
    def offLight(self, rgb1='eeff00', rgb2='ffbb00', rgb3='ff3c00'):
        try:
            bte = self.connect()
            bte.offMode()
            self._light_state = False
            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self.log('Kettle Light OFF', rgb1, rgb2, rgb3)
        except Exception as e:
            self.disconnect()
            raise Exception('Kettle Light OFF Error', e)

    def _update_data_mode(self, mode):
        if mode:
            self._state_boil = True if mode['mode'] == 'boil' and mode['status'] == 'on' else False
            self._state_heat = True if mode['mode'] == 'heat' and mode['status'] == 'on' else False
            self._light_state = True if mode['mode'] == 'light' and mode['status'] == 'on' else False
            self._water_temperature_light_state = True if mode['mode'] == 'light' and mode['status'] == 'off' else False
            self._state = True if mode['status'] == 'on' else False
            self._mode = mode['mode']
            self._current_temperature = mode['current_temperature']
            self._target_temperature = mode['temperature']

    def update(self, *args, **kwargs):
        if self._touch_time <= time.time():
            return
        try:
            self.log('Update', args, kwargs)
            bte = self.connect()
            mode = bte.mode()
            self._update_data_mode(mode)
            stat = bte.stat()
            if stat:
                self._energy_kwh = stat['energy_kwh'] / 1000
                self._started_count = stat['count']

            if self._hass:
                async_dispatcher_send(self._hass, 'ready4sky_update')
            self._touch_time = time.time() + 25
        except Exception as e:
            self.disconnect()
            self._update_data_mode({
                'mode': None,
                'status': None,
                'current_temperature': None,
                'temperature': None
            })
            raise Exception('Update Error', e)