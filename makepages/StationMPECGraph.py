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

import sqlite3, plotly.express as px, pandas as pd, datetime, numpy as np, json

mpecconn = sqlite3.connect("../mpecwatch_v3.db")
cursor = mpecconn.cursor()

mpccode = '../mpccode.json'
with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)

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

# prints columns headers of a table
def printColumns(table):
    cursor.execute("select * from {}".format(table))
    results = list(map(lambda x: x[0], cursor.description))
    print(results)
            
def main():
    for station_name in tableNames():
        try:
            mpccode[station_name[0][-3:]]
        except Exception as e:
            print(e)
            continue
		
        df = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []})
        station = station_name[0]
        editorials = set()
        discoveries = set()
        orbitupdates = set()
        dous = set()
        listupdates = set()
        retractions = set()
        others = set()
        page = "../www/byStation/" + str(station) + ".html"

        o = """
<!doctype html>
<html lang="en">
  <head>
        <!-- Google tag (gtag.js) -->
          <script async src="https://www.googletagmanager.com/gtag/js?id=G-WTXHKC28G9"></script>
          <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-WTXHKC28G9');
          </script>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="icon" href="../favicon.ico">

    <title>MPEC Watch</title>

    <!-- Bootstrap core CSS -->
    <link href="../dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap theme -->
    <link href="../dist/css/bootstrap-theme.min.css" rel="stylesheet">
    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <link href="../assets/css/ie10-viewport-bug-workaround.css" rel="stylesheet">

    <!-- Custom styles for this template -->
    <link href="../theme.css" rel="stylesheet">

    <!-- Just for debugging purposes. Don't actually copy these 2 lines! -->
    <!--[if lt IE 9]><script src="../assets/js/ie8-responsive-file-warning.js"></script><![endif]-->
    <script src="../assets/js/ie-emulation-modes-warning.js"></script>
    <script src="../dist/extensions/export/tableExport.min.js"></script>
        <script src="../dist/extensions/export/tableExport.js"></script>

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>

  <body>

    <!-- Fixed navbar -->
    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">MPEC Watch</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">
          <ul class="nav navbar-nav">
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/index.html">Home</a></li>
            <li class="active"><a href="https://sbnmpc.astro.umd.edu/mpecwatch/obs.html">Observatory Browser</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/stats.html">Various Statistics</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/mpc_stuff.html">MPC Stuff</a></li>
            <li><a href="https://github.com/Yeqzids/mpecwatch/issues">Issue Tracker</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu">SBN-MPC Annex</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container theme-showcase" role="main">

      <!-- Main jumbotron for a primary marketing message or call to action -->"""
        o += """<div class="row">
              <h2>{} {}</h2>""".format(station[-3:], mpccode[station[-3:]]['name'])
              
        if str(station[-3:]) not in ['244', '245', '247', '248', '249', '250', '258', '270', '274', '275', '500', 'C49', 'C50', 'C51', 'C52', 'C53', 'C54', 'C55', 'C56', 'C57', 'C59']:
            if mpccode[station[-3:]]['lon'] > 180:
                lon = mpccode[station[-3:]]['lon'] - 360
            else:
                lon = mpccode[station[-3:]]['lon']
            o += """<p><a href="https://geohack.toolforge.org/geohack.php?params={};{}">Where is this place?</a></p>""".format(mpccode[station[-3:]]['lat'], lon)
              
        o += """<p>
                  <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{}.html" height="525" width="100%"></iframe>
                  <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_Top_10_Observers.html" height="525" width="100%"></iframe>
                  <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_Top_10_Measurers.html" height="525" width="100%"></iframe>
                  <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_Top_10_Facilities.html" height="525" width="100%"></iframe>
              </p>
            </div>
            <div class="container">
            <table class="table table-striped" data-toggle="table" data-search="true" data-show-export="true" data-show-columns="true">
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
        """.format(str(station), str(station), str(station), str(station))
        
        for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
            year_start = datetime.datetime(year, 1, 1, 0, 0, 0).timestamp()
            year_end = datetime.datetime(year, 12, 31, 23, 59, 59).timestamp()
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'Editorial'))
            for i in cursor.fetchall():
                editorials.add(i[5])
            editorial = len(editorials)
            cursor.execute("select * from {} where Time >= {} and Time <= {} and Discovery == 1".format(station, year_start, year_end))
            for i in cursor.fetchall():
                discoveries.add(i[5])
            discovery = len(discoveries)
            #NEED TO UPDATE
            cursor.execute("select * from {} where Time >= {} and Time <= {} and MPECType = '{}'".format(station, year_start, year_end, 'OrbitUpdate'))
            for i in cursor.fetchall():
                orbitupdates.add(i[5])
            orbitupdate = len(orbitupdates)
            #NEED TO UPDATE
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
            
        try:
            fig = px.bar(df, x="Year", y="#MPECs", color="MPECType", title= station[-3:] + " " + mpccode[station[-3:]]['name']+" | Number and type of MPECs by year")
            fig.write_html("../www/byStation/Graphs/"+station+".html")
        except Exception as e:
            print(e)
        
        o += """    </table>
          </div>
        """
        
        o += """
	<footer class="pt-5 my-5 text-muted border-top">
    Script by <a href="https://www.astro.umd.edu/~qye/">Quanzhi Ye</a> and Taegon Hibbitts, hosted at <a href="https://sbnmpc.astro.umd.edu">SBN-MPC</a>. Powered by <a href="https://getbootstrap.com"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-bootstrap-fill" viewBox="0 0 16 16">
  <path d="M6.375 7.125V4.658h1.78c.973 0 1.542.457 1.542 1.237 0 .802-.604 1.23-1.764 1.23H6.375zm0 3.762h1.898c1.184 0 1.81-.48 1.81-1.377 0-.885-.65-1.348-1.886-1.348H6.375v2.725z"/>
  <path d="M4.002 0a4 4 0 0 0-4 4v8a4 4 0 0 0 4 4h8a4 4 0 0 0 4-4V4a4 4 0 0 0-4-4h-8zm1.06 12V3.545h3.399c1.587 0 2.543.809 2.543 2.11 0 .884-.65 1.675-1.483 1.816v.1c1.143.117 1.904.931 1.904 2.033 0 1.488-1.084 2.396-2.888 2.396H5.062z"/>
</svg> Bootstrap</a> and <a href="https://bootstrap-table.com">Bootstrap Table</a>.
        <a href="https://pdssbn.astro.umd.edu/"><img src="../sbn_logo5_v0.png" width="100" style="vertical-align:bottom"></a>
        <a href="https://github.com/Small-Bodies-Node/mpecwatch"><svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" fill="currentColor" class="bi bi-github" viewBox="0 0 16 16">
  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
</svg></a>
  </footer>

    <!-- Bootstrap core JavaScript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous"></script>
    <script>window.jQuery || document.write('<script src="../assets/js/vendor/jquery.min.js"><\/script>')</script>
    <script src="../dist/js/bootstrap.min.js"></script>
    <script src="../assets/js/docs.min.js"></script>
    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <script src="../assets/js/ie10-viewport-bug-workaround.js"></script>
  </body>
</html>"""

        with open(page, 'w') as f:
            
            f.write(o)

main()    
mpecconn.close()
print('finished')
