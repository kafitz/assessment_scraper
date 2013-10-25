#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import dataset
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# load database to lists for prototyping
db = dataset.connect('sqlite:///../../data/databases/clean_mls_data.sqlite')
sales_assessment_iter = db.query('''SELECT id,
                                        total_property_value_2011 AS assessed_value, 
                                        price_sold_1 as price_sold, 
                                        property_code
                                    FROM "clean_2009_sales"
                                ''')
sales_assessments = [x for x in sales_assessment_iter]

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
        if not item['price_sold'] or not item['assessed_value']:
            continue
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
            # price_diffs.append((price_diff / total_property_value, total_property_value, price_sold))
            continue
        ## upper bound
        # exclude properties sold for greater than x times its value
        if price_sold > (total_property_value * 5):
            continue

        # create lists for pandas dataframe
        points['price_sold'].append(price_sold)
        points['assessed_value'].append(total_property_value)

        ratio = total_property_value / price_sold
        if ratio == 1:            
            points['blue_x'].append(price_sold)
            points['blue_y'].append(total_property_value)
        if ratio > 1:
            points['green_x'].append(price_sold)
            points['green_y'].append(total_property_value)
            points['gt_price_diffs'].append(price_diff)
        if ratio < 1:
            points['red_x'].append(price_sold)
            points['red_y'].append(total_property_value)
            points['lt_price_diffs'].append(price_diff)
    return points

def plot_assessment_to_sales_price(points):
    fig, ax = plt.subplots()
    blue_points = ax.scatter(points['blue_x'], points['blue_y'], c='b', marker='o', alpha=0.5)
    green_points = ax.scatter(points['green_x'], points['green_y'], c='g', marker='o', alpha=0.5)
    red_points = ax.scatter(points['red_x'], points['red_y'], c='r', marker='o', alpha=0.5)

    plt.xlim(xmin=0, xmax=7000000)
    plt.ylim(ymin=0, ymax=7000000)
    ax.set_title('Assessment Value [2011] to Price Sold [2009]')
    ax.set_xlabel('Assessed Value', fontsize=15)
    ax.set_ylabel('Price Sold', fontsize=15)
    
    
    # best fit line
    line = [(points['best_fit'][0] * x + points['best_fit'][1]) for x in points['assessed_value']]
    plt.plot(points['assessed_value'], line, 'y-')

    # save plot
    plt.savefig('../../plots/assessment_2009.png')

if __name__ == '__main__':
    points = create_data_dict(sales_assessments)
    df_input = []
    for entry in sales_assessments:
        if not entry['price_sold'] or not entry['assessed_value']:
            continue    
        df_input.append({
                            'price_sold': float(entry['price_sold']),
                            'assessed_value': float(entry['assessed_value']),
                        })
    df = pd.DataFrame(df_input)
    # calculate degree of correlation between sales prices
    test_r = r = np.corrcoef(df['assessed_value'].tolist(), df['price_sold'].tolist())[0,1]
    r = np.corrcoef(points['assessed_value'], points['price_sold'])[0,1]

    # find line of best-fit
    A = np.array([ points['assessed_value'], np.ones(len(points['assessed_value'])) ])
    points['best_fit'] = np.linalg.lstsq(A.T, points['price_sold'])[0]

    print "Number of sales equal to assessment price: ", len(points['blue_x'])
    print "Number of sales above assessment price: ", len(points['green_x'])
    print "gt cum. sum: ", sum(points['gt_price_diffs'])
    print "Number of sales below assessment price: ", len(points['red_x'])
    print "lt cum. sum: ", sum(points['lt_price_diffs'])
    print "Linear regression slope: ", points['best_fit'][0]
    print "Linear regression y-intercept: ", points['best_fit'][1]
    print "R-squared value (unbounded): ", test_r ** 2
    print "R-squared value (bounded): ", r ** 2

    plot_assessment_to_sales_price(points)
