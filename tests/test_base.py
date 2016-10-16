import sys
sys.path.insert(0, '../')

from classes import Base
import unittest

class TestBase(unittest.TestCase):

    def test_prettyMac(self):
        result = Base.prettyMac(b'\x00\ro\x00\x03\xbb\xb9\xf8')
        expected = '00:0d:6f:00:03:bb:b9:f8'
        self.assertEqual(result, expected, 'Test MAC 1')

        result = Base.prettyMac(b'\x00\ro\x00\x02\xbb\xb7\xe8')
        expected = '00:0d:6f:00:02:bb:b7:e8'
        self.assertEqual(result, expected, 'Test MAC 2')

if __name__ == '__main__':
    unittest.main(verbosity=2)
