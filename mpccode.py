#!/usr/bin/env python3

"""
# Add additional information to MPC Code list and save it to a local file
  Usage: mpccode.py
 		
(C) Quanzhi Ye
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
import json

mpccode = "https://www.projectpluto.com/mpc_stat.txt"

# download MPC code file
html = urlopen(mpccode).read()
soup = BeautifulSoup(html, features="lxml")
mpccode = soup.get_text()
mpccode = list(filter(None, mpccode.split('\n')))
o = ""

geolocator = Nominatim(user_agent="geoapiExercises")

d = dict()

for i in mpccode[1:-1]:
    d[str(i[3:6])] = {}
    if float(i[19:29]) == 0 and float(i[8:16]) == 0:
        d[str(i[3:6])]['name'] = i[79:].strip()
    else:
        location = geolocator.reverse(str(float(i[19:29]))+","+i[8:16], language='en')
        address = location.raw['address']
        d[str(i[3:6])]['name'] = i[79:].strip()
        d[str(i[3:6])]['country'] = address.get('country', '') 
        d[str(i[3:6])]['state'] = address.get('state', '')
        d[str(i[3:6])]['county'] = address.get('county', '')
        d[str(i[3:6])]['city'] = address.get('city', '')
        d[str(i[3:6])]['lon'] = float(i[8:16])
        d[str(i[3:6])]['lat'] = float(i[19:29])
        d[str(i[3:6])]['elev'] = float(i[31:40])

with open('mpccode.json', 'w') as o:
    json.dump(d, o)
