from bluepy.btle import BTLEDisconnectError
from homeassistant.helpers.dispatcher import async_dispatcher_send
import traceback
import time
from datetime import datetime
from .kettle_controller import RedmondKettleController
from .exception import RedmondKettleConnectException
from .tool import iteration_decorator
import logging

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

    # @iteration_decorator
    def connect(self, permanent=False):
        self.log('Connect to device with', permanent)
        if permanent:
            try:
                self._connect.disconnect()
                self.log('Disconnected device', permanent)
                pass
            except:
                pass
            self._connect = None

        if not self._connect:
            try:
                self._connect = RedmondKettleController(self._mac, self._password, iface=self._iface)
                # self._connect.withDebug()
                self.log('Kettle Connected', self._mac, self._password)
                if not self._connect.auth():
                    raise Exception('bte.auth() error')
                if not self.init_activate:
                    if not self._connect.sync():
                        raise Exception('bte.sync() error')
                    self.init_activate = True
            except RedmondKettleConnectException as e:
                self.log('RedmondKettleConnectException', e)
                # print(traceback.format_exc())
                time.sleep(3)
                self.connect(permanent=True)
            except BTLEDisconnectError as e:
                self.log('BTLEDisconnectError', e)
                # print(traceback.format_exc())
                time.sleep(3)
                self.connect(permanent=True)

        return self._connect

    def log(self, *args, error=False):
        if error:
            _LOGGER.error(datetime.today().strftime("%d.%m.%y %H:%M:%S") + ' '.join([str(a) for a in args]))
        # else:
        #     _LOGGER.info(datetime.today().strftime("%d.%m.%y %H:%M:%S") + ' '.join([str(a) for a in args]))

    # @iteration_decorator
    def paring(self):
        self.log('CHeck Paring')
        bte = self.connect()
        mode = bte.mode()
        if not mode:
            raise Exception('bte.mode() error')
        self.log('Kettle MODE', mode)
        return mode

    # @iteration_decorator
    def mode(self):
        self.log('CHeck Mode')
        bte = self.connect()
        mode = bte.mode()
        if not mode:
            raise Exception('bte.mode() error')
        self._update_data_mode(mode)
        self.log('Kettle MODE', mode)
        return mode

    # @iteration_decorator
    def stat(self):
        self.log('CHeck stat')
        bte = self.connect()
        stat = bte.stat()
        if not stat:
            raise Exception('bte.stat() error')
        self.log('Kettle STAT', stat)
        return stat

    # @iteration_decorator
    def on(self):
        bte = self.connect()
        mode = bte.mode()
        if mode['mode'] == 'light' and mode['status'] == 'on':
            if not bte.offMode():
                raise Exception('bte.offMode() error')
        if not bte.on():
            raise Exception('bte.on() error')
        self._state_boil = True
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        self.log('Kettle ON')

    # @iteration_decorator
    def off(self):
        bte = self.connect()
        if not bte.off():
            raise Exception('bte.off() error')
        self._state_boil = False
        self._state_heat = False
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        self.log('Kettle OFF')

    # @iteration_decorator
    def onTemperatureToLight(self):
        bte = self.connect()
        if not bte.onTemperatureToLight():
            raise Exception('bte.onTemperatureToLight() error')
        self.log('Kettle Temperature Light ON')
        self._water_temperature_light_state = True
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        return True

    # @iteration_decorator
    def offTemperatureToLight(self):
        bte = self.connect()
        if not bte.offTemperatureToLight():
            raise Exception('bte.offTemperatureToLight() error')
        self.log('Kettle Temperature Light OFF')
        self._water_temperature_light_state = False
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        return True

    # @iteration_decorator
    def onModeHeat(self, temperature=80):
        bte = self.connect()
        if not bte.sendMode(mode='heat', temperature=temperature, howMuchBoil=80):
            raise Exception('bte.sendMode() error')
        if not bte.onMode():
            raise Exception('bte.onMode() error')
        self._state_heat = True
        mode = bte.mode()
        self._update_data_mode(mode)
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        self.log('Kettle Heat ON')

    # @iteration_decorator
    def offModeHeat(self):
        self.log('>>>>>>>>>>>>>>>>>>>>>>>>offModeHeat')
        bte = self.connect()
        if not bte.offMode():
            raise Exception('bte.offMode() error')
        self._state_heat = False
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        self.log('Kettle Heat OFF')

    # @iteration_decorator
    def onModeBoil(self):
        bte = self.connect()
        if not bte.sendMode(mode='boil', temperature=100, howMuchBoil=50):
            raise Exception('bte.sendMode() error')
        if not bte.onMode():
            raise Exception('bte.onMode() error')
        if not bte.onTemperatureToLight():
            raise Exception('bte.onTemperatureToLight() error')
        self._state_boil = True
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        self.log('Kettle Boil ON')

    # @iteration_decorator
    def onLight(self, rgb1='27FF00', rgb2='00FFEC', rgb3='000FFF'):
        self.log('>>>>>>>>>>>>>>>>>>>>>>>>OnLight', rgb1, rgb2, rgb3)
        bte = self.connect()
        if not bte.sendRGBLight('light', rgb1=rgb1, rgb2=rgb2, rgb3=rgb3):
            raise Exception('bte.sendRGBLight() error')
        if not bte.sendMode(mode='light'):
            raise Exception('bte.sendMode() error')
        if not bte.onMode():
            raise Exception('bte.onMode() error')
        self._light_state = True
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        self.log('Kettle Light ON')

    # @iteration_decorator
    def offLight(self, rgb1='eeff00', rgb2='ffbb00', rgb3='ff3c00'):
        self.log('>>>>>>>>>>>>>>>>>>>>>>>>OffLight', rgb1, rgb2, rgb3)
        bte = self.connect()
        if not bte.offMode():
            raise Exception('bte.offMode() error')
        self._light_state = False
        if self._hass:
            async_dispatcher_send(self._hass, 'ready4sky_update')
        self.log('Kettle Light OFF')

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