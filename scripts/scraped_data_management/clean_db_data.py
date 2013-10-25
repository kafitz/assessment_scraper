#!/usr/bin/python
# 2013 Kyle Fitzsimmons
'''Cleans databases sales data by removing assessment results for address ranges.

    Requires a blank table to be duplicated manually from input table
    schema so PostGIS field types are retained.'''

import dataset

# input postgis table to cleanse
input_table = '2009_sales'
input_db = dataset.connect('sqlite:///../../data/databases/geocoded_mls_sales.sqlite')
input_rows = input_db[input_table].all()
output_db = dataset.connect('sqlite:///../../data/databases/clean_mls_data.sqlite')

def cleanse_number(test_number):
    # print test_number[:-1]
    try:
        return int(test_number[:-1])
    except:
        return False


output_rows = []
failed_rows = []
for row in input_rows:
    start_address = row.get('start_address')
    end_address = row.get('end_address')
    # if db end address is a blank string, set it to None
    if end_address == '':
        end_address = None
    else:
        pass
    address_parts = row['address'].split()
    # make sure address parts actually has at least a number and a street name
    if len(address_parts) <= 1:
        continue
    if end_address:
        # cleanse end addresses of '1960A' to None if start_address is '1960'
        try:
            end_address = int(end_address)
        except:
            test_end_address = cleanse_number(end_address)
            if test_end_address == int(start_address):
                end_address = None
    if end_address:
        try:
            if int(address_parts[1]) == int(end_address):
                output_rows.append(row)
            else:
                # fail if integers dont match
                print "FAILED: ", [row['input_search'], row['address'], end_address]
                failed_rows.append([row['input_search'], row['address'], end_address])
        except:
            # fail if either term is not an integer
            print "FAILED: ", [row['input_search'], row['address'], end_address]
            failed_rows.append([row['input_search'], row['address'], end_address])    
    else:
        # add to success list if only a single address
        output_rows.append(row)

print '----------'
print "Added: ", len(output_rows)
print "Excluded: ", len(failed_rows)
output_db['clean_2009_sales'].insert_many(output_rows)