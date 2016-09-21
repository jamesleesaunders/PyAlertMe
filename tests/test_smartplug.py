import sys
sys.path.insert(0, '../')

from classes import SmartPlug
import unittest

class TestSmartPlug(unittest.TestCase):

    def test_parsePowerInfo(self):
        result = SmartPlug.parsePowerInfo('\t\x00\x81%\x00')
        expected = 37
        self.assertEqual(result, expected)

    def test_parseUsageInfo(self):
        result = SmartPlug.parseUsageInfo('\t\x00\x82Z\xbb\x04\x00\xdf\x86\x04\x00\x00')
        expected = {
            'UsageWattSeconds': 310106, 
            'UsageWattHours': 86.140624468, 
            'UpTime': 296671
        }
        self.assertEqual(result, expected)

    def test_parseSwitchStatus(self):
        result = SmartPlug.parseSwitchStatus('\th\x80\x07\x01')
        expected = 1
        self.assertEqual(result, expected)

        result = SmartPlug.parseSwitchStatus('\th\x80\x06\x00')
        expected = 0
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
