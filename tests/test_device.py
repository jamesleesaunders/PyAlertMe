import sys
sys.path.insert(0, '../')

from classes import Device
import unittest

class TestDevice(unittest.TestCase):

    def test_parseVersionInfo(self):
        result = Device.parseVersionInfo('\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26')
        expected = {
            'Version': 20045,
            'String': 'AlertMe.com\nSmartPlug\n2013-09-26',
            'Manu':   'AlertMe.com',
            'Type':   'SmartPlug',
            'Date':   '2013-09-26'
        }
        self.assertEqual(result, expected)

        result = Device.parseVersionInfo('\tp\xfe+\xe8\xc0ax\x00\x00o\r\x009\x10\x01\x00\x01#\x00\x01\x0bAlertMe.com\rButton Device\n2010-11-15')
        expected = {
            'Version': 59435,
            'String': 'AlertMe.com\nButton Device\n2010-11-15',
            'Manu':   'AlertMe.com',
            'Type':   'Button Device',
            'Date':   '2010-11-15'
        }
        self.assertEqual(result, expected)

        result = Device.parseVersionInfo('\tp\xfe\xb6\xb7x\x1dx\x00\x00o\r\x009\x10\x06\x00\x00#\x00\x02\x0bAlertMe.com\nPIR Device\n2010-11-24')
        expected = {
            'Version': 47030,
            'String': 'AlertMe.com\nPIR Device\n2010-11-24',
            'Manu':   'AlertMe.com',
            'Type':   'PIR Device',
            'Date':   '2010-11-24'
        }
        self.assertEqual(result, expected)

    def test_parseRangeInfo(self):
        result = Device.parseRangeInfo('\t+\xfd\xc5w')
        expected = 197
        self.assertEqual(result, expected)

    def test_receiveMessage(self):
        zb = None
        message = {   
            'cluster':          '\x00\xf6',
            'dest_endpoint':    '\x02',
            'id':               'rx_explicit',
            'options':          '\x01',
            'profile':          '\xc2\x16',
            'rf_data':          '\tp\xfe\x9f\x88\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26',
            'source_addr':      '\x88\x9f',
            'source_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8',
            'source_endpoint':  '\x02'
        }
        device = Device(zb, message['source_addr_long'])
        device.receiveMessage(message)
        result = device.getType()
        expected = 'SmartPlug'
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
