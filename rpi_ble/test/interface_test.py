
import unittest
from unittest.mock import Mock

from rpi_ble.interfaces import ObdReceiver


class TestInterface(unittest.TestCase):

    def test_obd_receiver_receives_temp(self):
        mock = Mock()
        receiver = ObdReceiver(mock)
        receiver.set_temp_f(100)
        mock.set_temp_f.assert_called_once_with(100)

    def test_obd_receiver_receives_fuel(self):
        mock = Mock()
        receiver = ObdReceiver(mock)
        receiver.set_fuel_percent_remaining(50)
        mock.set_fuel_percent_remaining.assert_called_once_with(50)
