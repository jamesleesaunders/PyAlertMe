#!/usr/bin/python

# Filename:    smartplug.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2017 James Saunders
# License:     MIT
# Version:     0.1.2

from flask import Flask, jsonify, abort, make_response, request

API_NAME    = 'pialertme'
API_VERSION = '1.0'
API_BASE    = '/' + API_NAME + '/api/v' + API_VERSION

app = Flask(__name__)

nodes = [{
    "id": "91bcbaea-0ed7-4216-9b7a-351bb6f8ac26",
    "name": "ActivePlug",
    "nodeType": "http://alertme.com/schema/json/node.class.smartplug.json#",
    "lastSeen": 1465759225444,
    "createdOn": 1461790278989,
    "attributes": {
        "lastSeen": {
            "reportedValue": "2016-06-12T19:10:39.519+0000",
            "reportReceivedTime": 1465758664240
        },
        "state": {
            "reportedValue": "OFF",
            "targetValue": "ON",
            "reportReceivedTime": 1465759147698,
            "targetSetTime": 1465509783258,
            "targetExpiryTime": 1465510083258,
            "targetSetTXId": "5e096157-07b3-4fd9-b162-23dbf43e7bb7",
            "propertyStatus": "COMPLETE"
        },
        "model": {
            "reportedValue": "SLR1",
            "reportReceivedTime": 1465148470959
        },
        "RSSI": {
            "reportedValue": -40,
            "reportReceivedTime": 1465151300198
        },
        "hwVersion": {
            "reportedValue": 1,
            "reportReceivedTime": 1464554457247
        },
        "manufacturer": {
            "reportedValue": "Computime",
            "reportReceivedTime": 1465148470959
        }
    }
}]


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)


@app.route(API_BASE + '/nodes', methods=['GET'])
def get_nodes():
    return jsonify({'nodes': nodes})


@app.route(API_BASE + '/nodes/<string:node_id>', methods=['GET'])
def get_node(node_id):
    node = [node for node in nodes if node['id'] == node_id]
    if len(node) == 0:
        abort(404)
    return jsonify(node[0])


@app.route(API_BASE + '/nodes/<string:node_id>', methods=['PUT'])
def update_node(node_id):
    if not request.json:
        abort(400)
    node = [node for node in nodes if node['id'] == node_id]
    if len(node) == 0:
        abort(404)
        
    return jsonify(request.json['nodes'][0]['attributes']), 200




if __name__ == '__main__':
    app.run(debug=True)