import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestDevice(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = Node(self.ser)

    def test_pretty_mac(self):
        result = Node.pretty_mac(b'\x00\x1E\x5E\x09\x02\x14\xC5\xAB')
        expected = '00:1e:5e:09:02:14:c5:ab'
        self.assertEqual(result, expected, 'Test MAC 1')

        result = Node.pretty_mac(b'\x00\ro\x00\x03\xbb\xb9\xf8')
        expected = '00:0d:6f:00:03:bb:b9:f8'
        self.assertEqual(result, expected, 'Test MAC 2')

if __name__ == '__main__':
    unittest.main(verbosity=2)
