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

# Constants
EARTH_MAJOR_AXIS = 6378137.0
EARTH_MINOR_AXIS = 6356752.314140347

def calculate_latitude(rho_sin_phi, rho_cos_phi):
    a = 1
    b = EARTH_MINOR_AXIS / EARTH_MAJOR_AXIS
    fy = abs(rho_sin_phi)
    fx = abs(rho_cos_phi)

    if rho_cos_phi == 0:
        lat = math.pi / 2
    else:
        c_squared = a * a - b * b
        e = (b * fy - c_squared) / (a * fx)
        f = (b * fy + c_squared) / (a * fx)
        p = (4. / 3.) * (e * f + 1.)
        q = 2. * (e * e - f * f)
        d = p * p * p + q * q

        if d >= 0:
            sqrt_d = math.sqrt(d)
            v = math.pow(sqrt_d - q, 1/3) - math.pow(sqrt_d + q, 1/3)

        else:
            sqp = math.sqrt(-p)
            temp_ang = math.acos( q / (sqp * p))

            v = 2 * sqp * math.cos(temp_ang / 3)

        g = (math.sqrt(e * e + v) + e) * .5
        t = math.sqrt(g * g + (f - v * g) / (2. * g - e)) - g
        lat = math.atan2(a * (1. - t * t), 2. * b * t)

    if rho_sin_phi < 0:
        lat = -lat
    if rho_cos_phi < 0:
        lat = math.pi - lat
    return math.degrees(lat)  # Convert radians to degrees

def parse_table_entry(entry):
    if len(entry.strip()) < 3:
        return None  # Ignore entries with less than 3 characters

    # Extracting data using regular expressions
    match = re.match(r'(\w{3})\s+(\d+\.\d+)\s*(\d+\.\d+)\s*(\+|-)?(0\.\d+)\s*(.*)', entry)
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

for line in mpccode[1:]:
    code = str(line[0:3])
    d[code] = parse_table_entry(line)

with open('mpccode.json', 'w') as o:
    json.dump(d, o)
