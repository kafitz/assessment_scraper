#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import dataset
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

db = dataset.connect('sqlite:///../../data/databases/2005_distmatrix.sqlite')
sales_assessment_iter = db.query('''SELECT id,
                                        total_property_value_2007 AS assessed_value, 
                                        price_sold_1,
                                        price_sold_2,
                                        price_sold_3, 
                                        property_code,
                                        distance as cbd_distance
                                    FROM "2005_distmatrix"
                                ''')
sales_assessments = [x for x in sales_assessment_iter]

points = {
            'x': [],
            'y': []
    }

for item in sales_assessments:
    if not item['price_sold_1'] or not item['assessed_value']:
        # skip if either price_sold or assessed_value has no corresponding value
        continue
    price_difference = int(item['price_sold_1']) - int(item['assessed_value'])
    points['x'].append(float(item['cbd_distance']))
    points['y'].append(price_difference)
    if item['price_sold_2']:
        price_difference = int(item['price_sold_2']) - int(item['assessed_value'])
        points['x'].append(float(item['cbd_distance']))
        points['y'].append(price_difference)
    if item['price_sold_3']:
        price_difference = int(item['price_sold_3']) - int(item['assessed_value'])
        points['x'].append(float(item['cbd_distance']))
        points['y'].append(price_difference)

fig, ax = plt.subplots()
plot_points = ax.scatter(points['x'], points['y'], c='b', marker='o', alpha=0.5)
plt.ylim(ymin=-700000, ymax=700000)
plt.xlim(xmin=0)
ax.set_title('Price Difference [2005] to Distance From CBD')
ax.set_xlabel('Distance (m) from CBD', fontsize=15)
ax.set_ylabel('Sale Price - Assessed Value', fontsize=15)

plt.savefig('../../plots/price_diff_from_cbd_2005.png')
# plt.show()