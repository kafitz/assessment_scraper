#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import time
import sys
import urllib
import csv
from BeautifulSoup import BeautifulSoup
from unidecode import unidecode
# Custom file imports
import FuzzyString as fuzzy
from Browser import Browser
import TableParser
from MontrealAddressParser import AddressParser

AP = AddressParser()

def get_nbhoods_list(BrowserInstance, street_name):
    Scraper = BrowserInstance.br
    CookieJar = BrowserInstance.cj
    #### Log-in Sequence ####
    # Log into Role d'Evaluation Fonciere main page (to set browser ASP.NET cookie)
    init_url = 'http://evalweb.ville.montreal.qc.ca/default.asp'
    Scraper.open(init_url)
    # Navigate first page: enter street name to retrieve list of neighborhoods it runs through
    Scraper.select_form(name='Formulaire')
    Scraper.form['text1'] = street_name #fill in street name form field
    BrowserInstance.mimic_cookie_js(urllib.quote(street_name))
    response = Scraper.submit().read()
    # Look for select_field containing the list of neighboorhoods in the response
    soup = BeautifulSoup(response)
    neighborhoods_html = soup.find('select', {'id':'select1'})
    try:
        nbhood_choices = neighborhoods_html.findAll('option')
    except:
        raise
    nbhood_choices.pop(0) #remove junk header entry
    # Iterate through the displayed options matching them to the site URL_ID
    nbhood_full_list = []
    nbhood_form_fields = [] #list corresponding with the site's "selectControl" field
    index = 1
    for choice in nbhood_choices:
        nbhood_url_id = choice.attrs[0][1]  #url id embedded in attributes in a tuple pair
        address_elements = AP.parse_nbhoods(choice.text)    #extract list of neighborhood attributes (e.g., name)
        address_elements.append(nbhood_url_id)
        nbhood_full_list.append(address_elements)
        # Create the parallel user output address list
        address_string = str(index) + ". " + address_elements[0] + \
                        " -- " + address_elements[1] + ", " + address_elements[2]
        nbhood_form_fields.append(address_string)
        index += 1
    return nbhood_form_fields, nbhood_full_list

def enter_street_address(BrowserInstance, nbhood_full_list, street_index, start_address, end_address):
    '''Main scraper guts. Enter street address (amongst other things), receive list(s) for each unit available'''
    Scraper = BrowserInstance.br
    nbhood_id = nbhood_full_list[street_index]

    ## Get list of units
    # List of units
    units_page = 'http://evalweb.ville.montreal.qc.ca/Role2011actualise/RechAdresse.ASP?IdAdrr=' + \
                    str(nbhood_id[3])
    Scraper.open(units_page)
    response = Scraper.response().read()
    soup = BeautifulSoup(response)
    units_html = soup.find('select', {'id':'select2'})
    unit_choices = units_html.findAll('option')
    unit_choices.pop(0)
    property_address_list = []
    unit_id_list = []
    for choice in unit_choices:
        unit_id = choice.attrs[0][1]
        unit_id_list.append(unit_id)
        property_address = unicode(choice.text)
        property_address_list.append([property_address, unit_id])
        AP.parse_street_number(property_address, unit_id)


    # print AP.street_number_dict
    scraped_data = {}
    time_between_requests = 5

    # Test if scrape is only for a single address...
    if end_address is None:
        is_start_address_valid, corresponding_id_dict, msg = AP.check_valid_address(start_address)
        # Get unit ids from single-entry dictionary
        for address, unit_id_list in corresponding_id_dict.items():
            address = str(address)
            unit_id_list = list(unit_id_list)
        if is_start_address_valid is False:
            error = "Scrape Error: start address - " + msg
            raise NameError(error)
        elif is_start_address_valid is True:
            data_tuple_list = []
            for unit_id in unit_id_list:
                lookupURL = 'http://evalweb.ville.montreal.qc.ca/Role2011actualise/CompteFoncier.ASP?id_uef=%20' + \
                                    str(unit_id)
                print lookupURL
                Scraper.open(lookupURL)
                response = Scraper.response().read()
                tp = TableParser.ParseTable(response)
                tp.extract_tables()
                csv_list = tp.return_table
                data_tuple = (unit_id, csv_list)
                data_tuple_list.append(data_tuple)
            scraped_data[address] = data_tuple_list
    # ...or multiple addresses
    else:
        is_end_address_valid, end_unit_id, msg = AP.check_valid_address(end_address)
        if is_end_address_valid is False:
            error = "Scrape Error: end address - " + msg
            raise NameError(error)
        # Account for python's handling of range
        end_address = end_address + 1
        # Iterate for each address from input range
        for address_number in range(start_address, end_address):
            is_address_valid, corresponding_id_dict, msg = AP.check_valid_address(address_number)
            # For each address_number generated from the input range, get an address string and list of
            # units corresponding to that particular street number
            if is_address_valid is True:
                for address, unit_id_list in corresponding_id_dict.items():
                    data_tuple_list = []
                    for unit_id in unit_id_list:
                        ## Data Scraping
                        lookupURL = 'http://evalweb.ville.montreal.qc.ca/Role2011actualise/CompteFoncier.ASP?id_uef=%20' + \
                                        str(unit_id)
                        # print lookupURL
                        Scraper.open(lookupURL)
                        response = Scraper.response().read()
                        tp = TableParser.ParseTable(response)
                        tp.extract_tables()
                        csv_list = tp.return_table
                        data_tuple = (unit_id, csv_list)
                        data_tuple_list.append(data_tuple)
                    scraped_data[address] = data_tuple_list
            time.sleep(time_between_requests)
    # Reset dict in case back button is pushed
    AP.street_number_dict = {}
    return scraped_data

def csv_writer(filename, csv_list):
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Montreal, Quebec Property Assessment']) # This is for a very specific behavior of excel that 
        for row in csv_list:                                    # detects the file as the wrong format if the first
            if type(row) is tuple:                              # 2 characters are "ID" (our first label is 'IDENTIFIANTS')
                key, value = row
                utf_row = (key.encode('utf-8'), value.encode('utf-8'))
            else:
                utf_row = (row.encode('utf-8'),)
            writer.writerow(utf_row)
    return
