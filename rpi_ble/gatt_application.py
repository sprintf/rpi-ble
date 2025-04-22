
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from gi.repository import GLib

from main import mainloop
from rpi_ble.constants import BLUEZ_SERVICE_NAME, GATT_MANAGER_IFACE, DBUS_OM_IFACE


class GattApplication(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        from rpi_ble.temp_gatt_service import ThermometerGattService
        self.thermometerService = ThermometerGattService(bus, 0)
        self.add_service(self.thermometerService)
        from rpi_ble.device_status_gatt_service import DeviceStatusGattService
        self.add_service(DeviceStatusGattService(bus, 1))
        #from rpi_ble.gps_gatt_service import GpsGattService
        from rpi_ble.obd_gatt_service import ObdGattService
        #self.gps_service = GpsGattService(bus, 0)
        # self.obd_service = ObdGattService(bus, 1)
        #self.services.append(self.gps_service)
        # self.services.append(self.obd_service)

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

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'), DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            return o

    return None
