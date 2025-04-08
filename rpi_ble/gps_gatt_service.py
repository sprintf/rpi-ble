import dbus

from rpi_ble.interfaces import GpsReceiver
from service import GattService, GattCharacteristic, GATT_CHRC_IFACE


class GpsGattService(GattService, GpsReceiver):
    """
    Send gps data on a frequent basis
    """
    GPS_UUID = '00001101-0000-1000-8000-00805F9B34FB'

    def __init__(self, bus, index):
        GattService.__init__(self, bus, index, self.GPS_UUID, True)
        self.gps_characteristic = GpsChrc(bus, 0, self)
        self.add_characteristic(self.gps_characteristic)
        self.energy_expended = 0

    def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int) -> None:
        self.gps_characteristic.set_gps_position()

class GpsChrc(GattCharacteristic, GpsReceiver):
    # this is a general sensor
    # todo ... need more in here
    GPS_DATA_UUID = '0x0541'

    def __init__(self, bus, index, service):
        GattCharacteristic.__init__(
            self, bus, index,
            self.GPS_DATA_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.hr_ee_count = 0

    def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int):
        value = []
        ## length = 64 + 64 + 64 + 32 ... about 220 bytes
        # if we need to we can unpack these into int and fraction .. use 1 byte for int and a 32 or a 16 for the fraction
        value.append(dbus.Double(lat))
        value.append(dbus.Double(long))
        value.append(dbus.UInt16(heading * 10))
        # todo : can an int timestamp be set into an array like this?
        value.append(dbus.UInt32(int(tstamp)))
        # todo : can the float part get there with the correct precision
        value.append(dbus.UInt32(tstamp - int(tstamp)))
        value.append(dbus.UInt16(speed * 10))

        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

