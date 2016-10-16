import sys
sys.path.insert(0, '../')

from classes import SmartPlug
import unittest

class TestSmartPlug(unittest.TestCase):

    def test_parsePowerInfo(self):
        result = SmartPlug.parsePowerInfo(b'\t\x00\x81%\x00')
        expected = 37
        self.assertEqual(result, expected)

    def test_parseUsageInfo(self):
        result = SmartPlug.parseUsageInfo(b'\t\x00\x82Z\xbb\x04\x00\xdf\x86\x04\x00\x00')
        expected = {
            'UsageWattSeconds': 310106, 
            'UsageWattHours': 86.140624468, 
            'UpTime': 296671
        }
        self.assertEqual(result, expected)

    def test_parseSwitchStatus(self):
        result = SmartPlug.parseSwitchStatus(b'\th\x80\x07\x01')
        expected = 1
        self.assertEqual(result, expected)

        result = SmartPlug.parseSwitchStatus(b'\th\x80\x06\x00')
        expected = 0
        self.assertEqual(result, expected)

    def test_listAction(self):
        deviceObj = SmartPlug(b'\x00\x00\x00\x00\x00\x00\x00\x00', 'Test SmartPlug')

        result = deviceObj.listActions()
        expected = {
            'match_descriptor': 'Match Descriptor', 
            'hardware_join_1': 'Hardware Join Messages 1', 
            'hardware_join_2': 'Hardware Join Messages 2',
            'endpoint_request': 'Active Endpoint Request', 
            'version_info': 'Version Request', 
            'plug_on': 'Switch Plug On',
            'plug_off': 'Switch Plug Off', 
            'switch_status': 'Switch Status', 
            'silent_mode': 'Silent Mode', 
            'range_test': 'Range Test', 
            'normal_mode': 'Restore Normal Mode', 
            'locked_mode': 'Locked Mode'
        }
        self.assertEqual(result, expected)
 
    def test_getAction(self):
        deviceObj = SmartPlug(b'\x00\x00\x00\x00\x00\x00\x00\x00', 'Test SmartPlug')

        result = deviceObj.getAction('plug_on')
        expected = [{
            'profile': '\xc2\x16', 
            'description': 'Switch Plug On', 
            'src_endpoint': '\x00', 
            'cluster': '\x00\xee', 
            'data': '\x11\x00\x02\x01\x01', 
            'dest_endpoint': '\x02',
            'dest_addr': None,
            'dest_addr_long': '\x00\x00\x00\x00\x00\x00\x00\x00',
            'device_name': 'Test SmartPlug',
            'device_type': 'SmartPlug'
        }]
        self.assertEqual(result, expected)
 
if __name__ == '__main__':
    unittest.main(verbosity=2)
