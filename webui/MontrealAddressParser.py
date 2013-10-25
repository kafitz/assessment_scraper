#!/usr/bin/python
# coding=utf-8
# 2013 Kyle Fitzsimmons

import re
import sys
from collections import defaultdict

class AddressParser():
	"""Class specific to regexing Montreal Role d'Evaluation Fonciere"""

	def __init__(self):
		self.street_number_dict = {}

	def cut_string(self, result_to_cut, neighborhood):
		splice_point = len(result_to_cut)
		# Should instead set nbhood_label instead of returning variable?
		return neighborhood[splice_point:]
	def parse_nbhoods(self, nbhood_label):
		'''Regex-fu; don't bother trying to decipher unless headaches are enjoyed.
			Cuts up results list into strings that make sense for our program.'''
		# Search for where first block of newlines to begin our results list
		# (call re.U for unicode [French here] characters)
		street = re.search(r'(\w*\s?-?\'?)*', nbhood_label, re.U).group()
		# Remove the matched part of string and continue
		nbhood_label = self.cut_string(street, nbhood_label)
		
		street_prefix = re.search(r', \w*', nbhood_label, re.U).group()
		nbhood_label = self.cut_string(street_prefix, nbhood_label)
		nbhood_label = nbhood_label.strip()
		# Remove leading slash from Assessment Role string
		nbhood_label = nbhood_label[1:]

		nbhood_name = re.search(r'(\w*\s?-?\'?)*', nbhood_label, re.U).group()
		nbhood_label = self.cut_string(nbhood_name, nbhood_label)
		nbhood_name = nbhood_name.strip()
		if nbhood_name == "":
			nbhood_name = "N/A"
		nbhood_label = nbhood_label.strip()
		city = nbhood_label = nbhood_label[1:]
		address_list = [street + street_prefix, nbhood_name, city]
		return address_list

	def parse_street_number(self, address, unit_id):
		'''Creates a key pair in self.street_number_dict for the address range corresponding
			to a particular unit_id. (Accounts for address range within apartment buildings)'''
		try:
			# Determine if address is for a range by matching for a pattern
			# of '1234 - 5678 streetname'
			address_string = address.encode('utf-8')
			address = re.match(ur'\d+ ?-? ?\d+', address, re.U).group()
			if '-' in address:
				addresses_list = []
				address_range = address.split(' - ')
				start_address = int(address_range[0])
				end_address = int(address_range[1]) + 1
				# Range 2 for even side/odd side of the street
				for address_number in range(start_address, end_address, 2):
					addresses_list.append(address_number)
				self.street_number_dict[unit_id] = (address_string, addresses_list)
			else:
				# Put address in single list to match range data
				single_address = int(address)
				self.street_number_dict[unit_id] = (address_string, [single_address])
				pass
		except Exception, e:
			# print Exception, e
			pass

	def check_valid_address(self, address_input):
		address_input = int(address_input)
		is_address_valid = False
		corresponding_unit_ids = defaultdict(list)

		matching_units = []
		total_address_range = []
		for unit_id, address_tuple in self.street_number_dict.items():
			address_string, unit_street_address_list = address_tuple
			address_string = str(address_string)
			if address_input in unit_street_address_list:	
				is_address_valid = True
				corresponding_unit_ids[address_string].append(unit_id)
			for street_addresses in unit_street_address_list:
				total_address_range.append(street_addresses)

		if is_address_valid is True:
			msg = ''
			return True, corresponding_unit_ids, msg
		else:
			# Find the highest/lowest addresses in the neighborhood list to better inform
			# the user of their query in the scope of the assessment search
			list(set(total_address_range))

			highest_address = max(total_address_range)
			lowest_address = min(total_address_range)
			if address_input > int(highest_address):
				msg = 'Input address is higher than address range for selected neighborhood.'
			elif address_input < int(lowest_address):
				msg = 'Input address is lower than address range for selected neighborhood.'
			else:
				msg = ("Address in neighborhood range but does not correspond to an actual street address.")	
			unit_id = None
			return False, corresponding_unit_ids, msg