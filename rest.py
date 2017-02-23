#!/usr/bin/python

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
logger = logging.getLogger('pihive')
logger.setLevel(logging.DEBUG)

# Speficy log message format
formatter = logging.Formatter('%(asctime)s %(levelname)-3s %(module)-5s %(message)s')

# create console handler and set level to info
#sh = logging.StreamHandler()
#sh.setLevel(logging.DEBUG)
#sh.setFormatter(formatter)
#logger.addHandler(sh)

# create debug file handler and set level to debug
fh = logging.FileHandler("debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)


API_NAME    = 'pialertme'
API_VERSION = '1.0'
API_BASE    = '/' + API_NAME + '/api/v' + API_VERSION


# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
XBEE_BAUD = 9600
serialObj = serial.Serial(XBEE_PORT, XBEE_BAUD)

hubObj = Hub(serialObj)
hubObj.discovery()

app = Flask(__name__)

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)


@app.route(API_BASE + '/nodes', methods=['GET'])
def get_nodes():
    nodes = hubObj.list_nodes()
    return jsonify({'nodes': nodes})


@app.route(API_BASE + '/nodes/<string:node_id>', methods=['GET'])
def get_node(node_id):
    nodes = hubObj.list_nodes()

    matches = [node for node in nodes if node['id'] == node_id]
    if len(matches) == 0:
        abort(404)
    node = matches[0]
    return jsonify(node)


@app.route(API_BASE + '/nodes/<string:node_id>', methods=['PUT'])
def update_node(node_id):
    # If the request is not JSON error 400 Bad Request
    if not request.json or not request.json['nodes'][0].has_key('attributes'):
        abort(400)

    nodes = hubObj.list_nodes()

    # Check requested node exists
    for node_index, node in enumerate(nodes):
        if node['id'] == node_id:
            # Loop round attribute update request updating values
            for attribute in request.json['nodes'][0]['attributes']:
                if nodes[node_index]['attributes'].has_key(attribute):
                    for key in request.json['nodes'][0]['attributes'][attribute]:
                        nodes[node_index]['attributes'][attribute][key] = request.json['nodes'][0]['attributes'][attribute][key]
                        hubObj.command(node_index, 'state', key)

                else:
                    abort(404)

            return jsonify(node), 200

    # Node not found error 404 Not Found
    abort(404)

@app.route(API_BASE + '/discovery', methods=['POST'])
def discovery():
    hubObj.discovery()
    return jsonify({'discovery': 1})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)