#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('nodes.db')
print "Database successfully created"

conn.execute('''CREATE TABLE Node (
    Id               INTEGER PRIMARY KEY AUTOINCREMENT,
    AddressLong      BLOB NOT NULL,
    AddressShort     BLOB,
    Name             CHAR(50) DEFAULT '',
    Type             CHAR(50) DEFAULT '',
    Version          INTEGER,
    Manufacturer     CHAR(50) DEFAULT '',
    ManufactureDate  CHAR(10) DEFAULT '',
    FirstSeen        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastSeen         DATETIME,
    MessagesReceived INT DEFAULT 0
);''')
conn.execute('''CREATE UNIQUE INDEX AddressLong on Node (AddressLong);''')
print "Node table successfully created"

conn.execute('''CREATE TABLE NodeAttribute (
    Id               INTEGER PRIMARY KEY AUTOINCREMENT,
    NodeId           INTEGER,
    Attribute        CHAR(20) NOT NULL,
    Value            CHAR(50) NOT NULL,
    Time             DATETIME NOT NULL
);''')
print "NodeAttribute table successfully created"

conn.close()