#!/usr/bin/python
# coding: utf-8

# Filename:    console.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2017 James Saunders
# License:     MIT

import sys
sys.path.insert(0, '../')
from commander import *
import serial
from pyalertme import *
import logging
import pprint

class TestCmd(Command):
    def do_discovery(self, *args):
        # Discovery
        hub_obj.discovery()
        return 'Discovery Started'

    def do_broadcast(self, *args):
        # Send broadcast
        message = hub_obj.get_action('routing_table_request')
        hub_obj.send_message(message, hub_obj.BROADCAST_LONG, hub_obj.BROADCAST_SHORT)
        return 'broadcast'

    def do_nodes(self, *args):
        if args[0] == 'list':
            # Construct a lise of nodes
            output = "List of Nodes: \n"

            nodes = hub_obj.get_nodes()
            for id, node in nodes.iteritems():
                output += str(id) + ". " + node['Type'] + " [" + node['Name'] + "] (" + Base.pretty_mac(
                    node['AddressLong']) + ")\n"

            return output

        if args[0].isdigit():
            node_id = int(args[0])

            if args[1] == "rename":
                # Concatenate all following params
                name = " ".join(map(lambda s: '"%s"' % s if ' ' in s else s, args[2:]))
                if name == '':
                    raise Exception('Name too short!')

                hub_obj.save_node_name(node_id, name)
                return 'Node: ' + str(node_id) + ' Renamed: ' + name

            if args[1] == "state":
                value = args[2]
                hub_obj.call_node_command(node_id, 'State', value)
                return 'Node: ' + str(node_id) + ' State Changed: ' + value

            if args[1] == "mode":
                value = args[2]
                hub_obj.call_node_command(node_id, 'Mode', value)
                return 'Node: ' + str(node_id) + ' Mode: ' + value

            if args[1] == "attributes":
                attrib_name = args[2]
                return hub_obj.get_node_attribute_history(node_id, attrib_name, 338083200, 1537228800)

            if args[1] == "type":
                message = hub_obj.generate_type_request_message()
                hub_obj.send_message(message, *hub_obj.node_id_to_addrs(node_id))
                return 'Type Request Sent'

            if args[1] == "detail":
                return hub_obj.get_node(node_id)

        return 'Unknown Argument'

    def do_halt(self, *args):
        # Close up shop
        hub_obj.halt()
        return Commander.Exit

    def do_echo(self, *args):
        return ' '.join(args)

    def do_raise(self, *args):
        raise Exception('Some Error')

if __name__ == '__main__':
    # Setup logging
    pp = pprint.PrettyPrinter(indent=4)
    logger = logging.getLogger('pyalertme')
    logger.setLevel(logging.DEBUG)

    # Specify log message format
    formatter = logging.Formatter('%(asctime)s %(levelname)-3s %(module)-5s %(message)s')

    # Create console handler and set level to info
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Create debug file handler and set level to debug
    fh = logging.FileHandler("debug.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Serial configuration
    XBEE_PORT = '/dev/tty.usbserial-A1014P7W'
    XBEE_BAUD = 9600
    ser = serial.Serial(XBEE_PORT, XBEE_BAUD)

    # Start hub
    hub_obj = Hub()
    hub_obj.start(ser)

    # Start commander
    cmd = Commander('PyAlertMe', cmd_cb=TestCmd())
    cmd.loop()

