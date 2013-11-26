#!/usr/bin/python
# 2013 Kyle Fitzsimmons
'''Iterates through massive shapefiles which freeze QGIS and ArcMap to
    clean out unnecessary records.'''

import os
import ogr


# set shapefile directory
os.chdir('/Users/kyle/Downloads/ArcView/NAD83/EPOI/CANADA')

# Connect to shapefile source
driver = ogr.GetDriverByName('ESRI Shapefile')
data_source = driver.Open('CANADA.shp')
in_layer = data_source.GetLayerByIndex(0)
# Create output shapefile
out_fn = 'Montreal_POIs.shp'
if os.path.exists(out_fn):
    driver.DeleteDataSource(out_fn)
out_shpfile = driver.CreateDataSource(out_fn)
out_layer = out_shpfile.CreateLayer('Montreal_POIs', geom_type=ogr.wkbPoint)
# Copy the fields from the input shapefile to the output
model_row = in_layer.GetFeature(0)
for field_name in model_row.keys():
    out_layer.CreateField(model_row.GetFieldDefnRef(field_name))
feature_defn = out_layer.GetLayerDefn()

number_of_features = in_layer.GetFeatureCount()
index = 0.0
in_feature = in_layer.GetNextFeature()
while in_feature:
    progress_percentage = (index / number_of_features) * 100
    province = in_feature.GetField('PROV')
    print province, "{:.3f}% of {}".format(progress_percentage, number_of_features),
    
    if province == 'QC':
        out_feature = ogr.Feature(feature_defn)
        geom = in_feature.GetGeometryRef()
        out_feature.SetGeometry(geom)
        for key, value in in_feature.items().iteritems():
            out_feature.SetField(key, value)
        out_layer.CreateFeature(out_feature)
        out_feature.Destroy()
        print 'kept'
    else:
        print 'ignored'

    in_feature.Destroy()
    in_feature = in_layer.GetNextFeature()
    index += 1

data_source.Destroy()
out_shpfile.Destroy()
