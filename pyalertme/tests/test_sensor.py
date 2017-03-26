import sys
sys.path.insert(0, '../../')

from pyalertme import *
import unittest
from mock_serial import Serial

class TestSensor(unittest.TestCase):

    def setUp(self):
        self.serialObj = Serial()
        self.deviceObj = Sensor()
        self.deviceObj.start(self.serialObj)

    def tearDown(self):
        self.deviceObj.halt()

    def test_render_type_message(self):
        result = self.deviceObj.render_type_message()
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