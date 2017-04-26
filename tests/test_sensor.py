from pyalertme import *
import unittest
from mock_serial import Serial

class TestSensor(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = Sensor()
        self.device_obj.start(self.ser)

    def tearDown(self):
        self.device_obj.halt()

    def test_generate_type_update(self):
        result = self.device_obj.generate_type_update()
        expected = {
            'description': 'Type Info',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': b'\xc2\x16',
            'data': b'\tq\xfe90\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bPyAlertMe\nButton Device\n2017-01-01'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)