from .bte import BTEConnect
from .exception import RedmondKettleException, RedmondKettleConnectException
import binascii
from textwrap import wrap
from datetime import datetime
import traceback
from time import sleep
import time
from bluepy.btle import BTLEException, BTLEDisconnectError


class RedmondKettleController:

    def __init__(self, addr, key, iface='hci0'):
        self._withDebug = False
        self._mac = addr
        self._key = key
        self._iface = iface
        self._conn = BTEConnect(self._mac, self._key, self._iface)
        # self._conn = Peripheral(deviceAddr=self._mac, addrType=btle.ADDR_TYPE_RANDOM)
        # self._conn.setDelegate(NotifyDelegate())
        self._iter = 0

    def disconnect(self):
        self._conn.Peripheral.disconnect()

    def withDebug(self):
        self._withDebug = True

    def log(self, *args):
        print(', '.join([str(a) for a in args]))

    def debug(self, *args):
        if self._withDebug:
            print(', '.join([str(a) for a in args]))

    def hexToDec(self, chr):
        return int(str(chr), 16)

    def decToHex(self, num):
        char = str(hex(int(num))[2:])
        if len(char) < 2:
            char = '0' + char
        return char

    def iterase(self): # counter
        self._iter+=1
        # print('iter', self._iter)
        if self._iter >= 64: self._iter = 0

    def auth(self):
        ''' Авторизуемся в чайнике '''
        self.debug('auth:')
        try:
            # подписываемся на обмен сообщениями
            str2b = binascii.a2b_hex(bytes('0100', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(0x000c, str2b, withResponse=True)
            # вторизуенмся
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + 'ff' + self._key + 'aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(5.0)
            self.iterase()
            self.debug('notify', self._conn.notify)


            s = binascii.b2a_hex(self._conn.notify[0:]).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)

            return True if str(arr[3]) == '01' else False
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            # print(traceback.format_exc())
            raise RedmondKettleConnectException(e)
        except BaseException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
        return False

    def on(self):
        ''' Включаем чайник '''
        self.debug('on:')
        try:
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '03aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.debug('notify', self._conn.notify)
            self.iterase()
            return True
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
        except BaseException as e:
            self.log('Error:', e)
        return False

    def off(self):
        ''' Выключаем чайник '''
        self.debug('off:')
        try:
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '04aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.debug('notify', self._conn.notify)
            self.iterase()
            return True
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
        except BaseException as e:
            self.log('Error:', e)
        return False

    def sync(self, timezone = 3):
        ''' Синхронизируемся с чайником '''
        self.debug('sync:')
        tmz_hex_list = wrap(str(self.decToHex(timezone*60*60)), 2)
        tmz_str = ''
        for i in reversed(tmz_hex_list):
            tmz_str+=i
        timeNow_list = wrap(str(self.decToHex(time.mktime(datetime.now().timetuple()))), 2)
        timeNow_str = ''
        for i in reversed(timeNow_list):
            timeNow_str+=i
        str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '6e' + timeNow_str + tmz_str + '0000aa', 'utf-8'))
        try:
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            return True
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            print(traceback.format_exc())
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        except BaseException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e

        return False

    def stat(self):
        ''' Отображение текущей информации о чайнике '''
        self.debug('stat:')
        try:
            # self._conn.setDelegate(NotifyStatusDelegate())
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '4700aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)

            s = binascii.b2a_hex(self._conn.notify).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)
            energy_kwh = self.hexToDec(str(arr[11] + arr[10] + arr[9]))
            time = round(energy_kwh / 2200, 1)

            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '5000aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)
            s = binascii.b2a_hex(self._conn.notify).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)
            count = self.hexToDec(str(arr[7] + arr[6]))

            self.debug('energy_kwh', energy_kwh, 'time', time, 'count', count)

            return {
                'energy_kwh': energy_kwh,
                'time': time,
                'count': count
            }
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
        except BaseException as e:
            self.log('Error:', e)
        return False

    def mode(self):
        ''' Получаем текущий режим работы чайника '''
        self.debug('mode:')
        try:
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '06aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)

            s = binascii.b2a_hex(self._conn.notify[0:]).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)
            status = str(arr[11]) if len(arr) > 11 else str(arr[3])
            current_temperature = self.hexToDec(str(arr[8])) if len(arr) > 11 else str(0)
            temperature = self.hexToDec(str(arr[5])) if len(arr) > 11 else str(0)
            mode = str(arr[3])
            time = str(arr[16]) if len(arr) > 11 else str(0)

            self.debug('status', status, 'temperature', temperature, 'current_temperature', current_temperature, 'mode', mode, 'time', time)

            mode_statuses = {
                '00': 'boil',
                '01': 'heat',
                '03': 'light',
            }
            statuses = {
                '00': 'off',
                '02': 'on',
            }

            return {
                # возвращает статус чайника
                'status': statuses[status] if status in statuses else status,
                # текущая температура воды (2a=42 по Цельсию)
                'current_temperature': current_temperature,
                # температура, до которой нужно нагревать в режиме работы «нагрев», в режиме кипячения равен 00.
                'temperature': temperature if temperature > 0 else 100,
                # Режим работы
                # 00 - boil 01 - heat to temp 03 - backlight (boil by default)    temp - in HEX
                'mode': mode_statuses[mode] if mode in mode_statuses else mode,
                # это продолжительность работы чайника после достижения нужной температуры, по умолчанию равна 80 в hex
                # (видимо, это какие то относительные единицы, точно не секунды)
                'time': time
            }
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            print(traceback.format_exc())
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        except BaseException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        return False

    def sendMode(self, mode='boil', temperature='40', howMuchBoil='80'):
        ''' Устанавливаем режим работы
        mode: boil — кипячение, heat — нагрев до температуры, light — ночник
        temp — hex температура, до которой нужно нагревать в режиме работы «нагрев», в режиме кипячения он равен 00
        howMuchBoil — это продолжительность работы чайника после достижения нужной температуры, по умолчанию равна 80 в hex
        '''
        self.debug('sendMode:')
        try:
            if mode == 'heat' and (temperature < 40 or temperature > 95):
                raise RedmondKettleException('Temp must be > 40 and < 95')

            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '06aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)

            s = binascii.b2a_hex(self._conn.notify[0:]).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]

            modeBitesDict = {
                'boil': '00',
                'heat': '01',
                'light': '03'
            }

            tempBite = self.decToHex(temperature)
            if (mode == 'boil'):
                tempBite = '00'
            if (mode == 'light'):
                tempBite = '00'

            howMuchBoilBite = self.decToHex(howMuchBoil)

            arr[1] = self.decToHex(self._iter)
            arr[2] = '05'
            arr[3] = modeBitesDict.get(mode, '00') # программа
            arr[4] = '00' # sprog под программа программа
            '''
status, 00, temperature, 0, current_temperature, 58, mode, 03, time, 80, 00
sendRGBLight:
notify, b'U\x112\x00\xaa'
sendMode:
notify, b'U\x112\x00\xaa'
Error:, list assignment index out of range
Traceback (most recent call last):
  File "/home/suver/project/homekit/core/config/custom_components/r4sky/lib/kettle_controller.py", line 273, in sendMode
    arr[5] = tempBite
IndexError: list assignment index out of range

bte.sendMode() error
Traceback (most recent call last):
  File "/home/suver/project/homekit/core/config/custom_components/r4sky/lib/tool.py", line 16, in wrapper
    result = method(*args, **kwargs)
  File "/home/suver/project/homekit/core/config/custom_components/r4sky/lib/kettle.py", line 124, in onLight
    raise Exception('bte.sendMode() error')
Exception: bte.sendMode() error

            '''
            arr[5] = tempBite
            # arr[6] = '00' # hours
            # arr[7] = '00' # minutes
            # arr[8] = '00' # dhours
            # arr[9] = '00' # dminutes
            # arr[10] = howMuchBoilBite # heat

            self.debug('sendMode', ''.join(arr))
            str2b = binascii.a2b_hex(bytes(''.join(arr), 'utf-8'))
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '05' + modeBitesDict.get(mode, '00') + '00' + tempBite +
                                           '00000000000000000000' + howMuchBoilBite + '0000aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)

            s = binascii.b2a_hex(self._conn.notify[0:]).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)
            status = str(arr[3])

            self.debug('status', status)

            statuses = {
                '00': 'fail',
                '01': 'ok',
            }

            return {
                # возвращает статус чайника
                'status': statuses.get(status, status)
            }
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            print(traceback.format_exc())
            raise RedmondKettleConnectException(e)
        except RedmondKettleException as e:
            print(traceback.format_exc())
            raise e
        except BTLEException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        except BaseException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        return False

    def onMode(self):
        ''' Запустить текущий режим работы
        Перед тем как запустить следует указать режим работы sendMode. Что бы прочесть режим работы используйте mode
        '''
        self.debug('onMode:')
        try:
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '03aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)

            s = binascii.b2a_hex(self._conn.notify[0:]).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)
            status = str(arr[3])

            self.debug('status', status)

            statuses = {
                '00': 'fail',
                '01': 'ok',
            }

            return {
                # возвращает статус чайника
                'status': statuses[status] if status in statuses else status,
            }
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            print(traceback.format_exc())
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        except BaseException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        return False

    def offMode(self):
        ''' Запустить текущий режим работы
        Перед тем как запустить следует указать режим работы sendMode. Что бы прочесть режим работы используйте mode
        '''
        self.debug('offMode:')
        try:
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '04aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)

            s = binascii.b2a_hex(self._conn.notify[0:]).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)
            status = str(arr[3])

            self.debug('status', status)

            statuses = {
                '00': 'fail',
                '01': 'ok',
            }

            return {
                # возвращает статус чайника
                'status': statuses[status] if status in statuses else status,
            }
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            print(traceback.format_exc())
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        except BaseException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        return False

    def onTemperatureToLight(self):
        ''' Отображение текущей температуры цветом в простое ON '''
        self.debug('onTemperatureToLight:')
        try:
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '37c8c801aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)
            return True
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
        except BaseException as e:
            self.log('Error:', e)
        return False

    def offTemperatureToLight(self):
        ''' Отображение текущей температуры цветом в простое OFF '''
        self.debug('offTemperatureToLight:')
        try:
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '37c8c800aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)
            return True
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
        except BaseException as e:
            self.log('Error:', e)
        return False

    def sendRGBLight(self, mode='light', rgb1='0000ff', rgb2='00ff00', rgb3='0000ff'):
        ''' Устанавливаем цвет подсветки
        boil, если мы настраиваем режим отображения текущей температуры или
        light, если мы настраиваем режим ночника
        '''
        self.debug('sendRGBLight:')
        try:
            rand = '5e' # яркость e5, cc, 7f
            if mode == "00":
                scaleLight = ['28', '46', '64']
            else:
                scaleLight = ['00', '32', '64']
            boilOrLightDict = {
                'boil': '00',
                'light': '01'
            }
            boilOrLightBit = boilOrLightDict.get(mode, 00)
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '32' + boilOrLightBit +
                                           scaleLight[0] + rand + rgb1 +
                                           scaleLight[1] + rand + rgb2 +
                                           scaleLight[2] + rand + rgb3 + 'aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)
            return True
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            print(traceback.format_exc())
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        except BaseException as e:
            self.log('Error:', e)
            print(traceback.format_exc())
            raise e
        return False

    def RGBLight(self, mode='boil'):
        ''' Прочесть цвет подсветки
        boil, если мы настраиваем режим отображения текущей температуры или
        light, если мы настраиваем режим ночника
        '''
        self.debug('RGBLight:')
        try:
            boilOrLightDict = {
                'boil': '00',
                'light': '01'
            }
            boilOrLightBit = boilOrLightDict[mode] if mode in boilOrLightDict else mode
            str2b = binascii.a2b_hex(bytes('55' + self.decToHex(self._iter) + '33' + boilOrLightBit + 'aa', 'utf-8'))
            self._conn.Peripheral.writeCharacteristic(14, str2b, withResponse=True)
            self._conn.Peripheral.waitForNotifications(2.0)
            self.iterase()
            self.debug('notify', self._conn.notify)
            s = binascii.b2a_hex(self._conn.notify[0:]).decode("utf-8")
            arr = [s[x:x + 2] for x in range(0, len(s), 2)]
            self.debug(arr)

            temperatureStart = self.hexToDec(str(arr[4]))
            randStart = str(arr[5])
            colorStart = str(arr[6]) + str(arr[7]) + str(arr[8])
            temperatureMid = self.hexToDec(str(arr[9]))
            randMid = str(arr[10])
            colorMidt = str(arr[11]) + str(arr[12]) + str(arr[13])
            temperatureHard = self.hexToDec(str(arr[14]))
            randHard= str(arr[15])
            colorHard = str(arr[16]) + str(arr[17]) + str(arr[18])

            return {
                'start': {
                    'temperature': temperatureStart, # температура
                    'rand': randStart, # яркость
                    'color': colorStart, # цвет
                },
                'mid': {
                    'temperature': temperatureMid,
                    'rand': randMid,
                    'color': colorMidt,
                },
                'hard': {
                    'temperature': temperatureHard,
                    'rand': randHard,
                    'color': colorHard,
                },
            }
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
        except BaseException as e:
            self.log('Error:', e)
        return False

    def info(self):
        ''' Отображение текущей информации о чайнике '''
        self.debug('info:')
        try:
            characteristics = self._conn.Peripheral.getCharacteristics()
            info = {}
            for i in characteristics:
                info[i.uuid.getCommonName()] = str(i.uuid)
            descriptors = self._conn.Peripheral.getDescriptors()
            for i in descriptors:
                info[i.uuid.getCommonName()] = str(i.uuid)
            self.iterase()

            self.debug('info', info)

            return info
        except BTLEDisconnectError as e:
            self.log('Error BTLEDisconnectError:', e)
            raise RedmondKettleConnectException(e)
        except BTLEException as e:
            self.log('Error:', e)
        except BaseException as e:
            self.log('Error:', e)
        return False