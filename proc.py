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
    ObjectId 	TEXT		Object designation in packed form. This is the same as ObjectId in TABLE Objects
    PageHash	TEXT		Hash of the MPEC page to check if it has changed since last run (proc.py will skip unchanged MPEC pages)
    
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

TABLE Objects: Stores information about objects
    ObjectId		TEXT PRIMARY KEY		Object designation in packed form
    Discovery		BOOLEAN				Flag indicating if the object was discovered by the station (1=discovery, 0=not discovery)
    Note1			TEXT				First note from the MPEC (https://www.minorplanetcenter.net/iau/info/ObsNote.html)
    Note2			TEXT				Second note from the MPEC (https://www.minorplanetcenter.net/iau/info/OpticalObs.html)
    Timestamp		INTEGER				Last timestamp of the observation
    Mag				REAL				Magnitude of the object
    Band			TEXT				Band of the observation (e.g., 'R', 'V', 'I')
    Star_cat_code	TEXT				Catalog code of the star (https://minorplanetcenter.net/iau/info/CatalogueCodes.html)

TABLE LastRun: Tracks processing status of stations and other entities
    MPECId        TEXT PRIMARY KEY   Identifier (e.g., 'station_G96' for observatory code G96)
    LastRunTime   INTEGER            Unix timestamp of when the data was last processed (currently not used)
    StationHash   TEXT               MD5 hash of the station's JSON data structure
    Changed       BOOLEAN            Flag indicating if data changed since last processing (1=changed, 0=unchanged)

LastRun Workflow:
    1. obscode_stat.py updates LastRunTime, StationHash, and Changed when processing station statistics
    2. StationMPECGraph.py queries for stations with Changed=1 to determine which pages need regeneration
    3. After successful page generation, StationMPECGraph.py sets Changed=0
"""

import sqlite3, os, datetime as dt, numpy as np, sys, re, hashlib
import time, csv, traceback, calendar
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
    if '! ' in mpec_firstline[0] or '<' in mpec_firstline[0] or '>' in mpec_firstline[0]:
        mpec_firstline = mpec_text[1].split(": ")
        print("WARNING: MPEC first line has HTML code, using second line instead.")
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

def extract_designations_from_dou_line(line_parts):
    designations = []
    author = None
    reference = None
    
    remaining_parts = line_parts.copy()
    
    # Check for MPC reference pattern at the end
    if len(remaining_parts) >= 2 and remaining_parts[-2] == "MPC" and remaining_parts[-1].isdigit():
        reference = f"MPC {remaining_parts[-1]}"
        remaining_parts = remaining_parts[:-2]
    
    # The last remaining part is likely the author (if not a designation)
    if remaining_parts and (len(remaining_parts[-1]) != 7 or remaining_parts[-1][0] not in ['J', 'K', 'T']):
        author = remaining_parts[-1]
        remaining_parts = remaining_parts[:-1]
    
    # All other parts that match designation pattern are designations
    for part in remaining_parts:
        if len(part) == 7 and part[0] in ['J', 'K', 'T']:
            designations.append(part)
    
    return designations, author, reference

class PageParseError(Exception):
    """Raised when an MPEC page is missing an expected section."""
    pass

def log_error(mpec_id, error, context=""):
    timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    exc_type, exc_value, exc_traceback = sys.exc_info()

    tb_frame = exc_traceback.tb_frame
    line_number = exc_traceback.tb_lineno
    function_name = tb_frame.f_code.co_name
    filename = tb_frame.f_code.co_filename.split('/')[-1]  # Just the filename, not full path
    
    # Get the full stack trace
    stack_trace = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Create detailed error message
    detailed_error = f"File: {filename}, Function: {function_name}, Line: {line_number}, Error: {str(error)}"
    if context:
        detailed_error = f"{context} | {detailed_error}"
    
    # Correct indentation for the `with` block
    with open('logs/mpec_errors.log', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, mpec_id, line_number, function_name, detailed_error, stack_trace])
    
    # Also print to console for immediate feedback
    if context:
        print(f"Context: {context}")
    print(f"Stack trace: {stack_trace}")

########
# main #
########

time_start = time.time()

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
            PageHash TEXT
        )
    """)
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
    # Junction table with the foreign keys
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MPECObjects (
            MPECId TEXT,
            ObjectId TEXT,
            PRIMARY KEY (MPECId, ObjectId),
            FOREIGN KEY (MPECId) REFERENCES MPEC(MPECId),
            FOREIGN KEY (ObjectId) REFERENCES Objects(ObjectId)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS DOUIdentifier (
            MPECId TEXT,
            DOU TEXT,
            RelatedDOU TEXT,
            RelationType TEXT,
            Author TEXT,
            IsRetracted BOOLEAN DEFAULT 0,
            PRIMARY KEY (MPECId, DOU, RelatedDOU)
        )
    """)
    db.commit()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS LastRun (
            MPECId TEXT PRIMARY KEY,
            LastRunTime INTEGER,
            StationHash TEXT,
            Changed BOOLEAN DEFAULT 1
        )
    """)

# Keep track of the current line being parsed for debugging
current_line = ""
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

            # set of unique objects in this MPEC
            mpec_objects = set()

            ## push observation into MPEC TABLE of individual observatory code if mpec_type is Discovery, OrbitUpdate or DOU
            if mpec_type in ('Discovery', 'OrbitUpdate', 'DOU'):
                obs_start = -1
                obs_end = -1

                ## DOU Identifiers
                if mpec_type == 'DOU':
                    try:
                        # Look for the standard DOU sections
                        dou_sections = []
                        relationship_mapping = {
                            'New identifications:': 'identification',
                            'New identification:': 'identification',
                            'New double designations:': 'double',
                            'New double designation:': 'double',
                            'Erroneous double designations:': 'erroneous',
                            'Erroneous double designation:': 'erroneous'
                        }
                        
                        # Find all sections that exist in this MPEC
                        for section in relationship_mapping:
                            if section in mpec_text:
                                dou_sections.append(section)
                        
                        # Process each section
                        for section_idx, section_header in enumerate(dou_sections):
                            relation_type = relationship_mapping.get(section_header)
                            section_start_idx = mpec_text.index(section_header)
                            section_start = section_start_idx + 1  # Skip the header line
                            
                            # Find the end of this section (next empty line)
                            section_end = section_start
                            while section_end < len(mpec_text):
                                current_line = mpec_text[section_end]
                                current_line_s = current_line.strip()
                                # Stop at empty line or a line that starts with a non-space character
                                # (which indicates the start of a new section)
                                if not current_line_s or (current_line_s and not current_line.startswith(' ')):
                                    break
                                section_end += 1

                            # print(f"Processing {section_header} from line {section_start} to {section_end}")

                            # Process the lines in this section
                            for line_idx in range(section_start, section_end):
                                line = mpec_text[line_idx]
                                current_line = line  # Update current_line for error logging
                                stripped_line = line.strip()
                                if not stripped_line:  # Skip empty lines
                                    continue

                                # check for commented/retracted entries (eg. 1998-A03)
                                is_retracted = stripped_line.startswith('#')
                                if is_retracted:
                                    stripped_line = stripped_line[1:].strip()

                                parts = stripped_line.split()
                                if not parts:  # Skip if no parts after splitting
                                    continue
                                
                                designations, author, reference = extract_designations_from_dou_line(parts)

                                # Skip lines with fewer than 2 designations
                                if len(designations) < 2:
                                    continue

                                # If author is not provided, use 'Unknown'
                                if not author:
                                    author = 'Unknown'
                                    
                                # Insert relationships based on section type
                                if relation_type == 'identification' or relation_type == 'double':
                                    # For these types, establish relationships between all designations
                                    for i in range(len(designations) - 1):
                                        for j in range(i + 1, len(designations)):
                                            # Forward relationship
                                            cursor.execute(
                                                """INSERT OR IGNORE INTO DOUIdentifier 
                                                (MPECId, DOU, RelatedDOU, RelationType, Author, IsRetracted) 
                                                VALUES (?,?,?,?,?,?)""",
                                                (mpec_id, designations[i], designations[j], relation_type, author, 1 if is_retracted else 0)
                                            )
                                            
                                            # Reverse relationship
                                            cursor.execute(
                                                """INSERT OR IGNORE INTO DOUIdentifier 
                                                (MPECId, DOU, RelatedDOU, RelationType, Author, IsRetracted) 
                                                VALUES (?,?,?,?,?,?)""",
                                                (mpec_id, designations[j], designations[i], relation_type, author, 1 if is_retracted else 0)
                                            )

                                elif relation_type == 'erroneous':
                                    # For erroneous designations, mark the relationship (both ways) but set IsRetracted to true
                                    for i in range(len(designations) - 1):
                                        for j in range(i + 1, len(designations)):
                                            # Forward relationship
                                            cursor.execute(
                                                """INSERT OR IGNORE INTO DOUIdentifier 
                                                (MPECId, DOU, RelatedDOU, RelationType, Author, IsRetracted) 
                                                VALUES (?,?,?,?,?,?)""",
                                                (mpec_id, designations[i], designations[j], 'double', author, 1)
                                            )

                                            # Reverse relationship
                                            cursor.execute(
                                                """INSERT OR IGNORE INTO DOUIdentifier 
                                                (MPECId, DOU, RelatedDOU, RelationType, Author, IsRetracted) 
                                                VALUES (?,?,?,?,?,?)""",
                                                (mpec_id, designations[j], designations[i], 'double', author, 1)
                                            )

                                else:
                                    # For the rare case with more than 2 designations, log a warning
                                    # but still process them as pairs (this handles unusual formatting)
                                    print(f"Warning: {len(designations)} designations in double section: {line.strip()}")
                                    for i in range(len(designations) - 1):
                                        cursor.execute(
                                            "INSERT OR IGNORE INTO DOUIdentifier (MPECId, DOU, RelatedDOU, RelationType, Author) VALUES (?,?,?,?,?)",
                                            (mpec_id, designations[i], designations[i+1], relation_type, author)
                                        )
                                        cursor.execute(
                                            "INSERT OR IGNORE INTO DOUIdentifier (MPECId, DOU, RelatedDOU, RelationType, Author) VALUES (?,?,?,?,?)",
                                            (mpec_id, designations[i+1], designations[i], relation_type, author)
                                        )
                        
                        db.commit()
                    except Exception as e:
                        log_error(mpec_id, f"Error processing DOU identifiers: {str(e)}", f"Error processing DOU identifiers in {mpec_id}: {str(e)}\nCurrent line: {current_line}")
                        continue

                # Observations
                try:
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
                    
                    obs_obj = ''
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
                            current_line = line  # Update current_line for error logging
                            if line[14:15] == 's' or line[14:15] == 'v':	# skip SAT or roving observer's location line
                                continue
                            if not len(line.rstrip()) == 80:	# skip weird problems, e.g. the notes in 1995-C07
                                continue
                            obs_obj = line[0:12].strip()
                            date = line[15:25].replace(' ', '-')
                            note1 = line[13].strip()
                            note2 = line[14].strip()
                            if line[25:32].strip() == '' or line[24:32].isspace():		# some MPECs do not have time
                                hours = 0
                                minutes = 0
                                seconds = 0
                                print(f"WARNING: Missing time in observation line: {line}. Using default 00:00:00.")
                            else:
                                hours = int(float(line[25:32])*24 % 24)
                                minutes = int(float(line[25:32])*1440 % 60)
                                seconds = int(float(line[25:32])*86400 % 60)
                            obs_date_time_string = date + ' ' + str('%02i' % hours) + ':' + str('%02i' % minutes) + ':' + str('%02i' % seconds)
                            try:
                                obs_date = dt.datetime(int(date[0:4]), int(date[5:7]), int(date[8:10]), int(hours), int(minutes), int(seconds))
                            except ValueError as e:
                                log_error(mpec_id, e, f"Invalid date/time: {str(e)}\nLine: {line}\nSkipping this line.")
                                continue # Skip this line if date is invalid
                            obs_date_timestamp = calendar.timegm(obs_date.utctimetuple())
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

                            mpec_objects.add(obs_obj)

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
                                # Keeps most recent observation (overwrite older observation)
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
                except PageParseError as e:
                    log_error(mpec_id, e, f"PageParseError while processing {this_mpec}")
                    print(f"Error on line: \"{current_line}\"")
                    continue
                except Exception as e:
                    log_error(mpec_id, e, f"Unexpected error while processing {this_mpec}")
                    print(f"Error on line: \"{current_line}\"")
                    continue
            
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
            try:
                if mpec_type in ('Discovery', 'OrbitUpdate', 'DOU'):
                    # Observational MPECs
                    cursor.execute('''INSERT INTO MPEC(MPECId, Title, Time, Station, DiscStation, FirstConf, MPECType, ObjectType, OrbitComp, Issuer, PageHash) VALUES(?,?,?,?,?,?,?,?,?,?,?)''', \
                    (mpec_id, mpec_title, mpec_timestamp, obs_code_collection_string, disc_obs_code, firstconf, mpec_type, mpec_obj_type, orbit_comp, issuer, h))
                else:
                    # Non-observational MPECs
                    cursor.execute('''INSERT INTO MPEC(MPECId, Title, Time, Station, DiscStation, FirstConf, MPECType, ObjectType, OrbitComp, Issuer, PageHash) VALUES(?,?,?,?,?,?,?,?,?,?,?)''', \
                    (mpec_id, mpec_title, mpec_timestamp, '', '', '', mpec_type, '', '', issuer, h))
                db.commit()
            except sqlite3.IntegrityError as e:
                error_message = f"Integrity error inserting MPEC {this_mpec}: {str(e)}"
                log_error(mpec_id, e, error_message)
                continue

            ### write to TABLE MPECObjects
            for obj in mpec_objects:
                try:
                    cursor.execute("INSERT OR IGNORE INTO MPECObjects (MPECId, ObjectId) VALUES(?,?)", (mpec_id, obj))
                    db.commit()
                except sqlite3.IntegrityError as e:
                    error_message = f"Integrity error inserting into MPECObjects for MPEC {this_mpec} and Object {obj}: {str(e)}"
                    log_error(mpec_id, e, error_message)
                    continue

        except PageParseError as e:
            error_message = f"General parsing error. {this_mpec}: {str(e)}"
            log_error(mpec_id, e, error_message)
            continue
        except Exception as e:
            error_message = f"Unexpected error. {this_mpec}: {str(e)}"
            log_error(mpec_id, e, error_message)
            continue

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

time_end = time.time()
print(f'Processing time for {ym}: {str(time_end - time_start)} seconds')
db.close()