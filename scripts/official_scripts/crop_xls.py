#!/usr/bin/env python
# 2013 Kyle Fitzsimmons

import xlrd
import xlwt
from IPython import embed

### GLOBALS
INPUT_SPREADSHEET = '../../data/input/kyle3.xls'
KEEP_CRITERIA = 2009
OUTPUT_SPREADSHEET = '2009_sales.xls'

def get_spreadsheet_rows(spreadsheet_filename):
    '''Load excel spreadsheet to a list of rows'''
    workbook = xlrd.open_workbook(spreadsheet_filename)
    sheet = workbook.sheet_by_index(1)
    sheet_name = sheet.name

    row_list = []
    for index in range(sheet.nrows):
        # fetch header row
        if index == 0:
            headers = sheet.row_values(index)
            continue
        row = sheet.row_values(index)
        # remove rows that do match the desired year from input
        row_year = int(row[1].split('/')[-1])
        if row_year == KEEP_CRITERIA:
            row_list.append(row)
        else:
            pass
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