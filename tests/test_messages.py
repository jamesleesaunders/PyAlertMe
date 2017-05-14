import sys
sys.path.insert(0, '../')
from pyalertme.messages import *
import unittest

class TestMessages(unittest.TestCase):

    def test_get_message(self):
        # Test message with data lambda
        result = get_message('switch_state_update', {'State': 1})
        expected = {'profile': b'\xc2\x16', 'cluster': b'\x00\xee', 'dest_endpoint': b'\x02', 'src_endpoint': b'\x02', 'data': b'\th\x80\x07\x01'}
        self.assertEqual(result, expected)
        result = get_message('switch_state_update', {'State': 0})
        expected = {'profile': b'\xc2\x16', 'cluster': b'\x00\xee', 'dest_endpoint': b'\x02', 'src_endpoint': b'\x02', 'data': b'\th\x80\x06\x00'}
        self.assertEqual(result, expected)

        # Test message without data lambda
        result = get_message('missing_link')
        expected = {'profile': b'\xc2\x16', 'cluster': b'\x00\xf0', 'dest_endpoint': b'\x02', 'src_endpoint': b'\x02', 'data': b'\x11\x39\xfd'}
        self.assertEqual(result, expected)

        # Test message that does not exist throws exception
        with self.assertRaises(Exception) as context:
            get_message('foo_lorem_ipsum')
        self.assertTrue('Message does not exist' in context.exception)

    def test_parse_tamper_state(self):
        result = parse_tamper_state(b'\t\x00\x00\x02\xe8\xa6\x00\x00')
        expected = {'TamperSwitch': 'OPEN'}
        self.assertEqual(result, expected, "Tamper Detected")

        result = parse_tamper_state(b'\t\x00\x01\x01+\xab\x00\x00')
        expected = {'TamperSwitch': 'CLOSED'}
        self.assertEqual(result, expected, "Tamper OK")

    def test_parse_power_demand(self):
        result = parse_power_demand(b'\tj\x81\x00\x00')
        expected = {'PowerDemand': 0}
        self.assertEqual(result, expected)

        result = parse_power_demand(b'\tj\x81%\x00')
        expected = {'PowerDemand': 37}
        self.assertEqual(result, expected)
        
        result = parse_power_demand(b'\tj\x81\x16\x00')
        expected = {'PowerDemand': 22}
        self.assertEqual(result, expected)

    def test_generate_power_demand_update(self):
        result = generate_power_demand_update({'PowerDemand': 0})
        expected = b'\tj\x81\x00\x00'
        self.assertEqual(result, expected)

        result = generate_power_demand_update({'PowerDemand': 37})
        expected = b'\tj\x81%\x00'
        self.assertEqual(result, expected)

        result = generate_power_demand_update({'PowerDemand': 22.4})
        expected = b'\tj\x81\x16\x00'
        self.assertEqual(result, expected)

    def test_parse_power_consumption(self):
        result = parse_power_consumption(b'\t\x00\x82Z\xbb\x04\x00\xdf\x86\x04\x00\x00')
        expected = {
            'PowerConsumption': 310106,
            'UpTime': 296671
        }
        self.assertEqual(result, expected)

    def test_parse_relay_state_request(self):
        result = parse_switch_state_request(b'\x11\x00\x02\x01\x01')
        self.assertEqual(result, 1)

        result = parse_switch_state_request(b'\x11\x00\x02\x00\x01')
        self.assertEqual(result, 0)

    def test_parse_switch_state(self):
        result = parse_switch_state_update(b'\th\x80\x07\x01')
        expected = {'State': 1}
        self.assertEqual(result, expected)

        result = parse_switch_state_update(b'\th\x80\x06\x00')
        expected = {'State': 0}
        self.assertEqual(result, expected)

    def test_generate_relay_state_response(self):
        result = generate_switch_state_update({'State': 1})
        expected = b'\th\x80\x07\x01'
        self.assertEqual(result, expected)

        result = generate_switch_state_update({'State': 0})
        expected = b'\th\x80\x06\x00'
        self.assertEqual(result, expected)

    def test_generate_mode_change_request(self):
        result = generate_mode_change_request({'Mode': 'Normal'})
        expected = b'\x11\x00\xfa\x00\x01'
        self.assertEqual(result, expected)

        result = generate_mode_change_request({'Mode': 'RangeTest'})
        expected = b'\x11\x00\xfa\x01\x01'
        self.assertEqual(result, expected)

        result = generate_mode_change_request({'Mode': 'Locked'})
        expected = b'\x11\x00\xfa\x02\x01'
        self.assertEqual(result, expected)

        result = generate_mode_change_request({'Mode': 'Silent'})
        expected = b'\x11\x00\xfa\x03\x01'
        self.assertEqual(result, expected)

    def test_generate_switch_state_request(self):
        # Test On Request
        expected = b'\x11\x00\x02\x01\x01'
        self.assertEqual(generate_switch_state_request({'State': 1}), expected)
        self.assertEqual(generate_switch_state_request({'State': True}), expected)
        self.assertEqual(generate_switch_state_request({'State': 23}), expected)

        # Test Off Request
        expected = b'\x11\x00\x02\x00\x01'
        self.assertEqual(generate_switch_state_request({'State': 0}), expected)
        self.assertEqual(generate_switch_state_request({'State': False}), expected)
        self.assertEqual(generate_switch_state_request({'State': None}), expected)

        # Test Check Only
        expected = b'\x11\x00\x01\x01'
        self.assertEqual(generate_switch_state_request({}), expected)

    def test_generate_version_info_request(self):
        result = generate_version_info_request()
        expected = b'\x11\x00\xfc'
        self.assertEqual(result, expected)

    def test_parse_version_info_update(self):
        result = parse_version_info_update(b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26')
        expected = {
            'Version': 20045,
            'Manufacturer': 'AlertMe.com',
            'Type': 'SmartPlug',
            'ManufactureDate': '2013-09-26'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\tp\xfebI\xb2\x8a\xc2\x00\x00o\r\x009\x10\r\x00\x03#\x01\x01\x0bAlertMe.com\x0bPower Clamp\n2010-05-19')
        expected = {
            'Version': 18786,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Power Clamp',
            'ManufactureDate': '2010-05-19'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\tp\xfe+\xe8\xc0ax\x00\x00o\r\x009\x10\x01\x00\x01#\x00\x01\x0bAlertMe.com\rButton Device\n2010-11-15')
        expected = {
            'Version': 59435,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Button Device',
            'ManufactureDate': '2010-11-15'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\tp\xfe\xb6\xb7x\x1dx\x00\x00o\r\x009\x10\x06\x00\x00#\x00\x02\x0bAlertMe.com\nPIR Device\n2010-11-24')
        expected = {
            'Version': 47030,
            'Manufacturer': 'AlertMe.com',
            'Type': 'PIR Device',
            'ManufactureDate': '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\t\x00\xfe\xad\xe3jj\x1b\x00\x00o\r\x009\x10\x05\x00\x06\x12\x00\x01\x0bAlertMe.com\x12Door/Window sensor\n2008-04-17')
        expected = {
            'Version': 58285,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Door/Window sensor',
            'ManufactureDate': '2008-04-17'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\tp\xfe\x82@\xc1e\x1d\x00\x00o\r\x009\x10\x04\x00\x01#\x00\x01\x0bAlertMe.com\x0eAlarm Detector\n2010-11-24')
        expected = {
            'Version': 16514,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Alarm Detector',
            'ManufactureDate': '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\t0\xfe3B\x08BI\x00\x00o\r\x009\x10\x03\x00\x03#\x00\x01\x0bAlertMe.com\rKeyfob Device\n2010-11-10')
        expected = {
            'Version': 16947,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Keyfob Device',
            'ManufactureDate': '2010-11-10'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\t\x00\xfe\x1b\x15V_\x1b\x00\x00o\r\x009\x10\x02\x00\x07\x12\x00\x02\x0bAlertMe.com\x06Beacon\n2008-07-08')
        expected = {
            'Version': 5403,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Beacon',
            'ManufactureDate': '2008-07-08'
        }
        self.assertEqual(result, expected)

        result = parse_version_info_update(b'\t\x00\xfe\xde\xa4\xeav\x1b\x00\x00o\r\x009\x10\x02\x00\x06\x12\x01\x01\x0bAlertMe.com\x04Lamp\n2008-04-17')
        expected = {
            'Version': 42206,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Lamp',
            'ManufactureDate': '2008-04-17'
        }
        self.assertEqual(result, expected)

    def test_generate_version_info_update(self):
        params = {
            'Version': 12345,
            'Manufacturer': 'PyAlertMe',
            'Type': 'Generic',
            'ManufactureDate': '2017-01-01'
        }
        result = generate_version_info_update(params)
        expected = b'\tq\xfe90\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bPyAlertMe\nGeneric\n2017-01-01'

        self.assertEqual(result, expected)

    def test_parse_range_info_update(self):
        result = parse_range_info_update(b'\t+\xfd\xc5w')
        expected = {'RSSI': 197}
        self.assertEqual(result, expected)

    def test_generate_range_update(self):
        result = generate_range_update({'RSSI': 197})
        expected = b'\t+\xfd\xc5\x00'
        self.assertEqual(result, expected)

    def test_parse_button_press(self):
        result = parse_button_press(b'\t\x00\x00\x00\x02\xbf\xc3\x00\x00')
        expected = {'Counter': 50111, 'State': 0}
        self.assertEqual(result, expected, "State OFF, Counter 50111")

        result = parse_button_press(b'\t\x00\x01\x00\x01\x12\xca\x00\x00')
        expected = {'Counter': 51730, 'State': 1}
        self.assertEqual(result, expected, "State ON, Counter 51730")

    def test_parse_status_update(self):
        result = parse_status_update(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'TempFahrenheit': 87.008, 'Counter': 13019}
        self.assertEqual(result, expected)

        result = parse_status_update(b'\t\x00\xfb\x1b\x97H\x00\x00H\x0c\x9c\x01\xd4\xff\x00\x00')
        expected = {}
        self.assertEqual(result, expected)

    def test_parse_security_state(self):
        result = parse_security_state(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'ReedSwitch': 'OPEN', 'TamperSwitch': 'CLOSED'}
        self.assertEqual(result, expected)

    def test_generate_missing_link(self):
        result = generate_missing_link()
        expected = b'\x11\x39\xfd'
        self.assertEqual(result, expected)

    def test_generate_security_init(self):
        result = generate_security_init()
        expected = b'\x11\x80\x00\x00\x05'
        self.assertEqual(result, expected)

    def test_generate_active_endpoints_request(self):
        source_addr_short = b'\x88\x9f'
        message = get_message('active_endpoints_request', {'AddressShort': source_addr_short})
        result = message['data']
        expected = b'\xaa\x9f\x88'
        self.assertEqual(result, expected)

    def test_generate_match_descriptor_request(self):
        message = get_message('match_descriptor_request')
        result = message['data']
        expected = '\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        self.assertEqual(result, expected)

    def test_generate_match_descriptor_response(self):
        rf_data = b'\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        message = get_message('match_descriptor_response', {'rf_data': rf_data})
        result = message['data']
        expected = b'\x03\x00\x00\x00\x01\x02'
        self.assertEqual(result, expected)

    def test_generate_routing_table_request(self):
        message = get_message('routing_table_request')
        result = message['data']
        expected = b'\x12\x01'
        self.assertEqual(result, expected)

    def test_permit_join_request(self):
        message = get_message('permit_join_request')
        result = message['data']
        expected = b'\xff\x00'
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)