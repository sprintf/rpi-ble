
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
    def __init__(self, bus, test_mode=False):
        self.path = '/'
        self.services = []
        self.bus = bus
        self.connected_devices = set()
        self.advertisement = None
        self.is_advertising = False
        self.test_mode = test_mode

        dbus.service.Object.__init__(self, bus, self.path)
        from rpi_ble.device_status_gatt_service import DeviceStatusGattService
        from rpi_ble.gps_gatt_service import GpsGattService
        from rpi_ble.obd_gatt_service import ObdGattService
        self.gps_service = GpsGattService(bus, 0, test_mode=test_mode)
        self.obd_service = ObdGattService(bus, 1, test_mode=test_mode)
        self.add_service(self.gps_service)
        self.add_service(self.obd_service)
        self.add_service(DeviceStatusGattService(bus, 2))

        bus.add_signal_receiver(
            self._properties_changed,
            dbus_interface=DBUS_PROP_IFACE,
            signal_name="PropertiesChanged",
            path_keyword="path"
        )

    def add_service(self, service):
        self.services.append(service)

    def register_application(self, bus):
        adapter = find_adapter(bus)
        if not adapter:
            logger.error('GattManager1 interface not found')
            return

        self.adapter_path = adapter
        service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

        service_manager.RegisterApplication(self.get_path(), {},
                                            reply_handler=register_app_cb,
                                            error_handler=register_app_error_cb)

    def unregister_application(self):
        """Unregister GATT application from BlueZ"""
        if hasattr(self, 'adapter_path') and self.adapter_path:
            try:
                service_manager = dbus.Interface(
                    self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
                    GATT_MANAGER_IFACE)
                service_manager.UnregisterApplication(self.get_path())
                logger.info("GATT application unregistered")
            except Exception as e:
                logger.error(f"Failed to unregister GATT application: {e}")

    def cleanup(self):
        """Clean up all BlueZ and D-Bus resources"""
        logger.info("Starting cleanup...")
        
        # Stop advertising first
        self.stop_advertising()
        
        # Unregister GATT application
        self.unregister_application()
        
        # Remove signal receiver
        try:
            self.bus.remove_signal_receiver(
                self._properties_changed,
                dbus_interface=DBUS_PROP_IFACE,
                signal_name="PropertiesChanged"
            )
            logger.info("Signal receiver removed")
        except Exception as e:
            logger.error(f"Failed to remove signal receiver: {e}")
        
        logger.info("Cleanup completed")

    def get_mainloop(self):
        global mainloop
        mainloop = GLib.MainLoop()
        return mainloop

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_gps_service(self):
        return self.gps_service

    def get_obd_service(self):
        return self.obd_service

    def set_advertisement(self, advertisement):
        self.advertisement = advertisement

    def start_advertising(self):
        if self.advertisement and not self.is_advertising:
            try:
                self.advertisement.register(self.bus)
                self.is_advertising = True
                logger.info("BLE advertising started")
            except Exception as e:
                logger.error(f"Failed to start advertising: {e}")

    def stop_advertising(self):
        if self.advertisement and self.is_advertising:
            try:
                self.advertisement.unregister()
                self.is_advertising = False
                logger.info("BLE advertising stopped")
            except Exception as e:
                logger.error(f"Failed to stop advertising: {e}")

    def _properties_changed(self, interface, changed, invalidated, path):
        if interface == "org.bluez.Device1" and "Connected" in changed:
            if changed["Connected"]:
                self.connected_devices.add(path)
                if self.is_advertising:
                    self.stop_advertising()
                logger.info(f"BLE client connected: {path}")
            else:
                self.connected_devices.discard(path)
                logger.info(f"BLE client disconnected: {path}")
                
                # Re-advertise when client disconnects
                if len(self.connected_devices) == 0:
                    logger.info("Client disconnected, restarting advertising")
                    from gi.repository import GLib
                    GLib.timeout_add(1000, self._restart_advertising)
        elif interface == "org.bluez.Device1":
            logger.debug(f"Device property changed on {path}: {changed}")
        # this is far too noisy
        # else:
        #     logger.debug(f"Property changed: {interface} on {path}: {changed}")

    def _restart_advertising(self):
        if len(self.connected_devices) == 0:
            self.start_advertising()
        return False

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
    logger.info('GATT application registered')

def register_app_error_cb(error):
    logger.error(f'Failed to register application: {error}')
    mainloop.quit()




