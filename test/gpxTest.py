# Test script to write a new lat and long to the fi_collar.gpx file

import time
import os
from datetime import datetime

# test location coordinates
EllaBailey = (47.64375334268604, -122.38680748333081)
Bayview = (47.644121466230025, -122.38636588707352)
NorthPlayfield = (47.645087965391916, -122.39959020734445)
SouthPlayfield = (47.641543779792684, -122.39898679386312)

# list of test locations
locations = [EllaBailey, Bayview, NorthPlayfield, SouthPlayfield]

# loop over the locations
for i, (latitude, longitude) in enumerate(locations):
    # get the current time in ISO 8601 format
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")

    # write the lat and long to the fi collar gpx file
    location_path = "/home/alexh/Fiinder/fi_collar.gpx"
    with open(location_path, "w") as f:
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f.write("<gpx version=\"1.1\" creator=\"Fiinder\" xmlns=\"http://www.topografix.com/GPX/1/1\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd\">\n")
        f.write("  <wpt lat=\"{:.6f}\" lon=\"{:.6f}\">\n".format(latitude, longitude))
        f.write("    <name>Bruce</name>\n")
        f.write("    <time>{}</time>\n".format(timestamp))
        f.write("  </wpt>\n")
        f.write("</gpx>\n")
    
    # print a message indicating that the GPX file has been updated
    print("Updated the GPX file with location {}".format(i+1))

    # wait for 30 seconds before moving to the next location
    time.sleep(30)