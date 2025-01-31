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

import sqlite3, plotly.express as px, pandas as pd, datetime, numpy as np, json, signal, concurrent.futures, multiprocessing, traceback, os
from datetime import date
import logging
import ctypes, time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

stop_event = multiprocessing.Event()

def signal_handler(sig, frame):
    logging.info('Exit signal received, shutting down...')
    stop_event.set()

def make_monthly_page(df_monthly, station, year):
    if stop_event.is_set():
        return

    station_code = station[-3:]
    station_year = station + "_" + str(year)

    fig = px.bar(df_monthly, x="Month", y="#MPECs", color="MPECType")
    fig.write_html(f"../www/byStation/monthly/graphs/{station_year}.html")
    
    # Log DataFrame contents if it does not contain the expected columns
    if not all(col in df_monthly.columns for col in ["Month", "#MPECs", "MPECType"]):
        logging.info(f"DataFrame contents for station {station_code}, year {year}:\n{df_monthly}")
        stop_event.set()
        return

    df_monthly.set_index(['Month', 'MPECType'], inplace=True) # set index after making the graph to avoid error
    page_monthly = f"../www/byStation/monthly/{station_year}.html"
    o = f"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MPECWatch: {year} Monthly Summary | {station_code}</title>
        <!-- Bootstrap CSS -->
        <link href="../../dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- Bootstrap Theme CSS -->
        <link href="../../dist/css/bootstrap-theme.min.css" rel="stylesheet">
        <!-- Bootstrap Table CSS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-table@1.24.0/dist/bootstrap-table.min.css">

        <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
        <link href="../../assets/css/ie10-viewport-bug-workaround.css" rel="stylesheet">

        <!-- Custom styles for this template -->
        <link href="../../theme.css" rel="stylesheet">

        <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
        <!--[if lt IE 9]>
        <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
        <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
        <![endif]-->
    </head>
    <body>
        <div class="container" role="main" style="padding-bottom: 20px;">
            <h2 style="margin-top: 20px;">{mpccode[station_code]['name']} {year} | Monthly Breakdown</h2>
            <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="graphs/{station_year}.html" height="525" width="100%"></iframe>
            <table id="month_table"
                class="table table-striped table-hover table-sm table-responsive"
                data-toggle="table"
                data-show-export="true"
                data-show-columns="true">
                <thead>
                    <tr>
                        <th>Month</th>
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
                </thead>"""
    for month in MONTHS:
        o += f"""   
                <tr>
                    <td>{month}</td>"""
        for mpecType in MPEC_TYPES:
            o += f"""
                    <td>{int(df_monthly.loc[(month, mpecType)]['#MPECs'])}</td>"""
        o+= """</tr>"""
    o += """
            </table>            
        </div>
        <!-- jQuery -->
        <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
        <script>window.jQuery || document.write('<script src="../assets/js/vendor/jquery.min.js"><\/script>')</script>
        <!-- Popper JS -->
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" integrity="sha384-I7E8VVD/ismYTF4hNIPjVp/Zjvgyol6VFvRkX/vR+Vc4jQkC+hVqc2pM8ODewa9r" crossorigin="anonymous"></script>
        <!-- Bootrap JS -->
        <script src="../../dist/js/bootstrap.min.js"></script>
        <!-- Bootstrap Table JS -->
        <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/tableExport.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/libs/jsPDF/jspdf.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.24.0/dist/bootstrap-table.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.24.0/dist/extensions/export/bootstrap-table-export.min.js"></script>
    </body>
</html>"""

    if stop_event.is_set():
        return

    with open(page_monthly, 'w') as f:
        f.write(o)

# main loop that traversed through all stations in obscodestat.py
def make_station_page(station_code):
    if stop_event.is_set():
        return
    
    logging.info(f"Starting processing for station: {station_code}")

    station = 'station_'+station_code
    page = f"../www/byStation/{station}.html"

    o = f"""
<!doctype html>
<html lang="en">
  <head>
        <!-- Google tag (gtag.js) -->
          <script async src="https://www.googletagmanager.com/gtag/js?id=G-WTXHKC28G9"></script>
          <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
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

    <title>MPEC Watch | Station Statistics {station_code}</title>

    <!-- Bootstrap CSS -->
    <link href="../dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Theme CSS -->
    <link href="../dist/css/bootstrap-theme.min.css" rel="stylesheet">
    <!-- Bootstrap Table CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-table@1.24.0/dist/bootstrap-table.min.css">

    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <link href="../assets/css/ie10-viewport-bug-workaround.css" rel="stylesheet">

    <!-- Custom styles for this template -->
    <link href="../theme.css" rel="stylesheet">

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
        <div class="row">
            <!-- Main jumbotron for a primary marketing message or call to action -->
            <h2>{station_code} {mpccode[station_code]['name']}</h2>"""
              
    if station_code not in ['244', '245', '247', '248', '249', '250', '258', '270', '273', '274', '275', '500', 'C49', 'C50', 'C51', 'C52', 'C53', 'C54', 'C55', 'C56', 'C57', 'C58', 'C59']:
        #print(station_code)
        #print(mpccode[station_code])
        if mpccode[station_code]['lon'] > 180:
            lon = mpccode[station_code]['lon'] - 360
        else:
            lon = mpccode[station_code]['lon']
        o += f"""
            <p><a href="https://geohack.toolforge.org/geohack.php?params={mpccode[station_code]['lat']};{lon}">Where is this observatory?</a></p>"""

    o += f"""
            <p>
                <h3>Graphs</h3>
                <h4>Yearly Breakdown of MPEC Types</h4>
                <b>Term definition:</b>
                <br>
                Editorial - Editorial MPECs associated with this station.<br>
                Discovery - MPECs associated with discovery made by this station.<br>
                OrbitUpdate - MPECs associated with orbit updates involving observations made by this station. Typically, these are recoveries of single-opposition objects.<br>
                DOU - Daily Orbit Update MPECs involving observations made by this station.<br>
                ListUpdate - MPECs associated with list updates involving observations made by this station. This category has largely been retired since 2012.<br>
                Retraction - Retracted MPECs involving observations made by this station.<br>
                Followup - MPECs associated with follow-up observations made by this station to an object discovered elsewhere.<br>
                FirstFollowup - MPECs associated with follow-up observations made by this station to an object discovered elsewhere, with this station being the first station to follow-up.<br>
                Other - MPECs that do not fit into categories listed above and involve observations made by this station.
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{station}.html" height="525" width="100%"></iframe>
                <h4>Yearly Breakdown of Discovery Object Types</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{station}_disc_obj.html" height="525" width="100%"></iframe>
                <h4>Yearly Breakdown of Orbit Update Object Types</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="Graphs/{station}_OU_obj.html" height="525" width="100%"></iframe>
                <h4>Breakdown by Observers</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{station}_Top_10_Observers.html" height="525" width="100%"></iframe>
                <h4>Breakdown by Measurers</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{station}_Top_10_Measurers.html" height="525" width="100%"></iframe>
                <h4>Breakdown by Facilities</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{station}_Top_10_Facilities.html" height="525" width="100%"></iframe>
                <h4>Breakdown by Objects</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{station}_Top_10_Objects.html" height="525" width="100%"></iframe>
                <h4>Annual Breakdown</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{station}_yearly.html" height="525" width="100%"></iframe>
                <h4>Weekly Breakdown</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{station}_weekly.html" height="525" width="100%"></iframe>
                <h4>Hourly Breakdown</h4>
                <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="OMF/{station}_hourly.html" height="525" width="100%"></iframe>
            </p>
        </div>
        <div class="row">
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
                </thead>"""
    
    df_yearly = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []})
    disc_obj = pd.DataFrame({"Year": [], "ObjectType": [], "#MPECs": []})
    OU_obj = pd.DataFrame({"Year": [], "ObjectType": [], "#MPECs": []})
    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
        # yearly breakdown of MPEC types
        df_yearly = pd.concat([df_yearly, pd.DataFrame({"Year": [year]*len(MPEC_TYPES), "MPECType": MPEC_TYPES, "#MPECs": [obscode[station_code][mpecType][str(year)]['total'] for mpecType in MPEC_TYPES]})])
        disc_obj = pd.concat([disc_obj, pd.DataFrame({"Year": [year]*len(OBJ_TYPES), "ObjectType": OBJ_TYPES, "#MPECs": [obscode[station_code]['Discovery'][str(year)][obj] for obj in OBJ_TYPES]})])
        OU_obj = pd.concat([OU_obj, pd.DataFrame({"Year": [year]*len(OBJ_TYPES), "ObjectType": OBJ_TYPES, "#MPECs": [obscode[station_code]['OrbitUpdate'][str(year)][obj] for obj in OBJ_TYPES]})])

        df_monthly = pd.DataFrame({"Month": [], "MPECType": [], "#MPECs": []})
        # monthly breakdown of MPEC types
        for month in MONTHS:
            df_monthly = pd.concat([df_monthly, pd.DataFrame({"Month": [month] * len(MPEC_TYPES), "MPECType": MPEC_TYPES, "#MPECs": [obscode[station_code][mpecType][str(year)][month] for mpecType in MPEC_TYPES]})])
        make_monthly_page(df_monthly, station, year)

        o += f"""
                <tr>
                    <td><a href="monthly/{station}_{year}.html">{year}</a></td>
                    <td>{sum([obscode[station_code][mpecType][str(year)]['total'] for mpecType in MPEC_TYPES])}</td>"""
        for mpecType in MPEC_TYPES:
            o += f"""
                    <td>{obscode[station_code][mpecType][str(year)]['total']}</td>"""
        o += """
                </tr>"""            
    
    o += """
            </table>
        </div>
        <div class="row">
            <h4 style="padding-top: 20px;">List of Individual MPECs</h4>
            <table id="mpec_table" 
                class="table table-striped table-bordered table-sm"
                data-height="460"
                data-toggle="table"
                data-pagination="true"
                data-search="true"
                data-show-export="true"
                data-show-columns="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="index" data-sortable="true">Index</th>
                        <th class="th-sm" data-field="name" data-sortable="true">Name</th>
                        <th class="th-sm" data-field="date" data-sortable="true">Date/Time</th>
                        <th class="th-sm" data-field="ds" data-sortable="true">Discoverer</th>
                        <th class="th-sm" data-field="fs" data-sortable="true">First-responding Confirmer</th>
                        <th class="th-sm" data-field="obj" data-sortable="true">Object Type</th>
                        <th class="th-sm" data-field="catch" data-sortable="true">Search Archival Image</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
    """

    index = 1
    for i in obscode[station_code]['MPECs']:
        o += f"""
                        <td>{index}</td>
                        <td>{i[0]}</td>
                        <td>{datetime.datetime.fromtimestamp(i[1])}</td>
                        <td>{i[2]}</td>
                        <td>{i[3]}</td>
                        <td>{i[4]}</td>
                        <td>{i[5]}</td>
                    </tr>
        """
        index += 1
        
    o += """
                </tbody>
            </table>
            <h4>List of Observers</h4>
            <table id="OBS_table" 
                class="table table-striped table-bordered table-sm"
                data-toggle="table"
                data-search="true"
                data-pagination="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="observer" data-sortable="true">Observers</th>
                        <th class="th-sm" data-field="count" data-sortable="true">Count</th>
                    </tr>
                </thead>
                <tbody>"""
    for observer, count in obscode[station_code]['OBS'].items():
        o += f"""
                    <tr>
                        <td>{observer}</td>
                        <td>{count}</td>
                    </tr>"""
        
    o += """
                </tbody>
            </table>
            <h4>List of Measurers</h4>
            <table id="MEA_table" 
                class="table table-striped table-bordered table-sm"
                data-toggle="table"
                data-search="true"
                data-pagination="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="measurer" data-sortable="true">Measurers</th>
                        <th class="th-sm" data-field="count" data-sortable="true">Count</th>
                    </tr>
                </thead>
                <tbody>"""
    for measurer, count in obscode[station_code]['MEA'].items():
        o += f"""
                    <tr>
                        <td>{measurer}</td>
                        <td>{count}</td>
                    </tr>"""
        
    o += """
                </tbody>
            </table>
            <h4>List of Facilities</h4>
            <table id="FAC_table" 
                class="table table-striped table-bordered table-sm"
                data-toggle="table"
                data-search="true"
                data-pagination="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="facility" data-sortable="true">Facilities</th>
                        <th class="th-sm" data-field="count" data-sortable="true">Count</th>
                    </tr>
                </thead>
                <tbody>"""
    for facility, count in obscode[station_code]['FAC'].items():
        o += f"""
                    <tr>
                        <td>{facility}</td>
                        <td>{count}</td>
                    </tr>"""
        
    o += """
                </tbody>
            </table>
        </div>
        <footer class="pt-5 my-5 text-muted border-top">
        Script by <a href="https://www.astro.umd.edu/~qye/">Quanzhi Ye</a> and <a href="https://taegonhibbitts.com">Taegon Hibbitts</a>, hosted at <a href="https://sbnmpc.astro.umd.edu">SBN-MPC</a>. Powered by <a href="https://getbootstrap.com"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-bootstrap-fill" viewBox="0 0 16 16">
        <path d="M6.375 7.125V4.658h1.78c.973 0 1.542.457 1.542 1.237 0 .802-.604 1.23-1.764 1.23H6.375zm0 3.762h1.898c1.184 0 1.81-.48 1.81-1.377 0-.885-.65-1.348-1.886-1.348H6.375v2.725z"/>
        <path d="M4.002 0a4 4 0 0 0-4 4v8a4 4 0 0 0 4 4h8a4 4 0 0 0 4-4V4a4 4 0 0 0-4-4h-8zm1.06 12V3.545h3.399c1.587 0 2.543.809 2.543 2.11 0 .884-.65 1.675-1.483 1.816v.1c1.143.117 1.904.931 1.904 2.033 0 1.488-1.084 2.396-2.888 2.396H5.062z"/>
        </svg> Bootstrap</a> and <a href="https://bootstrap-table.com">Bootstrap Table</a>.
            <a href="https://pdssbn.astro.umd.edu/"><img src="../sbn_logo5_v0.png" width="100" style="vertical-align:bottom"></a>
            <a href="https://github.com/Small-Bodies-Node/mpecwatch"><svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" fill="currentColor" class="bi bi-github" viewBox="0 0 16 16">
        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
        </svg></a>
        </footer>
    </div> <!-- /container -->
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script>window.jQuery || document.write('<script src="../assets/js/vendor/jquery.min.js"><\/script>')</script>
    <!-- Popper JS -->
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" integrity="sha384-I7E8VVD/ismYTF4hNIPjVp/Zjvgyol6VFvRkX/vR+Vc4jQkC+hVqc2pM8ODewa9r" crossorigin="anonymous"></script>
    <!-- Bootrap JS -->
    <script src="../dist/js/bootstrap.min.js"></script>
    <!-- Bootstrap Table JS -->
    <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/tableExport.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/libs/jsPDF/jspdf.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.24.0/dist/bootstrap-table.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.24.0/dist/extensions/export/bootstrap-table-export.min.js"></script>
  </body>
</html>"""    
     
    ## figures ##
     # figure: yearly breakdown of MPEC types   
    fig = px.bar(df_yearly, x="Year", y="#MPECs", color="MPECType", title= station[-3:] + " " + mpccode[station[-3:]]['name']+" | Number and type of MPECs by year")
    fig.update_layout(barmode='stack')
    fig.write_html(f"../www/byStation/Graphs/{station}.html")

    # figure: yearly breakdown of Discovery object types
    fig = px.bar(disc_obj, x="Year", y="#MPECs", color="ObjectType", title= station[-3:] + " " + mpccode[station[-3:]]['name']+" | Number of Discovery MPECs by object type")
    fig.update_layout(barmode='stack')
    fig.write_html(f"../www/byStation/Graphs/{station}_disc_obj.html")

    # figure: yearly breakdown of Orbit Update object types
    fig = px.bar(OU_obj, x="Year", y="#MPECs", color="ObjectType", title= station[-3:] + " " + mpccode[station[-3:]]['name']+" | Number of Orbit Update MPECs by object type")
    fig.update_layout(barmode='stack')
    fig.write_html(f"../www/byStation/Graphs/{station}_OU_obj.html")

    if stop_event.is_set():
        return

    #print(station)
    with open(page, 'w') as f:
        f.write(o)

    logging.info(f"Finished processing for station: {station_code}")

make_station_page('004')

# ES_CONTINUOUS = 0x80000000
# ES_SYSTEM_REQUIRED = 0x00000001

# def prevent_sleep():
#     ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

# def allow_sleep():
#     ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

# if __name__ == "__main__":
#     prevent_sleep()
#     try:
#         time_start = datetime.datetime.now()
#         signal.signal(signal.SIGINT, signal_handler)
#         max_workers = os.cpu_count()
#         with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
#             futures = {executor.submit(make_station_page, station_code): station_code for station_code in obscode}
#             for future in concurrent.futures.as_completed(futures):
#                 station_code = futures[future]
#                 try:
#                     future.result()
#                 except Exception as exc:
#                     print(f'Generated an exception: {exc}')
#                     traceback.print_exc()
#                     stop_event.set()
#                     print(f'Error processing station: {station_code}')
#         time_end = datetime.datetime.now()
#         logging.info(f"Total time taken: {time_end - time_start}")
#     finally:
#         allow_sleep()
#         mpecconn.close()
#         logging.shutdown()