

NOT IN USE


#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import os.path
import xlrd
import dataset
from unidecode import unidecode

YEAR = '2009'

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

def match_db_data(test_db):
    test_table = test_db[YEAR + '_unmatched_entries']
    # load input .xls to a list
    sales_table = test_db[YEAR + '_sales']
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
    ram_test_db = [x for x in test_table.all()]
    ram_sales_db = [x for x in sales_table.all()]

    current_row = 0
    total_matches = 0
    output_entries = []
    unmatched_entries = []
    for index, row in enumerate(ram_test_db):
        # Part I: For each entry in .xls, if year matches input, find the respective db entry for the .csv (will be unique)
        # For speed reasons, first attempt to compare strings exactly, and then if that fails, compare by sanitizing both .xls and db's input address
        sale_year = row["date_changement_statut"].split('/')[-1]
        if sale_year == YEAR:
            matched_entry = None
            # load .xls rows to variables
            sale_date = "-".join(row["date_changement_statut"].split("/"))
            property_code = row["catg_code"]
            start_address = row["no_civique_debut"]
            end_address = row["no_civique_debut"]
            suite = row["appartement"]
            street_name = row["nom_complet"]
            if row["prix_vendu"]:
                sale_price = int(float(row["prix_vendu"]))
            else:
                unmatched_entries.append(dict(zip(keys, row)))
                continue
            address_query = start_address + ' ' + street_name
            current_row += 1
            if suite:
                address_query = address_query + ', suite ' + suite
            # first try to match a single address without using unidecode (to improve script speed)
            db_search = [(index, entry) for index, entry in enumerate(ram_sales_db) if entry[u'input_search'] == address_query]
            print address_query
            if not db_search:
                db_search = [(index, entry) for index, entry in enumerate(ram_sales_db) if unidecode(entry['input_search']) == unidecode(address_query)]
                if db_search:
                    print str(current_row) + " Unidecode match found (" + address_query + ")"
                else:
                    print current_row
            else:
                print current_row
                print db_search
                break


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

if __name__ == '__main__':
    # add new data from .xls spreadsheet
    test_db = dataset.connect('sqlite:///../../data/databases/temp/ungeocoded_temp_data.sqlite')
    # save data as pickle if doesn't exist as a temp backup database for database debugging (saves previously matched results)
    temp_db_entries, unmatched_temp_db_entries = match_db_data(test_db)
    temp_db_filepath = '../../data/databases/temp/duplicated_data.sqlite'
    temp_db = dataset.connect('sqlite:///' + temp_db_filepath)
    temp_table = temp_db.get_table(YEAR + '_duplicates')
    unmatched_entries_table = temp_db[YEAR + '_unmatched_entries']    
    save_db(temp_table, temp_db_entries)
    save_db(unmatched_entries_table, unmatched_temp_db_entries)
