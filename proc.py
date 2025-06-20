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
	Time		INTEGER  	Publication Unix timestamp
	Station		TEXT		List of observatory stations involved in the observation. Only used when MPECType is Discovery, OrbitUpdate, or DOU		
	DiscStation	TEXT		Observatory station marked by the discovery asterisk. Only used when MPECType is Discovery.
	FirstConf	TEXT		First observatory station to confirm. Only used when MPECType is Discovery.
	MPECType	TEXT		Type of the MPEC: Editorial, Discovery, OrbitUpdate, DOU, ListUpdate, Retraction, Other
	ObjectType	TEXT		Type of the object: NEA, Comet, Satellite, TNO, Unusual, Interstellar, unk. Only used when MPECType is Discovery or OrbitUpdate
	OrbitComp	TEXT		Orbit computer. Only used when MPECType is Discovery or OrbitUpdate
	Issuer		TEXT		Issuer of the MPEC
	
TABLE XXX (observatory code):
	Object		TEXT		Object designation in packed form
	Time		INTEGER		Time of the observation (Unix timestamp)
	Observer	TEXT		List of observers as published in MPEC
	Measurer	TEXT		List of measurers as published in MPEC
	Facility	TEXT		List of telescope/instrument as published in MPEC
	MPEC		TEXT		MPECId
	MPECType	TEXT		Type of the MPEC: Discovery, OrbitUpdate, DOU
	ObjectType	TEXT		Type of the object: NEA, Comet, Satellite, TNO, Unusual, Interstellar, unk
	Discovery	INTEGER		Corresponding to discovery asterisk
"""

import sqlite3, os, datetime as dt, numpy as np, sys, re, hashlib
from urllib.request import urlopen
from bs4 import BeautifulSoup

ym = sys.argv[1]
dbFile = 'mpecwatch_v4.db'

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

# download PHA list (to check if an object is PHA)
html = urlopen('http://cgi.minorplanetcenter.net/cgi-bin/textversion.cgi?f=lists/PHAs.html').read()
soup = BeautifulSoup(html, features="lxml")
pha_lst = soup.get_text()
pha_lst = list(filter(None, pha_lst.split('\n')))

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
	mpec_firstline = mpec_text[0].split(": ")
	if len(mpec_firstline) == 2:
		mpecid, title = mpec_firstline
	else:
		mpecid = mpec_firstline[0]
		title = ': '.join(mpec_firstline[1:])
	mpecid = mpecid.strip()			# MPECs before 100 has an extra space at the end
	tt = [s for s in mpec_text if s.startswith(mpecid.replace('MPEC', 'M.P.E.C.'))][0]
	if title == '':		# odd MPEC bug after 2019: title missing
		title = mpec_text[[i for i, s in enumerate(mpec_text) if 'URL' in s][0]+1]
	elif '(C)' in title:			# odd MPEC bug showing the last line of the circular
		title = mpec_text[[i for i, s in enumerate(mpec_text) if 'URL' in s][0]+1]
	elif mpecid in ['MPEC 2018-H54', 'MPEC 2018-N52', 'MPEC 2019-C53']:			# other odd rare bugs
		title = mpec_text[[i for i, s in enumerate(mpec_text) if 'URL' in s][0]+1]
	title = title.strip()
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
	

def find_mpec_type(mpec_text, title):
	"""
	Determine the type of the MPEC. Can be the following:
	---
	* Editorial
	* Discovery
	* OrbitUpdate
	* DOU
	* ListUpdate
	* Retraction
	* Other
	---
	Note: title is required to fix some rare but weird MPEC title bug
	"""
	
	if 'editorial' in title.lower() and not 'delet' in title.lower() and not 'retract' in title.lower():
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
	elif any(s in mpec_text[0].lower() for s in ['retract', 'abandon', 'delet']):
		return('Retraction')
	else:
		return('Other')
		
def find_obj_type(mpec_text, title):
	"""
	Determine the object type of the MPEC; MPEC type needs to be 'Discovery' or 'OrbitUpdate'. Can be the following:
	---
	* NEAl18 (NEA with H<18)
	* NEA1822 (NEA with 18<H<22)
	* NEAg22 (NEA with H>22)
	* PHAl18 (PHA with H<18)
	* PHAg18 (PHA with H>18)
	* Comet
	* Satellite
	* TNO
	* Unusual
	* Interstellar
	* unk (unknown)
	---
	Note: title is required to fix some rare but weird MPEC title bug
	"""
	
	if 'comet' in title.lower() or 'sungrazer' in title.lower() or 'c/' in title.lower() or 'a/' in title.lower():
		return('Comet')
	elif 's/' in title.lower():
		return('Satellite')
	elif 'i/' in title.lower():
		return('Interstellar')
	elif 'tno' in title.lower():
		return('TNO')
	elif any('Outer Solar System Survey' in s for s in mpec_text):		# certain MPECs do not have 'TNO' flag in their titles, e.g. 1999-L24
		return('TNO')
	elif 'MPEC 2000-V09' in mpec_text[0]:			# older format MPECs, easier to do this quick fix
		return('TNO')
	elif 'precoveries' in title.lower():			# rare MPECs that does not have orbits; note: this will be assigned as "unk" and will be fixed manually later
		return('unk')
	else:
		if len([s for s in mpec_text if 'a,e,i = ' in s]) > 0:
			tt = [s for s in mpec_text if 'a,e,i = ' in s][0]
			if 'q = ' in tt:
				qq = float(tt.split('q = ')[-1])
			else:
				tt = tt.split('a,e,i = ')[-1].split(',')
				qq = float(tt[0]) * (1-float(tt[1]))
		else:
			aa = 100.00			# if it can't find a, e, it's typically a batch of multiple TNOs
			ee = 0.00
			for s in mpec_text:
				if s.startswith('a '):
					aa = float(s[2:15])
				elif s.startswith('e '):
					ee = float(s[2:15])
					break
			qq = aa * (1 - ee)
			
		try:
			obj_name = mpec_text[mpec_text.index('Orbital elements:')+1][0:20].strip()
		except:
			obj_name = mpec_text[mpec_text.index('Ephemeris:')+1][0:20].strip()
			pass
			
		if any(obj_name in s for s in pha_lst):
			pha = True
		else:
			pha = False
		
		for s in mpec_text:
			if s.startswith('P '):
				try:
					hh = float(s[23:28])
				except:				# sometimes there's no H
					hh = 99.99
					pass
	
		if qq < 1.3:
			if hh <= 18:
				if pha:
					return('PHAl18')
				else:
					return('NEAl18')
			elif hh > 18 and hh <= 22:
				if pha:
					return('PHAg18')
				else:
					return('NEA1822')
			elif hh > 22:
				if pha:
					return('PHAg18')
				else:
					return('NEAg22')
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
	
def find_orb_computer(mpec_text):
	for s in mpec_text:
		if s.startswith('Epoch '):
			return(s[56:].strip())

def find_issuer(mpec_text):
	for s in mpec_text:
		if '(C)' in s:
			return(s[0:28].strip())

class PageParseError(Exception):
    """Raised when an MPEC page is missing an expected section."""
    pass

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
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS MPEC (
			MPECId TEXT PRIMARY KEY,
			Title TEXT,
			Time INTEGER,
			Station TEXT,
			DiscStation TEXT,
			FirstConf TEXT,
			MPECType TEXT,
			ObjectType TEXT,
			OrbitComp TEXT,
			Issuer TEXT,
			ObjectId TEXT,
			PageHash TEXT,
			FOREIGN KEY(ObjectId) REFERENCES Objects(ObjectId)
		)
	""")
	# decoding note1: https://www.minorplanetcenter.net/iau/info/ObsNote.html
	# decoding note2: https://www.minorplanetcenter.net/iau/info/OpticalObs.html
	# decoding catalog code: https://minorplanetcenter.net/iau/info/CatalogueCodes.html
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS Objects (
			ObjectId TEXT PRIMARY KEY,
			Discovery BOOLEAN DEFAULT 0,
			Note1 TEXT,
			Note2 TEXT,
			Timestamp INTEGER,
			Mag REAL,
			Band TEXT,
			Star_cat_code TEXT
		)
	""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS DOUIdentifier (
			MPECId TEXT,
			DOU TEXT
		)
	""")
	db.commit()
	# store json hash of each station's last run
	# obscode_stat.py updates LastRunTime, StationHash, and Changed
	# StationMPECGraph.py uses Changed to determine if the station page needs to be updated
	# note that LastRunTime is not used, but it is useful for debugging purposes
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS LastRun (
			MPECId TEXT PRIMARY KEY,
			LastRunTime INTEGER,
			StationHash TEXT,
			Changed BOOLEAN DEFAULT 1
		)
	""")

for halfmonth in month_to_letter(ym[4:6]):
	for i in list(np.arange(1, 999, 1)):
		obs_code_collection = []
		disc_obs_code = []

		this_mpec = 'MPEC ' + ym[0:4] + '-' + halfmonth + '%02i' % i

		try:
			# read and parse the MPEC
			tens_digit = encode(int(np.floor(i/10)))
			ones_digit = i - np.floor(i/10)*10
			url = 'https://www.minorplanetcenter.net/mpec/' + century + ym[2:4] + '/' + century + ym[2:4] + halfmonth + str(tens_digit) + str(int(ones_digit)) + '.html'
			
			try:
				html = urlopen(url).read()
			except:
				break		# reaching the end of this halfmonth
				
			# check if the hash of the MPEC page has changed; if not, skip
			h = hashlib.md5(html).hexdigest()
			cursor.execute("SELECT PageHash FROM MPEC WHERE MPECId=?", (this_mpec,))
			existing_hash = cursor.fetchone()
			if existing_hash and existing_hash[0] == h: # page is identical to last run
				print(f"{this_mpec} unchanged, skipping")
				continue
			
			# check if this MPEC is in the database; if yes, pass this one
			cursor.execute("SELECT 1 FROM MPEC WHERE MPECId = ?", (this_mpec,))
			if cursor.fetchone(): # MPEC already exists in the database
				continue
				
			# Continue with existing code to process the MPEC
			soup = BeautifulSoup(html, features="lxml")
			for script in soup(["script", "style"]):
				script.extract() 
				
			## collect info for TABLE MPEC

			mpec_text = soup.get_text()
			mpec_text = list(filter(None, mpec_text.split('\n')))
			
			mpec_id, mpec_title, mpec_time = id_title_time(mpec_text)
			mpec_timestamp = dt.datetime(int(mpec_time[0:4]), int(mpec_time[5:7]), int(mpec_time[8:10]), int(mpec_time[11:13]), int(mpec_time[14:16]), int(mpec_time[17:19])).timestamp()
			mpec_type = find_mpec_type(mpec_text, mpec_title)
			if mpec_type == 'Discovery' or mpec_type == 'OrbitUpdate':
				mpec_obj_type = find_obj_type(mpec_text, mpec_title)
				orbit_comp = find_orb_computer(mpec_text)
				issuer = find_issuer(mpec_text)
			else:
				mpec_obj_type = ''
				orbit_comp = ''
				issuer = ''
			
			### test output (note: recommend not commenting this out to show progress)
			print(mpec_id, mpec_title, mpec_time, mpec_type, mpec_obj_type)

			## push observation into MPEC TABLE of individual observatory code if mpec_type is Discovery, OrbitUpdate or DOU
			if mpec_type in ('Discovery', 'OrbitUpdate', 'DOU'):
				obs_start = -1
				obs_end = -1

				## DOU Identifiers
				if mpec_type == 'DOU':
					if 'New identifications:' not in mpec_text or 'New old-numbered orbits:' not in mpec_text:
						raise PageParseError(f"{mpec_id}: missing DOU markers")
					start = mpec_text.index('New identifications:') + 1
					end   = mpec_text.index('New old-numbered orbits:')
					for line in mpec_text[start:end]:
						parts = line.split()
						if not parts: # skip empty lines
							continue
						dou = parts[-1]
						# insert DOU into DOUIdentifier table if (MPECId, DOU) does not exist
						cursor.execute("INSERT OR IGNORE INTO DOUIdentifier (MPECId, DOU) VALUES (?,?)",(mpec_id, dou))
					db.commit()

				## Observations
				obs_headers = [
					'Observations:',
					'Additional observations:',
					'Additional Observations:',
					'Available observations:',
					'Corrected observations:',
					'New observations:',
				]

				for hdr in obs_headers:
					if hdr in mpec_text:
						obs_start = mpec_text.index(hdr) + 1
						break
				
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
						note1 = line[13].strip()
						note2 = line[14].strip()
						minutes = int(float(line[25:32])*1440 % 60)
						seconds = int(float(line[25:32])*86400 % 60)
						obs_date_time_string = date + ' ' + str('%02i' % hours) + ':' + str('%02i' % minutes) + ':' + str('%02i' % seconds)
						obs_date_timestamp = dt.datetime(int(date[0:4]), int(date[5:7]), int(date[8:10]), int(hours), int(minutes), int(seconds)).timestamp()
						mag = line[65:70].strip()
						band = line[70]
						code = line[71]
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
							cursor.execute("CREATE TABLE station_" + obs_code + "(Object TEXT, Time INTEGER, Observer TEXT, Measurer TEXT, Facility TEXT, MPEC TEXT, MPECType TEXT, ObjectType TEXT, Discovery INTEGER)")
							db.commit()
						
						cursor.execute("INSERT INTO station_" + obs_code + "(Object, Time, Observer, Measurer, Facility, MPEC, MPECType, ObjectType, Discovery) VALUES(?,?,?,?,?,?,?,?,?)", \
						(obs_obj, obs_date_timestamp, observer, measurer, facility, mpec_id, mpec_type, mpec_obj_type, int(discovery_asterisk)))
						db.commit()

						### write to TABLE Objects
						cursor.execute("SELECT 1 FROM Objects WHERE ObjectId = ?", (obs_obj,))
						existing = cursor.fetchone() # Object already exists in the database
						if existing:
							# Overwrite the existing information with the new data.
							cursor.execute("""
								UPDATE Objects SET Discovery = ?, Note1 = ?, Note2 = ?, Timestamp = ?, Mag = ?, Band = ?, Star_cat_code = ?
								WHERE ObjectId = ?
							""", (discovery_asterisk, note1, note2, obs_date_timestamp, mag, band, code, obs_obj))
						else:
							cursor.execute("""
								INSERT INTO Objects (ObjectId, Discovery, Note1, Note2, Timestamp, Mag, Band, Star_cat_code)
								VALUES (?,?,?,?,?,?,?,?)
							""", (obs_obj, discovery_asterisk, note1, note2, obs_date_timestamp, mag, band, code))
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
			cursor.execute('''INSERT INTO MPEC(MPECId, Title, Time, Station, DiscStation, FirstConf, MPECType, ObjectType, OrbitComp, Issuer, ObjectId, PageHash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', \
			(mpec_id, mpec_title, mpec_timestamp, obs_code_collection_string, disc_obs_code, firstconf, mpec_type, mpec_obj_type, orbit_comp, issuer, obs_obj, h))
			db.commit()
		except Exception as e:
			print('ERROR processing ' + this_mpec + ': ')
			print(e)
			pass

# create indexes for TABLE MPEC to speed up queries
cursor.execute("CREATE INDEX IF NOT EXISTS idx_mpec_time ON MPEC(Time);") # Found in home_stat.py, mpc_stat.py, MPECTally.py
cursor.execute("CREATE INDEX IF NOT EXISTS idx_discstation_type_time ON MPEC(DiscStation, MPECType, Time);") # Found in home_stat.py, survey.py, obscode_stat.py
cursor.execute("CREATE INDEX IF NOT EXISTS idx_station_type_time ON MPEC(Station, MPECType, Time);") # Found in home_stat.py, survey.py
cursor.execute("CREATE INDEX IF NOT EXISTS idx_discstation_time ON MPEC(DiscStation, Time);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_discstation_object_time ON MPEC(DiscStation, ObjectType, Time);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_station_object_time ON MPEC(Station, ObjectType, Time);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_mpec_id ON MPEC(MPECId);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_mpec_object_id ON MPEC(ObjectId);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_object_id ON Objects(ObjectId);") # Found in TopObjectsObs_PieChart.py
cursor.execute("CREATE INDEX IF NOT EXISTS idx_objecttype_time ON MPEC(ObjectType, Time);") # Found in MPECTally.py, survey.py
db.commit()
db.close()