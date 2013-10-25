#!/usr/bin/env python
# Kyle Fitzsimmons 2013

import sqlite3
import os

class Database():
	def __init__(self):
		self.conn = None
		self.c = None

	def connect(self, database_name):
	    '''Initiate database connection'''
	    if not os.path.exists(database_name):
	        print "Database does not exist. Creating new database file..."
	    self.conn = sqlite3.connect(database_name)
	    self.c = self.conn.cursor()
	    self.conn.text_factory = str # magically accounts for our unicode strings

	def query(self, sql_command):
		'''Execute a query against the connected SQLite database'''
		self.c.execute(sql_command)

	def fetchone(self):
		return self.c.fetchone()

	def fetchall(self):
		return self.c.fetchall()