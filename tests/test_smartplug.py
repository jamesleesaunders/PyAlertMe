import sys

sys.path.insert(0, '../')

from classes import *
import unittest
from mock_serial import Serial

class TestSmartPlug(unittest.TestCase):

    def setUp(self):
        self.serialObj = Serial()
        self.deviceObj = SmartPlug(self.serialObj)

    def tearDown(self):
        self.deviceObj.halt()

    def test_get_type(self):

        result = self.deviceObj.get_type()
        expected = {
            'description': 'Type Info',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': b'\xc2\x16',
            'data': b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\nSmartPlug\n2013-09-26'
        }
        self.assertEqual(result, expected)

    def test_state_change(self):

        message_on = {
            'cluster':          b'\x00\xee',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\xc2\x16',
            'rf_data':          b'\x11\x00\x02\x01\x01',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint':     b'\x02'
        }
        self.deviceObj.receive_message(message_on)
        self.assertEqual(self.deviceObj.state, 1)

        message_off = {
            'cluster':          b'\x00\xee',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\xc2\x16',
            'rf_data':          b'\x11\x00\x02\x00\x01',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint':     b'\x02'
        }
        self.deviceObj.receive_message(message_off)
        self.assertEqual(self.deviceObj.state, 0)


    def test_send_message(self):

        message = {
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'source_addr':      b'\x88\x9f',
            'cluster':          b'\x00\xee',
            'rf_data':          b'\x11\x00\x01\x01',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\xc2\x16',
            'src_endpoint':     b'\x02'
        }
        self.deviceObj.receive_message(message)
        result = self.serialObj.get_data_written()
        expected = b'~\x00\x19\x11\x00\x00\ro\x00\x03\xbb\xb9\xf8\x88\x9f\x00\x02\x00\xee\xc2\x16\x00\x00\th\x80\x07\x01\x1b'
        self.assertEqual(result, expected)

    def test_get_state(self):
        self.deviceObj.state = 0
        result = self.deviceObj.get_state()
        expected = {
            'profile': '\xc2\x16',
            'description': 'Switch State',
            'src_endpoint': '\x00',
            'cluster': '\x00\xee',
            'data': '\th\x80\x07\x01',
            'dest_endpoint': '\x02'
        }
        self.assertEqual(result, expected)
        self.deviceObj.state = 1
        result = self.deviceObj.get_state()
        expected = {
            'profile': '\xc2\x16',
            'description': 'Switch State',
            'src_endpoint': '\x00',
            'cluster': '\x00\xee',
            'data': '\th\x80\x06\x00',
            'dest_endpoint': '\x02'
        }
        self.assertEqual(result, expected)

    def test_parse_switch_state_change(self):
        result = SmartPlug.parse_switch_state_change(b'\x11\x00\x02\x01\x01')
        self.assertEqual(result, 1)
        result = SmartPlug.parse_switch_state_change(b'\x11\x00\x02\x00\x01')
        self.assertEqual(result, 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)