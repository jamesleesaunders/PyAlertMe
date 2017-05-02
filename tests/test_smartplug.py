import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestSmartPlug(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.device_obj = SmartPlug()
        self.device_obj.start(self.ser)
        self.device_obj.set_addr_long(b'\x00\x1E\x5E\x09\x02\x14\xC5\xAB')

    def tearDown(self):
        self.device_obj.halt()

    def test_generate_type_update(self):
        result = self.device_obj.generate_type_update()
        expected = {
            'description': 'Type Info',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': b'\xc2\x16',
            'data': b'\tq\xfe90\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bPyAlertMe\nSmartPlug\n2017-01-01'
        }
        self.assertEqual(result, expected)

    def test_state_change(self):
        message_on = {
            'cluster': b'\x00\xee',
            'dest_endpoint': b'\x02',
            'id': 'rx_explicit',
            'options': b'\x01',
            'profile': b'\xc2\x16',
            'rf_data': b'\x11\x00\x02\x01\x01',
            'source_addr': b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint': b'\x02'
        }
        self.device_obj.receive_message(message_on)
        self.assertEqual(self.device_obj.relay_state, True)

        message_off = {
            'cluster': b'\x00\xee',
            'dest_endpoint': b'\x02',
            'id': 'rx_explicit',
            'options': b'\x01',
            'profile': b'\xc2\x16',
            'rf_data': b'\x11\x00\x02\x00\x01',
            'source_addr': b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint': b'\x02'
        }
        self.device_obj.receive_message(message_off)
        self.assertEqual(self.device_obj.relay_state, False)

    def test_generate_state_update(self):
        self.device_obj.relay_state = 1
        result = self.device_obj.generate_relay_state_update()
        expected = {
            'profile': b'\xc2\x16',
            'description': 'Switch State Update',
            'src_endpoint': b'\x00',
            'cluster': b'\x00\xee',
            'data': b'\th\x80\x07\x01',
            'dest_endpoint': '\x02'
        }
        self.assertEqual(result, expected)
        self.device_obj.relay_state = 0
        result = self.device_obj.generate_relay_state_update()
        expected = {
            'profile': b'\xc2\x16',
            'description': 'Switch State Update',
            'src_endpoint': b'\x00',
            'cluster': b'\x00\xee',
            'data': b'\th\x80\x06\x00',
            'dest_endpoint': b'\x02'
        }
        self.assertEqual(result, expected)

    def test_parse_relay_state_change(self):
        result = SmartPlug.parse_relay_state_request(b'\x11\x00\x02\x01\x01')
        self.assertEqual(result, 1)
        result = SmartPlug.parse_relay_state_request(b'\x11\x00\x02\x00\x01')
        self.assertEqual(result, 0)

    def test_send_message(self):
        message = {
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'source_addr': b'\x88\x9f',
            'cluster': b'\x00\xee',
            'rf_data': b'\x11\x00\x01\x01',
            'dest_endpoint': b'\x02',
            'id': 'rx_explicit',
            'options': b'\x01',
            'profile': b'\xc2\x16',
            'src_endpoint': b'\x02'
        }
        self.device_obj.receive_message(message)
        result = self.ser.get_data_written()
        expected = b'~\x00\x19}1\x00\x00\ro\x00\x03\xbb\xb9\xf8\x88\x9f\x00\x02\x00\xee\xc2\x16\x00\x00\th\x80\x06\x00\x1d'
        self.assertEqual(result, expected)

    def test_generate_power_factor(self):
        self.device_obj.set_power_demand(0)
        result = self.device_obj.generate_power_demand_update()
        expected = {
            'description': 'Current Power Demand',
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xef',
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'data': b'\tj\x81\x00\x00'
        }
        self.assertEqual(result, expected)

        self.device_obj.set_power_demand(60)
        result = self.device_obj.generate_power_demand_update()
        expected = {
            'description': 'Current Power Demand',
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xef',
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'data': b'\tj\x81<\x00'
        }
        self.assertEqual(result, expected)

        self.device_obj.set_power_demand(22.4)
        result = self.device_obj.generate_power_demand_update()
        expected = {
            'description': 'Current Power Demand',
            'profile': b'\xc2\x16',
            'cluster': b'\x00\xef',
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'data': b'\tj\x81\x16\x00'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)