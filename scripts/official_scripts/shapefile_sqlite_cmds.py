#!/usr/bin/env python
# Kyle Fitzsimmons 2013

import os.path
import sqlite3
import osgeo.ogr
from collections import OrderedDict
import re

from pprint import pprint

def init_database(database_name):
    '''Initiate database connection'''
    if not os.path.exists(database_name):
        print "Database does not exist. Creating new database file..."
    conn = sqlite3.connect(database_name)
    c = conn.cursor()
    conn.text_factory = str # magically accounts for our unicode strings
    return (conn, c)

def get_table_structure(c, table_name):
    '''Returns master sqlite entry describing how database was created with 1st entry as replaceable table name'''
    table_structure_tuple = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=\'" + table_name + "\'").fetchone()
    if table_structure_tuple:
        table_structure = table_structure_tuple[0]
        table_structure = table_structure.replace(",0", "")
        # Copy everything after the table name (columns and types)
        ## done string slicing because regex "look-behind requires fixed-width pattern"
        leading_junk = len(re.match('''CREATE TABLE ['\"\''].*?['\'\"'].*?\(''', table_structure).group())
        # split the string into a list of column names/types, strip the remaining whitespace
        raw_column_properties1 = [entry.strip() for entry in table_structure[leading_junk:-1].split(',') if entry != '']
        raw_column_properties2 = [entry.rstrip(",") for entry in raw_column_properties1]
        column_properties = [tuple(entry.split()) for entry in raw_column_properties2]
        return column_properties
    else:
        print "No existing table \'" + table_name + "\' found."

def duplicate_table(database_fn, old_table, new_table):
    '''Creates a duplicate of a specified table in the same database'''
    (conn, c) = init_database(database_fn)
    print "Retrieving old table structure..."
    old_table_structure = get_table_structure(c, old_table)
    num_columns = len(old_table_structure)
    sql_columns = "( "
    for index, column in enumerate(old_table_structure):
        sql_columns = sql_columns + column[0] + " " + column[1]
        if index + 1 != num_columns:
            sql_columns = sql_columns + ", "
    sql_columns = sql_columns + " )"
    print "Creating new table..."
    create_sql = "CREATE TABLE \'" + new_table + "\' " + sql_columns
    c.execute(create_sql)
    print "Copying information..."
    c.execute("INSERT INTO " + new_table + " SELECT * FROM " + old_table)
    conn.commit()
    conn.close()
    print "Table duplication complete!"
    return

def copy_table(from_database, from_table, to_database, to_table):
    '''Copies tables from multiple databases into one'''
    (conn1, c1) = init_database(from_database)
    (conn2, c2) = init_database(to_database)
    # Check if a to_table exists with the same name in the new db
    existing_table = c2.execute("SELECT name FROM sqlite_master WHERE type='table' and name=\'" + to_table + "\'").fetchall()
    # Drop table if exists (user confirmed)
    if existing_table:
        drop_table_reply = raw_input("A table already exists in the source db by the same name. Overwrite? (press 'Y' or anything else to cancel): ")
        if drop_table_reply.lower() in ['y', 1, '1', 'yes']:
            c2.execute('DROP TABLE ' + to_table)
        else:
            print 'Quitting...'
            conn1.close()
            conn2.close()
            return
    else:
        print "No existing table '%s' found, continuing..." % to_table
    # Duplicate table structure in new database
    old_table_structure = get_table_structure(c1, from_table)
    c2.execute(old_table_structure[0] + to_table + old_table_structure[2])
    # Get columns and copy the data over
    table_attributes = c1.execute("PRAGMA table_info(" + from_table + ")").fetchall()
    columns_tuple = tuple([attribute[1].encode('utf-8') for attribute in table_attributes])
    table1 = c1.execute("SELECT * FROM " + from_table).fetchall()
    column_names = str(columns_tuple).replace("'", "")
    insert_sql = "INSERT INTO %s %s VALUES (%s)" % (from_table, column_names, ','.join(['?'] * len(table1[0])))
    c2.executemany(insert_sql, table1)
    conn2.commit()
    conn1.close()
    conn2.close()
    return

def detect_db_type(input_object):
    '''Determines the type of object returned by a shapefile the type for an sqlite table'''
    if isinstance(input_object, int):
        return 'INTEGER'
    elif isinstance(input_object, float):
        return 'REAL'
    elif isinstance(input_object, str):
        return 'TEXT'
    else:
        return 'BLOB'

def dbf_to_db_table(dbf, database):
    '''Convert .dbf file to an SQLite table'''
    dbf_data = osgeo.ogr.Open(dbf)
    layer = dbf_data.GetLayer()
    table_name = layer.GetName()
    fields = layer.GetFeature(0)
    num_fields = fields.GetFieldCount()
    # Check to see if output table already exists in database
    (conn, c) = init_database(database)
    existing_table = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=\'" + table_name + "\'").fetchone()
    if existing_table:
        drop_table_reply = raw_input("Table for .dbf already exists. Overwrite? (press 'Y' or any other key to cancel): ")
        if drop_table_reply.lower() in ['y', 1, '1', 'yes']:
            c.execute('DROP TABLE ' + table_name)
        else:
            print 'Quitting...'
            c.close()
            return        
    feature_rows = []
    # Copy attribute rows from .dbf to memory
    for index in xrange(layer.GetFeatureCount()):
        feature = layer.GetFeature(index)
        row = tuple([feature.GetField(index) for index in xrange(num_fields)])
        feature_rows.append(row)
    # Check if features match the input expected by SQLite3 wrapper
    if isinstance(feature_rows, list) and isinstance(feature_rows[0], tuple):
        columns_tuple = tuple(fields.keys())
        # Determine schema and create output table in SQLite db
        column_types_list = []
        for column_index in xrange(0, len(columns_tuple)):
            column_name = columns_tuple[column_index]
            column_types_list.append(column_name + " " + detect_db_type(feature_rows[0][column_index]))
        column_types = str(tuple(column_types_list)).replace("'", "")
        create_sql = "CREATE TABLE \'" + table_name + "\' " + column_types
        c.execute(create_sql)
        # Copy .dbf attribute table into new db table
        column_names = str(columns_tuple).replace("'", "")
        insert_sql = "INSERT INTO %s %s VALUES (%s)" % (table_name, column_names,','.join(['?'] * len(feature_rows[0])))
        c.executemany(insert_sql, feature_rows)
        conn.commit()
        conn.close()
    else:
        print "Error: .dbf returned rows of wrong format"
        # No commits to db
        conn.close()
    return

def dbf_types_to_sqlite(table_structure):
    '''Converts shapefile fields to their appropriate sqlite counterpart'''
    fixed_schema = []
    for field in table_structure:
        # add various fields to fix here
        if "VARCHAR" in field[1]:
            field = (field[0].strip('\'\"'), "TEXT")
            fixed_schema.append(field)
        elif "PRIMARY" in field[0] and "KEY" in field[1]:
            continue
        else:
            field = (field[0].strip('\'\"'), field[1].strip('\'\"'))
            fixed_schema.append(field)
    return fixed_schema

def join_to_new_table(database_fn, table_to_join, table_get_join, match_column, new_table_name):
    '''Executes an SQL 'INNER JOIN' between two tables to a new one'''
    (conn, c) = init_database(database_fn)
    match_column1 = table_to_join + "." + match_column
    match_column2 = table_get_join + "." + match_column
    table1_schema = get_table_structure(c, table_to_join)
    table2_schema = get_table_structure(c, table_get_join)
    # Create the schema for creating the output table
    print 'Determining new table schema...'
    new_columns_schema = []
    for schema in [table2_schema, table1_schema]:
        schema = dbf_types_to_sqlite(schema)
        for field in schema:
            field_name = field[0].strip('\'"')
            # Check for duplicates and append "_1" to field name if found
            matching_fields = []
            for field_tuple in new_columns_schema:
                f = field_tuple[0]
                if field_name in f:
                    matching_fields.append(field_tuple)
            dup_list = [f[0] for f in matching_fields if '__dup' in f[0]]
            if matching_fields:
                if dup_list:
                    index = int(sorted(dup_list)[-1].split('__dup')[-1])
                    dup_ext = '__dup' + str(index + 1)
                else:
                    dup_ext = '__dup1'
                duplicate_field = (field_name + dup_ext, field[1])
                new_columns_schema.append(duplicate_field)
            else:
                new_columns_schema.append(field)
    # Create a properly formatted SQL string from the retrieved column properties
    new_columns_tuple = tuple(new_columns_schema)
    new_columns_sql = '( '
    for index, column in enumerate(new_columns_tuple):
        new_columns_sql = new_columns_sql + column[0] + " " + column[1]
        if column[1] == 'TEXT':
            new_columns_sql = new_columns_sql + " collate nocase"
        if index + 1 != len(new_columns_tuple):
            new_columns_sql = new_columns_sql + ", "
    new_columns_sql = new_columns_sql + " )"
    # Create the output table and copy data over
    print 'Creating the new table...'
    c.execute("CREATE TABLE \'" + new_table_name + "\' " + new_columns_sql)
    print 'Joining and copying data to new table...'
    join_and_copy_sql = "INSERT INTO {} SELECT * FROM {} INNER JOIN {} WHERE {}={}".format(new_table_name, table_get_join, table_to_join, match_column2, match_column1)
    c.execute(join_and_copy_sql)
    conn.commit()
    conn.close()
    print 'Join complete!'
    return


# DUPLICATING A TABLE
database_filename = 'test.sqlite'
old_table_name = 'test_join2'
new_table_name = 'joined_data'
duplicate_table(database_filename, old_table_name, new_table_name)

# COPY TABLE TO NEW DB
# from_database = 'DOM_B72LIEN1_TAB.sqlite'
# from_table = 'dom_b72lien1_tab'
# to_database = 'full_shapefile_data.sqlite'
# to_table = 'dom_b72lien1_tab'
# copy_table(from_database, from_table, to_database, to_table)

# SHAPEFILE .DBF TO SQLITE
# dbf_filename = 'MLS_mtl_only_4269.dbf'
# database_filename = 'abcdefg.sqlite'
# dbf_to_db_table(dbf_filename, database_filename)

# JOIN TWO TABLES TO A NEW TABLE
# database_filename = 'test.sqlite'
# table_to_join = 'rol_b61_tab'
# table_get_join = 'test_join'
# match_column = 'mat18'
# new_table_name = 'test_join2'
# join_to_new_table(database_filename, table_to_join, table_get_join, match_column, new_table_name)