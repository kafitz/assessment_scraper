#!/usr/bin/env python
# 2013 Kyle Fitzsimmons
'''Collection of functions for parsing various data sets to dictionaries'''

import datetime
import xlrd
from unidecode import unidecode
from LookupTables import LookupTable as LT


def get_xls_dict(spreadsheet_filename, target_year):
    '''Load MLS sales spreadsheet to a dictionary'''
    
    def _create_row_dict(headers, row):
        return dict(zip(headers, row))

    workbook = xlrd.open_workbook(spreadsheet_filename)
    sheet = workbook.sheet_by_index(0)

    row_list = []
    for index in range(sheet.nrows):
        # fetch header row
        if index == 0:
            headers = sheet.row_values(index)
            continue
        row = sheet.row_values(index)
        if int(row[-1]) == 0:
            continue
        # read date from excel (try as string, then as excel date)
        try:
            row_year = int(row[1].split('/')[-1])
        except:
            row_date = datetime.datetime(*xlrd.xldate_as_tuple(row[8], workbook.datemode))
            row_year = row_date.year
        # remove rows that do match the desired year from input            
        if row_year == target_year:
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
    article_code = db_articles.get(article)
    if article_code:
        # trim the article from the street_name string
        test_street = ' '.join(name_parts)
        street_nominal = test_street.split(article)[-1].strip().upper()
    else:
        article = None
        street_nominal = ' '.join(name_parts).upper()
    ## STREET NUMBERS
    lower_street_num = row['no_civique_debut']
    upper_street_num = None
    if row['no_civique_fin']:
        upper_street_num = row['no_civique_fin']
    ## SUITE NUMBER
    suite = None
    if row['appartement']:
        suite = row['appartement']
    # MUNICIPAL CODE
    muni_code = int(row['CODE_INT'] )
    ## OUTPUT DICT
    street_parameters = {
        'street_nominal': street_nominal,
        'street_type': street_type,
        'type_code': street_type_code,
        'orientation': orientation,
        'joining_article': article,
        'article_code': article_code,
        'street_number_lower': lower_street_num,
        'street_number_upper': upper_street_num,
        'suite_num': suite,
        'role_muni_code': muni_code
        }
    return street_parameters
