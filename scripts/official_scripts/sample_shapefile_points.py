#!/usr/bin/env python
# Kyle Fitzsimmons 2013

import shapefile

POINTS_JOINED_REGIONS = 'correlated_sale_points_municipalities'
REGION_BASEMAP = 'assessment_role_regions'
OUTPUT_SHAPEFILE = 'assessment_role_regions_correlated'


points_sf = shapefile.Reader(POINTS_JOINED_REGIONS)
points_records = points_sf.records()

# create a dict of polygon regions each with a list of roll_codes from the joined polygon_name
points_by_regions = {}
for p_record in points_records:
    # init dict structure for new regions
    if not points_by_regions.get(p_record[-3]):
        points_by_regions[p_record[-3]] = []
    # points_by_regions[region_name] = [list of codes]
    points_by_regions[p_record[-3]].append(int(p_record[5]))

# find the most common role code for each region name
region_codes = {}
for region in points_by_regions:
    code = max(set(points_by_regions[region]), key=points_by_regions[region].count)
    region_codes[region] = code

# join code to original (pre-join from step 1) regional shapefile
regions_sf = shapefile.Reader(REGION_BASEMAP)
regions_records = regions_sf.records()
output_sf = shapefile.Writer()
output_sf.fields = list(regions_sf.fields)
output_sf.field('CODE_INT', 'N', '40')

for reg_record in regions_records:
    if region_codes.get(reg_record[0]):
        reg_record.append(region_codes[reg_record[0]])
    else:
        reg_record.append(None)
    output_sf.records.append(reg_record)

output_sf._shapes.extend(regions_sf.shapes())
output_sf.save(OUTPUT_SHAPEFILE)

# copy old projection file
old_prj = open('%s.prj' % POINTS_JOINED_REGIONS, 'rb')
epsg = old_prj.read()
new_prj = open('%s.prj' % OUTPUT_SHAPEFILE, 'wb')
new_prj.write(epsg)
new_prj.close()
