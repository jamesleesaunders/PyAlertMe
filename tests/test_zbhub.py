import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestZBHub(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.hub_ser = Serial()
        self.hub_obj = ZBHub(self.hub_ser)
        self.hub_obj.addr_long = b'\x00\x1e\x5e\x09\x02\x14\xc5\xab'
        self.hub_obj.addr_short = b'\x88\xd2'

        self.device_ser = Serial()
        self.device_obj = ZBDevice(self.device_ser)

    def tearDown(self):
        self.hub_obj.halt()
        self.device_obj.halt()

    def test_receive_message(self):
        # First, lets manually construct a Version message and send it into the Hub.
        message = {
            'cluster': b'\x00\xf6',
            'dest_endpoint': b'\x02',
            'id': 'rx_explicit',
            'options': b'\x01',
            'profile': b'\xc2\x16',
            'rf_data': b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26',
            'source_addr': b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint': b'\x02'
        }
        self.hub_obj.receive_message(message)
        result = self.hub_obj.list_devices()
        expected = {
            '00:0d:6f:00:03:bb:b9:f8': {
                'type': 'SmartPlug',
                'version': 20045,
                'manu': 'AlertMe.com'
            }
        }
        self.assertEqual(result, expected)

        # Next, lets get the class to generate a Version message and send it into the Hub.
        params = {
            'type': 'Generic',
            'version': 12345,
            'manu': 'PyAlertMe',
            'manu_date': '2017-01-01'
        }
        message = self.device_obj.get_message('version_info_update', params)
        message['id'] = 'rx_explicit'
        message['source_addr'] = b'\x88\xfd'
        message['source_addr_long'] = b'\x00\x0d\x6f\x00\x00\x00\xff\xff'
        message['rf_data'] = message['data']
        self.hub_obj.receive_message(message)
        result = self.hub_obj.list_devices()
        expected = {
            '00:0d:6f:00:03:bb:b9:f8': {
                'type': 'SmartPlug',
                'version': 20045,
                'manu': 'AlertMe.com'
            },
            '00:0d:6f:00:00:00:ff:ff': {
                'type': 'Generic',
                'version': 12345,
                'manu': 'PyAlertMe'
            }
        }
        self.assertEqual(result, expected)

    def test_mock_serial(self):
        message = {
            'source_addr': b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint': b'\x00',
            'profile': b'\x00\x00',
            'cluster': b'\x00\x06',
            'dest_endpoint': b'\x00',
            'rf_data': b'\x04',
            'id': 'rx_explicit',
            'options': b'\x01',
        }
        self.hub_obj.receive_message(message)
        result = self.hub_ser.get_data_written()
        expected = b'~\x00\x19}1\x00\x00\ro\x00\x03\xbb\xb9\xf8\x88\x9f\x02\x02\x00\xf0\xc2\x16\x00\x00}1\x00\xfa\x00\x01\x04'
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)