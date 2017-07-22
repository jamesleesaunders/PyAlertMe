#! /usr/bin/python
"""
test_zbsensor.py

By James Saunders, 2017

Tests PyAlertMe Module.
"""
import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial


class TestZBSensor(unittest.TestCase):
    """
    Test PyAlertMe ZBSensor Class.
    """

    def setUp(self):
        """
        Create a node object for each test.
        """
        self.ser = Serial()
        self.device_obj = ZBSensor(self.ser)

    def tearDown(self):
        """
        Teardown node object.
        """
        self.device_obj.halt()

    def test_generate_type_update(self):
        """
        Test Generate Type Update.
        """
        result = self.device_obj.message_version_info_update()
        expected = {
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': b'\xc2\x16',
            'data': b'\tq\xfe90\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bPyAlertMe\nZBSensor\n2017-01-01'
        }
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)