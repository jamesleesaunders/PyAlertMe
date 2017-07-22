#! /usr/bin/python
"""
test_zbdevice.py

By James Saunders, 2017

Tests PyAlertMe Module.
"""
import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial


class TestZBDevice(unittest.TestCase):
    """
    Test PyAlertMe ZBDevice Class.
    """
    def setUp(self):
        """
        Create a node object for each test.
        """
        self.ser = Serial()
        self.device_obj = ZBDevice(self.ser)

    def tearDown(self):
        """
        Teardown node object.
        """
        self.device_obj.halt()

    def test_message_range_update(self):
        """
        Test Range Update Message.
        """
        self.device_obj.rssi = 0
        result = self.device_obj.message_range_update()
        expected = {
            'cluster': b'\x00\xf6',
            'data': b'\t+\xfd\x00\x00',
            'dest_endpoint': b'\x02',
            'profile': b'\xc2\x16',
            'src_endpoint': b'\x02'
        }
        self.assertEqual(result, expected)

        self.device_obj.rssi = 197
        result = self.device_obj.message_range_update()
        expected = {
            'cluster': b'\x00\xf6',
            'data': b'\t+\xfd\xc5\x00',
            'dest_endpoint': b'\x02',
            'profile': b'\xc2\x16',
            'src_endpoint': b'\x02'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
