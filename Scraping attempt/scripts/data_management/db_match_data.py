#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import pickle
import os.path
import xlrd
import dataset
from unidecode import unidecode

YEAR = '2009'

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

def save_db(output_table, output_entries):
    '''Save matched database to a new file'''
    size = len(output_entries)
    unwritable_entries = []
    for index, entry in enumerate(output_entries):
        progress = float(index) / float(size) * 100
        print  "{:.2f}%".format(progress)
        try:
            output_table.upsert(entry, ['id'])
        except Exception, e:
            # VERBOSE debug if fails: print every row entry
            print e
            for x, y in entry.iteritems():
                print x, y
            break

def add_xls_data(xls_sheet, csv_db):
    csv_table = csv_db[YEAR]
    # load input .xls to a list
    xls_list = [xls_sheet.row_values(rownum) for rownum in range(xls_sheet.nrows)]
    keys = ["no_inscription", 
        "date_changement_statut", 
        "catg_code", 
        "no_civique_debut", 
        "no_civique_fin", 
        "appartement", 
        "nom_complet", 
        "quart_mun_arr_id", 
        "prix_vendu"]
    
    # load table to ram so unidecode can be run on both terms to
    # elminate error caused by accents
    # -a better way to do this would be to have a duplicate non-accented copy of the
    # -the column in the database to begin with and to use SQL queries 
    # -(however in practice, this method seems to iterate through)
    ram_db = [x for x in csv_table.all()]

    ram_db_size = len(ram_db)
    current_row = 0
    total_matches = 0
    output_entries = []
    unmatched_entries = []
    xls_list.pop(0) #header row of column names
    for index, row in enumerate(xls_list):
        # Part I: For each entry in .xls, if year matches input, find the respective db entry for the .csv (will be unique)
        # For speed reasons, first attempt to compare strings exactly, and then if that fails, compare by sanitizing both .xls and db's input address
        sale_year = row[1].split('/')[-1]
        if sale_year == YEAR:
            matched_entry = None
            # load .xls rows to variables
            sale_date = "-".join(row[1].split("/"))
            property_code = row[2]
            start_address = row[3]
            end_address = row[4]
            suite = row[5]
            street_name = row[6]
            if row[8]:
                sale_price = int(float(row[8]))
            else:
                unmatched_entries.append(dict(zip(keys, row)))
                continue
            address_query = start_address + ' ' + street_name
            current_row += 1
            if suite:
                address_query = address_query + ', suite ' + suite
            # first try to match a single address without using unidecode (to improve script speed)
            db_search = [(index, entry) for index, entry in enumerate(ram_db) if entry[u'input_search'] == address_query]
            if not db_search:
                db_search = [(index, entry) for index, entry in enumerate(ram_db) if unidecode(entry['input_search']) == unidecode(address_query)]
                if db_search:
                    print str(current_row) + " Unidecode match found (" + address_query + ")"
                else:
                    print current_row
            else:
                print current_row
            
            # Part II: If a match, add to output entries. Else, add to unmatched entries.
            # DB's are returned as a list to implement a basic SQL 'transaction'-style system
            if db_search:
                db_search_index = db_search[0][0]
                db_search = db_search[0][1]
                # clean out old single-entry sales prices to allow multiple sales recorded per year
                if db_search.get(u'price_sold'):
                    db_search[u'price_sold_1'] = int(float(db_search[u'price_sold']))
                    del(db_search[u'price_sold'])
                    db_search[u'date_sold_1'] = db_search[u'date_sold']
                    del(db_search[u'date_sold'])
                else:
                    # record the new sale consecutively from last entered
                    previous_sales = sorted([sale_key for sale_key in db_search.keys() if "price_sold" in sale_key])
                    if previous_sales:
                        last_sale_number = int(previous_sales[-1].split('_')[-1])
                        sale_index = str(last_sale_number + 1)
                        # exclude duplicate sale if previous date and sale price are the same
                        if sale_price != db_search[u'price_sold_' + str(last_sale_number)] and sale_date != db_search['date_sold_' + str(last_sale_number)]:
                            db_search[u'price_sold_' + sale_index] = sale_price
                            db_search[u'date_sold_' + sale_index] = sale_date
                        else:
                            continue
                    else:
                        db_search[u'price_sold_1'] = sale_price
                        db_search[u'date_sold_1'] = sale_date
                db_search[u'property_code'] = property_code
                db_search[u'start_address'] = start_address
                db_search[u'end_address'] = end_address
                output_entries.append(db_search)
                total_matches += 1
            else:
                output_row = dict(zip(keys, row))
                for key, value in output_row.iteritems():
                    if key == 'prix_vendu':
                        output_row[key] = str(value)
                unmatched_entries.append(output_row)
    print total_matches, "/", current_row
    return output_entries, unmatched_entries

def match_latlng(temp_table, latlng_table):
    output_db_list = []
    ram_table = [x for x in temp_table.all()]
    ram_latlng_table = [x for x in latlng_table.all()]
    table_size = str(len(ram_table))
    current_row = 0
    for input_sale in ram_table:
        search_address = input_sale[u'address']
        print current_row, "/", table_size + ",", search_address
        found_addresses = [q for q in ram_latlng_table if q[u'address'] == search_address]
        matching_db_entry = None
        for matching_address in found_addresses:
            matching_db_entry = matching_address
            input_sale[u'latitude'] = matching_address[u'latitude']
            input_sale[u'longitude'] = matching_address[u'longitude']
            break
        if not matching_db_entry:
            # set lat, lng as 0, 0 to be geocoded by update_db_latlng.py
            input_sale[u'latitude'], input_sale[u'longitude'] = (0, 0)
        output_db_list.append(input_sale)
        current_row += 1
    return(output_db_list)

if __name__ == '__main__':
    # load pickle of raw database from previous runs if exists
    pickle_object = YEAR + '.obj'
    temp_db_entries = load_pickle(pickle_object)
    # load input .xls
    wb = xlrd.open_workbook('../../data/input/kyle3.xls')
    xls_sheet = wb.sheet_by_index(1)
    # add new data from .xls spreadsheet
    csv_db = dataset.connect('sqlite:///../../data/databases/csv_db.sqlite')
    # save data as pickle if doesn't exist as a temp backup database for database debugging (saves previously matched results)
    if not temp_db_entries:
        temp_db_entries, unmatched_temp_db_entries = add_xls_data(xls_sheet, csv_db)
        save_pickle(temp_db_entries, pickle_object)
    temp_db_filepath = '../../data/databases/temp/ungeocoded_temp_data.sqlite'
    temp_db = dataset.connect('sqlite:///' + temp_db_filepath)
    temp_table = temp_db.get_table(YEAR + '_sales')
    unmatched_entries_table = temp_db[YEAR + '_unmatched_entries']    
    save_db(temp_table, temp_db_entries)
    save_db(unmatched_entries_table, unmatched_temp_db_entries)
    # update data with latitude/longitudes from previous geocoding, else attempt to geocode it now
    output_db_filepath = '../../data/databases/geocoded_mls_sales.sqlite'
    temp_db = dataset.connect('sqlite:///' + temp_db_filepath)
    temp_table = temp_db.get_table(YEAR + '_sales')
    latlng_db = dataset.connect('sqlite:///../../data/databases/latlng_db.sqlite')
    latlng_table = latlng_db[YEAR + '_sales']
    geocoded_entries = match_latlng(temp_table, latlng_table)
    output_db = dataset.connect('sqlite:///' + output_db_filepath)    
    output_table = output_db.get_table(YEAR + '_sales')
    save_db(output_table, geocoded_entries)
