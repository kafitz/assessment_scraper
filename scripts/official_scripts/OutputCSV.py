#!/usr/bin/env python
# 2013 Kyle Fitzsimmons

import csv

class OutputCSV:
	def write_dicts(self, rows, field_order):
		output_fn = 'matched_data.csv'
		with open(output_fn, 'wb') as csv_file:
			writer = csv.DictWriter(csv_file, field_order)
			writer.writerows(rows)
