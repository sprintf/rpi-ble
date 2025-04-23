

import unittest
from json import JSONDecoder
from unittest.mock import Mock

import sys

sys.modules['gi.repository'] = Mock()
sys.modules['gpiozero'] = Mock()

from rpi_ble.gatt_application import GattApplication

class TestApplication(unittest.TestCase):

    def test_construction(self) :
        bus = Mock()
        app = GattApplication(bus)
        props = app.GetManagedObjects()
        self.assertEqual(12, len(props))
