#!/usr/bin/python
# coding: utf-8

# Filename:    rest-example.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2017 James Saunders
# License:     MIT

import sys
sys.path.insert(0, '../')
from flask import Flask, jsonify, abort, make_response, request
import serial
from pyalertme import *
import logging
import pprint

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

# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-DN018OI6' # MacBook Serial Port
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)

hub_obj = ZBHub()
hub_obj.start(ser)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = True

API_NAME    = 'pyalertme'
API_VERSION = '1.0'
API_BASE    = '/' + API_NAME + '/api/v' + API_VERSION

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)

@app.route(API_BASE + '/nodes', methods=['GET'])
def get_nodes():
    nodes = hub_obj.list_devices()
    for id, node in nodes.iteritems():
        nodes[id]['AddressLong'] = ''
        nodes[id]['AddressShort'] = ''
    return jsonify({'Nodes': nodes})

@app.route(API_BASE + '/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    node = hub_obj.device_obj_from_id(node_id)

    if node:
        # Blank out the addresses for now
        node['AddressLong'] = ''
        node['AddressShort'] = ''
        return jsonify(node)
    else:
        abort(404)

@app.route(API_BASE + '/history/<int:node_id>', methods=['GET'])
def attribute_history(node_id):
    attrib_name = 'PowerFactor'
    history = hub_obj.get_node_attribute_history(node_id, attrib_name, 338083200, 1537228800)
    return jsonify(history)

@app.route(API_BASE + '/nodes/<int:node_id>', methods=['PUT'])
def update_node(node_id):
    # If the request is not JSON error 400 Bad Request
    if not request.json or not request.json['Nodes'][0].has_key('Attributes'):
        abort(400)

    node = hub_obj.device_obj_from_id(node_id)

    # Loop round attribute update request updating values
    for attribute in request.json['Nodes'][0]['Attributes']:
        if node['Attributes'].has_key(attribute):
            for key in request.json['Nodes'][0]['Attributes'][attribute]:
                value = request.json['Nodes'][0]['Attributes'][attribute][key]
                hub_obj.call_device_command(node_id, attribute, value)
        else:
            abort(404)

    node['AddressLong'] = ''
    node['AddressShort'] = ''
    return jsonify(node), 200

@app.route(API_BASE + '/discovery', methods=['POST'])
def discovery():
    hub_obj.discovery()
    return jsonify({'discovery': 1})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)