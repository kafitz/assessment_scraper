#!/usr/bin/env python
# Kyle Fitzsimmons, 2013
'''Updates database with info from a new .xls'''

import xlrd
import dataset
from unidecode import unidecode
import pickle

def load_pickle(filename):
    '''Load existing dataset if exists'''
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)             
    except IOError:
        return None

def save_pickle(pickling_obj, filename):
    '''Pickle a data object to a file'''
    with open(filename, 'wb') as f:
        pickle.dump(pickling_obj, f)

def save_db(output_entries):
    '''Save matched database to a new file'''
    out_db = dataset.connect('sqlite:///../../data/full_mls_db.sqlite')
    out_table = out_db.get_table('2009_sales')
    size = len(output_entries)
    for index, entry in enumerate(output_entries):
        progress = float(index) / float(size) * 100
        print  "{:.2f}%".format(progress)
        out_table.upsert(entry, ['id'])

def match_data():
    '''Match property_code of sales in excel spreadsheet to existing
        entries in an sqlite database'''
    wb = xlrd.open_workbook('../../data/input/kyle3.xls')
    sh = wb.sheet_by_index(1)
    db = dataset.connect('sqlite:///../../data/geocoding/geocoded_mls_sales.sqlite')
    sales_table = db.get_table('2009_sales')

    row_list = []
    for rownum in range(sh.nrows):
        row_list.append(sh.row_values(rownum))

    ram_db = [x for x in sales_table.all()]

    header_row = row_list.pop(0)
    current_row = 0
    total_rows = len(row_list)
    total_matches = 0
    date_mismatches = 0
    unmatched = []
    output_entries = []
    for index, row in enumerate(row_list):
        matched_entry = None
        date = "-".join(row[1].split("/"))
        property_code = row[2]
        start_address = row[3]
        end_address = row[4]
        suite = row[5]
        street_name = row[6]
        sale_price = row[8]
        address_query = start_address + ' ' + street_name
        year = row[1].split('/')[-1]
        if year == '2009':
            current_row += 1
            if suite:
                address_query = address_query + ', suite ' + suite
            db_search = [q for q in ram_db if q['input_search'] == address_query]
            if not db_search:
                db_search = [q for q in ram_db if unidecode(q['input_search']) == unidecode(address_query)]
                if db_search:
                    print str(current_row) + " Unidecode match found (" + address_query + ")"
                else:
                    print current_row
            else:
                print current_row
            if db_search:
                db_search = db_search[0]
                db_search[u'property_code'] = property_code
                db_search[u'start_address'] = start_address
                db_search[u'end_address'] = end_address
                output_entries.append(db_search)
                total_matches += 1
            else:
                unmatched.append(address_query)
    save_pickle(unmatched, 'unmatched.obj')
    return output_entries

if __name__ == '__main__':
    pickle_object = '2009.obj'
    output_entries = load_pickle(pickle_object)
    if not output_entries:
        output_entries = match_data()
        save_pickle(output_entries, pickle_object)
    save_db(output_entries)