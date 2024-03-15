#!/usr/bin/env python3

"""
# Add additional information to MPC Code list and save it to a local file
  Usage: mpccode.py
 		
(C) Quanzhi Ye
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
import json, math
import re

def calculate_latitude(rho_sin_phi, rho_cos_phi):
    latitude = math.atan2(rho_sin_phi, rho_cos_phi)
    return math.degrees(latitude)  # Convert radians to degrees

def parse_table_entry(entry):
    if len(entry.strip()) < 3:
        return None  # Ignore entries with less than 3 characters

    # Extracting data using regular expressions
    match = re.match(r'(\w{3})\s+(\d+\.\d+)\s*(0\.\d+)\s*(\+|-)?(0\.\d+)\s*(.*)', entry)
    match1 = re.match(r'(\w{3})\s+(\w+)', entry)
    if match:
        longitude = float(match.group(2))
        cos_val = float(match.group(3))
        sign = match.group(4)
        if sign is None:
            sign = ""
        sin_val = float(sign + match.group(5))
        name = match.group(6).strip()
        latitude = calculate_latitude(sin_val, cos_val)  
        if longitude == 0 and latitude == 0:
            return {
                'name': name,
            }
        
        location = geolocator.reverse(str(latitude)+","+str(longitude), language='en')
        if location is None:
            return {
                'name': name,
                'lon': longitude,
                'lat': latitude,
            }

        address = location.raw['address']
        return {
                'name': name,
                'country': address.get('country', ''),
                'state': address.get('state', ''),
                'county': address.get('county', ''),
                'city': address.get('city', ''),
                'lon': longitude,
                'lat': latitude,
            }
    
    elif match1:
        return {
            'name': match1.group(2)
        }
    else:
        print(entry)
        raise ValueError("Invalid input format")

mpccode = "https://www.minorplanetcenter.net/iau/lists/ObsCodes.html"

# download MPC code file
html = urlopen(mpccode).read()
soup = BeautifulSoup(html, features="lxml")
mpccode = soup.get_text()
mpccode = list(filter(None, mpccode.split('\n')))
o = ""

geolocator = Nominatim(user_agent="MPECWatch", timeout=10)

d = dict()

for line in mpccode[1:-1]:
    code = str(line[0:3])
    d[code] = {}
 
    entry_data = parse_table_entry(line)

    d[code] = entry_data
    # if float(i[19:29]) == 0 and float(i[8:16]) == 0:
    #     d[str(i[3:6])][' name'] = i[79:].strip()
    # else:
    #     location = geolocator.reverse(str(float(i[19:29]))+","+i[8:16], language='en')
    #     address = location.raw['address']
    #     d[str(i[3:6])]['name'] = i[79:].strip()
    #     d[str(i[3:6])]['country'] = address.get('country', '') 
    #     d[str(i[3:6])]['state'] = address.get('state', '')
    #     d[str(i[3:6])]['county'] = address.get('county', '')
    #     d[str(i[3:6])]['city'] = address.get('city', '')
    #     d[str(i[3:6])]['lon'] = float(i[8:16])
    #     d[str(i[3:6])]['lat'] = float(i[19:29])
    #     d[str(i[3:6])]['elev'] = float(i[31:40])

with open('mpccode.json', 'w') as o:
    json.dump(d, o)
