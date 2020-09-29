from homeassistant import config_entries
from homeassistant import data_entry_flow
from bluepy.btle import Scanner, DefaultDelegate
from subprocess import check_output
import traceback
import random
import string
from re import search
import voluptuous as vol
from homeassistant.core import callback
from .lib import RedmondKettle
from .const import (
    DOMAIN,
    DEFAULT_INTERFACE,
    DEFAULT_SCAN_INTERVAL,
    CONF_BLUETOOTH_FACE_NAME,
    CONF_BLUETOOTH_FACE_INDEX,
    CONF_UNIQUE_ID,
    CONF_MODEL,
    CONF_MANUFACTURER,
    CONF_NAME,
    CONF_TEMPERATURE_LIGHT,
    STRING_HEX_SYMBOLS
)

from homeassistant.const import (
    CONF_DEVICE,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL
)

# create a delegate class to receive the BLE broadcast packets
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    # when this python script discovers a BLE broadcast packet, print a message with the device's MAC address
    def handleDiscovery(self, dev, isNewDev, isNewData):
        # if isNewDev:
        #     print("Discovered device", dev.addr)
        # elif isNewData:
        #     print("Received new data from", dev.addr)
        pass


@config_entries.HANDLERS.register(DOMAIN)
class R4skyConfigFlow(data_entry_flow.FlowHandler):
    """Example config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    # (this is not implemented yet)
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    _hci_devices = {'hci0': 'hci0'}
    _ble_devices = {}
    _info = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return R4skyOptionsFlowHandler(config_entry)

    def get_devices(self):
        '''Scan bluetooth devices'''
        try:
            scanner = Scanner(iface=self._info[CONF_BLUETOOTH_FACE_INDEX]).withDelegate(ScanDelegate())
            devices = scanner.scan(3.0)
            self._ble_devices = {str(device.addr):str(device.getValueText(9))+','+str(device.addr) for device in scanner.scan(3.0)}
        except Exception as e:
            print('Error:', e)
            print(traceback.format_exc())

    async def iface_form(self, user_input={}, errors={}):
        '''Get bluetooth iface form'''
        if user_input is None:
            user_input = {}
        device = user_input.get(CONF_BLUETOOTH_FACE_NAME, DEFAULT_INTERFACE)
        data_schema = {
            vol.Required(CONF_BLUETOOTH_FACE_NAME, default=device): vol.In(self._hci_devices),
        }
        if self.show_advanced_options:
            data_schema["allow_groups"]: bool
        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=errors)

    async def configure_form(self, user_input={}, errors={}):
        '''configure devices'''
        if user_input is None:
            user_input = {}
        # device = user_input.get(CONF_DEVICE, DEFAULT_INTERFACE)
        mac = user_input.get(CONF_MAC)
        # password = user_input.get(CONF_PASSWORD)
        scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        data_schema = {
            # vol.Required(CONF_DEVICE, default=device): vol.In(self._hci_devices),
            vol.Required(CONF_MAC, default=mac): vol.In(self._ble_devices),
            # vol.Required(CONF_PASSWORD, default=password): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=scan_interval): int,
        }
        return self.async_show_form(step_id="configure", data_schema=vol.Schema(data_schema), errors=errors)

    async def paring_form(self, user_input={}, errors={}):
        '''Paring form'''
        mac = user_input.get(CONF_MAC)
        identifier = f'{DOMAIN}[{mac}]'
        # await self.async_set_unique_id(identifier)
        return self.async_show_form(step_id="paring", errors=errors)

    async def paring_proccess(self, user_input={}, errors={}):
        '''Paring form'''
        # await self.async_set_unique_id(identifier)
        instance = RedmondKettle(
            mac=self._info.get(CONF_MAC),
            password=self._info.get(CONF_PASSWORD),
            iface=self._info.get(CONF_BLUETOOTH_FACE_INDEX),
        )
        try:
            instance.paring()
            return self.async_create_entry(
                title=f"{self._info.get(CONF_NAME)}\n{self._info.get(CONF_MAC)}", data=self._info
            )
        except Exception as e:
            return {'base': 'wrong_pairing'}

    async def async_step_user(self, user_input=None):
        # Specify items in the order they are to be displayed in the UI
        print('user_input', user_input)
        try:
            byte_output = check_output(['hciconfig'])
            string_output = byte_output.decode('utf-8')
            lines = string_output.splitlines()
            hci_devices = [line.split(':')[0] for line in lines if 'hci' in line]
            self._hci_devices = {line: line for line in hci_devices}
            self._info[CONF_BLUETOOTH_FACE_NAME] = hci_devices[0]
            self._info[CONF_BLUETOOTH_FACE_INDEX] = 0
        except:
            self._hci_devices = {'hci0': 'hci0'}
        if user_input:
            if user_input.get(CONF_BLUETOOTH_FACE_NAME, False) and not user_input.get(CONF_MAC, False):
                match_result = search(r'hci([\d]+)', user_input.get(CONF_BLUETOOTH_FACE_NAME, DEFAULT_INTERFACE))
                if match_result:
                    self._info[CONF_BLUETOOTH_FACE_NAME] = user_input.get(CONF_BLUETOOTH_FACE_NAME, DEFAULT_INTERFACE)
                    self._info[CONF_BLUETOOTH_FACE_INDEX] = int(match_result.group(1))
                return await self.async_step_configure(user_input=user_input)
        return await self.iface_form(user_input=user_input)

    async def async_step_configure(self, user_input=None):
        # Specify items in the order they are to be displayed in the UI
        if user_input.get(CONF_MAC, False):
            password = user_input.get(CONF_PASSWORD, ''.join(random.choice(STRING_HEX_SYMBOLS) for i in range(16)))
            scan_interval = user_input.get(CONF_SCAN_INTERVAL)
            mac = user_input.get(CONF_MAC)
            # Validate user input
            if len(password) != 16:
                return {'base': 'wrong_password'}
            if scan_interval < 10 or scan_interval > 300:
                return {'base': 'wrong_scan_interval'}
            identifier = f'{DOMAIN}[{mac}]'
            # if identifier in self._async_current_ids():
            #     return self.async_abort(reason='already_configured')
            # Store info to use in next step
            self._info[CONF_MANUFACTURER] = 'Radmond'
            self._info[CONF_UNIQUE_ID] = identifier
            self.unique_id = identifier
            self._info[CONF_MAC] = mac
            self._info[CONF_PASSWORD] = password
            self._info[CONF_SCAN_INTERVAL] = scan_interval
            try:
                name = self._ble_devices.get(mac).split(',')[0]
            except:
                pass
            self._info[CONF_MODEL] = name if name else ''
            self._info[CONF_NAME] = f"{self._info[CONF_MANUFACTURER]} {self._info[CONF_MODEL]}"
            # Return the form of the next step
            return await self.async_step_paring_info(user_input=user_input)
        else:
            self.get_devices()
        return await self.configure_form(user_input=user_input)

    async def async_step_paring_info(self, user_input=None):
        # Specify items in the order they are to be displayed in the UI
        return await self.paring_form(user_input=user_input)

    async def async_step_paring(self, user_input=None):
        # Specify items in the order they are to be displayed in the UI
        return await self.paring_proccess(user_input=user_input)



class R4skyOptionsFlowHandler(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self._info = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            match_result = search(r'hci([\d]+)', user_input.get(CONF_BLUETOOTH_FACE_NAME))
            if match_result:
                self._info[CONF_BLUETOOTH_FACE_NAME] = user_input.get(CONF_BLUETOOTH_FACE_NAME)
                self._info[CONF_BLUETOOTH_FACE_INDEX] = int(match_result.group(1))
            self._info[CONF_TEMPERATURE_LIGHT] = user_input.get(CONF_TEMPERATURE_LIGHT)
            print('self._info', self._info, type(self._info))
            return self.async_create_entry(
                title=f"{self._info.get(CONF_NAME)}\n{self._info.get(CONF_MAC)}", data=self._info
            )
        if user_input is None:
            user_input = {}

        try:
            byte_output = check_output(['hciconfig'])
            string_output = byte_output.decode('utf-8')
            lines = string_output.splitlines()
            hci_devices = [line.split(':')[0] for line in lines if 'hci' in line]
            self._hci_devices = {line: line for line in hci_devices}
        except:
            self._hci_devices = {'hci0': 'hci0'}

        iface_name = self._info.get(CONF_BLUETOOTH_FACE_NAME)
        temperatureLight = self._info.get(CONF_TEMPERATURE_LIGHT, True)
        device = user_input.get(CONF_BLUETOOTH_FACE_NAME, iface_name)
        data_schema = {
            vol.Required(CONF_BLUETOOTH_FACE_NAME, default=device): vol.In(self._hci_devices),
            vol.Optional(CONF_TEMPERATURE_LIGHT, default=temperatureLight): bool,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(data_schema),
        )