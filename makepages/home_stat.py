#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Generate some statistics for the home page

 (C) Quanzhi Ye
 
"""

import sqlite3, datetime, re, json

dbFile = '../mpecwatch_v3.db'
mpccode = '../mpccode.json'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)

mpec_count = '{:3s} {:10s} {:10s} {:10s}\n'.format('cod', 'count1y', 'count5y', 'countall')
disc_count = '{:3s} {:10s} {:10s} {:10s}\n'.format('cod', 'count1y', 'count5y', 'countall')
fu_count = '{:3s} {:10s} {:10s} {:10s}\n'.format('cod', 'count1y', 'count5y', 'countall')
fu1_count = '{:3s} {:10s} {:10s} {:10s}\n'.format('cod', 'count1y', 'count5y', 'countall')
pc_count = '{:3s} {:10s} {:10s} {:10s}\n'.format('cod', 'count1y', 'count5y', 'countall')

for s in mpccode:
    t_1y = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    t_5y = datetime.datetime.utcnow() - datetime.timedelta(days=365*5)
    
    # Count numbers of MPECs for each station for last 1, 5 year and all time
    
    cursor.execute("select station from MPEC where station like '%{}%' and time >= {};".format(s, t_1y.timestamp()))
    c_1y = len(cursor.fetchall())
    cursor.execute("select station from MPEC where station like '%{}%' and time >= {};".format(s, t_5y.timestamp()))
    c_5y = len(cursor.fetchall())
    cursor.execute("select station from MPEC where station like '%{}%';".format(s))
    c_all = len(cursor.fetchall())
    mpec_count += '{:3s} {:10s} {:10s} {:10s}\n'.format(s, str(c_1y), str(c_5y), str(c_all))
    
    # Count numbers of discovery MPECs for each station for last 1, 5 year and all time
    
    cursor.execute("select DiscStation from MPEC where DiscStation like '{}' and time >= {};".format(s, t_1y.timestamp()))
    c_1y = len(cursor.fetchall())
    cursor.execute("select DiscStation from MPEC where DiscStation like '{}' and time >= {};".format(s, t_5y.timestamp()))
    c_5y = len(cursor.fetchall())
    cursor.execute("select DiscStation from MPEC where DiscStation like '{}';".format(s))
    c_all = len(cursor.fetchall())
    disc_count += '{:3s} {:10s} {:10s} {:10s}\n'.format(s, str(c_1y), str(c_5y), str(c_all))
    
    # Count numbers of follow-up MPECs (precoveries/follow-ups, but not DOUs) for each station for last 1, 5 year and all time
    
    cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, t_1y.timestamp(), s))
    c_1y = len(cursor.fetchall())
    cursor.execute("select Station from MPEC where Station like '%{}%' and time >= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, t_5y.timestamp(), s))
    c_5y = len(cursor.fetchall())
    cursor.execute("select Station from MPEC where Station like '%{}%' and MPECType = 'Discovery' and DiscStation != '{}';".format(s, s))
    c_all = len(cursor.fetchall())
    fu_count += '{:3s} {:10s} {:10s} {:10s}\n'.format(s, str(c_1y), str(c_5y), str(c_all))
    
    # Count numbers of first follow-up MPECs for each station for last 1, 5 year and all time
    
    cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and time >= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, t_1y.timestamp(), s))
    d_1y = cursor.fetchall()
    c_1y = 0
    for i in d_1y:
        if i[0] + ', ' + s in i[1]:
            c_1y += 1
            
    cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and time >= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, t_5y.timestamp(), s))
    d_5y = cursor.fetchall()
    c_5y = 0
    for i in d_5y:
        if i[0] + ', ' + s in i[1]:
            c_5y += 1
            
    cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and MPECType = 'Discovery' and DiscStation != '{}';".format(s, s))
    d_all = cursor.fetchall()
    c_all = 0
    for i in d_all:
        if i[0] + ', ' + s in i[1]:
            c_all += 1
            
    fu1_count += '{:3s} {:10s} {:10s} {:10s}\n'.format(s, str(c_1y), str(c_5y), str(c_all))
    
    # Count numbers of precovery MPECs for each station for last 1, 5 year and all time
    
    cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and time >= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, t_1y.timestamp(), s))
    d_1y = cursor.fetchall()
    c_1y = 0
    for i in d_1y:
        if bool(re.match('.*' + s + '.*' + i[0] + '.*', i[1])):
            c_1y += 1
            
    cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and time >= {} and MPECType = 'Discovery' and DiscStation != '{}';".format(s, t_5y.timestamp(), s))
    d_5y = cursor.fetchall()
    c_5y = 0
    for i in d_5y:
        if bool(re.match('.*' + s + '.*' + i[0] + '.*', i[1])):
            c_5y += 1
            
    cursor.execute("select DiscStation, Station from MPEC where Station like '%{}%' and MPECType = 'Discovery' and DiscStation != '{}';".format(s, s))
    d_all = cursor.fetchall()
    c_all = 0
    for i in d_all:
        if bool(re.match('.*' + s + '.*' + i[0] + '.*', i[1])):
            c_all += 1
            
    pc_count += '{:3s} {:10s} {:10s} {:10s}\n'.format(s, str(c_1y), str(c_5y), str(c_all))
    
with open('mpec_count.txt', 'w') as f:
	f.write(mpec_count)

with open('disc_count.txt', 'w') as f:
	f.write(disc_count)
    
with open('fu_count.txt', 'w') as f:
	f.write(fu_count)
    
with open('fu1_count.txt', 'w') as f:
	f.write(fu1_count)
    
with open('pc_count.txt', 'w') as f:
	f.write(pc_count)
