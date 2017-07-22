import sys
sys.path.insert(0, '../')
from pyalertme.zbnode import *
import unittest
from mock_serial import Serial

class TestZBNode(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.node_obj = ZBNode(self.ser)

    def tearDown(self):
        self.node_obj.halt()

    def test_parse_message(self):
        self.maxDiff = None
        self.node_obj.addr_short = b'\x00\x00'

        # Match Descriptor Request
        message = {
            'source_addr_long': '\x00\x13\xa2\x00@\xa2;\t',
            'source_addr': 'RK',
            'source_endpoint': '\x00',
            'dest_endpoint': '\x00',
            'profile': '\x00\x00',
            'cluster': '\x00\x06',
            'id': 'rx_explicit',
            'options': '\x01',
            'rf_data': '\x01\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        }

        result = self.node_obj.parse_message(message)
        expected = {
            'attributes': {},
            'replies': [
                {'cluster': '\x80\x06', 'data': '\x04\x00\x00\x00\x01\x02', 'dest_endpoint': '\x00', 'profile': '\x00\x00', 'src_endpoint': '\x00'},
                {'cluster': '\x00\xf6', 'data': '\x11\x00\xfc', 'dest_endpoint': '\x02', 'profile': '\xc2\x16', 'src_endpoint': '\x02'},
                {'cluster': '\x00\xf0', 'data': '\x11\x00\xfa\x00\x01', 'dest_endpoint': '\x02', 'profile': '\xc2\x16', 'src_endpoint': '\x02'}
            ]
        }
        self.assertEqual(result, expected)

        # Version Information Response
        message = {
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'source_addr': b'\x88\x9f',
            'source_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xf6',
            'id': 'rx_explicit',
            'options': b'\x01',
            'rf_data': b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26'
        }
        result = self.node_obj.parse_message(message)
        expected = {
            'attributes': {
                'manu': 'AlertMe.com',
                'manu_date': '2013-09-26',
                'type': 'SmartPlug',
                'version': 20045
            },
            'replies': []
        }
        self.assertEqual(result, expected)

    def test_get_addresses(self):
        self.node_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'\x88\x9f', 'command': 'MY', 'id': 'at_response'})
        self.assertEqual(self.node_obj.addr_short, b'\x88\x9f')

        self.node_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'\x00\x13\xa2\x00', 'command': 'SH', 'id': 'at_response'})
        self.node_obj.receive_message({'status': b'\x00', 'frame_id': b'\x01', 'parameter': b'@\xe9\xa4\xc0', 'command': 'SL', 'id': 'at_response'})
        self.assertEqual(self.node_obj.addr_long, b'\x00\x13\xa2\x00@\xe9\xa4\xc0')

        self.assertEqual(self.node_obj.id, '00:13:a2:00:40:e9:a4:c0')

    def test_get_message(self):
        # Test providing all the appropriate parameters
        result = self.node_obj.generate_message('version_info_update', {'version': 20045, 'manu': 'AlertMe.com', 'type': 'SmartPlug', 'manu_date': '2013-09-26'})
        expected = {'profile': b'\xc2\x16', 'cluster': '\x00\xf6', 'dest_endpoint': b'\x02', 'src_endpoint': b'\x02', 'data': b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\nSmartPlug\n2013-09-26'}
        self.assertEqual(result, expected)

        # Test providing a couple of parameters missing
        # Should throw exception detailing the parameters which are missing
        with self.assertRaises(Exception) as context:
            self.node_obj.generate_message('version_info_update', {'manu': 'AlertMe.com', 'type': 'SmartPlug'})
        self.assertTrue("Missing Parameters: ['manu_date', 'version']" in context.exception)

        # Test providing no parameters
        with self.assertRaises(Exception) as context:
            self.node_obj.generate_message('version_info_update', {})
        self.assertTrue("Missing Parameters: ['manu', 'manu_date', 'type', 'version']" in context.exception)
        with self.assertRaises(Exception) as context:
            self.node_obj.generate_message('version_info_update')
        self.assertTrue("Missing Parameters: ['manu', 'manu_date', 'type', 'version']" in context.exception)

        # Test message without data lambda
        result = self.node_obj.generate_message('permit_join_request')
        expected = {'profile': b'\x00\x00', 'cluster': b'\x00\x36', 'dest_endpoint': b'\x00', 'src_endpoint': b'\x00', 'data': b'\xff\x00'}
        self.assertEqual(result, expected)

        # Test calling for a message which does not exist
        # Should throws exception that message does not exist
        with self.assertRaises(Exception) as context:
            self.node_obj.generate_message('foo_lorem_ipsum')
        self.assertTrue("Message 'foo_lorem_ipsum' does not exist" in context.exception)

    def test_list_messages(self):
        # Test the resulting dict is in the expected structure.
        # We don't test the entire dict matches but check one message.
        messages = self.node_obj.list_messages()
        message = messages['version_info_update']
        expected = {
            'name': 'Version Info Update',
            'expected_params': ['version', 'type', 'manu', 'manu_date']
        }
        self.assertEqual(message, expected)

    def test_parse_tamper_state(self):
        result = self.node_obj.parse_tamper_state(b'\t\x00\x00\x02\xe8\xa6\x00\x00')
        expected = {'counter': 42728, 'tamper_state': 1}
        self.assertEqual(result, expected)

        result = self.node_obj.parse_tamper_state(b'\t\x00\x01\x01+\xab\x00\x00')
        expected = {'counter': 43819, 'tamper_state': 0}
        self.assertEqual(result, expected)

    def test_parse_power_demand(self):
        result = self.node_obj.parse_power_demand(b'\tj\x81\x00\x00')
        expected = {'power_demand': 0}
        self.assertEqual(result, expected)

        result = self.node_obj.parse_power_demand(b'\tj\x81%\x00')
        expected = {'power_demand': 37}
        self.assertEqual(result, expected)
        
        result = self.node_obj.parse_power_demand(b'\tj\x81\x16\x00')
        expected = {'power_demand': 22}
        self.assertEqual(result, expected)

    def test_generate_power_demand_update(self):
        result = self.node_obj.generate_power_demand_update({'power_demand': 0})
        expected = b'\tj\x81\x00\x00'
        self.assertEqual(result, expected)

        result = self.node_obj.generate_power_demand_update({'power_demand': 37})
        expected = b'\tj\x81%\x00'
        self.assertEqual(result, expected)

        result = self.node_obj.generate_power_demand_update({'power_demand': 22.4})
        expected = b'\tj\x81\x16\x00'
        self.assertEqual(result, expected)

    def test_generate_power_consumption_update(self):
        params = {
            'power_consumption': 19973,
            'up_time': 33207
        }
        message = self.node_obj.generate_message('power_consumption_update', params)
        result = message['data']
        expected = b'\tn\x82\x05N\x00\x00\xb7\x81\x00\x00\x01'
        self.assertEqual(result, expected)

    def test_parse_power_consumption(self):
        result = self.node_obj.parse_power_consumption(b'\t\x00\x82Z\xbb\x04\x00\xdf\x86\x04\x00\x00')
        expected = {
            'power_consumption': 310106,
            'up_time': 296671
        }
        self.assertEqual(result, expected)

    def test_parse_switch_state_request(self):
        result = self.node_obj.parse_switch_state_request(b'\x11\x00\x02\x01\x01')
        self.assertEqual(result, {'switch_state': 1})

        result = self.node_obj.parse_switch_state_request(b'\x11\x00\x02\x00\x01')
        self.assertEqual(result, {'switch_state': 0})

    def test_parse_switch_state_update(self):
        result = self.node_obj.parse_switch_state_update(b'\th\x80\x07\x01')
        expected = {'switch_state': 1}
        self.assertEqual(result, expected)

        result = self.node_obj.parse_switch_state_update(b'\th\x80\x06\x00')
        expected = {'switch_state': 0}
        self.assertEqual(result, expected)

    def test_generate_switch_state_response(self):
        result = self.node_obj.generate_switch_state_update({'switch_state': 1})
        expected = b'\th\x80\x07\x01'
        self.assertEqual(result, expected)

        result = self.node_obj.generate_switch_state_update({'switch_state': 0})
        expected = b'\th\x80\x06\x00'
        self.assertEqual(result, expected)

    def test_generate_mode_change_request(self):
        result = self.node_obj.generate_mode_change_request({'mode': 'Normal'})
        expected = b'\x11\x00\xfa\x00\x01'
        self.assertEqual(result, expected)

        result = self.node_obj.generate_mode_change_request({'mode': 'RangeTest'})
        expected = b'\x11\x00\xfa\x01\x01'
        self.assertEqual(result, expected)

        result = self.node_obj.generate_mode_change_request({'mode': 'Locked'})
        expected = b'\x11\x00\xfa\x02\x01'
        self.assertEqual(result, expected)

        result = self.node_obj.generate_mode_change_request({'mode': 'Silent'})
        expected = b'\x11\x00\xfa\x03\x01'
        self.assertEqual(result, expected)

    def test_generate_switch_state_request(self):
        # Test On Request
        expected = b'\x11\x00\x02\x01\x01'
        self.assertEqual(self.node_obj.generate_switch_state_request({'switch_state': 1}), expected)

        # Test Off Request
        expected = b'\x11\x00\x02\x00\x01'
        self.assertEqual(self.node_obj.generate_switch_state_request({'switch_state': 0}), expected)

        # Test Check Only
        expected = b'\x11\x00\x01\x01'
        self.assertEqual(self.node_obj.generate_switch_state_request({'switch_state': ''}), expected)

    def test_generate_version_info_request(self):
        result = self.node_obj.generate_version_info_request()
        expected = b'\x11\x00\xfc'
        self.assertEqual(result, expected)

    def test_parse_version_info_update(self):
        result = self.node_obj.parse_version_info_update(b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26')
        expected = {
            'type': 'SmartPlug',
            'version': 20045,
            'manu': 'AlertMe.com',
            'manu_date': '2013-09-26'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\tp\xfebI\xb2\x8a\xc2\x00\x00o\r\x009\x10\r\x00\x03#\x01\x01\x0bAlertMe.com\x0bPower Clamp\n2010-05-19')
        expected = {
            'type': 'Power Clamp',
            'version': 18786,
            'manu': 'AlertMe.com',
            'manu_date': '2010-05-19'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\tp\xfe+\xe8\xc0ax\x00\x00o\r\x009\x10\x01\x00\x01#\x00\x01\x0bAlertMe.com\rButton Device\n2010-11-15')
        expected = {
            'type': 'Button Device',
            'version': 59435,
            'manu': 'AlertMe.com',
            'manu_date': '2010-11-15'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\tp\xfe\xb6\xb7x\x1dx\x00\x00o\r\x009\x10\x06\x00\x00#\x00\x02\x0bAlertMe.com\nPIR Device\n2010-11-24')
        expected = {
            'type': 'PIR Device',
            'version': 47030,
            'manu': 'AlertMe.com',
            'manu_date': '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\t\x00\xfe\xad\xe3jj\x1b\x00\x00o\r\x009\x10\x05\x00\x06\x12\x00\x01\x0bAlertMe.com\x12Door/Window sensor\n2008-04-17')
        expected = {
            'type': 'Door/Window sensor',
            'version': 58285,
            'manu': 'AlertMe.com',
            'manu_date': '2008-04-17'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\tp\xfe\x82@\xc1e\x1d\x00\x00o\r\x009\x10\x04\x00\x01#\x00\x01\x0bAlertMe.com\x0eAlarm Detector\n2010-11-24')
        expected = {
            'type': 'Alarm Detector',
            'version': 16514,
            'manu': 'AlertMe.com',
            'manu_date': '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\t0\xfe3B\x08BI\x00\x00o\r\x009\x10\x03\x00\x03#\x00\x01\x0bAlertMe.com\rKeyfob Device\n2010-11-10')
        expected = {
            'type': 'Keyfob Device',
            'version': 16947,
            'manu': 'AlertMe.com',
            'manu_date': '2010-11-10'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\t\x00\xfe\x1b\x15V_\x1b\x00\x00o\r\x009\x10\x02\x00\x07\x12\x00\x02\x0bAlertMe.com\x06Beacon\n2008-07-08')
        expected = {
            'type': 'Beacon',
            'version': 5403,
            'manu': 'AlertMe.com',
            'manu_date': '2008-07-08'
        }
        self.assertEqual(result, expected)

        result = self.node_obj.parse_version_info_update(b'\t\x00\xfe\xde\xa4\xeav\x1b\x00\x00o\r\x009\x10\x02\x00\x06\x12\x01\x01\x0bAlertMe.com\x04Lamp\n2008-04-17')
        expected = {
            'type': 'Lamp',
            'version': 42206,
            'manu': 'AlertMe.com',
            'manu_date': '2008-04-17'
        }
        self.assertEqual(result, expected)

    def test_generate_version_info_update(self):
        params = {
            'type': 'Generic',
            'version': 12345,
            'manu': 'PyAlertMe',
            'manu_date': '2017-01-01'
        }
        result = self.node_obj.generate_version_info_update(params)
        expected = b'\tq\xfe90\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bPyAlertMe\nGeneric\n2017-01-01'

        self.assertEqual(result, expected)

    def test_parse_range_info_update(self):
        result = self.node_obj.parse_range_info_update(b'\t+\xfd\xc5w')
        expected = {'rssi': 197}
        self.assertEqual(result, expected)

    def test_generate_range_update(self):
        result = self.node_obj.generate_range_update({'rssi': 197})
        expected = b'\t+\xfd\xc5\x00'
        self.assertEqual(result, expected)

    def test_generate_button_press(self):
        params = {'state': 1, 'counter': 62552}
        result = self.node_obj.generate_button_press(params)
        expected = b'\t\x00\x01\x00\x01X\xf4\x00\x00'
        self.assertEqual(result, expected)

    def test_parse_button_press(self):
        result = self.node_obj.parse_button_press(b'\t\x00\x00\x00\x02\xbf\xc3\x00\x00')
        expected = {'counter': 50111, 'button_state': 0}
        self.assertEqual(result, expected, "State OFF, Counter 50111")

        result = self.node_obj.parse_button_press(b'\t\x00\x01\x00\x01\x12\xca\x00\x00')
        expected = {'counter': 51730, 'button_state': 1}
        self.assertEqual(result, expected, "State ON, Counter 51730")

    def test_parse_status_update(self):
        result = self.node_obj.parse_status_update(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'temperature': 87.008, 'counter': 13019}
        self.assertEqual(result, expected)

        result = self.node_obj.parse_status_update(b'\t\x00\xfb\x1b\x97H\x00\x00H\x0c\x9c\x01\xd4\xff\x00\x00')
        expected = {}
        self.assertEqual(result, expected)

    def test_parse_security_state(self):
        result = self.node_obj.parse_security_state('\t\x00\x00\x05\x00\x00')
        expected = {'trigger_state': 1, 'tamper_state': 1}
        self.assertEqual(result, expected)

        result = self.node_obj.parse_security_state(b'\t\x00\x00\x01\x00\x00')
        expected = {'trigger_state': 1, 'tamper_state': 0}
        self.assertEqual(result, expected)

        result = self.node_obj.parse_security_state(b'\t\x00\x00\x00\x00\x00')
        expected = {'trigger_state': 0, 'tamper_state': 0}
        self.assertEqual(result, expected)

        result = self.node_obj.parse_security_state(b'\t\x00\x00\x04\x00\x00')
        expected = {'trigger_state': 0, 'tamper_state': 1}
        self.assertEqual(result, expected)

    def test_generate_active_endpoints_request(self):
        params = {
            'sequence':  170,
            'addr_short': b'\x88\x9f'
        }
        message = self.node_obj.generate_message('active_endpoints_request', params)
        result = message['data']
        expected = b'\xaa\x9f\x88'
        self.assertEqual(result, expected)

    def test_generate_match_descriptor_request(self):
        params = {
            'sequence': 1,
            'addr_short': b'\xff\xfd',
            'profile_id': PROFILE_ID_ALERTME,
            'in_cluster_list': b'',
            'out_cluster_list': b'\x00\xf0'
        }
        message = self.node_obj.generate_message('match_descriptor_request', params)
        result = message['data']
        expected = b'\x01\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        self.assertEqual(result, expected)

    def test_status_update(self):
        params = {
            'trigger_state': 0,
            'temperature': 106.574,
            'tamper_state': 1
        }
        message = self.node_obj.generate_message('status_update', params)
        result = message['data']
        expected = b'\t\r\xfb\x1f<\xf1\x08\x02/\x10D\x02\xcf\xff\x01\x00'
        self.assertEqual(result, expected)

    def test_generate_match_descriptor_response(self):
        params = {
            'sequence': 3,
            'addr_short': b'\xe1\x00',
            'endpoint_list': b'\x00\x02'
        }
        message = self.node_obj.generate_message('match_descriptor_response', params)
        result = message['data']
        expected = b'\x03\x00\x00\xe1\x02\x00\x02'
        self.assertEqual(result, expected)

    def test_generate_routing_table_request(self):
        message = self.node_obj.generate_message('routing_table_request')
        result = message['data']
        expected = b'\x12\x01'
        self.assertEqual(result, expected)

    def test_permit_join_request(self):
        message = self.node_obj.generate_message('permit_join_request')
        result = message['data']
        expected = b'\xff\x00'
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)