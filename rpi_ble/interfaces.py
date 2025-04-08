


class TemperatureReceiver:

    def set_temp_f(self, temperature: int) -> None:
        pass


class FuelLevelReceiver:

    def set_fuel_percent_remaining(self, percent: int) -> None:
        pass


class GpsReceiver:

    def set_gps_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int) -> None:
        pass


class ObdReceiver(TemperatureReceiver, FuelLevelReceiver):

    def __init__(self, delegate):
        self.delegate = delegate

    def set_temp_f(self, temperature: int) -> None:
        self.delegate.set_temp_f(temperature)

    def set_fuel_percent_remaining(self, percent: int) -> None:
        self.delegate.set_fuel_percent_remaining(percent)