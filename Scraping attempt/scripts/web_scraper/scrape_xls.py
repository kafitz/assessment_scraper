'''Module for automated assessment scraping from a templated MLS spreadsheet (.xls)'''
#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import xlrd
from unidecode import unidecode
import assessment_scraper as AS
import time
import os
import errno
import csv
import datetime
from random import random
from urllib2 import URLError

INPUT_SPREADSHEET = 'failed_addresses.xls'            # .xls
LOGS = {
    'repeat': 'logs/repeats.csv',           # .csv
    'fail': 'logs/failed.csv',              # .csv
    'timeout': 'logs/timeouts.csv'          # .csv
    }
# Checks for presence of .csv for both current and next row of input
# table for faster resuming of timed-out sessions
LOOKAHEAD = False

def format_streetname(street_name, orientations):
    '''Make replacements necessary for inputting to website form 
        (might be better suited by a dict)'''
    street_name = street_name.upper()
    if street_name[:2] == "D'":  # only replace if starts the name
        street_name = street_name.replace("D'", "")
    if street_name[:2] == "L'":  # only replace if starts the name
        street_name = street_name.replace("L'", "")
    street_name = street_name.replace("'", " ")
    street_name = street_name.replace("-", " ")
    street_name = street_name.replace(".", "")
    street_name = street_name.replace(" ST ", " SAINT ")
    street_name = street_name.replace(" STE ", " SAINTE ")
    if street_name[:3] == "ST ":
        street_name = street_name.replace("ST ", "SAINT ")
    if street_name[:4] == "STE ":
        street_name = street_name.replace("STE ", "SAINTE ")
    if street_name[-2:] in [str(' ' + o) for o in orientations]:
        street_name = street_name[:-2]
    return street_name.title()

def format_parameters(workbook, row):
    '''Method for formatting variables from the input spreadsheet to a dictionary'''
    output = {}
    # A dictionary to map terms used by spreadsheet to terms used on scraper site
    road_signifiers = {
        'RUE': 'RUE', 'BOUL': 'BOUL', 'AV': 'AV', 'IMP.': 'IMP',
        'AVENUE': 'AV', 'PLACE': 'PL', 'CH': 'CH', 'ALLEE': 'AL', 
        'CROIS': 'CROIS', 'TSSE': 'TSSE'}
    orientations = ['N', 'S', 'E', 'O']
    if isinstance(row[5], unicode):
        output['search_street'] = unidecode(row[5])
    else:
        output['search_street'] = row[5]
    output['input'] = str(row[2]).split(".")[0] + " " + row[5].encode('utf-8')
    if row[4] is not '':
        output['input'] = output['input'] + \
            ", suite " + str(row[4]).split(".")[0]
    street_list = row[5].split()  # divide the street name into parts
    output['direction'] = None
    output['street_type'] = None
    street_no_signifiers = []
    for part in street_list:
        og_part = part
        part = unidecode(part).upper()
        part = part.translate(None, ',.;') # remove punctuation from string
        if part[0] == '(':
            street_list.remove(og_part)
            continue
        if part in orientations:
            output['direction'] = part
        elif part in road_signifiers.keys():  # find what sort of road/street/boul the feature is
            output['street_type'] = road_signifiers[part]
        else:
            street_no_signifiers.append(part)

    arrondissement = row[8].split("(")[0].strip()  # tries for city name in parentheses
    if isinstance(arrondissement, unicode):
        arrondissement = unidecode(arrondissement)
    arr_parts = arrondissement.split('/')
    if len(arr_parts) > 1:
        output['arrondissement'] = " - ".join(arr_parts)
    else:
        output['arrondissement'] = arrondissement
    output['street_name'] = format_streetname(" ".join(street_no_signifiers), orientations)
    if isinstance(output['street_name'], unicode):
        output['street_name'] = unidecode(output['street_name'])
    output['muni_code'] = str(row[6])
    output['price_sold'] = str(row[7])
    output['street_number'] = str(row[2]).split(".", 1)[0]  # to account for excel returning a float
    output['suite'] = str(row[4]).split(".", 1)[0]
    if output['suite'] != '':  # format for filename
        output['suite_fname'] = "-" + output['suite']
    else:
        output['suite_fname'] = ''
    excel_date_str = str(row[1]).split(".")[0]
    excel_date_str = excel_date_str.replace("-", "/") # make common delimiter
    excel_date_list = excel_date_str.split("/")
    if len(excel_date_list) == 3:
        # if date returned as a three-part string
        excel_date = datetime.date(
            int(excel_date_list[2]), int(excel_date_list[1]),
            int(excel_date_list[0]))
    else:
        # if date returned in its integer format
        excel_date = xlrd.xldate_as_tuple(int(str(row[1]).split(".")[0]), workbook.datemode)
        excel_date = datetime.date(*excel_date[:3])  # expand datetime
    output['date_sold'] = excel_date.strftime('%d-%m-%Y')
    output['filename'] = "output/{street_num}{suite}_{street_name}_{arrondissement}.csv".format(
        street_num=output['street_number'], suite=output['suite_fname'], 
        street_name=output['street_name'], arrondissement=output['arrondissement'])
    return output


def csv_writer(filename, csv_list):
    '''CSV generator for possible unicode input'''
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        # This header is for a very specific behavior of excel that
        # detects the file as the wrong format if the first
        # 2 characters are "ID" (our first label is 'IDENTIFIANTS')
        writer.writerow(['Montreal, Quebec Property Assessment'])
        for row in csv_list:
            if type(row) is tuple:
                key, value = row
                if isinstance(key, unicode):
                    key = unidecode(key)
                if isinstance(value, unicode):
                    value = unidecode(value)
                utf_row = (key, value)
            else:
                if isinstance(row, unicode):
                    row = unidecode(row)
                utf_row = (row,)
            writer.writerow(utf_row)
    return

def write_logs(row, output, fname_type):
    filename = LOGS[fname_type]
    crawled_address = output['search_street']
    if isinstance(crawled_address, unicode):
        crawled_address = unidecode(crawled_address)
    with open(filename, 'a') as log_csv:
        writer = csv.writer(log_csv)
        row[0] = str(row[0]).split(".")[0]  # remove float decimals
        row[1] = output['date_sold']
        row[5] = crawled_address
        row[6] = output['muni_code']
        row[7] = output['price_sold']
        row[8] = output['arrondissement']
        writer.writerow(row)
    return

def main():
    '''Passes parameters to scraper, outputs to user, and keeps logs of failed or repeated attempts.'''
    manual_run = False
    workbook = xlrd.open_workbook(INPUT_SPREADSHEET)
    sheet = workbook.sheet_by_index(0)
    try:
        os.makedirs("output")
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    try:
        os.makedirs("logs")
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    for log in LOGS:
        # Append to the fail log so results are not rewritten
        if log is 'fail':
            if os.path.isfile(LOGS[log]):
                continue
        with open(LOGS[log], 'wb') as log_csv:
            writer = csv.writer(log_csv)
            writer.writerow(
                ['no_inscrip', 'date_change', 'no_civique_start', 'no_civiq_end', 'appartement',
                 'nom_complet', 'quart_mun_arr_id', 'prix_vendu', 'arrondissement'])

    row_list = []
    for rownum in range(sheet.nrows):
        row_list.append(sheet.row_values(rownum))
    row_list.pop(0)  # remove header row from spreadsheet data
    for row in row_list:
        print "\n"
        if LOOKAHEAD is True:
            idx = row_list.index(row)
            next_row_idx = idx + 1
            next_row = row_list[next_row_idx]
            output_params = format_parameters(workbook, next_row)
            next_filename = output_params['filename']

        output_params = format_parameters(workbook, row)
        print "--New search: " + output_params['input']

        if LOOKAHEAD is True:
            if os.path.isfile(next_filename):
                if not os.path.isfile(output_params['filename']):
                    print "{0}{1} {2}, {3} scrape: Previous fail assummed not HTTP related".format(
                        output_params['street_number'], output_params['suite_fname'],
                        output_params['street_name'], output_params['arrondissement'])
                    # ADD CATCH TO WRITE TO FAILED ADDRESSES HERE
                    continue
                print "{0}{1} {2}, {3} scrape: Previously completed".format(
                    output_params['street_number'], output_params['suite_fname'],
                    output_params['street_name'], output_params['arrondissement'])
                write_logs(row, output_params, 'repeat')
                continue
            elif not os.path.isfile(next_filename) and os.path.isfile(output_params['filename']):
                print "{0}{1} {2}, {3} scrape: Previously completed".format(
                    output_params['street_number'], output_params['suite_fname'],
                    output_params['street_name'], output_params['arrondissement'])
                write_logs(row, output_params, 'repeat')
                continue
        # Mode for first run or as a clean-up pass
        else:
            if os.path.isfile(output_params['filename']):
                print "{0}{1} {2}, {3} scrape: Previously completed".format(
                    output_params['street_number'], output_params['suite_fname'],
                    output_params['street_name'], output_params['arrondissement'])
                write_logs(row, output_params, 'repeat')
                continue
        
        try:
            # Run scraper backend for interfacing with the website
            scraped_data = AS.scrape(manual_run, output_params['street_name'], 
                output_params['arrondissement'], output_params['street_type'], 
                output_params['street_number'], output_params['suite'], 
                output_params['direction'])
        except URLError:
            print "{0}{1} {2}, {3} scrape: Timed out".format(
                output_params['street_number'], output_params['suite_fname'],
                output_params['street_name'], output_params['arrondissement'])
            write_logs(row, output_params, 'timeout')
            continue
        except Exception, e:
            print e
            scraped_data = None
        if scraped_data:
            scraped_data.append("MLS DATA")
            scraped_data.append(('date_sold', output_params['date_sold']))
            scraped_data.append(('price_sold', output_params['price_sold']))
            scraped_data.append("SCRAPER INPUT")
            scraped_data.append(('input_search', output_params['input']))
            scraped_data.append(('geocoded_arrondissement', output_params['arrondissement']))
            csv_writer(output_params['filename'], scraped_data)
            print "{0}{1} {2}, {3} scrape: Success".format(
                output_params['street_number'], output_params['suite_fname'],
                output_params['street_name'], output_params['arrondissement'])
        else:
            print "{0}{1} {2}, {3} scrape: Failed".format(
                output_params['street_number'], output_params['suite_fname'],
                output_params['street_name'], output_params['arrondissement'])
            try:
                write_logs(row, output_params, 'fail')
            except Exception, e:
                print e

        # time.sleep(6)
        time.sleep((5 * random()) + 12)


if __name__ == "__main__":
    main()
