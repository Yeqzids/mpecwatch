#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Generate two plots:
				(1) Types of MPECs vs year
				(2) Object types of MPEC vs year

 (C) Quanzhi Ye
 
"""

import sqlite3, plotly.express as px, pandas as pd, datetime, numpy as np

dbFile = '../mpecwatch_v3.db'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

df = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []}) 
df2 = pd.DataFrame({"Year": [], "ObjType": [], "#MPECs": []}) 

for year in list(np.arange(1993, datetime.datetime.now().year+1, 1)):
	year_start = datetime.datetime(year, 1, 1, 0, 0, 0).timestamp()
	year_end = datetime.datetime(year, 12, 31, 23, 59, 59).timestamp()
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and MPECType = '{}'".format(year_start, year_end, 'Editorial'))
	editorial = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and MPECType = '{}'".format(year_start, year_end, 'Discovery'))
	discovery = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and MPECType = '{}'".format(year_start, year_end, 'OrbitUpdate'))
	orbitupdate = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and MPECType = '{}'".format(year_start, year_end, 'DOU'))
	dou = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and MPECType = '{}'".format(year_start, year_end, 'ListUpdate'))
	listupdate = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and MPECType = '{}'".format(year_start, year_end, 'Retraction'))
	retraction = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and MPECType = '{}'".format(year_start, year_end, 'Other'))
	other = len(cursor.fetchall())
	
	df = pd.concat([df, pd.DataFrame({"Year": [year, year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, retraction, other]})], ignore_index = True)

	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and ObjectType = '{}'".format(year_start, year_end, 'NEA'))
	nea = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and ObjectType = '{}'".format(year_start, year_end, 'Comet'))
	comet = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and ObjectType = '{}'".format(year_start, year_end, 'Satellite'))
	satellite = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and ObjectType = '{}'".format(year_start, year_end, 'Unusual'))
	unusual = len(cursor.fetchall())
	cursor.execute("select * from MPEC where Time >= {} and Time <= {} and ObjectType = '{}'".format(year_start, year_end, 'Interstellar'))
	interstellar = len(cursor.fetchall())
	
	#df = df.append(pd.DataFrame({"Year": [year, year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, retraction, other]}), ignore_index = True)

fig = px.bar(df, x="Year", y="#MPECs", color="MPECType", title="Number and type of MPECs by year")
#fig.show()

fig.write_html("MPECTally_ByYear_Fig.html")


