import sys
import time
import logging
sys.path.insert(0, '../')

from classes import *
import unittest
from mock_serial import Serial

class TestHub(unittest.TestCase):

    def setUp(self):
        self.serialObj = Serial()
        self.hubObj = Hub(self.serialObj)

    def tearDown(self):
        self.hubObj.halt()

    def test_receive_message(self):
        message = {
            'cluster':          b'\x00\xf6',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\xc2\x16',
            'rf_data':          b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint':     b'\x02'
        }
        self.hubObj.receive_message(message)
        result = self.hubObj.list_known_devices()
        expected = {
            '00:0d:6f:00:03:bb:b9:f8': {
                'addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8',
                'addr_short': '\x88\x9f',
                'associated': True,
                'messages_received': 1,
                'messages_sent': 0,
                'date_found': int(time.time()),
                'date_last_message': int(time.time()),
                'name': 'Unknown Device',
                'type_info': {
                    'date': '2013-09-26',
                    'manu': 'AlertMe.com',
                    'type': 'SmartPlug',
                    'version': 20045
                }
            }
        }
        self.assertEqual(result, expected)

    def test_endpoint_request(self):
        message = {
            'cluster':          b'\x00\x06',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\x00\x00',
            'rf_data':          b'',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint':     b'\x02'
        }
        self.hubObj.receive_message(message)
        result = self.serialObj.get_data_written()
        expected = b'~\x00\x19\x11\x00\x00\ro\x00\x03\xbb\xb9\xf8\x88\x9f\x00\x02\x00\xf0\xc2\x16\x00\x00\x19\x01\xfa\x00\x01\xfd'
        self.assertEqual(result, expected)


    def test_parse_tamper(self):
        result = Hub.parse_tamper(b'\t\x00\x00\x02\xe8\xa6\x00\x00')
        expected = 1
        self.assertEqual(result, expected, "Tamper Detected")

        result = Hub.parse_tamper(b'\t\x00\x01\x01+\xab\x00\x00')
        expected = 0
        self.assertEqual(result, expected, "Tamper OK")

    def test_parsePowerInfo(self):
        result = Hub.parse_power_info(b'\t\x00\x81%\x00')
        expected = 37
        self.assertEqual(result, expected)

    def test_parse_usage_info(self):
        result = Hub.parse_usage_info(b'\t\x00\x82Z\xbb\x04\x00\xdf\x86\x04\x00\x00')
        expected = {
            'UsageWattSeconds': 310106,
            'UsageWattHours': 86.140624468,
            'UpTime': 296671
        }
        self.assertEqual(result, expected)

    def test_parse_switch_status(self):
        result = Hub.parse_switch_status(b'\th\x80\x07\x01')
        expected = 1
        self.assertEqual(result, expected)

        result = Hub.parse_switch_status(b'\th\x80\x06\x00')
        expected = 0
        self.assertEqual(result, expected)

    def test_parse_version_info(self):
        serialObj2 = Serial()
        deviceObj = SmartPlug(serialObj2)

        message = deviceObj.get_type()
        result = Hub.parse_version_info(message['data'])
        expected = {
            'version': 20045,
            'manu':   'AlertMe.com',
            'type':   'SmartPlug',
            'date':   '2013-09-26'
        }
        self.assertEqual(result, expected)
        deviceObj.halt()

        result = Hub.parse_version_info(b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26')
        expected = {
            'version': 20045,
            'manu':   'AlertMe.com',
            'type':   'SmartPlug',
            'date':   '2013-09-26'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfebI\xb2\x8a\xc2\x00\x00o\r\x009\x10\r\x00\x03#\x01\x01\x0bAlertMe.com\x0bPower Clamp\n2010-05-19')
        expected = {
            'version': 18786,
            'manu':   'AlertMe.com',
            'type':   'Power Clamp',
            'date':   '2010-05-19'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfe+\xe8\xc0ax\x00\x00o\r\x009\x10\x01\x00\x01#\x00\x01\x0bAlertMe.com\rButton Device\n2010-11-15')
        expected = {
            'version': 59435,
            'manu':   'AlertMe.com',
            'type':   'Button Device',
            'date':   '2010-11-15'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfe\xb6\xb7x\x1dx\x00\x00o\r\x009\x10\x06\x00\x00#\x00\x02\x0bAlertMe.com\nPIR Device\n2010-11-24')
        expected = {
            'version': 47030,
            'manu':   'AlertMe.com',
            'type':   'PIR Device',
            'date':   '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfe\x82@\xc1e\x1d\x00\x00o\r\x009\x10\x04\x00\x01#\x00\x01\x0bAlertMe.com\x0eAlarm Detector\n2010-11-24')
        expected = {
            'version': 16514,
            'manu':   'AlertMe.com',
            'type':   'Alarm Detector',
            'date':   '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\t0\xfe3B\x08BI\x00\x00o\r\x009\x10\x03\x00\x03#\x00\x01\x0bAlertMe.com\rKeyfob Device\n2010-11-10')
        expected = {
            'version': 16947,
            'manu':   'AlertMe.com',
            'type':   'Keyfob Device',
            'date':   '2010-11-10'
        }
        self.assertEqual(result, expected)

    def test_parse_range_info(self):
        result = Hub.parse_range_info(b'\t+\xfd\xc5w')
        expected = 197
        self.assertEqual(result, expected)

    def test_parse_button_press(self):
        result = Hub.parse_button_press(b'\t\x00\x00\x00\x02\xbf\xc3\x00\x00')
        expected = {'Counter': 50111, 'State': 0}
        self.assertEqual(result, expected, "State 0, Conter 50111")

        result = Hub.parse_button_press(b'\t\x00\x01\x00\x01\x12\xca\x00\x00')
        expected = {'Counter': 51730, 'State': 1}
        self.assertEqual(result, expected, "State 1, Conter 51730")

    def test_parse_status_update(self):
        result = Hub.parse_status_update(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'Temp_F': 87.008, 'Type': 'Key Fob', 'Counter': 13019}
        self.assertEqual(result, expected)

    def test_parse_security_device(self):
        result = Hub.parse_security_device(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'ReedSwitch': 'open', 'TamperSwith': 'closed'}
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
