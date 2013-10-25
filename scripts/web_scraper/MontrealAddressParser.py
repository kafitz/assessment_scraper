#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import re
import string
import unidecode

class AddressParser():
    """Class specific to regexing Montreal Role d'Evaluation Fonciere"""

    def __init__(self):
        self.street_number_dict = {}

    def cut_string(self, result_to_cut, neighborhood):
        splice_point = len(result_to_cut)
        # Should instead set nbhood_label instead of returning variable?
        return neighborhood[splice_point:]

    def parse_nbhoods(self, nbhood_label):
        delim1 = nbhood_label.split('/')
        delim2 = []
        for split_list in delim1:
            delim2 = delim2 + [item.strip() for item in split_list.split(',')]
        nbhood_list = delim2

        if len(nbhood_list) == 3:
            # Add filler for non-existant street type
            nbhood_list.insert(1, None)
        if len(nbhood_list) == 4:
            # Add filler for non-existent direction
            nbhood_list.insert(2, None)
        street = nbhood_list[0]
        # create a standardized format for street name comparisons
        street_prefix = nbhood_list[1]
        if street_prefix:
            street_prefix = street_prefix.replace('.', '')
            if street_prefix[-5:] == "DE LA":
                street_prefix = street_prefix[:-5].strip()
                street = "DE LA " + street
            if street_prefix[-4:] == "DE L":
                street_prefix = street_prefix[:-4].strip()
                street = "DE L " + street
            if street_prefix[-3:] == "DES":
                street_prefix = street_prefix[:-3].strip()
                street = "DES " + street
            if street_prefix[-3:] == "LES":
                street_prefix = street_prefix[:-3].strip()
                street = "LES " + street
            if street_prefix[-2:] == "DE":
                street_prefix = street_prefix[:-2].strip()
                street = "DU " + street
            if street_prefix[-2:] == "DU":
                street_prefix = street_prefix[:-2].strip()
                street = "DU " + street
        # Remove leading slash from Assessment Role string
        direction = nbhood_list[2]
        possible_directions = ['N', 'S', 'E', 'O']
        if direction in possible_directions:
            direction = unicode(direction)
        nbhood_name = nbhood_list[3]
        if nbhood_name == "":
            nbhood_name = "N/A"
        city = nbhood_list[4]
        address_list = [street, street_prefix, nbhood_name, city, direction]
        return address_list

    def parse_street_number(self, address, unit_id):
        # Determine if address is for range by matching for a pattern
        # of '1234 - 5678 streetname'
        try:
            street_number = re.match(r'\d+( - \d+)?', address, re.U).group()
        except:
            street_number = ''
        # Put address in single list to match range data
        if '-' in street_number:
            addresses_list = []
            address_range = street_number.split(' - ')
            start_address = int(address_range[0])
            end_address = int(address_range[1]) + 1
            # Range of 2 to account for alternating even/odd addresses
            # on either side of street
            for address_number in range(start_address, end_address, 2):
                addresses_list.append(str(address_number))
            self.street_number_dict[unit_id] = (addresses_list, None)
        elif street_number is not '':
            single_address = str(street_number)
            suites = None
            if ', Suite' in address:
                # Only add multiple units for a single address if they are listed as a suite
                suites = str(address.split()[-1])
                self.street_number_dict[unit_id] = ([single_address], suites)
            else:
                # Add ordinary address
                self.street_number_dict[unit_id] = ([single_address], suites)


    def check_valid_address(self, address_input):
        is_address_valid = False
        matched_addresses = []
        for key, address_suite_tuple in self.street_number_dict.items():
            address_list, suite = (address_suite_tuple)
            if address_input in address_list:
                matched_addresses.append((address_list, (suite, key)))
        suite_id_list = []
        if matched_addresses:
            # Search for coexisting addresses and give priority to a single unit 
            # over a range (assumed to be something like parking spaces)
            for address_tuple in matched_addresses:
                address_list, id_tuple = address_tuple
                if len(address_list) == 1:
                    suite_id_list.append(id_tuple)
            if not suite_id_list:
                for address_tuple in matched_addresses:
                    address_list, id_tuple = address_tuple
                    suite_id_list.append(id_tuple)
            is_address_valid = True
        if is_address_valid is True:
            return True, suite_id_list
        else:
            return False, suite_id_list

    def reset_dict(self):
        self.street_number_dict = {}
