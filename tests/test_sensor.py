import sys
sys.path.insert(0, '../')

from classes import *
import unittest
from mock_serial import Serial

class TestSensor(unittest.TestCase):

    def setUp(self):
        serialObj = Serial()
        self.deviceObj = Sensor(serialObj)

    def tearDown(self):
        self.deviceObj.halt()

    def test_get_type(self):
        result = self.deviceObj.get_type()
        expected = {
            'description': 'Type Info',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': b'\xc2\x16',
            'data': '\tq\xfe+\xe8\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\nButton Device\n2010-11-15'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)