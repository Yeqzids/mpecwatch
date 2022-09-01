# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 14:49:19 2022

(a) Bar chart + break-down table of the number and type of MPECs by year (like the one on the home page)

Database structure
---
    Key            Type        Description
TABLE MPEC: (summary of each MPEC)
    MPECId        TEXT        MPEC Number
    Title        TEXT        MPEC Title
    Time        INTEGER      Publication Unix timestamp
    Station        TEXT        List of observatory stations involved in the observation. Only used when MPECType is Discovery, OrbitUpdate, or DOU        
    DiscStation    TEXT        Observatory station marked by the discovery asterisk. Only used when MPECType is Discovery.
    FirstConf    TEXT        First observatory station to confirm. Only used when MPECType is Discovery.
    MPECType    TEXT        Type of the MPEC: Editorial, Discovery, OrbitUpdate, DOU, ListUpdate, Retraction, Other
    ObjectType    TEXT        Type of the object: NEA, Comet, Satellite, TNO, Unusual, Interstellar, unk. Only used when MPECType is Discovery or OrbitUpdate
    OrbitComp    TEXT        Orbit computer. Only used when MPECType is Discovery or OrbitUpdate
    Issuer        TEXT        Issuer of the MPEC
    
TABLE XXX (observatory code):
    Object        TEXT        Object designation in packed form
    Time        INTEGER        Time of the observation (Unix timestamp)
    Observer    TEXT        List of observers as published in MPEC
    Measurer    TEXT        List of measurers as published in MPEC
    Facility    TEXT        List of telescope/instrument as published in MPEC
    MPEC        TEXT        MPECId
    MPECType    TEXT        Type of the MPEC: Discovery, OrbitUpdate, DOU
    ObjectType    TEXT        Type of the object: NEA, Comet, Satellite, TNO, Unusual, Interstellar, unk
    Discovery    INTEGER        Corresponding to discovery asterisk
"""

import sqlite3, plotly.express as px, pandas as pd, datetime, numpy as np

mpecconn = sqlite3.connect("mpecwatch_v3.db")
cursor = mpecconn.cursor()

#prints the contents of a table w/ output limit
def printTableContent(table):
    rows = cursor.execute("SELECT * FROM {} WHERE Object = 'J99M00L' LIMIT 100".format(table)).fetchall()
    print(rows)


#List of table names
def tableNames():
    sql = '''SELECT name FROM sqlite_master WHERE type='table';'''
    cursor = mpecconn.execute(sql)
    results = cursor.fetchall()
    return(results[1::])
    
#create a graph of one station 
def createGraph(station_name):
    df = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []})
    editorials = set()
    discoveries = set()
    orbitupdates = set()
    dous = set()
    listupdates = set()
    retractions = set()
    others = set()
    station = str(station_name[0])
    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1)):
        year_start = datetime.datetime(year, 1, 1, 0, 0, 0).timestamp()
        year_end = datetime.datetime(year, 12, 31, 23, 59, 59).timestamp()
        cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Editorial'))
        for i in cursor.fetchall():
            editorials.add(i[5])
        editorial = len(editorials)
        cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Discovery'))
        for i in cursor.fetchall():
            discoveries.add(i[5])
        discovery = len(discoveries)
        cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'OrbitUpdate'))
        for i in cursor.fetchall():
            orbitupdates.add(i[5])
        orbitupdate = len(orbitupdates)
        cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'DOU'))
        for i in cursor.fetchall():
            dous.add(i[5])
        dou = len(dous)
        cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'ListUpdate'))
        for i in cursor.fetchall():
            listupdates.add(i[5])
        listupdate = len(listupdates)
        cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Retraction'))
        for i in cursor.fetchall():
            retractions.add(i[5])
        retraction = len(retractions)
        cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Other'))
        for i in cursor.fetchall():
            others.add(i[5])
        other = len(others)
           
        df = df.append(pd.DataFrame({"Year": [year, year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, retraction, other]}), ignore_index = True)
        editorials = set()
        discoveries = set()
        orbitupdates = set()
        dous = set()
        listupdates = set()
        retractions = set()
        others = set()
    
    print(df)  
    fig = px.bar(df, x="Year", y="#MPECs", color="MPECType", title= station.capitalize()+" | Number and type of MPECs by year")
    fig.write_html("WEB_Stations/Graphs/"+station+".html")
    #fig.show()

# prints columns headers of a table
def printColumns(table):
    cursor.execute("select * from {}".format(table))
    results = list(map(lambda x: x[0], cursor.description))
    print(results)

#MAIN    
def createWEB():
    for station in tableNames():
        createGraph(station)    
        page = "WEB_Stations/WEB_" + str(station[0]) + ".html"
        o = """
        <div class="jumbotron text-center">
          <h1>{}</h1>
          <p>Graphs supported by Plotly</p>
        </div>
        
        <div class="container">
          <div class="row">
            <div class="col-sm-4">
              <h3>Graph 1</h3>
              <p>
                  Testing
                  <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{}.html" height="525" width="100%"></iframe>
              </p>
            </div>
            <table>
                <tr>
                    <th>Year</th>
                    <th>Total MPECs</th>
                    <th>Editorial</th>
                    <th>Discovery</th>
                    <th>P/R/FU</th>
                    <th>DOU</th>
                    <th>List Update</th>
                    <th>Retraction</th>
                    <th>Other</th>
                </tr>
            </table>
        """.format(str(station[0]).capitalize(), str(station[0]))
        
        for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
            year_start = datetime.datetime(year, 1, 1, 0, 0, 0).timestamp()
            year_end = datetime.datetime(year, 12, 31, 23, 59, 59).timestamp()
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station[0], year_start, year_end, 'Editorial'))
            editorial = len(cursor.fetchall())
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station[0], year_start, year_end, 'Discovery'))
            discovery = len(cursor.fetchall())
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station[0], year_start, year_end, 'OrbitUpdate'))
            orbitupdate = len(cursor.fetchall())
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station[0], year_start, year_end, 'DOU'))
            dou = len(cursor.fetchall())
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station[0], year_start, year_end, 'ListUpdate'))
            listupdate = len(cursor.fetchall())
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station[0], year_start, year_end, 'Retraction'))
            retraction = len(cursor.fetchall())
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station[0], year_start, year_end, 'Other'))
            other = len(cursor.fetchall())
            
            o += """
              <tr>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
              </tr>
            """ % (year, sum([editorial, discovery, orbitupdate, dou, listupdate, retraction, other]), editorial, discovery, orbitupdate, dou, listupdate, retraction, other)
        
        o += """    
          </div>
        </div>
        """

        with open(page, 'w') as f:
            f.write(o)
            
def main():
    for station_name in tableNames():
        df = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []})
        station = station_name[0]
        editorials = set()
        discoveries = set()
        orbitupdates = set()
        dous = set()
        listupdates = set()
        retractions = set()
        others = set()
        page = "WEB_Stations/WEB_" + str(station) + ".html"
        o = """
        <div class="jumbotron text-center">
          <h1>{}</h1>
          <p>Graphs supported by Plotly</p>
        </div>
        
        <div class="container">
          <div class="row">
            <div class="col-sm-4">
              <h3>Graph 1</h3>
              <p>
                  Testing
                  <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{}.html" height="525" width="100%"></iframe>
              </p>
            </div>
            <table>
                <tr>
                    <th>Year</th>
                    <th>Total MPECs</th>
                    <th>Editorial</th>
                    <th>Discovery</th>
                    <th>P/R/FU</th>
                    <th>DOU</th>
                    <th>List Update</th>
                    <th>Retraction</th>
                    <th>Other</th>
                </tr>
            </table>
        """.format(station.capitalize(), station)
        
        for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
            year_start = datetime.datetime(year, 1, 1, 0, 0, 0).timestamp()
            year_end = datetime.datetime(year, 12, 31, 23, 59, 59).timestamp()
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Editorial'))
            for i in cursor.fetchall():
                editorials.add(i[5])
            editorial = len(editorials)
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Discovery'))
            for i in cursor.fetchall():
                discoveries.add(i[5])
            discovery = len(discoveries)
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'OrbitUpdate'))
            for i in cursor.fetchall():
                orbitupdates.add(i[5])
            orbitupdate = len(orbitupdates)
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'DOU'))
            for i in cursor.fetchall():
                dous.add(i[5])
            dou = len(dous)
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'ListUpdate'))
            for i in cursor.fetchall():
                listupdates.add(i[5])
            listupdate = len(listupdates)
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Retraction'))
            for i in cursor.fetchall():
                retractions.add(i[5])
            retraction = len(retractions)
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Other'))
            for i in cursor.fetchall():
                others.add(i[5])
            other = len(others)
            df = df.append(pd.DataFrame({"Year": [year, year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, retraction, other]}), ignore_index = True)
            
            o += """
              <tr>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
                <td>%i</td>
              </tr>
            """ % (year, sum([editorial, discovery, orbitupdate, dou, listupdate, retraction, other]), editorial, discovery, orbitupdate, dou, listupdate, retraction, other)
        
            editorials.clear()
            discoveries.clear()
            orbitupdates.clear()
            dous.clear()
            listupdates.clear()
            retractions.clear()
            others.clear()
            
        fig = px.bar(df, x="Year", y="#MPECs", color="MPECType", title= station.capitalize()+" | Number and type of MPECs by year")
        fig.write_html("WEB_Stations/Graphs/"+station+".html")
        
        o += """    
          </div>
        </div>
        """

        with open(page, 'w') as f:
            
            f.write(o)

main()    
mpecconn.close()
print('finished')