#!/usr/bin/env python
# 2013 Kyle Fitzsimmons

import xlrd
import xlwt
import datetime
from unidecode import unidecode

### GLOBALS
INPUT_SPREADSHEET = '../../data/input/kyle4.xls'
KEEP_CRITERIA = 2009
OUTPUT_SPREADSHEET = '../../data/geocoding/official_mls_2009_sales.xls'

def get_spreadsheet_rows(spreadsheet_filename):
    '''Load excel spreadsheet to a list of rows'''
    workbook = xlrd.open_workbook(spreadsheet_filename)
    sheet = workbook.sheet_by_index(0)
    sheet_name = sheet.name

    row_list = []
    for index in range(sheet.nrows):
        # fetch header row
        if index == 0:
            headers = sheet.row_values(index)
            row_list.append(headers)
            continue
        row = sheet.row_values(index)
        # remove rows that do match the desired year from input
        try:
            # if date read as a string from excel
            row_year = int(row[1].split('/')[-1])
        except:
            # if date read as a float
            row_date = datetime.datetime(*xlrd.xldate_as_tuple(row[1], workbook.datemode))
            row_year = row_date.year
        try:
            sale_price = int(row[8])
        except:
            sale_price = None
        try:
            start_address = str(row[3]).strip()
        except:
            start_address = unidecode(row[3]).strip()


        if row_year != KEEP_CRITERIA:
            continue
        elif start_address == '' or start_address == 'A VENIR':
            continue
        elif not sale_price:
            continue
        else:
            row_list.append(row)
    return sheet_name, row_list

def write_new_spreadsheet(sheet_name, rows):
    '''Write rows to new spreadsheet'''
    workbook = xlwt.Workbook(encoding='utf-8')
    sheet = workbook.add_sheet(sheet_name)
    index = 0
    for row_index in xrange(len(rows)):
        for column_index in xrange(len(rows[row_index])):
            sheet.write(row_index, column_index, rows[row_index][column_index])
        index += 1
        print "Pct. saved:", float(index) / len(rows) 
    workbook.save(OUTPUT_SPREADSHEET)
    return

sheet_name, xls_rows = get_spreadsheet_rows(INPUT_SPREADSHEET)
write_new_spreadsheet(sheet_name, xls_rows)