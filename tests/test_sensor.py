import sys
sys.path.insert(0, '../')

from classes import Sensor
import unittest

class TestSensor(unittest.TestCase):

    def test_parseButtonPress(self):
        result = Sensor.parseButtonPress(b'\t\x00\x00\x00\x02\xbf\xc3\x00\x00')
        expected = {'Counter': 50111, 'State': 0}
        self.assertEqual(result, expected, "State 0, Conter 50111")

        result = Sensor.parseButtonPress(b'\t\x00\x01\x00\x01\x12\xca\x00\x00')
        expected = {'Counter': 51730, 'State': 1}
        self.assertEqual(result, expected, "State 1, Conter 51730")

    def test_parseStatusUpdate(self):
        result = Sensor.parseStatusUpdate(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'Temp_F': 87.008, 'Type': 'Key Fob', 'Counter': 13019}
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
