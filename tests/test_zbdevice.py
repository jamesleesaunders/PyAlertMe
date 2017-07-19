import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestZBDevice(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = ZBDevice(self.ser)

    def tearDown(self):
        self.device_obj.halt()

    def test_message_range_update(self):
        self.device_obj.rssi = 0
        result = self.device_obj.message_range_update()
        expected = {
            'cluster': b'\x00\xf6',
            'data': b'\t+\xfd\x00\x00',
            'dest_endpoint': b'\x02',
            'profile': b'\xc2\x16',
            'src_endpoint': b'\x02'
        }
        self.assertEqual(result, expected)

        self.device_obj.rssi = 197
        result = self.device_obj.message_range_update()
        expected = {
            'cluster': b'\x00\xf6',
            'data': b'\t+\xfd\xc5\x00',
            'dest_endpoint': b'\x02',
            'profile': b'\xc2\x16',
            'src_endpoint': b'\x02'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
