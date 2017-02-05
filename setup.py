#!/usr/bin/python

import sqlite3

conn = sqlite3.connect('py-alertme.db')
print "Opened database successfully"

conn.execute('''CREATE TABLE Nodes (
    Id INT PRIMARY KEY      NOT NULL,
    Name           TEXT     NOT NULL,
    AddressLong    CHAR(50) NOT NULL,
    AddressShort   CHAR(50),
    Type           CHAR(50)
);''')

conn.execute('''CREATE TABLE Attributes (
    HubId          TEXT     NOT NULL,
    Attribute      CHAR(50) NOT NULL,
    Value          CHAR(50),
    Time           DATETIME
);''')

print "Tables created successfully"

conn.close()