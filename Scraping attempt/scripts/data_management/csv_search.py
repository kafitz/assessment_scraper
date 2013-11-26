#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons
'''Boiler plate code to be adapted for searching for fields in a .csv'''

import os
import csv

file_tuple = [x for x in os.walk('output/')][0]
files = [str(file_tuple[0] + filename) for filename in file_tuple[2]]

match_found = False
number_of_2011_sales = 0
for filename in files:
    with open(filename, 'rb') as csv_file:
        reader = csv.reader(csv_file)
        last_section_heading = ''
        for row in reader:
            ### Hard code attributes to search for here
            if str(row[0]) != '' and str(row[1]) == '':
                last_section_heading = str(row[0])
            if 'input_search' in str(row[0]):
                input_search = str(row[0])
            if 'geocoded_arrondissement' in str(row[0]):
                arrondissement = str(row[1])
            if 'ANTERIEUR' in last_section_heading:
                if 'role_year' in in str(row[0]):
                    first_assessment_year = str(row[1])
                if 'total_property_value' in str(row[0]):
                    first_assessment_price = str(row[1])
            if 'EN DATE DU' in last_section_heading:
                last_assessment_year = str(last_section_heading.split()[3])
                if 'total_property_value' in str(row[0]):
                    first_assessment_price = str(row[1])
            if 'date_sold' in str(row[0]):
                date_sold = str(row[1])
            if 'price_sold' on str(row[0]):
                price_sold = str(row[0])
            if "VALEUR AU" in str(row[0]) and "EN DATE DU" in str(row[0]):
                if "2011" not in str(row[0]):
                    print "FOUND A NON-MATCH"
                    match_found = True
            if "date_sold" in str(row[0]):
                print row
                if "2011" in str(row[1]):
                    number_of_2011_sales += 1
if not match_found:
    print "All evaluations for 2011."
    print "Number of sales in 2011: " + str(number_of_2011_sales)
