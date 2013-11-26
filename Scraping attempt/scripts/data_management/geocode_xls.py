#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import time
import xlrd
import dataset
from sqlalchemy.exc import StatementError
from unidecode import unidecode
import geopy


g = geopy.geocoders.GoogleV3(domain='maps.google.ca')
# Open excel
wb = xlrd.open_workbook('../../data/geocoding/mls_2009_sales.xls')
sh = wb.sheet_by_index(0)
# Output database
success_db = dataset.connect('sqlite:///../../data/geocoding/geocoded_xls_input.sqlite')
successful_geocodes = success_db['2009_sales']
failed_db = dataset.connect('sqlite:///../../data/geocoding/failed_lookup.sqlite')
failed_geocodes = failed_db['2009_failed_geocodes']

row_list = []
for rownum in range(sh.nrows):
    row_list.append(sh.row_values(rownum))

header_row = row_list.pop(0)
failed_header = header_row[:]
header_row.extend(['latitude', 'longitude'])
total_rows = len(row_list)
current_row = 0
failed_entries = []
for row in row_list:
    current_row += 1
    print("Row: {0}/{1} ({2:2f}%)".format(current_row, total_rows, float(current_row) / total_rows * 100))
    search_str = row[0].split(',')[0] + ", " + "Montreal"
    search_address = unidecode(search_str)
    # Look for entry in success results
    try:
        entry_exists = [x for x in success_db.query('''SELECT id FROM "2009_sales" WHERE input_search="%s"''' % row[0])]
    except:
        entry_exists = False
    # If not there, search in failed_lookups success_db
    if not entry_exists:
        try:
            entry_exists = [x for x in failed_db.query('''SELECT id FROM "failed_2009_sales" WHERE input_search="%s"''' % row[0])]
        except:
            entry_exists = False
    # If in neither, attempt to geocode
    if not entry_exists:    
        lat, lng = (None, None)
        table_update = dict(list(zip(failed_header, row)))
        for entry in table_update:
            if table_update[entry] == '':
                table_update[entry] = 0.0
        try:
            place, (lat, lng) = g.geocode(search_address)[0]
            print("Geocoded {0} to {1}: {2}, {3}".format(search_address, place.encode('utf-8'), lat, lng))
            table_update.update({'latitude': float(lat), 'longitude': float(lng)})
            successful_geocodes.insert(table_update)
        except geopy.geocoders.googlev3.GTooManyQueriesError:
            print("Geocoding quota exceeded.")
            break
        except geopy.geocoders.googlev3.GQueryError:
            print("Couldn't find address.")
            print(table_update)
            failed_geocodes.insert(table_update)
        except StatementError: #from sqlalchemy
            print("Couldn't insert entry, improperly formatted data?")
            print(table_update)
            failed_entries.append(table_update)
        time.sleep(1.5)

for item in failed_entries:
    print item
