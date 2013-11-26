#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import xlrd


wb = xlrd.open_workbook('../../data/input/kyle3.xls')
xls_sheet = wb.sheet_by_index(1)

rows = [tuple(xls_sheet.row_values(rownum)) for rownum in xrange(xls_sheet.nrows)]
rows.pop(0)

num_real_sales_2005 = 0
num_non_sales_2005 = 0
num_real_sales_2009 = 0
num_non_sales_2009 = 0
num_real_sales_nodate = 0
num_non_sales_nodate = 0
for row in rows:
    # count rows with any price assigned to the sale as 'real sales'
    prix_vendu = row[8]
    sale_year = row[1].split('/')[-1]
    if prix_vendu:
        if sale_year == '2005':
            num_real_sales_2005 += 1
        elif sale_year == '2009':
            num_real_sales_2009 += 1
        else:
            num_real_sales_nodate += 1
    else:
        if sale_year == '2005':
            num_non_sales_2005 += 1
        elif sale_year == '2009':
            num_non_sales_2009 += 1
        else:
            num_non_sales_nodate += 1

print "Sales (2005): ", num_real_sales_2005
print "Fake sales (2005): ", num_non_sales_2005
print "Total (2005): ", num_real_sales_2005 + num_non_sales_2005
print "----------"
print "Sales (2009): ", num_real_sales_2009
print "Fake sales (2009): ", num_non_sales_2009
print "Total (2009): ", num_real_sales_2009 + num_non_sales_2009
print "----------"
print "Sales (nodate): ", num_real_sales_nodate
print "Fake sales (nodate): ", num_non_sales_nodate
print "Total (nodate): ", num_real_sales_nodate + num_non_sales_nodate
print "----------"
print "Unique sales: ", len(set(rows)) # check to make sure sales aren't listed multiple times