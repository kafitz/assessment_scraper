#!/usr/bin/env python
# 2013 Kyle Fitzsimmons

import xlrd
from LookupTables import LookupTable as LT
from DatabaseConns import Database
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
        name_parts.pop(0)
    else:
        article = None

    ## STREET NUMBERS
    street_parameters['street_number_lower'] = row['no_civique_debut']
    street_parameters['street_number_upper'] = None
    if row['no_civique_fin']:
        street_parameters['street_number_upper'] = row['no_civique_fin']

    ## SUITE NUMBER
    street_parameters['suite_num'] = None
    if row['appartement']:
        street_parameters['suite_num'] = row['appartement']

    ## OUTPUT DICT
    street_nominal = ' '.join(name_parts).upper()
    street_parameters = {
        'street_nominal': street_nominal,
        'street_type': street_type,
        'type_code': street_type_code,
        'orientation': orientation,
        'joining_article': article,
        'article_code': article_code 
        }
    return street_parameters

def db_lookup(table, street_parameters):
    # create a list of tuples to specifiy the db search criteria
    sql_criteria = [('b72voie1', street_parameters['street_nominal'].upper()),
                    ('b72m1', street_parameters['street_number_lower'])]   
    if street_parameters['type_code']: # street type
        sql_criteria.append(('b72r1', street_parameters['type_code']))
    # concatenate the sql string to execute on the database
    # '''SELECT * FROM 'table' WHERE "foo"="132" and "bar"="MAIN"'''
    sql_command = '''SELECT * FROM '{}' WHERE'''.format(table)    
    for index, criteria in enumerate(sql_criteria):
        sql_command = sql_command + ''' "{}"="{}"'''.format(criteria[0], criteria[1])
        if index + 1 != len(sql_criteria):
            sql_command = sql_command + " AND"
    sql_command
    print sql_command
    db.query(sql_command)
    return db.fetchall()

def parse_query_response(street_parameters):
    '''Script specific function for matching database response to dict variables'''
    result = {}
    r = db_lookup('joined_data', street_parameters)
    if len(r) == 1:
        r = r[0]
        result['street_name'] = r[30]
        result['start_address'] = r[24]
        result['street_code'] = r[28]
        # result['start_address'] =
        # result['land_value'] = 
        # result['building_value'] =
        # result['total_value'] = 

        # print 'Search:', row
        # print 'Result:', result
        return result
    elif len(r) > 1:
        # print r
        print "!!!!!MULTIPLE MATCHES"
        pass
    else:
        # print r
        print "!!!!NO MATCHES"
        pass
    return None


### MAIN

row_dicts = get_spreadsheet_dict(INPUT_SPREADSHEET)
print 'Rows for %s:' % (YEAR,), len(row_dicts)

index = 0
matches = 0
for row in row_dicts:
    street_parameters = get_street_parameters(row)
        
    result = parse_query_response(street_parameters)
    street_parts = street_parameters['street_nominal'].split()
    if not result and len(street_parts) > 1:
        # special case: addresses like "25E AVENUE"--attempt scrape for both "25E AVENUE" and "25E"
        if street_parts[-1].upper() == 'AVENUE':
            street_parameters['street_nominal'] = street_parts[0]
            print 'Trying double query...',
            result = parse_query_response(street_parameters)
            if result:
                print 'Success'
            else:
                print 'Failure'


    if result:
        matches += 1
        print 'Matches: {}/{}'.format(matches, index + 1)
        print 'Pct. Matched: ', float(matches) / (index + 1)
        print 'Pct. of total: ', float(index + 1) / len(row_dicts)
    else:
        print 'Missed:', street_parameters['street_number_lower'] + " " + street_parameters['street_nominal']
        break
    index += 1
    # if index == 5000:
    #     break

