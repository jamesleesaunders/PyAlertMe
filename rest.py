#!/usr/bin/python
# coding: utf-8

# Filename:    rest.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2017 James Saunders
# License:     MIT
# Version:     0.1.2

from flask import Flask, jsonify, abort, make_response, request
import serial
import time
import logging
import sys
from classes import *
import pprint

pp = pprint.PrettyPrinter(indent=4)
logger = logging.getLogger('py-alertme')
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

API_NAME    = 'pyalertme'
API_VERSION = '1.0'
API_BASE    = '/' + API_NAME + '/api/v' + API_VERSION


# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
XBEE_BAUD = 9600
serialObj = serial.Serial(XBEE_PORT, XBEE_BAUD)

hubObj = Hub(serialObj)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = True

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)


@app.route(API_BASE + '/nodes', methods=['GET'])
def get_nodes():
    nodes = hubObj.get_nodes()
    for id, node in nodes.iteritems():
        nodes[id]['AddressLong'] = ''
        nodes[id]['AddressShort'] = ''
    return jsonify({'nodes': nodes})

@app.route(API_BASE + '/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    node = hubObj.get_node(node_id)

    if node:
        # Blank out the addresses for now
        node['AddressLong'] = ''
        node['AddressShort'] = ''
        return jsonify(node)
    else:
        abort(404)

@app.route(API_BASE + '/nodes/<string:node_id>', methods=['PUT'])
def update_node(node_id):
    # If the request is not JSON error 400 Bad Request
    if not request.json or not request.json['nodes'][0].has_key('attributes'):
        abort(400)

    nodes = hubObj.get_nodes()

    # Check requested node exists
    for node_index, node in enumerate(nodes):
        if node['id'] == node_id:
            # Loop round attribute update request updating values
            for attribute in request.json['nodes'][0]['attributes']:
                if nodes[node_index]['attributes'].has_key(attribute):
                    for key in request.json['nodes'][0]['attributes'][attribute]:
                        nodes[node_index]['attributes'][attribute][key] = request.json['nodes'][0]['attributes'][attribute][key]
                        hubObj.send_state_request(node_index, '')

                else:
                    abort(404)

            return jsonify(node), 200

    # Node not found error 404 Not Found
    abort(404)

@app.route(API_BASE + '/discovery', methods=['POST'])
def discovery():
    hubObj._discovery()
    return jsonify({'discovery': 1})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)