#! /usr/bin/python
"""
test_fake.py

By Paul Malmsten, 2010
pmalmsten@gmail.com

Tests fake device objects for proper functionality.
"""
import unittest
from mock_serial import Serial

class TestFakeSerialRead(unittest.TestCase):
    """
    Fake Serial class should work as intended to emluate reading from a serial port.
    """

    def setUp(self):
        """
        Create a fake read device for each test.
        """
        self.device = Serial()
        self.device.set_read_data("test")

    def test_read_single_byte(self):
        """
        Reading one byte at a time should work as expected.
        """
        self.assertEqual(self.device.read(), 't')
        self.assertEqual(self.device.read(), 'e')
        self.assertEqual(self.device.read(), 's')
        self.assertEqual(self.device.read(), 't')
        
    def test_read_multiple_bytes(self):
        """
        Reading multiple bytes at a time should work as expected.
        """
        self.assertEqual(self.device.read(3), 'tes')
        self.assertEqual(self.device.read(), 't')
        
    def test_write(self):
        """
        Test serial write function.
        """
        self.device.write("Hello World")
        self.assertEqual(self.device.get_data_written(), "Hello World")

    def test_open(self):
        """
        Test open(), close() and isOpen() functions.
        """
        self.device.open()
        self.assertEqual(self.device.isOpen(), True)
        self.device.close()
        self.assertEqual(self.device.isOpen(), False)

    def test_get_settings_dict(self):
        """
        Test getSettingsDict() function returns dictionary of settings.
        """
        expected = {
            'timeout': 1,
            'parity': 'N',
            'baudrate': 19200,
            'bytesize': 8,
            'stopbits': 1,
            'xonxoff': 0,
            'rtscts': 0
        }
        self.assertEqual(self.device.getSettingsDict(), expected)

    if __name__ == '__main__':
        unittest.main(verbosity=2)