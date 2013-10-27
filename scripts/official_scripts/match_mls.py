#!/usr/bin/env python
# 2013 Kyle Fitzsimmons

import xlrd
from LookupTables import LookupTable as LT
from DatabaseConns import Database
from OutputCSV import OutputCSV
from unidecode import unidecode

from pprint import pprint

### GLOBALS
INPUT_SPREADSHEET = '../../data/input/kyle3.xls'
LOOKUP_DB = '../../data/official_data/test.sqlite'
YEAR = 2009

db = Database(LOOKUP_DB)


def get_spreadsheet_dict(spreadsheet_filename):
    '''Load MLS sales spreadsheet to a dictionary'''
    
    def _create_row_dict(headers, row):
        return dict(zip(headers, row))

    workbook = xlrd.open_workbook(spreadsheet_filename)
    sheet = workbook.sheet_by_index(1)

    row_list = []
    for index in range(sheet.nrows):
        # fetch header row
        if index == 0:
            headers = sheet.row_values(index)
            continue
        row = sheet.row_values(index)
        # remove rows that do match the desired year from input
        row_year = int(row[1].split('/')[-1])
        if row_year == YEAR:
            row_list.append(row)
        else:
            pass
    return [_create_row_dict(headers, row) for row in row_list]

def get_street_parameters(row):
    '''Format input .xls row to dictionary'''
    street = row['nom_complet']
    street_name = unidecode(street).lower()
    name_parts = street_name.split()
    street_type_code = None
    orientation = None
    article = None # French articles such as "le" or "des"
    article_code = None

    ## STREET TYPE
    test_street_type = name_parts[0]
    for key, db_street_types in LT.dom_b72r1_tab.iteritems():
        if test_street_type in db_street_types:
            street_type_code = key
            street_type = test_street_type
            name_parts.pop(0)
            break
    if not street_type_code:
        street_type_code = None # prefix signifier detected to be as part of the street name (i.e., '9E AVENUE')
        street_type = None
    num_parts = len(name_parts)
    ## STREET ORIENTATION (is this noted in the database?)
    if num_parts > 1:
        # determine if there is an orientation included at the end of the street name
        orientations = ('N', 'S', 'O', 'E')
        last_word = name_parts[-1].upper().replace('.', '')
        if last_word in orientations:
            orientation = last_word
        if orientation:
            name_parts.pop() # remove orientation from street_name list
    else:
        pass
    ## FRENCH ARTICLE CODE
    # reverse article codes dictionary for easy lookup
    db_articles = {value:key for key, value in LT.dom_b72lien_tab.iteritems()}
    # exception cases for difficult apostrophe'd articles
    # (spaces to exclude articles within the identifying name which would use dashes)
    if " d'" in street_name:
        article = "d'"
    elif " de l'" in street_name:
        article = "de l'"
    elif "de la" in street_name:
        article = "de la"
    else:
        article = name_parts[0]
    # lookup code from database dict
    if article:
        article_code = db_articles.get(article)
    if article_code:
        test_street = " ".join(name_parts)
    else:
        article = None
    ## STREET NUMBERS
    lower_street_num = row['no_civique_debut']
    upper_street_num = None
    if row['no_civique_fin']:
        lower_street_num = row['no_civique_fin']
    ## SUITE NUMBER
    suite = None
    if row['appartement']:
        suite = row['appartement']
    ## OUTPUT DICT
    street_nominal = ' '.join(name_parts).upper()
    street_parameters = {
        'street_nominal': street_nominal,
        'street_type': street_type,
        'type_code': street_type_code,
        'orientation': orientation,
        'joining_article': article,
        'article_code': article_code,
        'street_number_lower': lower_street_num,
        'street_number_upper': upper_street_num,
        'suite_num': suite 
        }
    return street_parameters

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
    street_name = street_parameters['street_nominal']
    sql_command = '''SELECT "b72m1", "b72a1" FROM '{}' WHERE "b72voie1"="{}"'''.format(table, street_name)
    db.query(sql_command)
    street_number_lower = street_parameters['street_number_lower']
    possible_pairs = []
    for address_pair in sorted(db.fetchall()):
        # ignore tuples that do not form an address range for a property
        if address_pair[1] == 0:
            continue
        # find all tuple pairs that contain the specified addresses
        if address_pair[0] <= street_number_lower and address_pair[1] >= street_number_lower:
            possible_pairs.append(address_pair)
    matched_address_pair = None
    for matching_pair in possible_pairs:
        # generate the range of possible addresses for a certain property (inclusive of the last address)
        address_range = range(matching_pair[0], matching_pair[1], 2)
        address_range.append(matching_pair[1])
        if street_number_lower in [str(x) for x in address_range]:
            matched_address_pair = matching_pair
            break
    if matched_address_pair:
        street_parameters['street_number_lower'] = matched_address_pair[0]
        street_parameters['street_number_upper'] = matched_address_pair[1]
        return street_parameters
    else:
        return None

def get_query_response(street_parameters):
    '''Script specific function for matching database response to dict variables'''
    def _map_to_dict(db_entry):
        result_dict = {}
        result_dict['start_address'] = db_entry[24]
        result_dict['db_suite'] = db_entry[25]
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
        updated_parameters = db_search_entire_street(table_name, street_parameters)
        if updated_parameters:
            recursive_result = get_query_response(updated_parameters)
            print "Found address pair: {}-{} {}".format(updated_parameters['street_number_lower'], updated_parameters['street_number_upper'], updated_parameters['street_nominal'])
            return recursive_result
        else:
            print "No address match found: {} {}".format(street_parameters['street_number_lower'], street_parameters['street_nominal'])
    return None


### MAIN
row_dicts = get_spreadsheet_dict(INPUT_SPREADSHEET)
print 'Rows for %s:' % (YEAR,), len(row_dicts)
index = 0
matches = 0
output_rows = []
for row in row_dicts:
    street_parameters = get_street_parameters(row)
    
    print "Search:", "{}-{} {}, suite {}".format(street_parameters['street_number_upper'],
                                                    street_parameters['street_number_lower'],
                                                    street_parameters['street_nominal'],
                                                    street_parameters['suite_num'])
    # skip inputs without a designated street address
    if not street_parameters['street_number_lower'] and not street_parameters['street_number_upper']:
        continue
    if not street_parameters['street_number_lower']:
        continue
    if street_parameters['street_number_upper'] and not street_parameters['street_number_lower']:
        street_parameters['street_number_lower'] = street_parameters['street_number_upper']
        street_parameters['street_number_upper'] = None
    result = get_query_response(street_parameters)
    street_parts = street_parameters['street_nominal'].split()
    if not result and len(street_parts) > 1:
        # special case: addresses like "25E AVENUE"--attempt scrape for both "25E AVENUE" and "25E"
        if street_parts[-1].upper() == 'AVENUE':
            street_parameters['street_nominal'] = street_parts[0]
            print 'Trying double query...',
            result = get_query_response(street_parameters)
            if result:
                print 'Success'
            else:
                print 'Failure'

    if result:
        matches += 1
    else:
        print 'Missed:', str(street_parameters['street_number_lower']) + " " + street_parameters['street_nominal']
    
    output_list = street_parameters.items()
    if result:
        output_list = output_list + result.items()
    output_dict = dict(output_list)
    output_rows.append(output_dict)
    print 'Matches: {}/{}'.format(matches, index + 1)
    print 'Pct. Matched: ', float(matches) / (index + 1)
    print 'Pct. of total: ', float(index + 1) / len(row_dicts)
    index += 1
    # if index == 4:
    #     break

field_order = ['street_number_lower', 'street_number_upper', 'street_nominal',
                'orientation', 'suite_num', 'street_type', 'type_code',
                'joining_article', 'article_code', 'start_address', 'end_address',
                'street_name', 'db_suite', 'street_code', 'land_value',
                'building_value', 'total_value']
_csv = OutputCSV()
_csv.write_dicts(output_rows, field_order)
