#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import os
import csv
import xlwt

file_tuple = [x for x in os.walk('output/')][0]
files = [str(file_tuple[0] + filename) for filename in file_tuple[2]]

workbook = xlwt.Workbook(encoding='utf-8')
sheet = workbook.add_sheet('summary', cell_overwrite_ok=True)

match_found = False
number_of_2011_sales = 0
index_row = 0
header_list_1 = ['Input', '', 'Scraped results for',
                 '', 'Assessments', '', '', '', 'MLS Data']
header_list_2 = [
    'Address searched', 'Input arrondissement', 'Returned address', 'Return arrondissement',
    'First year', 'Price', 'Last year', 'Price', 'Date sold', 'Price sold']
for header in [header_list_1, header_list_2]:
    for index_column, word in enumerate(header):
        sheet.write(index_row, index_column, word)
    index_row += 1
for filename in files:
    with open(filename, 'rb') as csv_file:
        reader = csv.reader(csv_file)
        last_section_heading = ''
        for row in reader:
            if str(row[0]) != '' and len(row) == 1:
                last_section_heading = str(row[0])
            else:
                if 'input_search' in str(row[0]):
                    input_search = str(row[1])
                if 'geocoded_arrondissement' in str(row[0]):
                    arrondissement = str(row[1])
                if 'address' in str(row[0]):
                    scraped_address = str(row[1])
                if 'neighborhood' in str(row[0]):
                    scraped_arrondissement = str(row[1])
                if 'ANTERIEUR' in last_section_heading:
                    if 'role_year' in str(row[0]):
                        first_assessment_year = str(row[1])
                    if 'total_property_value' in str(row[0]):
                        first_assessment_price = str(row[1])
                if 'EN DATE DU' in last_section_heading:
                    last_assessment_year = str(last_section_heading.split()[3])
                    if 'total_property_value' in str(row[0]):
                        last_assessment_price = str(row[1])
                if 'date_sold' in str(row[0]):
                    date_sold = str(row[1])
                if 'price_sold' in str(row[0]):
                    price_sold = str(row[1])

        output_row = [
            input_search, arrondissement, scraped_address, scraped_arrondissement,
            first_assessment_year, first_assessment_price, last_assessment_year,
            last_assessment_price, date_sold, price_sold]
        for index_column, word in enumerate(output_row):
            sheet.write(index_row, index_column, word)
    index_row += 1
    workbook.save('summary.xls')
