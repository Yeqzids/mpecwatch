#!/usr/bin/env python3

"""
Observatory Code Statistics Generator

This script generates comprehensive statistical metrics for each observatory based on data
in the MPEC database. It processes all MPEC entries and collects observations, discoveries,
and follow-up activities organized by observatory code.

Purpose:
    - Generate statistics on MPEC involvement for each observatory station
    - Track discoveries, follow-ups, and orbit updates by time period and object type
    - Create aggregated JSON data for web visualization
    - Identify which station pages need regeneration through changed data detection

Outputs:
    - obscode_stat.json: Main observatory statistics file for data visualization
    - Updates to LastRun table for efficient page regeneration

Integration Points:
    - StationMPECGraph.py: Uses this data to create individual observatory pages
    - browser.py: Creates summary tables of stats across all observatories
    - survey.py: Generates statistics for survey programs (combining multiple observatories)

Database Tables Used:
    - MPEC: Source of circular data and observatory participation
    - LastRun: Tracks processing state for optimized page generation

Schema:
    The generated JSON structure includes for each station:
    {
        "station_code": {
            "total": int,                   # Total MPECs for this station
            "MPECs": [[name, time, ...]],   # List of individual MPECs
            "MPECId": {id: packed_desig},   # Object designations
            "Discovery": {                  # Discovery statistics
                "total": int,
                "YYYY": {                   # Per year statistics
                    "total": int,
                    "NEA": int,             # Object type counts
                    "PHA": int,
                    ...
                    "Jan": int,             # Monthly breakdown
                    "Feb": int,
                    ...
                }
            },
            "Followup": {...},              # Similar structure for follow-ups
            "FirstFollowup": {...},         # First follow-ups (subset of Followup)
            "OrbitUpdate": {...},           # Orbit updates
            "OBS": {name: count},           # Observer statistics
            "MEA": {name: count},           # Measurer statistics
            "FAC": {name: count}            # Facility statistics
        }
    }

Key Features:
    - Handles First Follow-Up as a subset of Follow-Up observations
    - Maintains efficient change detection using MD5 hashing
    - Processes observers, measurers, and facilities for each station
    - Generates comprehensive time series data for all statistics

Change Detection:
    For efficient web page generation, the script tracks changes in station data:
    1. Computes MD5 hash of each station's JSON data
    2. Compares with previous hash stored in LastRun table
    3. Sets 'Changed' flag when data differs
    4. StationMPECGraph.py only regenerates pages for stations with Changed=1

 (C) Quanzhi Ye
"""

# future improvements:
# adjust queries to take full advantage of db indexes
# --> tokenize station codes to avoid using LIKE
# --> junction table for MPECs and stations (foreign keys) --> enables use of JOINs
# allow single station processing (for testing)


import sqlite3, datetime, re, json, numpy as np, calendar, argparse
from datetime import date
import time
import hashlib

start_time = time.time()

dbFile = '../mpecwatch_v4.db'
mpccode = '../mpccode.json'
outputFile = 'obscode_stat.json'

# Argument parsing
parser = argparse.ArgumentParser(description='Observatory Code Statistics Generator')
parser.add_argument('-s', '--station', type=str, help='Process only a single station code')
args = parser.parse_args()

# Get current station hashes from LastRun table
db = sqlite3.connect(dbFile)
cursor = db.cursor()

with open(mpccode) as f:
    mpccode_data = json.load(f)

# If a single station is specified, validate it exists
target_station = None
if args.station:
    target_station = args.station.upper()
    if target_station not in mpccode_data:
        print(f"Error: Station {target_station} not found in {mpccode}")
        db.close()
        exit(1)
    print(f"Processing single station: {target_station}")

# Load existing data if processing a single station
d = {}
if target_station:
    try:
        with open(outputFile, 'r') as f:
            d = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: {outputFile} not found or invalid. Starting fresh for {target_station}.")
        d = {}

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

def getMonthName(month):
    return calendar.month_name[month][0:3]

# "Followup", "FirstFollowup", "Precovery", "Recovery", "1stRecovery" are not in database (calulated from other fields)
MPEC_TYPES = ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup", "Precovery", "1stRecovery"]
OBJ_TYPES = ["NEA", "PHA", "Comet", "Satellite", "TNO", "Unusual", "Interstellar", "Unknown"] #Only used when MPECType is Discovery or OrbitUpdate

# Determine which stations to iterate over
stations_to_process = [target_station] if target_station else mpccode_data.keys()

for s in stations_to_process:
    print(s)
    d[s] = {}
    d[s]['total'] = 0
    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1)):
        year = str(year)
        d[s][year] = 0
    d[s]['MPECId'] = {}
    
    for mpec_type in MPEC_TYPES: 
        d[s][mpec_type] = {'total': 0}
        for year in list(np.arange(1993, datetime.datetime.now().year+1, 1)):
            year = str(year)
            d[s][mpec_type][year] = {'total': 0}
            for month in np.arange(1, 13, 1):
                d[s][mpec_type][year][getMonthName(month)] = 0
            if mpec_type in ["Discovery", "OrbitUpdate", "DOU", "1stRecovery", "Followup", "FirstFollowup"]:
                for obj_type in OBJ_TYPES:
                    d[s][mpec_type][year][obj_type] = 0

    # each station has its own OBS, MEA, FAC and OBJ and are initialized as empty dictionaries
    d[s]['OBS'] = {}
    d[s]['MEA'] = {}
    d[s]['FAC'] = {}
    d[s]['OBJ'] = {}

    # For individual MPECs table 
    # nested array of the following (for each MPEC): [Name, timestamp, Discovery?, First Conf?, Object Type, CATCH]
    d[s]['MPECs'] = []

    # Grab MPECId
    try:
        for mpc_obj in cursor.execute("SELECT MPEC, Object FROM station_{}".format(s)).fetchall():
            d[s]['MPECId'][mpc_obj[0]] = mpc_obj[1]
    except:
        pass

    # Grab OBS, MEA, FAC, OBJ (respectiveley)
    # try/except blocks used in case of missing table or column
    try:
        # Count unique MPECs per observer
        cursor.execute(f"""
            SELECT 
                CASE WHEN Observer = '' OR Observer IS NULL 
                    THEN 'Unknown' 
                    ELSE Observer 
                END as ObserverName,
                COUNT(DISTINCT MPEC) as mpec_count 
            FROM station_{s} 
            GROUP BY ObserverName
        """)

        for obs in cursor.fetchall():
            d[s]['OBS'][obs[0]] = obs[1]
    except:
        pass

    try:
        # Count unique MPECs per measurer
        cursor.execute(f"""
            SELECT 
                CASE WHEN Measurer = '' OR Measurer IS NULL 
                    THEN 'Unknown' 
                    ELSE Measurer 
                END as MeasurerName,
                COUNT(DISTINCT MPEC) as mpec_count 
            FROM station_{s} 
            GROUP BY MeasurerName
        """)

        for meas in cursor.fetchall():
            d[s]['MEA'][meas[0]] = meas[1]
    except:
        pass

    try:
        # Count unique MPECs per facility
        cursor.execute(f"""
            SELECT 
                CASE WHEN Facility = '' OR Facility IS NULL 
                    THEN 'Unknown' 
                    ELSE Facility 
                END as FacilityName,
                COUNT(DISTINCT MPEC) as mpec_count 
            FROM station_{s} 
            GROUP BY FacilityName
        """)

        for fac in cursor.fetchall():
            d[s]['FAC'][fac[0]] = fac[1]
    except Exception as e:
        print(f"Error processing FAC for {s}: {e}")
        pass

    # New: Calculate Time Frequencies from SQL directly (Observation Time)
    try:
        # Initialize arrays
        d[s]['hourly_stats'] = [0] * 24
        d[s]['weekly_stats'] = [0] * 7
        d[s]['yearly_stats'] = [0] * 366
        
        # SQLite's strftime('%H') returns 00-23
        cursor.execute(f"SELECT strftime('%H', datetime(Time, 'unixepoch')), count(*) FROM station_{s} WHERE Time IS NOT NULL GROUP BY 1")
        for row in cursor.fetchall():
            if row[0]:
                d[s]['hourly_stats'][int(row[0])] = row[1]
                
        # SQLite's strftime('%w') returns 0-6 (Sunday=0), but Python's weekday() is Monday=0.
        # Let's align with individual_OMF.py expectation (Mon=0..Sun=6)
        # SQLite %w: 0=Sunday, 1=Monday... 6=Saturday
        # Mapping: 1->0, 2->1 ... 6->5, 0->6
        cursor.execute(f"SELECT strftime('%w', datetime(Time, 'unixepoch')), count(*) FROM station_{s} WHERE Time IS NOT NULL GROUP BY 1")
        for row in cursor.fetchall():
            if row[0] is not None:
                sqlite_w = int(row[0])
                py_w = (sqlite_w - 1) % 7
                d[s]['weekly_stats'][py_w] = row[1]

        # SQLite's strftime('%j') returns 001-366
        cursor.execute(f"SELECT strftime('%j', datetime(Time, 'unixepoch')), count(*) FROM station_{s} WHERE Time IS NOT NULL GROUP BY 1")
        for row in cursor.fetchall():
            if row[0]:
                d[s]['yearly_stats'][int(row[0]) - 1] = row[1]
    except Exception as e:
        print(f"Error processing time stats for {s}: {e}")
        pass

    try:
        # This counts EVERY observation line, need to change (unused right now)
        for obj in cursor.execute("SELECT Object FROM station_{}".format(s)).fetchall():
            if obj[0] != '':
                d[s]['OBJ'][obj[0]] = d[s]['OBJ'].get(obj[0], 0) + 1
    except:
        pass

# Optimization: Filter MPEC query if a single station is targeted
mpec_query = "SELECT * FROM MPEC"
query_params = ()
if target_station:
    mpec_query += " WHERE Station LIKE ?"
    query_params = (f'%{target_station}%',)

missed_stations = set()
for mpec in cursor.execute(mpec_query, query_params).fetchall():
    year = str(date.fromtimestamp(mpec[2]).year)
    month = getMonthName(int(date.fromtimestamp(mpec[2]).month))

    # cast to list to avoid tuple
    mpec = list(mpec)

    for station in mpec[3].split(', '):
        if station == '' or station == 'XXX':
            continue
            
        # If we are targeting a single station, skip others in the MPEC's list
        if target_station and station != target_station:
            continue

        try:
            d[station]
        except KeyError:
            missed_stations.add(station)
            continue

        # numbers of MPECs
        d[station]['total'] += 1
        d[station][year] += 1

        if mpec[7] == 'unk':
            mpec[7] = 'Unknown'

        # numbers of first followups: MPECType = 'Discovery' and DiscStation != '{}' and "disc_station, station" in stations
        if mpec[6] == 'Discovery' and station not in mpec[4] and mpec[4] + ', ' + station in mpec[3]:
            d[station]['FirstFollowup']['total'] += 1
            d[station]['FirstFollowup'][year]['total'] += 1
            d[station]['FirstFollowup'][year][month] += 1

        # numbers of Discovery MPECs by object type
        if station == mpec[4] and mpec[6] == 'Discovery':
            d[station]['Discovery']['total'] += 1 
            d[station]['Discovery'][year]['total'] += 1
            d[station]['Discovery'][year][month] += 1
            # Include NEA
            if 'NEA' in mpec[7]:
                d[station]['Discovery'][year]["NEA"] += 1
            elif 'PHA' in mpec[7]:
                d[station]['Discovery'][year]["PHA"] += 1
            else:
                d[station]['Discovery'][year][mpec[7]] += 1 #object type

        # numbers of follow-up MPECs by object type
        if mpec[6] == 'Discovery' and station != mpec[4]:
            d[station]['Followup']['total'] += 1
            d[station]['Followup'][year]['total'] += 1
            d[station]['Followup'][year][month] += 1
            if 'NEA' in mpec[7]:
                d[station]['Followup'][year]["NEA"] += 1
            elif 'PHA' in mpec[7]:
                d[station]['Followup'][year]["PHA"] += 1
            else:
                d[station]['Followup'][year][mpec[7]] += 1

        # numbers of Editorial, DOU, ListUpdate, Retraction, and Other MPECs
        for mpecType in ["Editorial", "DOU", "ListUpdate", "Retraction", "Other"]:
            if mpec[6] == mpecType:
                d[station][mpecType]['total'] += 1
                d[station][mpecType][year]['total'] += 1
                d[station][mpecType][year][month] += 1

        # recovery = orbit update
        if mpec[6] == "OrbitUpdate":
            d[station]['OrbitUpdate']['total'] += 1
            d[station]['OrbitUpdate'][year]['total'] += 1
            d[station]['OrbitUpdate'][year][month] += 1
            if 'NEA' in mpec[7]:
                d[station]['OrbitUpdate'][year]["NEA"] += 1
            elif 'PHA' in mpec[7]:
                d[station]['OrbitUpdate'][year]["PHA"] += 1
            else:
                d[station]['OrbitUpdate'][year][mpec[7]] += 1 #object type

        temp = [] #[Name, unix timestamp, Discovery?, First Conf?, Object Type, CATCH]
        name = mpec[0] + "\t" + mpec[1] # MPECId + Title
        if name not in d[station]['MPECs']: #prevents duplication of the same MPEC object
                id = mpec[0][5::]
                packed_front = ""
                packed_back = ""

                #packed front
                if id[0:2] == "18":
                    packed_front = "I" + id[2:4]
                elif id[0:2] == "19":
                    packed_front = "J" + id[2:4]
                elif id[0:2] == "20":
                    packed_front = "K" + id[2:4]
                    
                #packed_back
                if len(id) == 8:
                    packed_back = packed_front + id[-3::]
                elif len(id) == 9:
                    packed_back = packed_front + id[5] + encode(int(id[6:8])) + id[-1]
                
                url1 = "\"https://www.minorplanetcenter.net/mpec/{}/{}.html\"".format(packed_front, packed_back)
                mpec_url = "<a href={}>{}</a>".format(url1, name)

                temp.append(mpec_url) #name w/ url embedded
                temp.append(int(mpec[2])) #time: date and time
                #Discovery?
                if station == mpec[4] and mpec[6] == 'Discovery':
                    temp.append("&#x2713") #check mark
                else:
                    temp.append("")
                #First Conf?
                if station == mpec[5] and mpec[6] == 'Discovery':
                    temp.append("&#x2713") #check mark
                else:
                    temp.append("")
                
                obj_type = mpec[7]
                if obj_type == "Unk":
                    obj_type = "Unknown"
                elif obj_type == "NEAg22":
                    obj_type = "NEA (H>22)"
                elif obj_type == "NEA1822":
                    obj_type = "NEA (18>H>22)"
                elif obj_type == "NEAI18":
                    obj_type = "NEA (H<18)"
                elif obj_type == "PHAI18":
                    obj_type = "PHA (H<18)"
                elif obj_type == "PHAg18":
                    obj_type == "PHA (H>18)"
                temp.append(obj_type)


                if mpec[7]:
                    #obs_code = cursor.execute("SELECT Object FROM station_{} WHERE MPEC = '{}'".format(station, mpec[0])).fetchall()
                    #catch_url = "<a href=https://catch.astro.umd.edu/data?objid={}%20{}>CATCH</a>".format(obs_code[:3], obs_code[3::])
                    catch_url = "<a href=https://catch.astro.umd.edu/data?target={}>CATCH</a>".format(d[station]['MPECId'][mpec[0]])
                    #catch_url = "<a href=https://catch.astro.umd.edu/data?objid={}%20{}>CATCH</a>".format(mpec[0].split()[1][:4], mpec[0].split()[1][5::])
                    temp.append(catch_url)
                else:
                    temp.append("")

                d[station]['MPECs'].append(temp)

        # numbers of precovery MPECs'
        if bool(re.match('.*' + station + '.*' + mpec[4] + '.*', mpec[3])):
            d[station]['Precovery']['total'] += 1
            d[station]['Precovery'][year]['total'] += 1
            d[station]['Precovery'][year][month] += 1

        # numbers of "1st spotter" orbit update MPECs
        if mpec[6] == 'OrbitUpdate' and station == mpec[4]:
            d[station]['1stRecovery']['total'] += 1
            d[station]['1stRecovery'][year]['total'] += 1
            d[station]['1stRecovery'][year][month] += 1
            if 'NEA' in mpec[7]:
                d[station]['1stRecovery'][year]["NEA"] += 1
            elif 'PHA' in mpec[7]:
                d[station]['1stRecovery'][year]["PHA"] += 1
            else:
                d[station]['1stRecovery'][year][mpec[7]] += 1

# Print out missed stations
if missed_stations:
    print("The following stations were not found in mpccode.json. Try rerunning mpccode.py:")
    for station in sorted(missed_stations):
        print(f"  {station}")

# After all data is collected, save it to file
with open(outputFile, 'w') as o:
    json.dump(d, o)

# Update the LastRun table with current timestamps and hashes
for station_code in stations_to_process:
    station_id = f'station_{station_code}'
    # Create a hash of the station data to detect changes
    station_data_str = json.dumps(d[station_code], sort_keys=True)
    station_hash = hashlib.md5(station_data_str.encode()).hexdigest()
    
    # Get current hash from database (if exists)
    cursor.execute("SELECT StationHash FROM LastRun WHERE MPECId = ?", (station_id,))
    result = cursor.fetchone()
    old_hash = result[0] if result else None

    # Determine if data changed
    changed = 1 if old_hash != station_hash else 0

    # Update or insert the LastRun record
    cursor.execute("""
        INSERT OR REPLACE INTO LastRun (MPECId, LastRunTime, StationHash, Changed) 
        VALUES (?, ?, ?, ?)
    """, (station_id, int(time.time()), station_hash, changed))

db.commit()
db.close()

end_time = time.time()
print("Time elapsed: ", end_time - start_time)
