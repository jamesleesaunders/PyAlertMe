import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestHub(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.hub_obj = Hub()
        self.hub_obj.start(self.ser)
        self.hub_obj.set_addr_long(b'\x00\x1E\x5E\x09\x02\x14\xC5\xAB')

    def tearDown(self):
        self.hub_obj.halt()

    def test_receive_message(self):
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
        result = self.hub_obj.get_nodes()
        expected = {
            '00:0d:6f:00:03:bb:b9:f8': {
                'ManufactureDate': '2013-09-26',
                'Manufacturer': 'AlertMe.com',
                'Type': 'SmartPlug',
                'Version': 20045,
                'AddressLong': '\x00\ro\x00\x03\xbb\xb9\xf8',
                'AddressShort': '\x88\x9f',
                'Attributes': {}
            }
        }

        self.assertEqual(result, expected)

    def test_endpoint_request(self):
        message = {
            'source_addr': b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint': b'\x02',
            'profile': b'\x00\x00',
            'cluster': b'\x00\x06',
            'dest_endpoint': b'\x02',
            'rf_data': b'',
            'id': 'rx_explicit',
            'options': b'\x01',
        }
        self.hub_obj.receive_message(message)
        result = self.ser.get_data_written()
        expected = b'~\x00\x19}1\x00\x00\ro\x00\x03\xbb\xb9\xf8\x88\x9f\x00\x02\x00\xf0\xc2\x16\x00\x00}1\x00\xfa\x00\x01\x06'
        self.assertEqual(result, expected)

    def test_generate_state_request(self):
        result = self.hub_obj.generate_state_request(1)
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xee',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x00\x02\x01\x01'
        }
        self.assertEqual(result, expected)

        result = self.hub_obj.generate_state_request(0)
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xee',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x00\x02\x00\x01'
        }
        self.assertEqual(result, expected)

        result = self.hub_obj.generate_state_request()
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xee',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x00\x01\x01'
        }
        self.assertEqual(result, expected)

    def test_generate_mode_change_request(self):
        result = self.hub_obj.generate_mode_change_request('Normal')
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xf0',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x00\xfa\x00\x01'
        }
        self.assertEqual(result, expected)

        result = self.hub_obj.generate_mode_change_request('RangeTest')
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xf0',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x00\xfa\x01\x01'
        }
        self.assertEqual(result, expected)

    def test_generate_version_info_request(self):
        result = self.hub_obj.generate_version_info_request()
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xf6',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x00\xfc'
        }
        self.assertEqual(result, expected)

    def test_generate_active_endpoints_request(self):
        source_addr_short = b'\x88\x9f'
        result = self.hub_obj.generate_active_endpoints_request(source_addr_short)
        expected = {
            'description': 'Active Endpoints Request',
            'profile': b'\x00\x00',
            'cluster': b'\x00\x05',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'data': b'\xaa\x9f\x88'
        }
        self.assertEqual(result, expected)

    def test_generate_match_descriptor_response(self):
        rf_data = b'\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        result = self.hub_obj.generate_match_descriptor_response(rf_data)
        expected = {
            'description': 'Match Descriptor Response',
            'profile': b'\x00\x00',
            'cluster': b'\x80\x06',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'data': b'\x03\x00\x00\x00\x01\x02'
        }
        self.assertEqual(result, expected)

    def test_generate_security_init(self):
        result = self.hub_obj.generate_security_init()
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x05\x00',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x80\x00\x00\x05'
        }
        self.assertEqual(result, expected)

    def test_generate_missing_link(self):
        result = self.hub_obj.generate_missing_link()
        expected = {
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xf0',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x119\xfd'
        }
        self.assertEqual(result, expected)


#def test_parse_version_info(self):
#    ser2 = Serial()
#    device_obj = Device()
#    device_obj.start(ser2)
#
#    message = device_obj.generate_version_info_request()
#    result = Hub.parse_version_info(message['data'])
#    expected = {
#        'Version': 12345,
#        'Manufacturer': 'PyAlertMe',
#        'Type': 'Generic Device',
#        'ManufactureDate': '2017-01-01'
#    }
#    self.assertEqual(result, expected)
#    device_obj.halt()

if __name__ == '__main__':
    unittest.main(verbosity=2)