import sys
sys.path.insert(0, '../../')

from pyalertme import *
import unittest
from mock_serial import Serial

class TestDevice(unittest.TestCase):

    def setUp(self):
        self.serialObj = Serial()
        self.deviceObj = Device(self.serialObj)

    def tearDown(self):
        self.deviceObj.halt()

    def test_get_range(self):
        self.deviceObj.rssi = 0
        result = self.deviceObj.get_range()
        expected = {
            'cluster': '\x00\xf6',
            'data': '\t+\xfd\x00',
            'description': 'Range Info',
            'dest_endpoint': '\x02',
            'profile': '\xc2\x16',
            'src_endpoint': '\x00'
        }
        self.assertEqual(result, expected)

        self.deviceObj.rssi = 197
        result = self.deviceObj.get_range()
        expected = {
            'cluster': '\x00\xf6',
            'data': '\t+\xfd\xc5',
            'description': 'Range Info',
            'dest_endpoint': '\x02',
            'profile': '\xc2\x16',
            'src_endpoint': '\x00'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
