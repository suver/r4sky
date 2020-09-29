from bluepy.btle import Peripheral, Scanner, DefaultDelegate, ADDR_TYPE_RANDOM

# create a delegate class to receive the BLE broadcast packets
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    # when this python script discovers a BLE broadcast packet, print a message with the device's MAC address
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Received new data from", dev.addr)


class BTEConnect(DefaultDelegate):

    def __init__(self, addr, key, iface):
        DefaultDelegate.__init__(self)
        # ... initialise here
        self._mac = addr
        self._iface = iface
        self.Peripheral = None
        self.Peripheral = Peripheral(deviceAddr=self._mac, addrType=ADDR_TYPE_RANDOM, iface=self._iface)
        self.Peripheral.setDelegate(self)
        self._key = key
        self._iter = 0
        self._use_backlight = True
        self.notify = None
        self.handle = None

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
        print(cHandle, data)
        self.handle = cHandle
        self.notify = data

    def hexToDec(self, chr):
        return int(str(chr), 16)