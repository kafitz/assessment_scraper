#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import dataset
import geopy
import time

INPUT_DIRECTORY = '../../data/databases/'
TABLE_NAME = 'clean_2009_sales'

g = geopy.geocoders.GoogleV3(domain='maps.google.ca')
db_filepath = 'sqlite:///' + INPUT_DIRECTORY + 'clean_mls_data.sqlite'
db = dataset.connect(db_filepath)
table = db[TABLE_NAME]

def geocode_address(search_address):
    query = search_address + ", " + "Montreal"
    try:
        place, (lat, lng) = g.geocode(query)[0]
        print("Geocoded {0} to {1}: {2}, {3}".format(query, place.encode('utf-8'), lat, lng))
        return lat, lng
    except geopy.geocoders.googlev3.GTooManyQueriesError:
        print("Geocoding quota exceeded.")
        return 0, 0
    except geopy.geocoders.googlev3.GQueryError:
        print("Couldn't find address.")
        return 0, 0

# Unpacked to list to avoid SQLite lock from multiple connections from following for-loop
ungeocoded_addresses = [x for x in db.query('SELECT * FROM "' + TABLE_NAME  + '" WHERE latitude = 0')]
num_addresses = len(ungeocoded_addresses)

for index, entry in enumerate(ungeocoded_addresses):
    print str(index) + "/" + str(num_addresses)
    entry['latitude'], entry['longitude'] = geocode_address(entry['address'])
    table.update(entry, ['id'])
    time.sleep(0.2)