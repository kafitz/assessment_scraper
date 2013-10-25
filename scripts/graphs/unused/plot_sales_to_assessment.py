#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import dataset
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
# import sqlite3
# import pandas.io.sql as pd_sql

from IPython import embed

# load database to lists for prototyping
db = dataset.connect('sqlite:///../../data/full_mls_db.sqlite')
sales_assessment_iter = db.query('''SELECT id,
                                        total_property_value_2011 AS assessed_value, 
                                        price_sold, 
                                        property_code
                                    FROM "clean_2009_sales"
                                ''')
sales_assessments = [x for x in sales_assessment_iter]

def pandas_stuff():
    # load database to pandas dataframe
    conn = sqlite3.connect('../../data/full_mls_db.sqlite')
    test_data = pd_sql.read_frame('''SELECT id,
                                            total_property_value_2011 AS assessed_value, 
                                            price_sold, 
                                            property_code
                                        FROM "clean_2009_sales"
                                    ''', conn)

def create_data_dict(sales_assessments):
    '''Create lists correlated by index for plotting x and y values'''
    points = {
                'blue_x': [],
                'blue_y': [],
                'green_x': [],
                'green_y': [],
                'red_x': [],
                'red_y': [],
                'gt_price_diffs': [],
                'lt_price_diffs': [],
                'price_sold': [],
                'assessed_value': []
            }

    for item in sales_assessments:
        price_sold = float(item['price_sold'])
        total_property_value = float(item['assessed_value'])
        property_code = item['property_code']

        ### determine bounds of data
        ## property type
        # exclude commercial propertuies
        if property_code in ['PCI']:
            continue
        price_diff = price_sold - total_property_value
        ## lower bound
        # exclude properties sold for less than x times its value
        if price_sold < (total_property_value * 0.2):
            continue
        ## upper bound
        # exclude properties sold for greater than x times its value
        if price_sold > (total_property_value * 5):
            continue

        # create lists for pandas dataframe
        points['price_sold'].append(price_sold)
        points['assessed_value'].append(total_property_value)

        ratio = price_sold / total_property_value
        if ratio == 1:
            points['blue_x'].append(total_property_value)
            points['blue_y'].append(price_sold)
        if ratio > 1:
            points['green_x'].append(total_property_value)
            points['green_y'].append(price_sold)
            points['gt_price_diffs'].append(price_diff)
        if ratio < 1:
            points['red_x'].append(total_property_value)
            points['red_y'].append(price_sold)
            points['lt_price_diffs'].append(price_diff)
    return points

def plot_sales_price_to_assessment(points):
    fig, ax = plt.subplots()
    blue_points = ax.scatter(points['blue_x'], points['blue_y'], c='b', marker='o', alpha=0.5)
    green_points = ax.scatter(points['green_x'], points['green_y'], c='g', marker='o', alpha=0.5)
    red_points = ax.scatter(points['red_x'], points['red_y'], c='r', marker='o', alpha=0.5)

    plt.xlim(xmin=0, xmax=7000000)
    plt.ylim(ymin=0, ymax=7000000)
    ax.set_title('Price Sold [2009] to Assessment Value [2011]')
    ax.set_xlabel('Price Sold', fontsize=15)
    ax.set_ylabel('Assessed Value', fontsize=15)
    
    # best fit line
    line = [(points['best_fit'][0] * x + points['best_fit'][1]) for x in points['price_sold']]
    plt.plot(points['price_sold'], line, 'y-')

    # show plot
    plt.show()
    # plt.savefig('../../sales_2009.png')

points = create_data_dict(sales_assessments)
df_input = []
for entry in sales_assessments:
    df_input.append({
                        'price_sold': entry['price_sold'],
                        'assessed_value': entry['assessed_value'],
                    })
df = pd.DataFrame(df_input)
# calculate degree of correlation between sales prices
test_r = r = np.corrcoef(df['price_sold'].tolist(), df['assessed_value'].tolist())[0,1]
r = np.corrcoef(points['price_sold'], points['assessed_value'])[0,1]

# find line of best-fit
A = np.array([ points['price_sold'], np.ones(len(points['price_sold'])) ])
points['best_fit'] = np.linalg.lstsq(A.T, points['assessed_value'])[0]

print "Number of sales equal to assessment price: ", len(points['blue_x'])
print "Number of sales above assessment price: ", len(points['green_x'])
print "gt cum. sum: ", sum(points['gt_price_diffs'])
print "Number of sales below assessment price: ", len(points['red_x'])
print "lt cum. sum: ", sum(points['lt_price_diffs'])
print "Linear regression slope: ", points['best_fit'][0]
print "Linear regression y-intercept: ", points['best_fit'][1]
print "R-squared value (unbounded): ", test_r ** 2
print "R-squared value (bounded): ", r ** 2

plot_sales_price_to_assessment(points)
