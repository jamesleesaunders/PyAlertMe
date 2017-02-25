#!/usr/bin/python
# coding: utf-8

import sqlite3

# Setup DB Connection
conn = sqlite3.connect('nodes.db')
print "Database successfully created"

# Create Nodes Table
conn.execute('''CREATE TABLE Nodes (
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
conn.execute('''CREATE UNIQUE INDEX AddressLong on Nodes (AddressLong);''')
print "Nodes table successfully created"

# Create Attributes Table
conn.execute('''CREATE TABLE Attributes (
    Id               INTEGER PRIMARY KEY AUTOINCREMENT,
    NodeId           INTEGER,
    Name             CHAR(20) NOT NULL,
    Value            CHAR(50) NOT NULL,
    Time             DATETIME NOT NULL
);''')
conn.execute('''CREATE UNIQUE INDEX Attribute on Attributes (NodeId, Name, Value, Time);''')
print "Attributes table successfully created"

# Close Up Shop
conn.close()