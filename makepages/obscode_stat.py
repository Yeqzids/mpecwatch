#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Generate statistics for every observatory by year

 (C) Quanzhi Ye
 
"""

import sqlite3, datetime, re, json, numpy as np, calendar
from datetime import date

dbFile = '../mpecwatch_v3.db'
mpccode = '../mpccode.json'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

currentYear = datetime.datetime.now().year

with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)

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

# fix browser.py and survey.py after changing dictionary structure
obs_types = ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup", "Precovery", "Recovery", "1stRecovery"]
obj_types = ["NEA", "PHA", "Comet", "Satellite", "TNO", "Unusual", "Interstellar", "unk"] #Only used when MPECType is Discovery or OrbitUpdate
d = dict()
for s in mpccode:
#for i in range(1):
    #s = 'G96'
    print(s)
    d[s] = {}
    d[s]['total'] = 0
    d[s]['MPECId'] = {}
    
    for obs_type in obs_types: 
        d[s][obs_type] = {}

    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
        year = int(year)
        for obs_type in obs_types:
            d[s][obs_type][year] = {'total': 0}
            if obs_type == "Discovery" or obs_type == "OrbitUpdate":
                for obj_type in obj_types:
                    d[s][obs_type][year][obj_type] = 0

    d[s]['OBS'] = {} #observers at this station
    d[s]['MEA'] = {} #measurers at this station
    d[s]['FAC'] = {} #facilities at this station 
    d[s]['MPECs'] = {}
    # old structure used in line 491 StationMPECGraph.py: need to update
    for i in ["Name", "timestamp", "Discovery?", "First Conf?", "Object Type", "CATCH"]:
        d[s]['MPECs'][i] = None

    #Grab MPECId
    try:
        for mpc_obj in cursor.execute("SELECT MPEC, Object FROM station_{}".format(s)).fetchall():
            d[s]['MPECId'][mpc_obj[0]] = mpc_obj[1]
    except:
        pass

    #Grab OBS, MEA, FAC (respectiveley)
    try:
        for obs in cursor.execute("SELECT Observer FROM station_{}".format(s)).fetchall():
            if obs[0] != '':
                d[s]['OBS'][obs[0]] = d[s]['OBS'].get(obs[0], 0) + 1
    except:
        pass

    try:
        for meas in cursor.execute("SELECT Measurer FROM station_{}".format(s)).fetchall():
            if meas[0] != '':
                d[s]['MEA'][meas[0]] = d[s]['MEA'].get(meas[0], 0) + 1
    except:
        pass

    try:
        for fac in cursor.execute("SELECT Facility FROM station_{}".format(s)).fetchall():
            if fac[0] != '':
                d[s]['FAC'][fac[0]] = d[s]['FAC'].get(fac[0], 0) + 1
    except:
        pass

for mpec in cursor.execute("SELECT * FROM MPEC").fetchall():
    year = int(date.fromtimestamp(mpec[2]).year)
    month = int(date.fromtimestamp(mpec[2]).month)

    for station in mpec[3].split(', '):
        if station == '' or station == 'XXX':
            continue    

        # numbers of MPECs
        d[station]['total'] = d[station].get('total', 0) + 1
        d[station]['total'][year] = d[station].get(year, 0) + 1

        #MPECType = 'Discovery' and DiscStation != '{}'
        if mpec[6] == 'Discovery' and station != mpec[4]:
            d[station]['Followup'][year]['total'] += 1
            d[station]['Followup'][year][mpec[5]] += 1

        #MPECType = 'Discovery' and DiscStation != '{}' and "disc_station, station" in stations
        if mpec[6] == 'Discovery' and station not in mpec[4] and mpec[4] + ', ' + station in mpec[3]:
            d[station]['FirstFollowup'][year]['total'] = d[station]['FirstFollowup'][year].get('total',0)+1
            d[station]['FirstFollowup'][year][month] = d[station]['FirstFollowup'][year].get(month,0)+1

        #if station = discovery station
        if station == mpec[4]:
            d[station]['Discovery'][year]['total'] = d[station]['Discovery'][year].get('total',0)+1
            d[station]['Discovery'][year][month] = d[station]['Discovery'][year].get(month,0)+1
            if mpec[7] == "NEAg22" or mpec[7] == "NEA1822" or mpec[7] == "NEAI18" or mpec[7] == "PHAI18" or mpec[7] == "PHAg18":
                d[station]['Discovery'][year]["NEA"] = d[station]['Discovery'][year].get("NEA",0)+1
            else:
                d[station]['Discovery'][year][mpec[7]] = d[station]['Discovery'][year].get(mpec[7],0)+1 #object type

        for mpecType in ["Editorial", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"]:
            if mpec[6] == mpecType:
                d[station][mpecType][year]['total'] = d[station][mpecType][year].get('total',0)+1
                d[station][mpecType][year][month] = d[station][mpecType][year].get(month,0)+1

        if mpec[6] == "OrbitUpdate":
            if mpec[7] == "NEAg22" or mpec[7] == "NEA1822" or mpec[7] == "NEAI18" or mpec[7] == "PHAI18" or mpec[7] == "PHAg18":
                d[station]['OrbitUpdate'][year]["NEA"] = d[station]['OrbitUpdate'][year].get("NEA",0)+1
            else:
                d[station]['OrbitUpdate'][year][mpec[7]] = d[station]['OrbitUpdate'][year].get(mpec[7],0)+1 #object type

        # "Name", "timestamp", "Discovery?", "First Conf?", "Object Type", "CATCH"
        temp = [] #[Name, unix timestamp, Discovery?, First Conf?, Object Type, CATCH]
        name = mpec[0] + "\t" + mpec[1]
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

            d[station]['MPECs']["Name"] = mpec_url
            d[station]['MPECs']["timestamp"] = int(mpec[2])
            #Discovery?
            if station == mpec[4]:
                d[station]['MPECs']["Discovery?"] = "&#x2713" #check mark
            else:
                d[station]['MPECs']["Discovery?"] = ""
            #First Conf?
            if station == mpec[5]:
                d[station]['MPECs']["First Conf?"] = "&#x2713" #check mark
            else:
                d[station]['MPECs']["First Conf?"] = ""
            
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
            d[station]['MPECs']["Object Type"] = obj_type

            if mpec[7]:
                catch_url = "<a href=https://catch.astro.umd.edu/data?target={}>CATCH</a>".format(d[station]['MPECId'][mpec[0]])
                d[station]['MPECs']["CATCH"] = catch_url
            else:
                d[station]['MPECs']["CATCH"] = ""

        # numbers of PHAs
        if mpec[7] == 'PHA' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['PHA'][year] = d[station]['PHA'].get(year, 0) + 1

        # numbers of NEAs

        # numbers of discovery MPECs

        # numbers of NEAs Discovery MPECs

        # numbers of PHA Discovery MPECs

        # numbers of Comet Discovery MPECs

        # numbers of Satellite Discovery MPECs

        # numbers of TNO Discovery MPECs

        # numbers of Unusual Object Discovery MPECs

        # numbers of Interstellar Object Discovery MPECs

        # numbers of Unknown Object Discovery MPECs

        # numbers of follow-up MPECs

        # numbers of first follow-up MPECs

        # numbers of NEAs follow-up MPECs

        # numbers of PHAs follow-up MPECs

        # numbers of Comets follow-up MPECs

        # numbers of Satellites follow-up MPECs

        # numbers of TNOs follow-up MPECs

        # numbers of Unusual Objects follow-up MPECs

        # numbers of Interstellar Objects follow-up MPECs

        # numbers of Unknown Objects follow-up MPECs

        # numbers of precovery MPECs

        # numbers of orbit update MPECs

        # numbers of "1st spotter" orbit update MPECs

    # d[s]['mpec_discovery'] = {}
    # d[s]['NEA_Disc'] = {}
    # d[s]['PHA_Disc'] = {}
    # d[s]['Comet_Disc'] = {}
    # d[s]['Satellite_Disc'] = {}
    # d[s]['TNO_Disc'] = {}
    # d[s]['Unusual_Disc'] = {}
    # d[s]['Interstellar_Disc'] = {}
    # d[s]['Unknown_Disc'] = {}
    # d[s]['mpec_followup'] = {}
    # d[s]['NEA_FU'] = {}
    # d[s]['PHA_FU'] = {}
    # d[s]['Comet_FU'] = {}
    # d[s]['Satellite_FU'] = {}
    # d[s]['TNO_FU'] = {}
    # d[s]['Unusual_FU'] = {}
    # d[s]['Interstellar_FU'] = {}
    # d[s]['Unknown_FU'] = {}
    #d[s]['mpec_1st_followup'] = {}
    #d[s]['mpec_precovery'] = {}
    #d[s]['mpec_recovery'] = {}
    #d[s]['mpec_1st_recovery'] = {}
    
    for y in np.arange(1993, currentYear+1, 1):
        y = int(y)
        timestamp_start = calendar.timegm(datetime.date(y,1,1).timetuple())
        timestamp_end = calendar.timegm(datetime.date(y+1,1,1).timetuple())-1

        ## numbers of MPECs
        cursor.execute("select station from MPEC where station like '%{}%' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['mpec'][y] = len(cursor.fetchall())
    
        ## numbers of PHAs
        cursor.execute("select ObjectType from MPEC where Station like '%{}%' and ObjectType like '%PHA%' and ((MPECType like 'Discovery' and DiscStation like '%{}%')) and time >= {} and time <= {};".format(s, s, timestamp_start, timestamp_end))
        d[s]['PHA'][y] = len(cursor.fetchall())

        ## numbers of NEAs
        cursor.execute("select ObjectType from MPEC where Station like '%{}%' and ObjectType like '%NEA%' and ((MPECType like 'Discovery' and DiscStation like '%{}%')) and time >= {} and time <= {};".format(s, s, timestamp_start, timestamp_end))
        d[s]['NEA'][y] = len(cursor.fetchall())
        
        ## numbers of discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '{}' and time >= {} and time <= {} and MPECType like 'Discovery';".format(s, timestamp_start, timestamp_end))
        d[s]['mpec_discovery'][y] = len(cursor.fetchall())

        ## numbers of NEAs Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%NEA%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['NEA_Disc'][y] = len(cursor.fetchall())

        ## numbers of PHA Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%PHA%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['PHA_Disc'][y] = len(cursor.fetchall())

        ## numbers of Comet Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%Comet%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['Comet_Disc'][y] = len(cursor.fetchall())

        ## numbers of Satellite Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%Satellite%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['Satellite_Disc'][y] = len(cursor.fetchall())

        ## numbers of TNO Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%TNO%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['TNO_Disc'][y] = len(cursor.fetchall())

        ## numbers of Unusual Object Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%Unusual%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['Unusual_Disc'][y] = len(cursor.fetchall())

        ## numbers of Interstellar Object Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%Interstellar%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['Interstellar_Disc'][y] = len(cursor.fetchall())

        ## numbers of Unknown Object Discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '%{}%' and ObjectType like '%Unknown%' and MPECType like 'Discovery' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['Unknown_Disc'][y] = len(cursor.fetchall())
    
        ## numbers of follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, timestamp_start, timestamp_end, s))
        d[s]['mpec_followup'][y] = len(cursor.fetchall())
    
        ## numbers of first follow-up MPECs
        cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, timestamp_start, timestamp_end, s))
        tmp = cursor.fetchall()
        c = 0
        for i in tmp:
            if i[0] + ', ' + s in i[1]:
                c += 1
        
        d[s]['mpec_1st_followup'][y] = c

        ## numbers of NEAs follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%NEA%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['NEA_FU'][y] = len(cursor.fetchall())

        ## numbers of PHAs follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%PHA%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['PHA_FU'][y] = len(cursor.fetchall())

        ## numbers of Comets follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%Comet%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['Comet_FU'][y] = len(cursor.fetchall())

        ## numbers of Satellites follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%Satellite%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['Satellite_FU'][y] = len(cursor.fetchall())

        ## numbers of TNOs follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%TNO%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['TNO_FU'][y] = len(cursor.fetchall())

        ## numbers of Unusual Objects follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%Unusual%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['Unusual_FU'][y] = len(cursor.fetchall())

        ## numbers of Interstellar Objects follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%Interstellar%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['Interstellar_FU'][y] = len(cursor.fetchall())

        ## numbers of Unknown Objects follow-up MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}' and ObjectType like '%Unknown%';".format(s, timestamp_start, timestamp_end, s))
        d[s]['Unknown_FU'][y] = len(cursor.fetchall())

        ## numbers of precovery MPECs
        cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, timestamp_start, timestamp_end, s))
        tmp = cursor.fetchall()
        c = 0
        for i in tmp:
            if bool(re.match('.*' + s + '.*' + i[0] + '.*', i[1])):
                c += 1
            
        d[s]['mpec_precovery'][y] = c
        
        ## numbers of orbit update MPECs
        cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and time <= {} and MPECType = 'OrbitUpdate';".format(s, timestamp_start, timestamp_end))
        d[s]['mpec_recovery'][y] = len(cursor.fetchall())
        
        ## numbers of "1st spotter" orbit update MPECs
        cursor.execute("select Station from MPEC where Station like '{}%' and time >= {} and time <= {} and MPECType = 'OrbitUpdate';".format(s, timestamp_start, timestamp_end))
        d[s]['mpec_1st_recovery'][y] = len(cursor.fetchall())
    
with open('obscode_stat.json', 'w') as o:
    json.dump(d, o)
 
