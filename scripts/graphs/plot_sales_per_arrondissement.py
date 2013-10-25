#!/usr/bin/env python
# Kyle Fitzsimmons, 2013

import dataset
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

db = dataset.connect('sqlite:///../../data/databases/2009_distmatrix.sqlite')
sales_assessment_iter = db.query('''SELECT id,
                                        total_property_value_2011 as assessed_value,
                                        price_sold_1,
                                        price_sold_2,
                                        price_sold_3,
                                        property_code,
                                        geocoded_arrondissement
                                    FROM "2009_distmatrix"
                                    ''')

sales_assessments = [x for x in sales_assessment_iter]
arrondissement_names = sorted(list(set([x['geocoded_arrondissement'] for x in sales_assessments])))
arrondissement_points = dict((arrondissement, 0) for arrondissement in arrondissement_names)

for assessment in sales_assessments:
    if not assessment['price_sold_1'] or not assessment['assessed_value']:
        continue
    arrondissement_points[assessment['geocoded_arrondissement']] += 1

heights = []
for arrondissement in arrondissement_names:
    heights.append(arrondissement_points[arrondissement])
bar_heights = tuple(heights)

ind = np.arange(len(bar_heights))
width = .66

fig = plt.figure(figsize=(12, 6))
# gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1])
ax = plt.subplot(111)

rects = ax.bar(ind, bar_heights, width, color='b')
ax.set_ylabel('Sales')
ax.set_title('Sales per Arrondissement [2009]')
ax.set_xticks(ind + width / 2)
# align label 'right', reverse to match heights order, rotate 30 degrees, tuple expected by matplotlib
ax.set_xticklabels(tuple(arrondissement_names), rotation=30, ha='right')
# add number labels above each bar
for rect in rects:
    height = rect.get_height()
    ax.text(rect.get_x() + rect.get_width() / 2, 1.05 * height, '%d' % int(height),
                ha='center', va='bottom')

plt.ylim(ymin=0, ymax=1400)
fig.tight_layout()
# plt.show()
plt.savefig('../../plots/sales_per_arrondissement_2009.png')