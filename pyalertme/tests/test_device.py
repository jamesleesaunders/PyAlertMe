import sys
sys.path.insert(0, '../../')

from pyalertme import *
import unittest
from mock_serial import Serial

class TestDevice(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = Device()
        self.device_obj.start(self.ser)

    def tearDown(self):
        self.device_obj.halt()

    def test_generate_range_update(self):
        self.device_obj.rssi = 0
        result = self.device_obj.generate_range_update()
        expected = {
            'cluster': b'\x00\xf6',
            'data': b'\t+\xfd\x00',
            'description': 'Range Info',
            'dest_endpoint': b'\x02',
            'profile': b'\xc2\x16',
            'src_endpoint': b'\x00'
        }
        self.assertEqual(result, expected)

        self.device_obj.rssi = 197
        result = self.device_obj.generate_range_update()
        expected = {
            'cluster': b'\x00\xf6',
            'data': b'\t+\xfd\xc5',
            'description': 'Range Info',
            'dest_endpoint': b'\x02',
            'profile': b'\xc2\x16',
            'src_endpoint': b'\x00'
        }
        self.assertEqual(result, expected)

    def test_generate_type_update(self):
        result = self.device_obj.generate_type_update()
        expected = {
            'description': 'Type Info',
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xf6',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\tq\xfe\x01\x00\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bPyAlertMe\nGeneric Device\n2016-09-18'
        }
        self.assertEqual(result, expected)

    def test_generate_match_descriptor_request(self):
        result = self.device_obj.generate_match_descriptor_request()
        expected = {
            'description': 'Match Descriptor Request',
            'profile': b'\x00\x00',
            'cluster': b'\x00\x06',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'data': b'\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
