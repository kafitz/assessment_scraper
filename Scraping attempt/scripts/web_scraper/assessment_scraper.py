'''Emulates human interaction on the Montreal Assessment Role'''
#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import time
import sys
import urllib
from BeautifulSoup import BeautifulSoup
from unidecode import unidecode
# Custom imports
import FuzzyString as fuzzy
from Browser import Browser
import TableParser
from MontrealAddressParser import AddressParser

AP = AddressParser()
TIMEOUT = 10 # seconds for browser requests

def request_delay():
    '''Time buffer for waiting between requests of the same scrape'''
    time.sleep(0.4)
    return

def selection_prompt(select_control_list):
    '''Creates a simple menu to select the neighboorhood for a desired address'''
    print "This street runs through multiple neighborhoods, select the one "
    print "that corresponds to the desired street address."
    index = 1
    for option in select_control_list:
        if option[4]:
            direction = " " + option[4]
        else:
            direction = ''
        # 2. CLARK, RUE  -- Arrondissement d'Ahuntsic-Cartierville, MONTREAL
        choice_str = str(index) + ". " + option[0] + " " + option[1] + direction +\
            " -- " + option[2]
        print choice_str
        index += 1
    try:
        selected_nbhood = int(raw_input("> "))
    except:
        print "Error: Integer not entered."
        sys.exit()
    # Check here for integer in displayed range, raise error if doesn't exist
    if selected_nbhood in range(1, index):
        return selected_nbhood
    else:
        print "\nPlease enter the integer corresponding with the results.\n"
        sys.exit()

def enter_streetnumber(manual_run, unit_choices, input_address=None):
    '''Prompts for desired street address and checks to see if this address
        is valid for the arrondissement'''
    property_address_list = []
    for choice in unit_choices:
        unit_id = choice.attrs[0][1]
        property_address = choice.text
        if isinstance(property_address, unicode):
            property_address = unidecode(property_address)
        property_address_list.append([property_address, unit_id])
        AP.parse_street_number(property_address, unit_id)
    print "Enter street address: "
    if input_address:
        address_input = input_address
        print "> " + address_input
    elif not input_address and manual_run is True:
        address_input = raw_input("> ")
    else:
        raise NameError("No address found.")
    # Check if address entered is in data from site
    if isinstance(address_input, unicode):
        address_input = unidecode(address_input)
    is_address_valid, suite_id_list = AP.check_valid_address(address_input)
    if is_address_valid is False:
        raise NameError(
            "Entered address does not correspond with a building address.")
    else:
        return property_address_list, suite_id_list

def nbhd_search(neighborhood_selects, input_arrondissement, input_street, 
                input_street_type, input_direction):
    '''Called if an automated run only; parses input arrondissement and
        [E, O, N, S] direction in street name to select correct listing of
        the street and neighborhood.'''
    arrondissements_choices = []
    street_choices = []
    for address_list in neighborhood_selects:
        arrondissement_choice = address_list[2]
        arrondissement_parts = [
            x.upper() for x in arrondissement_choice.split()]
        parsed_choice_list = []
        for part in arrondissement_parts:
            if part not in ["ARRONDISSEMENT", "DE", "LE", "LA", "DU", "-"]:
                if part[:2] == "D'":
                    part = part[2:]
                if part[:2] == "L'":
                    part = part[2:]
                parsed_choice_list.append(part)
        # return list index of selected neighborhood
        temp_arrondissement = " - ".join(parsed_choice_list)
        if isinstance(temp_arrondissement, unicode):
            address_list[2] = unidecode(temp_arrondissement)
        else:
            address_list[2] = temp_arrondissement
        arrondissements_choices.append(address_list[2])
        street_choices.append(address_list[0])

    if isinstance(input_arrondissement, unicode):
        input_arrondissement = unidecode(input_arrondissement)
    input_arrondissement = input_arrondissement.upper()
    nbhood_match = fuzzy.match(input_arrondissement, arrondissements_choices)
    street_match = fuzzy.match(input_street, street_choices)

    for index, address_list in enumerate(neighborhood_selects):
        if nbhood_match in address_list and street_match in address_list:
            # print 1
            # Find street type in arrondissement choices
            choice_street_type = None
            if address_list[1] is not None:
                choice_street_type = unidecode(address_list[1])
            choice_direction = None
            if address_list[4] is not None:
                # print 2
                choice_direction = address_list[4]
            if input_direction and input_direction == choice_direction:
                # print 3
                if input_street_type and choice_street_type == input_street_type:
                    # print 4
                    print "Selected arrondissement: " + nbhood_match +\
                        ", street type: " + choice_street_type + \
                        ", direction: " + choice_direction
                    selected_nbhood = index
                    break
                elif not input_street_type:
                    # print 5
                    print "Selected arrondissement: " + nbhood_match +\
                    ", direction: " + choice_direction
                    selected_nbhood = index
                    break
            elif not input_direction:
                # print 6
                if input_street_type and choice_street_type == input_street_type:
                    # print 7
                    print "Selected arrondissement: " + nbhood_match +\
                        ", street type: " + choice_street_type
                    selected_nbhood = index
                    break
                if input_street_type and not choice_street_type:
                    # print 8
                    print "Selected arrondissement: " + nbhood_match +\
                        ", street type: "
                    selected_nbhood = index
                    break
                elif not input_street_type:
                    # print 9
                    print "Selected arrondissement: " + nbhood_match
                    selected_nbhood = index
                    break
    try:
        return selected_nbhood
    except:
        return None

def suite_search(manual_run, input_suite, suite_id_list):
    '''Prompts for desired suite if multiple units exist for a given address'''
    # Display to the user the list of suites since the format from the
    # assesment roll site can vary
    print "The address has multiple units, enter apartment unit or suite: "
    # Get suite #'s from tuple and remove None values
    suite_list = filter(None, [suite_tuple[0] for suite_tuple in suite_id_list])
    # this is a stop-gap until a better sorting method is implemented
    suite_list.sort()
    suite_string = ''
    for suite in suite_list:
        suite_string = suite_string + suite + ", "
    suite_string = suite_string.rstrip(", \n")  # remove the trailing comma
    print "Suites: " + suite_string
    if input_suite:
        suite_no = input_suite.upper()
        print "> " + suite_no
    elif not input_suite and manual_run is True:
        suite_no = str(raw_input("> ")).upper()
    for suite_id_tuple in suite_id_list:
        try:
            if str(suite_id_tuple[0]) == suite_no:
                suite, unit_id = suite_id_tuple
        except TypeError:
            # This is to catch for NoneType suites for addresses with multiple other suites.
            # Currently a mystery and needs to be resolved, possibly LOT or GARAGE?
            pass
    return unit_id

def scrape(manual_run, input_street_name=None, input_arrondissement=None, 
    input_street_type=None, input_address=None, input_suite=None, input_direction=None):
    '''Function to perform the interaction with the website like a human user'''
    AP.reset_dict()
    if not input_street_name:
        print "Input street name (partial names work best):"
        input_street = raw_input("> ")
    else:
        input_street = input_street_name
        print "Input street name (partial names work best):"
        print "> " + input_street
    input_street = input_street.upper()

    # Specifically try for case with "de la" or "des" in street name which
    # has tendency to screw things up
    input_street_list = [input_street]
    if input_street[:6] == "DE LA ":
        input_street_list.append(input_street[6:])
    elif input_street[:5] == "DE L ":
        input_street_list.append(input_street[5:])
    elif input_street[:4] == "DES ":
        input_street_list.append(input_street[4:])
    elif input_street[:3] == "DE ":
        input_street_list.append(input_street[3:])
    elif input_street[:3] == "DU ":
        input_street_list.append(input_street[3:])

    selected_nbhood = None
    # try best match with full string first and break on success,
    # otherwise attempt next best with "de la" or "des" removed
    for street_name in input_street_list:
        if not selected_nbhood:
            print 'Street search: "' + street_name + '"...'
            # Emulate web browse instance with Mechanize
            BrowserInstance = Browser()
            Scraper = BrowserInstance.br

            #### Log-in Sequence ####
            # Log into Role d'Evaluation Fonciere main page (to set browser
            # ASP.NET cookie)
            init_url = 'http://evalweb.ville.montreal.qc.ca/default.asp'
            Scraper.open(init_url, timeout=TIMEOUT)
            # Get list of neighborhoods for entered street name
            Scraper.select_form(name='Formulaire')
            Scraper.form['text1'] = street_name
            street_name = urllib.quote(street_name)
            BrowserInstance.mimic_cookie_js(street_name)
            response = Scraper.submit().read()

            # Look for select_field containing the list of neighboorhoods
            # from the returned webpage
            soup = BeautifulSoup(response)
            neighborhoods_html = soup.find('select', {'id': 'select1'})
            try:
                nbhood_choices = neighborhoods_html.findAll('option')
                nbhood_choices.pop(0) # Remove junk header entry
                # Iterate through the displayed options matching them to the
                # site URL_ID
                nbhd_selection_list = []
                for choice in nbhood_choices:
                    # url id embedded in attributes in a tuple pair
                    nbhood_url_id = choice.attrs[0][1]
                    # extract neighborhood name
                    address_list = AP.parse_nbhoods(choice.text)
                    address_list.append(nbhood_url_id)
                    nbhd_selection_list.append(address_list)
                if manual_run:  # display input selection prompt if run manually
                    selected_nbhood = selection_prompt(nbhd_selection_list)
                    selected_nbhood = selected_nbhood - 1
                else:
                    print "Looking for arrondissement: " + input_arrondissement
                    selected_nbhood = nbhd_search(
                        nbhd_selection_list, input_arrondissement, input_street,
                        input_street_type, input_direction)
            except Exception, e:
                print "Warning: No match found on assessment roll."
            time.sleep(1)

    if selected_nbhood is None:
        print "Neighborhood not found."
        return None

    # Since UI list starts w/ 1, subtract 1 to get python list index
    nbhood_id = nbhd_selection_list[selected_nbhood]

    # List of units
    units_page = 'http://evalweb.ville.montreal.qc.ca/' +\
        'Role2011actualise/RechAdresse.ASP?IdAdrr=' + str(nbhood_id[5])
    request_delay()
    Scraper.open(units_page, timeout=TIMEOUT)
    response = Scraper.response().read()
    soup = BeautifulSoup(response)
    units_html = soup.find('select', {'id': 'select2'})
    unit_choices = units_html.findAll('option')
    unit_choices.pop(0)
    try:
        property_address_list, suite_id_list = enter_streetnumber(manual_run, unit_choices, input_address)
    except Exception, e:
        print "Invalid address entered"
        return None
    # If address verifies, test to see if address has multiple units
    if input_suite:
        print "Enter suite:\n", "> " + input_suite
        suites = []
        for suite_id_tuple in suite_id_list:
            suites.append(suite_id_tuple[0])
        if input_suite not in suites:
            print "Input suite not found in results."
            return
    try:
        # See how many units without "None" as unit label
        total_suites = 0
        for suite in suite_id_list:
            if suite[0] is not None:
                total_suites += 1
        if total_suites > 1:
            unit_id = suite_search(manual_run, input_suite, suite_id_list)
        else:
            unit_id = suite_id_list[0][1]
    except:
        print "Invalid suite entered."
        return None
    for address_unit in property_address_list:
        # When the unit_id matches list pair in property_address_list, fetch the full
        # property range for the assessment roll page if there are multiple units
        if unit_id == address_unit[1]:
            # Get the addresses for a single building (which means a single
            # assessment)
            address_range_of_building = address_unit[0]
        else:
            pass
    try:
        print str(unit_id) + ' --- ' + address_range_of_building

        #### Data Scraping ####
        lookup_URL = 'http://evalweb.ville.montreal.qc.ca/' +\
            'Role2011actualise/CompteFoncier.ASP?id_uef=%20' + str(unit_id)
        print lookup_URL
        Scraper.open(lookup_URL, timeout=TIMEOUT)
        request_delay()
        response = Scraper.response().read()
        tp = TableParser.ParseTable(response)
        tp.extract_tables()
        scraped_data = tp.return_table
        if manual_run:
            for line in scraped_data:
                print line
        else:
            return scraped_data
    except UnboundLocalError:
        # invalid address so no unit_id
        return None
    except Exception, e:
        print e
        return None


if __name__ == '__main__':
    manual_run = True
    scrape(manual_run)
