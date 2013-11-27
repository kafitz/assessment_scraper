#!/usr/bin/env python
# 2013 Kyle Fitzsimmons
'''Add simple calculations to .csv output from matched_data db'''

import csv

csv_path = '../../data/outputs/matched_data.csv'
output_path = '../../data/outputs/matched_data_stats.csv'

# Open the csv file
rows = list(csv.reader(open(csv_path, 'rb')))
headers = rows.pop(0)
output_rows = []
headers += ['total_value/sale_price']
for row in rows:
	total_value = float(row[19])
	sale_price = float(row[6])
	row.append(total_value / sale_price)
	output_rows.append(row)

# output new .csv file
with open(output_path, 'wb') as csv_file:
	writer = csv.writer(csv_file)
	writer.writerow(headers)
	writer.writerows(output_rows)