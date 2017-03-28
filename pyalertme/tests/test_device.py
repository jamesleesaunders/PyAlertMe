import sys
sys.path.insert(0, '../../')

from pyalertme import *
import unittest
from mock_serial import Serial

class TestDevice(unittest.TestCase):

    def setUp(self):
        self.serialObj = Serial()
        self.deviceObj = Device()
        self.deviceObj.start(self.serialObj)

    def tearDown(self):
        self.deviceObj.halt()

    def test_generate_range_message(self):
        self.deviceObj.rssi = 0
        result = self.deviceObj.generate_range_message()
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
        result = self.deviceObj.generate_range_message()
        expected = {
            'cluster': '\x00\xf6',
            'data': '\t+\xfd\xc5',
            'description': 'Range Info',
            'dest_endpoint': '\x02',
            'profile': '\xc2\x16',
            'src_endpoint': '\x00'
        }
        self.assertEqual(result, expected)

    def test_generate_type_message(self):
        result = self.deviceObj.generate_type_message()
        expected = {
            'cluster': '\x00\xf6',
            'data': '\tq\xfe\x01\x00\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\nGeneric Device\n2017-01-02',
            'description': 'Type Info',
            'dest_endpoint': '\x02',
            'profile': '\xc2\x16',
            'src_endpoint': '\x00'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
