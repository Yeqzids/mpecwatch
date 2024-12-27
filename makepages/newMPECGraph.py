"""
Created on Wed Jul  6 14:49:19 2022

Generates individual station webpages including tables and statistics. Graphs are generated in IndividualOMF.py
Run this script AFTER IndividualOMF.py

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

import sqlite3, plotly.express as px, pandas as pd, datetime, numpy as np, json, threading, concurrent.futures
from datetime import date

mpec_data=dict()
mpecconn = sqlite3.connect("../mpecwatch_v3.db")
cursor = mpecconn.cursor()

mpccode = '../mpccode.json'
with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)

obscode = 'obscode_stat.json'
with open(obscode) as obscode:
    obscode = json.load(obscode)

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

MPEC_TYPES = ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup"]
OBJ_TYPES = ["NEA", "PHA", "Comet", "Satellite", "TNO", "Unusual", "Interstellar", "Unknown"]
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# main loop that traversed through all stations in obscodestat.py
for station_code in obscode:
    station = 'station_'+station_code
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

    <title>MPEC Watch | Station Statistics %s</title>

    <!-- Bootstrap core CSS -->
    <link href="https://unpkg.com/bootstrap-table@1.22.5/dist/bootstrap-table.min.css" rel="stylesheet">
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
    <!--
    <script src="../dist/extensions/export/tableExport.min.js"></script>
    <script src="../dist/extensions/export/tableExport.js"></script>
    -->

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
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/survey.html">Survey Browser</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/stats.html">Various Statistics</a></li>
            <!-- <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/mpc_stuff.html">MPC Stuff (non-public)</a></li> -->
            <li><a href="https://github.com/Yeqzids/mpecwatch/issues">Issue Tracker</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu">SBN-MPC Annex</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container theme-showcase" role="main">

      <!-- Main jumbotron for a primary marketing message or call to action -->""" % str(station[-3:])
    o += """<div class="row">
            <h2>{} {}</h2>""".format(station[-3:], mpccode[station[-3:]]['name'])
              
    if str(station[-3:]) not in ['244', '245', '247', '248', '249', '250', '258', '270', '273', '274', '275', '500', 'C49', 'C50', 'C51', 'C52', 'C53', 'C54', 'C55', 'C56', 'C57', 'C58', 'C59']:
        print(station[-3:])
        print(mpccode[station[-3:]])
        if mpccode[station[-3:]]['lon'] > 180:
            lon = mpccode[station[-3:]]['lon'] - 360
        else:
            lon = mpccode[station[-3:]]['lon']
        o += """<p><a href="https://geohack.toolforge.org/geohack.php?params={};{}">Where is this observatory?</a></p>""".format(mpccode[station[-3:]]['lat'], lon)

    o += """<p>
             <h3>Graphs</h3>
              <h4>Yearly Breakdown of MPEC Types</h4>
              <p>
              <b>Term definition:</b>
              Editorial - Editorial MPECs associated with this station.<br>
              Discovery - MPECs associated with discovery made by this station.<br>
              OrbitUpdate - MPECs associated with orbit updates involving observations made by this station. Typically, these are recoveries of single-opposition objects.<br>
              DOU - Daily Orbit Update MPECs involving observations made by this station.<br>
              ListUpdate - MPECs associated with list updates involving observations made by this station. This category has largely been retired since 2012.<br>
              Retraction - Retracted MPECs involving observations made by this station.<br>
              Followup - MPECs associated with follow-up observations made by this station to an object discovered elsewhere.<br>
              FirstFollowup - MPECs associated with follow-up observations made by this station to an object discovered elsewhere, with this station being the first station to follow-up.<br>
              Other - MPECs that do not fit into categories listed above and involve observations made by this station.
              </p>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{}.html" height="525" width="100%"></iframe>
              <h4>Yearly Breakdown of Discovery Object Types</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{}_disc_obj.html" height="525" width="100%"></iframe>
              <h4>Yearly Breakdown of Orbit Update Object Types</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{}_OU_obj.html" height="525" width="100%"></iframe>
              <h4>Breakdown by Observers</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_Top_10_Observers.html" height="525" width="100%"></iframe>
              <h4>Breakdown by Measurers</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_Top_10_Measurers.html" height="525" width="100%"></iframe>
              <h4>Breakdown by Facilities</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_Top_10_Facilities.html" height="525" width="100%"></iframe>
              <h4>Breakdown by Objects</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_Top_10_Objects.html" height="525" width="100%"></iframe>
              <h4>Annual Breakdown</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_yearly.html" height="525" width="100%"></iframe>
              <h4>Weekly Breakdown</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_weekly.html" height="525" width="100%"></iframe>
              <h4>Hourly Breakdown</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{}_hourly.html" height="525" width="100%"></iframe>
            </p>
        </div>
        <div class="container">
          <h3>Tables</h3>
          <h4>Yearly Breakdown of MPEC Types</h4>
            <table id="year_table" class="table table-striped table-sm" 
                data-toggle="table"
                data-show-export="true"
                data-show-columns="true">
                <thead>
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
                        <th>Follow-Up</th>
                        <th>First Follow-Up</th>
                    </tr>
                </thead>
        """.format(station, station, station, station, station, station, station, station, station, station)
    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
        # yearly breakdown of MPEC types
        df_yearly = pd.concat([pd.DataFrame({"Year": [year]*len(MPEC_TYPES), "MPECType": MPEC_TYPES, "#MPECs": [obscode[station_code][mpecType][str(year)]['total'] for mpecType in MPEC_TYPES]})])
        disc_obj = pd.concat([disc_obj, pd.DataFrame({"Year": [year]*len(OBJ_TYPES), "ObjectType": OBJ_TYPES, "#MPECs": [obscode[station_code]['Discovery'][str(year)][obj] for obj in OBJ_TYPES]})])
        OU_obj = pd.concat([OU_obj, pd.DataFrame({"Year": [year]*len(OBJ_TYPES), "ObjectType": OBJ_TYPES, "#MPECs": [obscode[station_code]['OrbitUpdate'][str(year)][obj] for obj in OBJ_TYPES]})])

        # monthly breakdown of MPEC types
