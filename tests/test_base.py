import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestBase(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = Base()
        self.device_obj.start(self.ser)

    def tearDown(self):
        self.device_obj.halt()

    def test_pretty_mac(self):
        result = Base.pretty_mac(b'\x00\x1E\x5E\x09\x02\x14\xC5\xAB')
        expected = '00:1e:5e:09:02:14:c5:ab'
        self.assertEqual(result, expected, 'Test MAC 1')

        result = Base.pretty_mac(b'\x00\ro\x00\x03\xbb\xb9\xf8')
        expected = '00:0d:6f:00:03:bb:b9:f8'
        self.assertEqual(result, expected, 'Test MAC 2')

    def test_get_addresses(self):
        self.device_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'\x88\x9f', 'command': 'MY', 'id': 'at_response'})
        self.assertEqual(self.device_obj.addr_short, b'\x88\x9f')

        self.device_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'\x00\x13\xa2\x00', 'command': 'SH', 'id': 'at_response'})
        self.device_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'@\xe9\xa4\xc0', 'command': 'SL', 'id': 'at_response'})
        self.assertEqual(self.device_obj.addr_long, b'\x00\x13\xa2\x00@\xe9\xa4\xc0')

        self.assertEqual(self.device_obj.get_node_id(), '00:13:a2:00:40:e9:a4:c0')

if __name__ == '__main__':
    unittest.main(verbosity=2)
