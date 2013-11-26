#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import os
import sys
import csv
import argparse
import unidecode
import dataset

year = '2005'
MLS_DIRECTORY = '../../data/scraper_runs/' + year + '_sales/' + year + '_sales_csvs'
OUTPUT_DIRECTORY = '../../data/databases'
TABLE_NAME = year

def get_csvs(input_dir):
    filepaths = []
    files_skipped = []
    # single-use generator (os.walk)
    for (dirpath, dirname, filenames) in os.walk(input_dir):
        for filename in filenames:
            if filename[-4:] == '.csv':
                filepaths.append(dirpath + '/' + filename)
            else:
                files_skipped.append(filename)
    if files_skipped:
        print("Non-.csv files skipped: ", ", ".join(files_skipped))
    return filepaths

def parse_csv(csv_filename):
    '''Returns a dictionary from the input assessment roll .csv'''
    with open(csv_filename, 'r') as csv_file:
        reader = csv.reader(csv_file)
        last_section_heading = ''
        db_entry = {}
        for row in reader:
            if len(row) == 1:
                last_section_heading = row[0]
            if 'ANTERIEUR' in last_section_heading:
                if row[0] != 'role_year':
                    row[0] = row[0] + '_' + '2007'
            elif 'EN DATE DU' in last_section_heading:
                row[0] = row[0] + '_' + '2011'
            elif 'CADASTRES' in last_section_heading:
                cadastre_num = str(last_section_heading[-1])
                row[0] = row[0] + '_' + cadastre_num
            if len(row) == 2:
                header = row[0].decode('utf-8')
                data = row[1].decode('utf-8')
                db_entry[header] = data
        return db_entry
        
def main():
    csvs_list = get_csvs(MLS_DIRECTORY)
    total_files = len(csvs_list)
    current_file_num = 1
    db_filepath = 'sqlite:///' + OUTPUT_DIRECTORY + '/csv_db.sqlite'
    db = dataset.connect(db_filepath)
    mls_sqlite = db[TABLE_NAME]
    for csv in csvs_list:
        try:
            sql_entry = parse_csv(csv)
            mls_sqlite.insert(sql_entry)
        except:
            print csv
            sys.exit()
        print("{:.2f}%, {}/{} files".format(float(current_file_num)/total_files*100, current_file_num, total_files))
        current_file_num += 1


if __name__ == '__main__':
    main()