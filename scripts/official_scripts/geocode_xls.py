#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import time
import xlrd
import dataset
from sqlalchemy.exc import StatementError
from unidecode import unidecode
import geopy


def coerce_to_int(possible_float):
    try:
        possible_float = int(possible_float)
        return possible_float
    except:
        return possible_float


year = '2009'
g = geopy.geocoders.GoogleV3(domain='maps.google.ca')
# Open excel
wb = xlrd.open_workbook('../../data/geocoding/official_mls_2009_sales.xls')
sh = wb.sheet_by_index(0)
# Output database
success_db = dataset.connect('sqlite:///../../data/geocoding/geocoded_xls_input.sqlite')
failed_db = dataset.connect('sqlite:///../../data/geocoding/failed_lookup.sqlite')
failed_geocodes = failed_db[year + '_failed_geocodes']
# create table with proper schema
if year + '_sales' not in success_db.tables:
    success_schema = open('geocode_db.schema').read()
    success_db.query(success_schema.format(year + '_sales'))
successful_geocodes = success_db[year + '_sales']    

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
    start_address = str(coerce_to_int(row[3]))
    street_address = start_address + ' ' + row[6].split(',')[0]
    search_str = street_address + ", " + "Montreal, QC"
    search_address = unidecode(search_str)
    # Look for entry in success results
    print '''SELECT id FROM "2009_sales" WHERE nom_complet="%s" AND no_civique_debut="%s"''' % (row[6], start_address)
    try:
        entry_exists = [x for x in success_db.query('''SELECT id FROM "2009_sales" WHERE nom_complet="%s" AND no_civique_debut="%s"''' % (row[6], start_address))]
    except:
        entry_exists = False
    # If not there, search in failed_lookups success_db
    if not entry_exists:
        try:
            entry_exists = [x for x in failed_db.query('''SELECT id FROM "failed_2009_sales" WHERE nom_complet="%s" AND no_civique_debut="%s"''' % (row[6], start_address))]
        except:
            entry_exists = False
    # If in neither, attempt to geocode
    if entry_exists:    
        print 'Skipped: existing entry found'
    else:
        lat, lng = (None, None)
        table_update = dict(list(zip(failed_header, row)))
        for entry in table_update:
            table_update[entry] = coerce_to_int(table_update[entry])
            if table_update[entry] == '':
                table_update[entry] = None
            if table_update[entry] == 0:
                table_update[entry] = None
        try:
            response = g.geocode(search_address, exactly_one=False)
            result = response[0]
            place, (lat, lng) = result
            print("Geocoded {0} to {1}: {2}, {3}".format(search_address, place.encode('utf-8'), lat, lng))
            table_update.update({'latitude': float(lat), 'longitude': float(lng)})
            if len(response) != 1:
                table_update.update({'multiple_matches': 1})
            successful_geocodes.insert(table_update)
        except geopy.geocoders.googlev3.GeocoderQueryError:
            print("Couldn't find address.")
            print(table_update)
            failed_geocodes.insert(table_update)
        except StatementError: #from sqlalchemy
            print("Couldn't insert entry, improperly formatted data?")
            print(table_update)
            failed_entries.append(table_update)
        except geopy.geocoders.googlev3.GeocoderQuotaExceeded:
            print("Geocoding quota exceeded.")
            break
        time.sleep(.5)


for item in failed_entries:
    print item
