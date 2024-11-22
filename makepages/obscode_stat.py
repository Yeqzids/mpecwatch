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
MPEC_types = ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup", "Precovery", "Recovery", "1stRecovery"]
obj_types = ["NEA", "PHA", "Comet", "Satellite", "TNO", "Unusual", "Interstellar", "unk"] #Only used when MPECType is Discovery or OrbitUpdate
d = dict()
for s in mpccode:
#for i in range(1):
    #s = 'G96'
    print(s)
    d[s] = {}
    d[s]['total'] = 0
    d[s]['MPECId'] = {}
    
    for obs_type in MPEC_types: 
        d[s][obs_type] = {}

    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
        year = int(year)
        for obs_type in MPEC_types:
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

        for mpecType in ["Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"]:
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
        if mpec[7] == 'NEA' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['NEA'][year] = d[station]['NEA'].get(year, 0) + 1

        # numbers of discovery MPECs
        if mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['mpec_discovery'][year] = d[station].get('mpec_discovery', 0) + 1

        # numbers of NEAs Discovery MPECs
        if mpec[7] == 'NEA' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['NEA_Disc'][year] = d[station].get('NEA_Disc', 0) + 1

        # numbers of PHA Discovery MPECs
        if mpec[7] == 'PHA' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['PHA_Disc'][year] = d[station].get('PHA_Disc', 0) + 1

        # numbers of Comet Discovery MPECs
        if mpec[7] == 'Comet' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['Comet_Disc'][year] = d[station].get('Comet_Disc', 0) + 1

        # numbers of Satellite Discovery MPECs
        if mpec[7] == 'Satellite' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['Satellite_Disc'][year] = d[station].get('Satellite_Disc', 0) + 1

        # numbers of TNO Discovery MPECs
        if mpec[7] == 'TNO' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['TNO_Disc'][year] = d[station].get('TNO_Disc', 0) + 1

        # numbers of Unusual Object Discovery MPECs
        if mpec[7] == 'Unusual' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['Unusual_Disc'][year] = d[station].get('Unusual_Disc', 0) + 1

        # numbers of Interstellar Object Discovery MPECs
        if mpec[7] == 'Interstellar' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['Interstellar_Disc'][year] = d[station].get('Interstellar_Disc', 0) + 1

        # numbers of Unknown Object Discovery MPECs
        if mpec[7] == 'Unknown' and mpec[6] == 'Discovery' and mpec[4] == station:
            d[station]['Unknown_Disc'][year] = d[station].get('Unknown_Disc', 0) + 1

        # numbers of follow-up MPECs
        if mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['mpec_followup'][year] = d[station].get('mpec_followup', 0) + 1

        # numbers of first follow-up MPECs
        if mpec[6] == 'Discovery' and mpec[4] != station and station + ', ' + mpec[4] in mpec[3]:
            d[station]['mpec_1st_followup'][year] = d[station].get('mpec_1st_followup', 0) + 1

        # numbers of NEAs follow-up MPECs
        if mpec[7] == 'NEA' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['NEA_FU'][year] = d[station].get('NEA_FU', 0) + 1

        # numbers of PHAs follow-up MPECs
        if mpec[7] == 'PHA' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['PHA_FU'][year] = d[station].get('PHA_FU', 0) + 1

        # numbers of Comets follow-up MPECs
        if mpec[7] == 'Comet' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['Comet_FU'][year] = d[station].get('Comet_FU', 0) + 1

        # numbers of Satellites follow-up MPECs
        if mpec[7] == 'Satellite' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['Satellite_FU'][year] = d[station].get('Satellite_FU', 0) + 1

        # numbers of TNOs follow-up MPECs
        if mpec[7] == 'TNO' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['TNO_FU'][year] = d[station].get('TNO_FU', 0) + 1

        # numbers of Unusual Objects follow-up MPECs
        if mpec[7] == 'Unusual' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['Unusual_FU'][year] = d[station].get('Unusual_FU', 0) + 1

        # numbers of Interstellar Objects follow-up MPECs
        if mpec[7] == 'Interstellar' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['Interstellar_FU'][year] = d[station].get('Interstellar_FU', 0) + 1

        # numbers of Unknown Objects follow-up MPECs
        if mpec[7] == 'Unknown' and mpec[6] == 'Discovery' and mpec[4] != station:
            d[station]['Unknown_FU'][year] = d[station].get('Unknown_FU', 0) + 1

        # numbers of precovery MPECs'
        if bool(re.match('.*' + station + '.*' + mpec[4] + '.*', mpec[3])):
            d[station]['mpec_precovery'][year] = d[station].get('mpec_precovery', 0) + 1

        # numbers of orbit update MPECs
        if mpec[6] == 'OrbitUpdate':
            d[station]['mpec_recovery'][year] = d[station].get('mpec_recovery', 0) + 1

        # numbers of "1st spotter" orbit update MPECs
        if mpec[6] == 'OrbitUpdate' and station[0] == mpec[4][0]:
            d[station]['mpec_1st_recovery'][year] = d[station].get('mpec_1st_recovery', 0) + 1
    
with open('obscode_stat.json', 'w') as o:
    json.dump(d, o)
 
