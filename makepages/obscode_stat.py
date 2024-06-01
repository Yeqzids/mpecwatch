#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Generate statistics for every observatory by year

 (C) Quanzhi Ye
 
"""

import sqlite3, datetime, re, json, numpy as np, calendar

dbFile = '../mpecwatch_v3.db'
mpccode = '../mpccode.json'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

currentYear = datetime.datetime.now().year

with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)
    
d = dict()

for s in mpccode:
#for i in range(1):
    #s = 'G96'

    d[s] = {}
    d[s]['mpec'] = {}
    d[s]['mpec_discovery'] = {}
    d[s]['NEA'] = {}
    d[s]['PHA'] = {}
    d[s]['mpec_followup'] = {}
    d[s]['mpec_1st_followup'] = {}
    d[s]['mpec_precovery'] = {}
    d[s]['mpec_recovery'] = {}
    d[s]['mpec_1st_recovery'] = {}
    
    for y in np.arange(1993, currentYear+1, 1):
        y = int(y)
        timestamp_start = calendar.timegm(datetime.date(y,1,1).timetuple())
        timestamp_end = calendar.timegm(datetime.date(y+1,1,1).timetuple())-1

        ## numbers of MPECs
        cursor.execute("select station from MPEC where station like '%{}%' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['mpec'][y] = len(cursor.fetchall())
    
        ## numbers of discovery MPECs
        cursor.execute("select DiscStation from MPEC where DiscStation like '{}' and time >= {} and time <= {};".format(s, timestamp_start, timestamp_end))
        d[s]['mpec_discovery'][y] = len(cursor.fetchall())

        ## numbers of PHAs
        cursor.execute("select ObjectType from MPEC where Station like '%{}%' and ObjectType like '%PHA%' and ((MPECType like 'Discovery' and DiscStation like '%{}%')) and time >= {} and time <= {};".format(s, s, timestamp_start, timestamp_end))
        d[s]['PHA'][y] = len(cursor.fetchall())

        ## numbers of NEAs
        cursor.execute("select ObjectType from MPEC where Station like '%{}%' and ObjectType like '%NEA%' and ((MPECType like 'Discovery' and DiscStation like '%{}%')) and time >= {} and time <= {};".format(s, s, timestamp_start, timestamp_end))
        d[s]['NEA'][y] = len(cursor.fetchall())
    
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
 
