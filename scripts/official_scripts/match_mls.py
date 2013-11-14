#!/usr/bin/env python
# 2013 Kyle Fitzsimmons

import DataParser as DP
from DatabaseConns import Database
from OutputCSV import OutputCSV
from unidecode import unidecode
from pprint import pprint
import time

### GLOBALS
INPUT_SPREADSHEET = '../../data/input/kyle3.xls'
LOOKUP_DB = '../../data/official_data/test.sqlite'
YEAR = 2009

db = Database(LOOKUP_DB)

def db_search_address(table, sql_criteria):
    '''Try to find the address in database by exact match'''
    # concatenate the sql string to execute on the database
    # '''SELECT * FROM 'table' WHERE "foo"="132" and "bar"="MAIN"'''
    sql_command = '''SELECT * FROM '{}' WHERE'''.format(table)
    for index, criteria in enumerate(sql_criteria):
        sql_command = sql_command + ''' "{}"="{}"'''.format(criteria[0], criteria[1])
        if index + 1 != len(sql_criteria):
            sql_command = sql_command + " AND"
    db.query(sql_command)
    return db.fetchall()

def db_match_suite(street_parameters, db_matches):
    '''If multiple addresses match SQL query, search these for a matching suite number'''
    matching_result = None
    for match in db_matches:
        if street_parameters['suite_num'] == match[31]:
            matching_result = match
    return matching_result

def db_search_entire_street(table, street_parameters):
    '''If exact match fails: search for address in the full range of 
    addresses for the particular street'''
    start_time = time.time()
    street_name = street_parameters['street_nominal']
    street_number_lower = street_parameters['street_number_lower']
    print time.time() - start_time
    sql_command = '''SELECT "b72m1", "b72a1" FROM '{}' WHERE "b72voie1"="{}"'''.format(table, street_name)
    print sql_command
    db.query(sql_command)
    possible_pairs = []
    print time.time() - start_time
    for address_pair in sorted(db.fetchall()):
        # ignore tuples that do not form an address range for a property
        if address_pair[1] == 0:
            continue
        # find all tuple pairs that contain the specified addresses
        if address_pair[0] <= street_number_lower and address_pair[1] >= street_number_lower:
            possible_pairs.append(address_pair)
    matched_address_pair = None
    print time.time() - start_time
    for matching_pair in possible_pairs:
        # generate the range of possible addresses for a certain property (inclusive of the last address)
        address_range = range(matching_pair[0], matching_pair[1], 2)
        address_range.append(matching_pair[1])
        if street_number_lower in [str(x) for x in address_range]:
            matched_address_pair = matching_pair
            break
    print time.time() - start_time
    if matched_address_pair:
        street_parameters['street_number_lower'] = matched_address_pair[0]
        street_parameters['street_number_upper'] = matched_address_pair[1]
        return street_parameters
    else:
        return None

def get_query_response(street_parameters):
    '''Script-specific function for matching database response to dict variables'''
    def _map_to_dict(db_entry):
        result_dict = {}
        result_dict['start_address'] = db_entry[24]
        result_dict['db_suite'] = db_entry[31]
        result_dict['end_address'] = db_entry[26]
        result_dict['street_code'] = db_entry[28]
        result_dict['street_name'] = db_entry[30]
        result_dict['land_value'] = db_entry[45]
        result_dict['building_value'] = db_entry[46]
        result_dict['total_value'] = db_entry[47]
        return result_dict
    ## SEARCH FOR XLS ADDRESS NUMBER AS BOTH START AND END (if needed) ADDRESS
    table_name = 'joined_data'
    # create a list of tuples to specifiy the db search criteria
    sql_criteria = [('b72voie1', street_parameters['street_nominal'].upper()),
                    ('b72m1', street_parameters['street_number_lower'])]   
    if street_parameters['type_code']: # street type
        sql_criteria.append(('b72r1', street_parameters['type_code']))
    r = db_search_address(table_name, sql_criteria)
    if not r:
        # create a list of tuples to specifiy the db search criteria
        sql_criteria = [('b72voie1', street_parameters['street_nominal'].upper()),
                        ('b72a1', street_parameters['street_number_lower'])]   
        if street_parameters['type_code']: # street type
            sql_criteria.append(('b72r1', street_parameters['type_code']))
        r = db_search_address(table_name, sql_criteria)
    # single address match
    if len(r) == 1:
        r = r[0]
        result = _map_to_dict(r)
        print "Address match: {}-{} {}".format(result['start_address'],
                                            result['end_address'],
                                            result['street_name'])
        return result
    # multiple results for a single address, narrow by suite
    elif len(r) > 1:
        matched_r = db_match_suite(street_parameters, r)
        if matched_r:
            result = _map_to_dict(matched_r)
            print "Suite match: {}-{} {}, suite {}".format(result['start_address'],
                                                        result['end_address'],
                                                        result['street_name'],
                                                        result['db_suite'])
            return result
        else:
            print "Multiple results returned for address, no matching suite found."
    # no results, look for address in db address range (e.g., 3564 in a building range of 3562-3566)
    else:
        pass
        # updated_parameters = db_search_entire_street(table_name, street_parameters)
        # if updated_parameters:
        #     recursive_result = get_query_response(updated_parameters)
        #     print "Found address pair: {}-{} {}".format(updated_parameters['street_number_lower'], updated_parameters['street_number_upper'], updated_parameters['street_nominal'])
        #     return recursive_result
        # else:
        #     print "No address match found: {} {}".format(street_parameters['street_number_lower'], street_parameters['street_nominal'])
    return None




### MAIN
row_dicts = DP.get_xls_dict(INPUT_SPREADSHEET, YEAR)
print 'Rows for %s:' % (YEAR,), len(row_dicts)
index = 0
matches = 0
output_rows = []
missed_addresses = []
row_dicts = [row for row in row_dicts if row['prix_vendu'] != ''] # remove rows with blank sales price
for row in row_dicts:
    street_parameters = DP.get_street_parameters(row)
    # skip inputs without a designated street address
    if not street_parameters['street_number_lower'] and not street_parameters['street_number_upper']:
        continue
    if not street_parameters['street_number_lower']:
        continue    
    print "Search:", "{}-{} {}, suite {}".format(street_parameters['street_number_lower'],
                                                    street_parameters['street_number_upper'],
                                                    street_parameters['street_nominal'],
                                                    street_parameters['suite_num'])
    if street_parameters['street_number_upper'] and not street_parameters['street_number_lower']:
        street_parameters['street_number_lower'] = street_parameters['street_number_upper']
    saved_street_part = None
    if street_parameters['joining_article']:
        saved_street_part = street_parameters['street_nominal']
        street_parameters['street_nominal'] = street_parameters['joining_article'].upper() + " " + street_parameters['street_nominal']

    result = get_query_response(street_parameters)
    street_parts = street_parameters['street_nominal'].split()
    # special cases for double query
    if not result:
        # addresses like "25E AVENUE"--attempt scrape for both "25E AVENUE" and "25E"
        if len(street_parts) > 1 and street_parts[-1].upper() == 'AVENUE':
            print 'Trying AVENUE query...',
            street_parameters['street_nominal'] = street_parts[0]
            result = get_query_response(street_parameters)
        if saved_street_part:
            print 12345
            street_parameters['street_nominal'] = saved_street_part
            result = get_query_response(street_parameters)

    #input search items
    output_list = [('street_number_lower', row['no_civique_debut']),
                   ('street_number_upper', row['no_civique_fin']),
                   ('street_nominal', unidecode(row['nom_complet'])),
                   ('suite_num', row['appartement']),
                   ('sale_price', row['prix_vendu']),
                   ('orientation', street_parameters['orientation']),
                   ('street_type', street_parameters['street_type']),
                   ('joining_article', street_parameters['joining_article']),
                   ('article_code', street_parameters['article_code'])
                   ]
    missing_data = [('start_address', None),
                    ('end_address', None),
                    ('street_name', None),
                    ('street_code', None),
                    ('db_suite', None), 
                    ('land_value', None),
                    ('building_value', None),
                    ('total_value', None)
                    ]
    if result:
        output_list += result.items() # results
        matches += 1
    else:
        address_str = '{}-{} {}, suite {}'.format(row['no_civique_debut'].encode('utf-8'), row['no_civique_fin'].encode('utf-8'),
                                                    row['nom_complet'].encode('utf-8'), row['appartement'].encode('utf-8'))
        print "Missed:", address_str
        output_list += missing_data
        missed_addresses.append(address_str)
    
    output_dict = dict(output_list)
    output_rows.append(output_dict)
    print 'Matches: {}/{}'.format(matches, index + 1)
    print 'Pct. Matched: ', float(matches) / (index + 1)
    print 'Pct. of total: ', float(index + 1) / len(row_dicts)
    print
    index += 1

pprint(len(missed_addresses))
pprint(len(output_rows))
field_order = ['street_number_lower', 'street_number_upper', 'street_nominal',
                'orientation', 'suite_num', 'sale_price', 'street_type', 'street_code',
                'joining_article', 'article_code', 'start_address', 'end_address',
                'street_name', 'db_suite', 'land_value', 'building_value', 'total_value']
output_db = Database('../../data/official_data/test_output.sqlite')
output_db.write_rows('test', output_rows, field_order)
