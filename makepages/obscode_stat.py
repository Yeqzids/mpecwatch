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
    d[s]['NEA_Disc'] = {}
    d[s]['PHA_Disc'] = {}
    d[s]['Comet_Disc'] = {}
    d[s]['Satellite_Disc'] = {}
    d[s]['TNO_Disc'] = {}
    d[s]['Unusual_Disc'] = {}
    d[s]['Interstellar_Disc'] = {}
    d[s]['Unknown_Disc'] = {}
    d[s]['mpec_followup'] = {}
    d[s]['NEA_FU'] = {}
    d[s]['PHA_FU'] = {}
    d[s]['Comet_FU'] = {}
    d[s]['Satellite_FU'] = {}
    d[s]['TNO_FU'] = {}
    d[s]['Unusual_FU'] = {}
    d[s]['Interstellar_FU'] = {}
    d[s]['Unknown_FU'] = {}
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
 
