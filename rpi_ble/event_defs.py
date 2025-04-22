from rpi_ble.events import Event

# the application is exiting
ExitApplicationEvent = Event("ExitApplication")

# OBD Events
OBDConnectedEvent = Event("OBD-Connected")
OBDDisconnectedEvent = Event("OBD-Disconnected")

# GPS Events
GPSConnectedEvent = Event("GPS-Connected")
GPSDisconnectedEvent = Event("GPS-Disconnected")


