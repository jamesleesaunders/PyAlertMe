import sys
sys.path.insert(0, '../')
from pyalertme import *
import unittest
from mock_serial import Serial

class TestNode(unittest.TestCase):

    def setUp(self):
        self.ser = Serial()
        self.node_obj = Node()
        self.node_obj.addr_long = b'\x00\x00\x00\x00\x00\x00\x00\x00'

    def test_pretty_mac(self):
        self.assertEqual(Node.pretty_mac(b'\x00\x1e\x5e\x09\x02\x14\xc5\xab'), '00:1e:5e:09:02:14:c5:ab', 'Test MAC 1')
        self.assertEqual(Node.pretty_mac(b'\x00\ro\x00\x03\xbb\xb9\xf8'), '00:0d:6f:00:03:bb:b9:f8', 'Test MAC 2')

    def test_set_attributes(self):
        attributes = {
            'type': 'Generic',
            'version': 12345,
            'manu': 'PyAlertMe',
            'manu_date': '2017-01-01'
        }
        self.node_obj.set_attributes(attributes)
        self.assertEqual(self.node_obj.type, 'Generic')
        self.assertEqual(self.node_obj.version, 12345)
        self.assertEqual(self.node_obj.manu, 'PyAlertMe')
        self.assertEqual(self.node_obj.manu_date, '2017-01-01')

    def test_set_get_attribute(self):
        self.node_obj.set_attribute('relay_state', 1)
        self.assertEqual(self.node_obj.relay_state, 1)
        self.assertEqual(self.node_obj.get_attribute('relay_state'), 1)

        self.node_obj.set_attribute('addr_short', b'\x00\x01')
        self.assertEqual(self.node_obj.addr_short, b'\x00\x01')
        self.assertEqual(self.node_obj.get_attribute('addr_short'), b'\x00\x01')

    def test_addr_tuple(self):
        self.node_obj.addr_long  = b'\x00\x1e\x5e\x09\x02\x14\xc5\xab'
        self.node_obj.addr_short = b'\x00\x01'
        self.assertEqual(self.node_obj.addr_tuple, (b'\x00\x1e\x5e\x09\x02\x14\xc5\xab', b'\x00\x01'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
