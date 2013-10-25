#!/usr/bin/env python
# Kyle Fitzsimmons, 2012

def format_streetname(street_name):
    '''Make replacements necessary for inputting to website form'''
    orientations = ['N', 'S', 'E', 'O']
    street_name = street_name.upper()
    if street_name[:2] == "D'":  # only replace if starts the name
        street_name = street_name.replace("D'", "")
    if street_name[:2] == "L'":  # only replace if starts the name
        street_name = street_name.replace("L'", "")
    street_name = street_name.replace("'", " ")
    street_name = street_name.replace("-", " ")
    street_name = street_name.replace(".", "")
    street_name = street_name.replace(" ST ", " SAINT ")
    street_name = street_name.replace(" STE ", " SAINTE ")
    if street_name[:3] == "ST ":
        street_name = street_name.replace("ST ", "SAINT ")
    if street_name[:4] == "STE ":
        street_name = street_name.replace("STE ", "SAINTE ")
    if street_name[-2:] in [str(' ' + o) for o in orientations]:
        street_name = street_name[:-2]
    return street_name.title()