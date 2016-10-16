import sys
sys.path.insert(0, '../')

from classes import Device
import unittest

class TestDevice(unittest.TestCase):
    def test_parseVersionInfo(self):
        result = Device.parseVersionInfo(b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26')
        expected = {
            'Version': 20045,
            'String': 'AlertMe.com\nSmartPlug\n2013-09-26',
            'Manu':   'AlertMe.com',
            'Type':   'SmartPlug',
            'Date':   '2013-09-26'
        }
        self.assertEqual(result, expected)

        result = Device.parseVersionInfo(b'\tp\xfe+\xe8\xc0ax\x00\x00o\r\x009\x10\x01\x00\x01#\x00\x01\x0bAlertMe.com\rButton Device\n2010-11-15')
        expected = {
            'Version': 59435,
            'String': 'AlertMe.com\nButton Device\n2010-11-15',
            'Manu':   'AlertMe.com',
            'Type':   'Button Device',
            'Date':   '2010-11-15'
        }
        self.assertEqual(result, expected)

        result = Device.parseVersionInfo(b'\tp\xfe\xb6\xb7x\x1dx\x00\x00o\r\x009\x10\x06\x00\x00#\x00\x02\x0bAlertMe.com\nPIR Device\n2010-11-24')
        expected = {
            'Version': 47030,
            'String': 'AlertMe.com\nPIR Device\n2010-11-24',
            'Manu':   'AlertMe.com',
            'Type':   'PIR Device',
            'Date':   '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = Device.parseVersionInfo(b'\tp\xfe\x82@\xc1e\x1d\x00\x00o\r\x009\x10\x04\x00\x01#\x00\x01\x0bAlertMe.com\x0eAlarm Detector\n2010-11-24')
        expected = {
            'Version': 16514,
            'String': 'AlertMe.com\nAlarm Detector\n2010-11-24',
            'Manu':   'AlertMe.com',
            'Type':   'Alarm Detector',
            'Date':   '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = Device.parseVersionInfo(b'\t0\xfe3B\x08BI\x00\x00o\r\x009\x10\x03\x00\x03#\x00\x01\x0bAlertMe.com\rKeyfob Device\n2010-11-10')
        expected = {
            'Version': 16947,
            'String': 'AlertMe.com\nKeyfob Device\n2010-11-10',
            'Manu':   'AlertMe.com',
            'Type':   'Keyfob Device',
            'Date':   '2010-11-10'
        }
        self.assertEqual(result, expected)

    def test_parseRangeInfo(self):
        result = Device.parseRangeInfo(b'\t+\xfd\xc5w')
        expected = 197
        self.assertEqual(result, expected)

    def test_receiveMessage(self):
        message = {   
            'cluster':          b'\x00\xf6',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\xc2\x16',
            'rf_data':          b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'source_endpoint':  b'\x02'
        }
        deviceObj = Device(message['source_addr_long'])
        deviceObj.receiveMessage(message)
        result = deviceObj.getType()
        expected = 'SmartPlug'
        self.assertEqual(result, expected)

    def test_endpointRequest(self):
        self.maxDiff = None
        message = {   
            'cluster':          b'\x00\x06',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\x00\x00',
            'rf_data':          b'',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'source_endpoint':  b'\x02'
        }
        expected = [
            {
                'cluster': '\x00\x05',
                'data': '\x00\x00',
                'description': 'Active Endpoint Request',
                'dest_addr': '\x88\x9f',
                'dest_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8',
                'dest_endpoint': '\x00',
                'device_name': 'Test Device',
                'device_type': None,
                'profile': '\x00\x00',
                'src_endpoint': '\x00'
            },{
                'cluster': '\x80\x06',
                'data': '\x00\x00\x00\x00\x01\x02',
                'description': 'Match Descriptor',
                'dest_addr': '\x88\x9f',
                'dest_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8',
                'dest_endpoint': '\x00',
                'device_name': 'Test Device',
                'device_type': None,
                'profile': '\x00\x00',
                'src_endpoint': '\x00'
            },{
                'cluster': '\x00\xf6',
                'data': '\x11\x01\xfc',
                'description': 'Hardware Join Messages 1',
                'dest_addr': '\x88\x9f',
                'dest_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8',
                'dest_endpoint': '\x02',
                'device_name': 'Test Device',
                'device_type': None,
                'profile': '\xc2\x16',
                'src_endpoint': '\x00'
            },{
                'cluster': '\x00\xf0',
                'data': '\x19\x01\xfa\x00\x01',
                'description': 'Hardware Join Messages 2',
                'dest_addr': '\x88\x9f',
                'dest_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8',
                'dest_endpoint': '\x02',
                'device_name': 'Test Device',
                'device_type': None,
                'profile': '\xc2\x16',
                'src_endpoint': '\x00'
            },{
                'cluster': '\x00\xf6',
                'data': '\x11\x00\xfc\x00\x01',
                'description': 'Version Request',
                'dest_addr': '\x88\x9f',
                'dest_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8',
                'dest_endpoint': '\x02',
                'device_name': 'Test Device',
                'device_type': None,
                'profile': '\xc2\x16',
                'src_endpoint': '\x00'
            }
        ]
        deviceObj = Device(message['source_addr_long'], 'Test Device')
        deviceObj.receiveMessage(message)
        result = deviceObj.messageQueue();
        self.assertEqual(result, expected)

    def test_parseTamper(self):
        result = Device.parseTamper(b'\t\x00\x00\x02\xe8\xa6\x00\x00')
        expected = 1
        self.assertEqual(result, expected, "Tamper Detected")

        result = Device.parseTamper(b'\t\x00\x01\x01+\xab\x00\x00')
        expected = 0
        self.assertEqual(result, expected, "Tamper OK")


if __name__ == '__main__':
    unittest.main(verbosity=2)
