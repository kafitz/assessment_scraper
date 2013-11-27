#!/usr/bin/env python
# 2013 Kyle Fitzsimmons

import DataParser as DP
from DatabaseConns import Database
from unidecode import unidecode
from pprint import pprint
import time

### GLOBALS
INPUT_ADDRESSES = '../../data/input/sales_with_muni_codes.csv'
LOOKUP_DB = '../../data/databases/roll_shapefile.sqlite'
OUTPUT_DB = '../../data/databases/matched_mls_assessments.sqlite'
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

def get_query_response(street_parameters):
    '''Script-specific function for matching database response to dict variables'''
    def _map_to_dict(db_entry):
        result_dict = {}
        result_dict['start_address'] = db_entry[21]
        result_dict['db_suite'] = db_entry[28]
        result_dict['end_address'] = db_entry[23]
        result_dict['street_code'] = db_entry[25]
        result_dict['street_name'] = db_entry[27]
        result_dict['land_value'] = db_entry[41]
        result_dict['building_value'] = db_entry[42]
        result_dict['total_value'] = db_entry[43]
        return result_dict
    ## SEARCH FOR XLS ADDRESS NUMBER AS BOTH START AND END (if needed) ADDRESS
    table_name = 'full_data'
    # create a list of tuples to specifiy the db search criteria
    sql_criteria = [('B72VOIE1', street_parameters['street_nominal'].upper()),
                    ('B72M1', street_parameters['street_number_lower']),
                    ('CODE_MUN', street_parameters['roll_muni_code'])]
    if street_parameters['type_code']: # street type
        sql_criteria.append(('B72R1', street_parameters['type_code']))
    r = db_search_address(table_name, sql_criteria)
    if not r:
        # create a list of tuples to specifiy the db search criteria
        sql_criteria = [('B72VOIE1', street_parameters['street_nominal'].upper()),
                        ('B72A1', street_parameters['street_number_lower']),
                        ('CODE_MUN', street_parameters['roll_muni_code'])] 
        if street_parameters['type_code']: # street type
            sql_criteria.append(('B72R1', street_parameters['type_code']))
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
    else:
        pass
    return None


### MAIN
row_dicts = DP.get_csv_dict(INPUT_ADDRESSES, YEAR)
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
    if street_parameters['street_number_upper'] and not street_parameters['street_number_lower']:
        street_parameters['street_number_lower'] = street_parameters['street_number_upper']
        street_parameters['street_number_upper'] = None
    print "Search:", "{}-{} {}, suite {}".format(street_parameters['street_number_lower'],
                                                    street_parameters['street_number_upper'],
                                                    street_parameters['street_nominal'],
                                                    street_parameters['suite_num'])
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
            street_parameters['street_nominal'] = saved_street_part
            result = get_query_response(street_parameters)

    #input search items
    output_list = [('street_number_lower', row['no_civique']),
                   ('street_number_upper', row['no_civiq_1']),
                   ('street_nominal', unidecode(row['nom_comple'])),
                   ('suite_num', row['appartemen']),
                   ('catg_code', row['catg_code']),
                   ('municipality', unidecode(row['name'])),
                   ('sale_price', row['prix_vendu']),
                   ('orientation', street_parameters['orientation']),
                   ('street_type', street_parameters['street_type']),
                   ('joining_article', street_parameters['joining_article']),
                   ('article_code', street_parameters['article_code']),
                   ('muni_code', street_parameters['roll_muni_code'])
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
        address_str = '{}-{} {}, suite {}'.format(row['no_civique'], row['no_civiq_1'],
                                                    row['nom_comple'], row['appartemen'])
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

# create a table with all the data submitted to matching function
pprint(len(missed_addresses))
pprint(len(output_rows))
field_order = ['street_number_lower', 'street_number_upper', 'street_nominal',
                'orientation', 'suite_num', 'catg_code', 'sale_price', 'street_type', 'street_code',
                'muni_code', 'municipality', 'joining_article', 'article_code', 'start_address', 'end_address',
                'street_name', 'db_suite', 'land_value', 'building_value', 'total_value']
output_db = Database(OUTPUT_DB)
output_db.write_rows('all_data', output_rows, field_order)

# create a table consisting only of a successful matches
matched_output_rows = [row for row in output_rows if row['total_value'] is not None]
output_db.write_rows('matched_data', matched_output_rows, field_order)
