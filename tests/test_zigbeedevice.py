import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestZigBeeDevice(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = ZBNode(self.ser)

    def tearDown(self):
        self.device_obj.halt()

    def test_get_addresses(self):
        self.device_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'\x88\x9f', 'command': 'MY', 'id': 'at_response'})
        self.assertEqual(self.device_obj.addr_short, b'\x88\x9f')

        self.device_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'\x00\x13\xa2\x00', 'command': 'SH', 'id': 'at_response'})
        self.device_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'@\xe9\xa4\xc0', 'command': 'SL', 'id': 'at_response'})
        self.assertEqual(self.device_obj.addr_long, b'\x00\x13\xa2\x00@\xe9\xa4\xc0')

        self.assertEqual(self.device_obj.id, '00:13:a2:00:40:e9:a4:c0')

if __name__ == '__main__':
    unittest.main(verbosity=2)
