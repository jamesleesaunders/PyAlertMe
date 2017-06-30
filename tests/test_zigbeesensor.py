import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestZigBeeSensor(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = ZigBeeSensor(self.ser)

    def tearDown(self):
        self.device_obj.halt()

    def test_generate_type_update(self):
        result = self.device_obj.generate_version_info_update()
        expected = {
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': b'\xc2\x16',
            'data': b'\tq\xfe90\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bPyAlertMe\nZigBeeSensor\n2017-01-01'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)