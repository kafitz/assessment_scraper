#!/usr/bin/env python
# Kyle Fitzsimmons 2013

import sqlite3
import os
import datetime

class Database(object):
	def __init__(self, database_name):
	    '''Initiate database connection'''
	    if not os.path.exists(database_name):
	        print "Database does not exist. Creating new database file..."
	    self.conn = sqlite3.connect(database_name)
	    self.c = self.conn.cursor()
	    self.conn.text_factory = str # magically accounts for our unicode strings
	    self.python_sqlite_types = {
	    	int: 'INTEGER',
	    	str: 'TEXT',
	    	float: 'REAL',
	    	datetime.datetime: 'NUMERIC',
	    	None: 'NULL'
	    }

	def query(self, sql_command):
		'''Execute a query against the connected SQLite database'''
		self.c.execute(sql_command)

	def fetchone(self):
		return self.c.fetchone()

	def fetchall(self):
		return self.c.fetchall()

	# def write_rows(self, table, input_rows):
	# 	'''Attempt to write rows (list of dicts as input) to specified table. If table does 
	# 	   not exist, deduce schema from first row. Otherwise, warn about incompatible data'''
	# 	   test_row = input_rows[0]
	# 	   