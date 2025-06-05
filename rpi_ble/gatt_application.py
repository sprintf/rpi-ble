
import logging
import time

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from gi.repository import GLib

from rpi_ble.constants import BLUEZ_SERVICE_NAME, GATT_MANAGER_IFACE, DBUS_OM_IFACE, DBUS_PROP_IFACE
from rpi_ble.gatt_advertisement import GattAdvertisement
from rpi_ble.utils import find_adapter

logger = logging.getLogger(__name__)

class LemonPiAdvertisement(GattAdvertisement):
    def __init__(self, bus, index):
        GattAdvertisement.__init__(self, bus, index, "peripheral")
        self.add_local_name("Lemon-Pi Device")
        self.include_tx_power = True

class GattApplication(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        from rpi_ble.device_status_gatt_service import DeviceStatusGattService
        from rpi_ble.gps_gatt_service import GpsGattService
        from rpi_ble.obd_gatt_service import ObdGattService
        self.gps_service = GpsGattService(bus, 0)
        self.obd_service = ObdGattService(bus, 1)
        self.add_service(self.gps_service)
        self.add_service(self.obd_service)
        self.add_service(DeviceStatusGattService(bus, 2))

        bus.add_signal_receiver(
            properties_changed,
            dbus_interface=DBUS_PROP_IFACE,
            signal_name="PropertiesChanged",
            path=None
        )

    def add_service(self, service):
        self.services.append(service)

    def register_application(self, bus):
        adapter = find_adapter(bus)
        if not adapter:
            print('GattManager1 interface not found')
            return

        service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

        service_manager.RegisterApplication(self.get_path(), {},
                                            reply_handler=register_app_cb,
                                            error_handler=register_app_error_cb)

    def get_mainloop(self):
        global mainloop
        mainloop = GLib.MainLoop()
        return mainloop

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_gps_service(self):
        return self.gps_service

    def get_obd_servics(self):
        return self.obd_service

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descriptors = chrc.get_descriptors()
                for desc in descriptors:
                    response[desc.get_path()] = desc.get_properties()
        return response

def register_app_cb():
    print('GATT application registered')

def register_app_error_cb(error):
    print(f'Failed to register application: {error}')
    mainloop.quit()

def properties_changed(interface, changed, invalidated, path):
    if interface == "org.bluez.Device1" and "Connected" in changed:
        if changed["Connected"]:
            print(f"{time.asctime()} - Client connected: {path}")
        else:
            print(f"{time.asctime()} - Something changed: {changed}")
    else:
        print(f"{time.asctime()} - Something happened: {interface} : {changed}")



