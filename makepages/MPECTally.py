#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Generate two plots:
				(1) Types of MPECs vs year
				(2) Object types of MPEC vs year

 (C) Quanzhi Ye
 
"""

import sqlite3, plotly.express as px, pandas as pd, datetime, numpy as np

dbFile = '../mpecwatch.db'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

df = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []}) 
df2 = pd.DataFrame({"Year": [], "ObjType": [], "#MPECs": []}) 

for year in list(np.arange(1993, datetime.datetime.now().year+1, 1)):
	cursor.execute("select * from MPEC where Time like '{}%' and MPECType = '{}'".format(year, 'Editorial'))
	editorial = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and MPECType = '{}'".format(year, 'Discovery'))
	discovery = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and MPECType = '{}'".format(year, 'OrbitUpdate'))
	orbitupdate = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and MPECType = '{}'".format(year, 'DOU'))
	dou = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and MPECType = '{}'".format(year, 'ListUpdate'))
	listupdate = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and MPECType = '{}'".format(year, 'Other'))
	other = len(cursor.fetchall())
	
	df = df.append(pd.DataFrame({"Year": [year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, other]}), ignore_index = True)
	
	cursor.execute("select * from MPEC where Time like '{}%' and ObjectType = '{}'".format(year, 'NEA'))
	nea = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and ObjectType = '{}'".format(year, 'Comet'))
	comet = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and ObjectType = '{}'".format(year, 'Satellite'))
	satellite = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time like '{}%' and ObjectType = '{}'".format(year, 'Unusual'))
	unusual = len(cursor.fetchall())
	
	df = df.append(pd.DataFrame({"Year": [year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, other]}), ignore_index = True)

fig = px.bar(df, x="Year", y="#MPECs", color="MPECType", title="Number and type of MPECs by year")
fig.show()

fig.write_html("MPECTally_ByYear_Fig.html")


