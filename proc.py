#!/usr/bin/env python3

"""
# Process MPECs in a given month and write the information to the database
  Usage: proc.py YYYYMM
 		YYYYMM	-	year/month to be process
 		
Database structure
---

	Key			Type		Description
TABLE MPEC: (summary of each MPEC)
	MPECId		TEXT		MPEC Number
	Title		TEXT		MPEC Title
	Time		TEXT		Publication datetime
	Station		TEXT		List of observatory stations involved in the observation. Only used when MPECType is Discovery, OrbitUpdate, or DOU		
	DiscStation	TEXT		Observatory station marked by the discovery asterisk. Only used when MPECType is Discovery.
	FirstConf	TEXT		First observatory station to confirm. Only used when MPECType is Discovery.
	MPECType	TEXT		Type of the MPEC: Editorial, Discovery, OrbitUpdate, DOU, ListUpdate, Other
	ObjectType	TEXT		Type of the object: NEA, Comet, Satellite, TNO, Unusual. Only used when MPECType is Discovery or OrbitUpdate
	
TABLE XXX (observatory code):
	Object		TEXT		Object designation in packed form
	Time		TEXT		Time of the observation
	Observer	TEXT		List of observers as published in MPEC
	Measurer	TEXT		List of measurers as published in MPEC
	Facility	TEXT		List of telescope/instrument as published in MPEC
	MPEC		TEXT		MPECId
	MPECType	TEXT		Type of the MPEC: Discovery, OrbitUpdate, DOU
	ObjectType	TEXT		Type of the object: NEA, Comet, Satellite, TNO, Unusual
	Discovery	INTEGER		Corresponding to discovery asterisk
"""

import sqlite3, os, datetime as dt, numpy as np, sys, re
from urllib.request import urlopen
from bs4 import BeautifulSoup

ym = sys.argv[1]
dbFile = 'mpecwatch.db'

def month_to_letter(month):		# turn month into letter following MPC scheme
	if month == '01':
		return(['A', 'B'])
	elif month == '02':
		return(['C', 'D'])
	elif month == '03':
		return(['E', 'F'])
	elif month == '04':
		return(['G', 'H'])
	elif month == '05':
		return(['J', 'K'])
	elif month == '06':
		return(['L', 'M'])
	elif month == '07':
		return(['N', 'O'])
	elif month == '08':
		return(['P', 'Q'])
	elif month == '09':
		return(['R', 'S'])
	elif month == '10':
		return(['T', 'U'])
	elif month == '11':
		return(['V', 'W'])
	elif month == '12':
		return(['X', 'Y'])
	else:
		exit('Wrong month!')
		
# the below code is from http://stackoverflow.com/questions/1119722/base-62-conversion
BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def encode(num, alphabet=BASE62):
	"""Encode a positive number in Base X
	Arguments:
	- `num`: The number to encode
	- `alphabet`: The alphabet to use for encoding
	"""
	if num == 0:
		return alphabet[0]
	arr = []
	base = len(alphabet)
	while num:
		num, rem = divmod(num, base)
		arr.append(alphabet[rem])
	arr.reverse()
	return ''.join(arr)

def decode(string, alphabet=BASE62):
	"""Decode a Base X encoded string into the number
	Arguments:
	- `string`: The encoded string
	- `alphabet`: The alphabet to use for encoding
	"""
	base = len(alphabet)
	strlen = len(string)
	num = 0
	idx = 0
	for char in string:
		power = (strlen - (idx + 1))
		num += alphabet.index(char) * (base ** power)
		idx += 1
	return num
# code borrow ended

def month_string_to_number(string):
	# from https://stackoverflow.com/questions/3418050/month-name-to-month-number-and-vice-versa-in-python
    m = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr': 4,
        'may': 5,
        'jun': 6,
        'jul': 7,
        'aug': 8,
        'sep': 9,
        'oct': 10,
        'nov': 11,
        'dec': 12
        }
    s = string.strip()[:3].lower()

    try:
        out = m[s]
        return out
    except:
        raise ValueError('Not a month')

def id_title_time(mpec_text):
	mpecid, title = mpec_text[0].split(": ")
	mpecid = mpecid.strip()			# MPECs before 100 has an extra space at the end
	tt = [s for s in mpec_text if s.startswith(mpecid.replace('MPEC', 'M.P.E.C.'))][0]
	if mpecid == 'MPEC 2000-G02':			# weird bug in these MPECs, time has no UT
		time = re.search('Issued (.*)', tt).group(1).split(" ")
	else:
		time = re.search('Issued (.*) UT', tt).group(1).split(" ")
	time = list(filter(None, time))
	if len(time) == 3:		# some MPEC has missed space between month and date (e.g. 1998-R22 to R25)
		datetime_string = time[0] + '-' + str('%02i' % month_string_to_number(time[1][:-3])) + '-' + '%02i' % int(float(time[1][-3:-1])) + ' ' + time[2] + ':00'
	elif len(time) == 4:
		datetime_string = time[0] + '-' + str('%02i' % month_string_to_number(time[1])) + '-' + '%02i' % int(float(time[2][:-1])) + ' ' + time[3] + ':00'
	return([mpecid, title, datetime_string])
	

def find_mpec_type(mpec_text):
	"""
	Determine the type of the MPEC. Can be the following:
	---
	* Editorial
	* Discovery
	* OrbitUpdate
	* DOU
	* ListUpdate
	* Other
	"""
	
	if 'editorial' in mpec_text[0].lower():
		return('Editorial')
	elif any(s.startswith('Observer details:') for s in mpec_text):
		if any(s.startswith('*', 12, 13) for s in mpec_text):
			if ' = ' in mpec_text[0].lower():		# some comet recoveries can contain discovery asterisks
				return('OrbitUpdate')
			else:
				return('Discovery')
		else:
			return('OrbitUpdate')
	elif any(s.startswith('Orbital elements:') for s in mpec_text) and any(s.startswith('Ephemeris:') for s in mpec_text) or 'precoveries' in mpec_text[0].lower():
		return('OrbitUpdate')
	elif 'daily orbit update' in mpec_text[0].lower():
		return('DOU')
	elif any(s in mpec_text[0].lower() for s in ['observable comets', 'distant minor planets', 'critical-list minor planets', \
	'atens and apollos', 'amors', 'unusual minor planets', 'phas']):
		return('ListUpdate')
	else:
		return('Other')
		
def find_obj_type(mpec_text):
	"""
	Determine the object type of the MPEC; MPEC type needs to be 'Discovery' or 'OrbitUpdate'. Can be the following:
	---
	* NEA
	* Comet
	* Satellite
	* TNO
	* Unusual
	"""
	
	if 'comet' in mpec_text[0].lower() or 'sungrazer' in mpec_text[0].lower() or 'c/' in mpec_text[0].lower() or 'a/' in mpec_text[0].lower():
		return('Comet')
	elif 's/' in mpec_text[0].lower():
		return('Satellite')
	elif 'tno' in mpec_text[0].lower():
		return('TNO')
	elif any('Outer Solar System Survey' in s for s in mpec_text):		# certain MPECs do not have 'TNO' flag in their titles, e.g. 1999-L24
		return('TNO')
	elif 'M.P.E.C. 1999-S18' in mpec_text[0] or 'M.P.E.C. 2000-F36' in mpec_text[0] or 'M.P.E.C. 2005-Y55' in mpec_text[0]:			# correct for weird title bug for some MPECs
		return('Comet')
	elif 'MPEC 2000-V09' in mpec_text[0]:			# older format MPECs, easier to do this quick fix
		return('TNO')
	elif 'precoveries' in mpec_text[0].lower():			# rare MPECs that does not have orbits
		return('NEA')
	else:
		if len([s for s in mpec_text if 'a,e,i = ' in s]) > 0:
			tt = [s for s in mpec_text if 'a,e,i = ' in s][0]
			if 'q = ' in tt:
				qq = float(tt.split('q = ')[-1])
			else:
				tt = tt.split('a,e,i = ')[-1].split(',')
				qq = float(tt[0]) * (1-float(tt[1]))
		else:
			for s in mpec_text:
				if s.startswith('a '):
					aa = float(s[2:15])
				elif s.startswith('e '):
					ee = float(s[2:15])
					break
			qq = aa * (1 - ee)
		
		if qq < 1.3:
			return('NEA')
		elif qq > 29.5:
			return('TNO')
		else:
			return('Unusual')
			
def observer_measurer_facility(obs_details, code):
	obs_line = ''

	tt = False
	for line in obs_details:
		if tt:
			if line[0:3] == '   ':
				if line[4:5].isdigit():			# MPEC skips spaces at linebreaks
					obs_line += ' ' + line[3:]
				elif line[4:].startswith('Measurer'):	# same as above
					obs_line += ' ' + line[3:]
				else:
					obs_line += line[3:]
			else:
				tt = False
		
		if line[0:3] == code:
			tt = True
			obs_line += line

	obs_line = obs_line.split('  ')
	
	observer = ''
	measurer = ''
	facility = ''
	
	obs_line = list(filter(None, obs_line))
	
	for obs_line0 in obs_line:
		if obs_line0.startswith('Observer'):
			tt = obs_line0.split('-m')[0]		# fix some older MPECs that has formatting issues
			tt = obs_line0.split(' Measurer')[0]		# fix some older MPECs that has formatting issues
			if tt[-1:] == '.':
				tt = tt[:-1]
			observer = ' '.join(tt.split(' ')[1:])
			observer = observer.replace(' and ', ', ')
			if re.search(r'\d', observer):		# older MPEC might be difficult to deal with; default to nothing
				observer = ''
				
			# remove certain strings from the observer variable:
			observer = observer.replace(' for the NEAT team', '')
			observer = observer.replace(', for the Spacewatch Outer Solar System Survey', '')
				
		elif obs_line0.startswith('Measurer'):
			measurer = ' '.join(obs_line0.split(' ')[1:])[:-1]
			measurer = measurer.replace(' and ', ', ')
			if re.search(r'\d', measurer):		# older MPEC might be difficult to deal with; default to nothing
				measurer = ''
		elif obs_line0[0].isdigit() and not obs_line0[3:4] == ' ':
			tt = obs_line0.split(' Observer')[0]		# fix some older MPECs that has formatting issues
			if tt[-1:] == '.':
				tt = tt[:-1]
			facility = tt.split('. ')[0]
		else:
			pass
	
	return([observer, measurer, facility])

########
# main #
########

if ym[0:2] == '19':
	century = 'J'
elif ym[0:2] == '20':
	century = 'K'
else:
	exit('Year needs to be 19xx or 20xx.')

if os.path.isfile(dbFile):
	db = sqlite3.connect(dbFile)
	cursor = db.cursor()
else:
	db = sqlite3.connect(dbFile)
	cursor = db.cursor()
	cursor.execute('''CREATE TABLE MPEC(MPECId TEXT, Title TEXT, Time TEXT, Station TEXT, DiscStation TEXT, FirstConf TEXT, MPECType TEXT, ObjectType TEXT)''')
	db.commit()

for halfmonth in month_to_letter(ym[4:6]):
	for i in list(np.arange(1, 999, 1)):
		obs_code_collection = []
		disc_obs_code = []
		
		# check if this MPEC is in the database; if yes, pass this one
		this_mpec = 'MPEC ' + ym[0:4] + '-' + halfmonth + '%02i' % i
		cursor.execute("SELECT * FROM MPEC WHERE MPECId = '" + this_mpec + "'")
		query_result_size = len(cursor.fetchall())
		if query_result_size > 0:		# this MPEC exists in database
			continue
		
		# TBW
				
		# read and parse the MPEC
		tens_digit = encode(int(np.floor(i/10)))
		ones_digit = i - np.floor(i/10)*10
		url = 'https://www.minorplanetcenter.net/mpec/' + century + ym[2:4] + '/' + century + ym[2:4] + halfmonth + str(tens_digit) + str(int(ones_digit)) + '.html'
		
		try:
			html = urlopen(url).read()
		except:
			break		# reaching the end of this halfmonth
		else:
			soup = BeautifulSoup(html)
			for script in soup(["script", "style"]):
				script.extract() 
				
			## collect info for TABLE MPEC

			mpec_text = soup.get_text()
			mpec_text = list(filter(None, mpec_text.split('\n')))
			
			mpec_id, mpec_title, mpec_time = id_title_time(mpec_text)
			mpec_type = find_mpec_type(mpec_text)
			if mpec_type == 'Discovery' or mpec_type == 'OrbitUpdate':
				mpec_obj_type = find_obj_type(mpec_text)
			else:
				mpec_obj_type = ''
			
			### test output (note: recommend not commenting this out to show progress)
			print(mpec_id, mpec_title, mpec_time, mpec_type, mpec_obj_type)
			
			## push observation into TABLE of individual observatory code if mpec_type is Discovery, OrbitUpdate or DOU
			
			if mpec_type == 'Discovery' or mpec_type == 'OrbitUpdate' or mpec_type == 'DOU':
				obs_start = -1
				obs_end = -1
				if any(s.startswith('Observations:') for s in mpec_text):
					obs_start = mpec_text.index('Observations:') + 1
				elif any(s.startswith('Additional observations:') for s in mpec_text):
					obs_start = mpec_text.index('Additional observations:') + 1
				elif any(s.startswith('Additional Observations:') for s in mpec_text):
					obs_start = mpec_text.index('Additional Observations:') + 1
				elif any(s.startswith('Available observations:') for s in mpec_text):
					obs_start = mpec_text.index('Available observations:') + 1
				elif any(s.startswith('Corrected observations:') for s in mpec_text):
					obs_start = mpec_text.index('Corrected observations:') + 1
				elif any(s.startswith('New observations:') for s in mpec_text):
					obs_start = mpec_text.index('New observations:') + 1
				else:
					pass
					
				if not obs_start == -1:		# only proceed if there are observations in the MPEC
					if any(s == 'Observer details:' for s in mpec_text):
						obs_end = mpec_text.index('Observer details:')
						obs_details_start = mpec_text.index('Observer details:') + 1
						if any(s == 'Orbital elements:' for s in mpec_text):
							obs_details_end = mpec_text.index('Orbital elements:')
						elif any(s == 'Orbital elements' for s in mpec_text):
							obs_details_end = mpec_text.index('Orbital elements')			# MPEC 2020-A121 does not have ":"
						else:		# 2002-G34: no "orbital elements"; using the last line as obs_details_end
							for i in np.arange(obs_details_start, len(mpec_text), 1):
								if '(C) Copyright' in mpec_text[i]:
									obs_details_end = i-1
									break
						obs_details = mpec_text[obs_details_start:obs_details_end]
					else:		# DOU does not have 'Observer details'
						obs_details = ''
						for i in np.arange(obs_start, len(mpec_text), 1):
							if not len(mpec_text[i]) == 80:
								obs_end = i
								break
						
						if mpec_text[obs_end-1].startswith('A. U. Tomatic'):	# newer MPECs has this line as ending, and it's also 80 characters long
							obs_end -= 1
					
					obs = mpec_text[obs_start:obs_end]
					
					for line in obs:
						if line[14:15] == 's' or line[14:15] == 'v':	# skip SAT or roving observer's location line
							continue
						if not len(line.rstrip()) == 80:	# skip weird problems, e.g. the notes in 1995-C07
							continue
						obs_obj = line[0:12].strip()
						date = line[15:25].replace(' ', '-')
						hours = int(float(line[25:32])*24 % 24)
						minutes = int(float(line[25:32])*1440 % 60)
						seconds = int(float(line[25:32])*86400 % 60)
						obs_date_time_string = date + ' ' + str('%02i' % hours) + ':' + str('%02i' % minutes) + ':' + str('%02i' % seconds)
						obs_code = line[77:80]
						if obs_details == '':
							observer = ''
							measurer = ''
							facility = ''
						else:
							observer, measurer, facility = observer_measurer_facility(obs_details, obs_code)
						
						obs_code_collection.append(obs_code)
						if line[12:13] == '*':
							discovery_asterisk = True
							disc_obs_code.append(obs_code)
						else:
							discovery_asterisk = False
							
						### test output
						#print('OBJECT: ', obs_obj, ' | DATETIME: ', obs_date_time_string, ' | OBSERVER:', observer, ' | MEASURER:', measurer, ' | FACILITY:', facility, ' | DISCOVERY:', discovery_asterisk)
						
						### write to the corresponding station TABLE (create if it does not exist)
						
						cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='station_" + obs_code + "'")

						if cursor.fetchone()[0] == 0:
							cursor.execute("CREATE TABLE station_" + obs_code + "(Object TEXT, Time TEXT, Observer TEXT, Measurer TEXT, Facility TEXT, MPEC TEXT, MPECType TEXT, ObjectType TEXT, Discovery INTEGER)")
							db.commit()
						
						cursor.execute("INSERT INTO station_" + obs_code + "(Object, Time, Observer, Measurer, Facility, MPEC, MPECType, ObjectType, Discovery) VALUES(?,?,?,?,?,?,?,?,?)", \
						(obs_obj, obs_date_time_string, observer, measurer, facility, mpec_id, mpec_type, mpec_obj_type, int(discovery_asterisk)))
						db.commit()
			
			indexes = np.unique(obs_code_collection, return_index=True)[1]
			obs_code_collection_uniq = [obs_code_collection[index] for index in sorted(indexes)]
			obs_code_collection_string = ', '.join(obs_code_collection_uniq)
			if len(disc_obs_code) > 0:
				disc_obs_code = disc_obs_code[0]		# in 99% case, MPECs with multiple discoveries have a single discoverer
				### figure out first confirming station
				firstconf = obs_code_collection_uniq.index(disc_obs_code) + 1
				
				if firstconf < len(obs_code_collection_uniq):	# to account for the scenario where there are only precoveries
					firstconf = obs_code_collection_uniq[firstconf]
				else:
					firstconf = ''
			else:
				disc_obs_code = ''
				firstconf = ''
			
			### test output
			#print('STATION:', obs_code_collection_string, ' | DISCOVERY STATION:', disc_obs_code, ' | FIRST TO CONFIRM:', firstconf)
			#print('=========================================')
			
			### write to TABLE MPEC
			cursor.execute('''INSERT INTO MPEC(MPECId, Title, Time, Station, DiscStation, FirstConf, MPECType, ObjectType) VALUES(?,?,?,?,?,?,?,?)''', \
			(mpec_id, mpec_title, mpec_time, obs_code_collection_string, disc_obs_code, firstconf, mpec_type, mpec_obj_type))
			db.commit()

db.close()
