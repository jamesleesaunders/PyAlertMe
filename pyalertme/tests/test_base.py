import sys
sys.path.insert(0, '../../')

from pyalertme import *
import unittest
from mock_serial import Serial

class TestBase(unittest.TestCase):

    def setUp(self):
        self.serialObj = Serial()
        self.deviceObj = Base()
        self.deviceObj.start(self.serialObj)

    def tearDown(self):
        self.deviceObj.halt()

    def test_test(self):
        self.assertEqual(Base.retired['test']['data'](self, 1), 2)

    def test_pretty_mac(self):
        result = Base.pretty_mac(b'\x00\ro\x00\x03\xbb\xb9\xf8')
        expected = '00:0d:6f:00:03:bb:b9:f8'
        self.assertEqual(result, expected, 'Test MAC 1')

        result = Base.pretty_mac(b'\x00\ro\x00\x02\xbb\xb7\xe8')
        expected = '00:0d:6f:00:02:bb:b7:e8'
        self.assertEqual(result, expected, 'Test MAC 2')

if __name__ == '__main__':
    unittest.main(verbosity=2)
