#!/usr/bin/python
# 2013 Kyle Fitzsimmons

import time
import arcpy
from arcpy import env

script_start = time.time()

# set ArcPy environment
env.workspace = 'C:/Users/kyle/Documents/ArcGIS/mls_db.gdb'

#set layers
inFeatures = 'centroids'
outFeatureClass = 'C:/Users/kyle/Documents/ArcGIS/mls_db.gdb/ring_buffers'

# concentric buffers of 500m for 30.5km (furthest edge of island)
distances = [x for x in range(2000, 30001, 2000)]
print "Number of buffers: ", len(distances), " - ", distances
bufferUnit = 'meters'
arcpy.MultipleRingBuffer_analysis(inFeatures, outFeatureClass, distances, '', 'ALL')

time_taken = time.time() - script_start
print "Success ({} sec.)".format(time_taken)
