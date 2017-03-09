import sys
sys.path.insert(0, '../')

from pyalertme import *
import unittest
from mock_serial import Serial

class TestBase(unittest.TestCase):

    def setUp(self):
        serialObj = Serial()
        self.deviceObj = Base(serialObj)

    def tearDown(self):
        self.deviceObj.halt()

    def test_pretty_mac(self):
        result = Base.pretty_mac(b'\x00\ro\x00\x03\xbb\xb9\xf8')
        expected = '00:0d:6f:00:03:bb:b9:f8'
        self.assertEqual(result, expected, 'Test MAC 1')

        result = Base.pretty_mac(b'\x00\ro\x00\x02\xbb\xb7\xe8')
        expected = '00:0d:6f:00:02:bb:b7:e8'
        self.assertEqual(result, expected, 'Test MAC 2')

    def test_list_action(self):
        self.maxDiff = None

        result = self.deviceObj.list_actions()
        expected = {
            'routing_table_request'     : 'Management Rtg (Routing Table) Request',
            'permit_join_request'       : 'Management Permit Join Request',
            # 'match_descriptor_response' : 'Match Descriptor Response',
            'hardware_join_1'           : 'Hardware Join Messages 1',
            'hardware_join_2'           : 'Hardware Join Messages 2',
            'active_endpoints_request'  : 'Active Endpoints Request',
            'version_info'              : 'Version Request',
            'plug_off'                  : 'Switch Plug Off',
            'plug_on'                   : 'Switch Plug On',
            'switch_status'             : 'Switch Status',
            'range_test'                : 'Range Test',
            'normal_mode'               : 'Normal Mode',
            'locked_mode'               : 'Locked Mode',
            'silent_mode'               : 'Silent Mode',
            'security_initialization'   : 'Security Initialization'
        }
        self.assertEqual(result, expected)

    def test_get_action(self):
        result = self.deviceObj.get_action('plug_on')
        expected = {
            'profile': '\xc2\x16',
            'description': 'Switch Plug On',
            'src_endpoint': '\x00',
            'cluster': '\x00\xee',
            'data': '\x11\x00\x02\x01\x01',
            'dest_endpoint': '\x02'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
