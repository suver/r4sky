from bluepy.btle import Peripheral, Scanner, DefaultDelegate, ADDR_TYPE_RANDOM, BTLEException, BTLEDisconnectError
from queue import Queue
from threading import Thread
import binascii
import logging
import traceback
import time
_LOGGER = logging.getLogger(__name__)

# create a delegate class to receive the BLE broadcast packets
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    # when this python script discovers a BLE broadcast packet, print a message with the device's MAC address
    def handleDiscovery(self, dev, isNewDev, isNewData):
        pass
        # if isNewDev:
        #     print("Discovered device", dev.addr)
        # elif isNewData:
        #     print("Received new data from", dev.addr)


class BTEConnect(DefaultDelegate):

    def __init__(self, addr, key, iface):
        DefaultDelegate.__init__(self)

        # ... initialise here
        self._mac = addr
        self._iface = iface
        self._peripheral = None
        # self.Peripheral = None
        # self.Peripheral = Peripheral(deviceAddr=self._mac, addrType=ADDR_TYPE_RANDOM, iface=self._iface)
        # self.Peripheral.setDelegate(self)
        self._tx_queue = Queue()
        self._nx_queue = Queue()
        self._key = key
        self._iter = 0
        self._use_backlight = True
        self.notify = None
        self.handle = None

        # start the bluepy IO thread
        self._bluepy_thread = Thread(target=self._bluepy_handler)
        self._bluepy_thread.name = "bluepy_handler"
        self._bluepy_thread.daemon = False
        self._bluepy_thread.start()

    def log(self, *args, msg='', level=1, error=False, log=False, debug=False):
        if error:
            _LOGGER.error(' '.join([str(a) for a in args]) + "\n" + traceback.format_exc())
        if log:
            _LOGGER.log(level, msg, args, traceback=traceback.format_exc())
        if debug:
            _LOGGER.debug(level, msg, args, traceback=traceback.format_exc())
        else:
            _LOGGER.info(' '.join([str(a) for a in args]))

    # def __enter__(self):
    #     try:
    #         self.__exit__()
    #         self.Peripheral = Peripheral(deviceAddr=self._mac, addrType=btle.ADDR_TYPE_RANDOM)
    #         self.Peripheral.setDelegate(self)
    #     except:
    #         return self.__enter__()
    #     return self

    # def __exit__(self):
    #     try:
    #         self.Peripheral.disconnect()
    #     except:
    #         pass
    #     self._conn = None

    @staticmethod
    def scan():
        ''' Скаинруем устройства и находим чайник '''
        # create a scanner object that sends BLE broadcast packets to the ScanDelegate
        scanner = Scanner().withDelegate(ScanDelegate())

        # create a list of unique devices that the scanner discovered during a 10-second scan
        devices = scanner.scan(10.0)

        # for each device  in the list of devices
        for dev in devices:
            # print  the device's MAC address, its address type,
            # and Received Signal Strength Indication that shows how strong the signal was when the script received the broadcast.
            print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))

            # For each of the device's advertising data items, print a description of the data type and value of the data itself
            # getScanData returns a list of tupples: adtype, desc, value
            # where AD Type means “advertising data type,” as defined by Bluetooth convention:
            # https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile
            # desc is a human-readable description of the data type and value is the data itself
            for (adtype, desc, value) in dev.getScanData():
                print("  %s = %s" % (desc, value))

    @property
    def mac(self):
        return self._mac

    @property
    def key(self):
        return self._key

    def handleNotification(self, cHandle, data):
        # print(cHandle, data)
        self.log('Bluetooth handleNotification', cHandle, data, binascii.b2a_hex(data[0:]).decode("utf-8"), debug=True)
        self.handle = cHandle
        self.notify = data
        self._nx_queue.put_nowait(binascii.b2a_hex(data[0:]).decode("utf-8"))

    def hexToDec(self, chr):
        return int(str(chr), 16)

    def _bluepy_handler(self):
        """This is the bluepy IO thread
        :return:
        """
        self._start()

    def _start(self):
        try:
            # Connect to the peripheral
            self._peripheral = Peripheral(deviceAddr=self._mac, addrType=ADDR_TYPE_RANDOM, iface=self._iface)
            # Set the notification delegate
            self._peripheral.setDelegate(self)

            # get the list of services
            services = self._peripheral.getServices()
            write_handle = None
            subscribe_handle = None

            # magic stuff for the Nordic UART GATT service
            uart_uuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
            uart_write_uuid_prefix = "6e400002"

            # this is general magic GATT stuff
            # notify handles will have a UUID that begins with this
            uart_notify_uuid_prefix = "00002902"
            # these are the byte values that we need to write to subscribe/unsubscribe for notifications
            subscribe_bytes = binascii.a2b_hex(bytes('0100', 'utf-8'))
            unsubscribe_bytes = binascii.a2b_hex(bytes('0000', 'utf-8'))

            # dump out some info for the services that we found
            for service in services:
                self.log("Found service: " + str(service) + ' uuid:' + str(service.uuid).lower(), debug=True)
                if str(service.uuid).lower() == uart_uuid:
                    # this is the Nordic UART service that we're looking for
                    chars = service.getCharacteristics()
                    for char in chars:
                        self.log(
                            "  char: " + str(char) + ", handle: " + str(char.handle) + ", props: " + str(char.properties),
                            debug=True)
                    descs = service.getDescriptors()
                    # this is the important part-
                    # find the handles that we will write to and subscribe for notifications
                    for desc in descs:
                        self.log("  desc: " + str(desc), debug=True)
                        str_uuid = str(desc.uuid).lower()
                        if str_uuid.startswith(uart_write_uuid_prefix):
                            write_handle = desc.handle
                            self.log("*** Found write handle: " + str(write_handle), debug=True)
                        elif str_uuid.startswith(uart_notify_uuid_prefix):
                            subscribe_handle = desc.handle
                            self.log("*** Found subscribe handle: " + str(subscribe_handle), debug=True)

            if write_handle is not None and subscribe_handle is not None:
                # we found the handles that we need

                # this call performs the subscribe for notifications
                response = self._peripheral.writeCharacteristic(subscribe_handle, subscribe_bytes, withResponse=True)

                # now that we're subscribed for notifications, waiting for TX/RX...
                while True:
                    while not self._tx_queue.empty():
                        msg = self._tx_queue.get_nowait()
                        msg_bytes = binascii.a2b_hex(bytes(msg, encoding="utf-8"))
                        self._peripheral.writeCharacteristic(14, msg_bytes)

                        self._peripheral.waitForNotifications(1.0)

        except BTLEDisconnectError as e:
            self._nx_queue.put_nowait('BTLEDisconnectError %s' % e)
            raise e
        except BTLEException as e:
            self._nx_queue.put_nowait('BTLEException %s' % e)
            raise e
        except Exception as e:
            self._nx_queue.put_nowait('Exception %s' % e)
            raise e

    def send(self, message):
        """Call this function to send a BLE message over the UART service
        :param message: Message to send
        :return:
        """

        # put the message in the TX queue
        self.log('Send message to ', self.mac, message)
        self._tx_queue.put_nowait(message)
        msg = self._nx_queue.get()
        if msg.split()[0] == 'BTLEDisconnectError':
            self.log('Request BTLEDisconnectError from', self.mac, msg)
            raise BTLEDisconnectError(msg)
        if msg.split()[0] == 'BTLEException':
            self.log('Request BTLEException from', self.mac , msg)
            raise BTLEException(msg)
        self.log('Request from', self.mac , msg)
        return msg