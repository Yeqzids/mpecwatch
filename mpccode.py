#!/usr/bin/env python3

"""
# Add additional information to MPC Code list and save it to a local file
  Usage: mpccode.py
 		
(C) Quanzhi Ye
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

mpccode = "https://www.projectpluto.com/mpc_stat.txt"

# download MPC code file
html = urlopen(mpccode).read()
soup = BeautifulSoup(html, features="lxml")
mpccode = soup.get_text()
mpccode = list(filter(None, mpccode.split('\n')))
o = ""

geolocator = Nominatim(user_agent="geoapiExercises")

for i in mpccode[1:-1]:
	if float(i[19:29]) == 0 and float(i[8:16]) == 0:
		if i[3:6] == '244':
			o += '{:3s} {:20s}  {:50s}\n'.format(i[3:6], 'Other', i[79:].strip())
		elif i[3:6] == '247':
			o += '{:3s} {:20s}  {:50s}\n'.format(i[3:6], 'Other', i[79:].strip())
		elif i[3:6] == '500':
			o += '{:3s} {:20s}  {:50s}\n'.format(i[3:6], 'Other', i[79:].strip())
		else:
			o += '{:3s} {:20s}  {:50s}\n'.format(i[3:6], 'Spacecraft', i[79:].strip())
	else:
		location = geolocator.reverse(str(float(i[19:29]))+","+i[8:16], language='en')
		address = location.raw['address'] 
		country = address.get('country', '') 
		o += '{:3s} {:20s}  {:50s}\n'.format(i[3:6], country, i[79:].strip())
	print(i[3:6] + ' ' + country)

with open('mpccode_trim.txt', 'w') as f:
	f.write(o)
