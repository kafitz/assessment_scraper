#!/usr/bin/env python
# Kyle Fitzsimmons 2013

import sqlite3
import os
import datetime
from pprint import pprint

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
            unicode: 'TEXT',
            float: 'REAL',
            datetime.datetime: 'NUMERIC',
            type(None): 'NONE'
        }

    # read functions
    def query(self, sql_command):
        '''Execute a query against the connected SQLite database'''
        self.c.execute(sql_command)

    def fetchone(self):
        return self.c.fetchone()

    def fetchall(self):
        return self.c.fetchall()

    # write functions
    def make_table(self, table, columns):
        sql = 'CREATE TABLE {} ({})'.format(table, columns)
        self.query(sql)
        self.conn.commit()

    def add_table_column(self, table, column_name, db_type):
        return

    def write_rows(self, table, input_rows, field_order=None):
        '''Attempt to write rows (list of dicts as input) to specified table. If table does 
           not exist, deduce schema from first row. Otherwise, warn about incompatible data'''       
        test_entry = input_rows[0]
        # check if specified table exists
        self.query('''SELECT name FROM sqlite_master WHERE type='table' AND name='{}' '''.format(table))
        tbl_check = self.fetchone()
        if not tbl_check:
            columns = ''
            index = 0
            if field_order:
                for column_name in field_order:
                    columns += column_name + ' ' + self.python_sqlite_types[type(test_entry[column_name])]
                    index += 1
                    if index != len(test_entry):
                        columns += ', '
            else:
                for column_name, cell in test_entry.items():
                    columns += column_name + ' ' + self.python_sqlite_types[type(cell)]
                    index += 1
                    if index != len(test_entry):
                        columns += ', '
            self.make_table(table, columns)
        # if/when table exists, write rows
        if not field_order:
            self.query('''SELECT sql FROM sqlite_master WHERE type='table' and name='{}' '''.format(table))
            tbl_sql = self.fetchone()[0]
            schema = tbl_sql.split('(')[1]
            schema = schema.split(')')[0]
            schema_columns = schema.split(',')
            field_order = [column.split()[0] for column in schema_columns]
        entries = [tuple([row[field] for field in field_order]) for row in input_rows]
        values = '?,' * (len(field_order) - 1) + '?'
        insert_sql = '''INSERT INTO {} VALUES ({})'''.format(table, values)
        self.c.executemany(insert_sql, entries)
        self.conn.commit()
        return
