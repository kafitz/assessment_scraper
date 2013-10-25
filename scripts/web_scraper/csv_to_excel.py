#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import xlwt
import csv


def main():
    '''One-off script for converting .csv to .xls'''
    workbook = xlwt.Workbook(encoding='utf-8')
    sheet = workbook.add_sheet('failed_addresses')

    csv_file = csv.reader(open('logs/failed.csv', 'rb'), delimiter=",")

    for row_i, row in enumerate(csv_file):
        for col_i, value in enumerate(row):
            sheet.write(row_i, col_i, value)
    workbook.save('failed_addresses.xls')

if __name__ == '__main__':
    main()
