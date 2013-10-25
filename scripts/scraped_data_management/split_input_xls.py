#!/usr/bin/python
# 2013 Kyle Fitzsimmons

import xlrd
import xlwt
import csv
import math

# Assign spreadsheet with id# -> arrondissement name to lookup dictionary
lookup_book = xlrd.open_workbook('territoire_enquete.xls')
lookup_sheet = lookup_book.sheet_by_index(0)
lookup_dict = {}
for rownum in range(lookup_sheet.nrows):
    row = lookup_sheet.row_values(rownum)
    # pass on header row
    if rownum is 0:
        continue
    id_key = row[0]
    arrondissement_value = row[1]
    lookup_dict[id_key] = arrondissement_value

# Load input .xls and decide how many worksheets (2000 lines ea.) are needed
workbook = xlrd.open_workbook('real_sales.xls')
input_sheet = workbook.sheet_by_index(0)
num_rows = input_sheet.nrows
row_list = []
for rownum in range(input_sheet.nrows):
    row_list.append(input_sheet.row_values(rownum))
output_sheets = []
num_sheets =  int(math.ceil(num_rows / float(2000)))
for x in range(1, num_sheets + 1):
    output_sheets.append("batch" + str(x) + ".xls")

# Setup each output sheet and write next 2000 rows from input .xls list
for sheet_name in output_sheets:
    workbook = xlwt.Workbook(encoding='utf-8')
    sheet = workbook.add_sheet('MLS data')
    header_row = ['no_inscription', 'date_changement_statut', 
                'no_civique_debut', 'no_civique_fin', 'appartement',
                'nom_complet', 'quart_mun_arr_id', 'prix_vendu', 
                'arrondissement']
    for col_index, cell in enumerate(header_row):
        sheet.write(0, col_index, cell)
    row_index = 1
    end_index = 2001
    while row_index < end_index:
        row = row_list.pop()
        # append arrondissement for website input
        row.append(lookup_dict(int(row[6])))
        for col_index, cell in enumerate(row):
            sheet.write(row_index, col_index, cell)
        row_index += 1
    workbook.save(sheet_name)
print "Saved to: ", output_sheets