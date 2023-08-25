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
from datetime import date

mpec_data=dict()
mpecconn = sqlite3.connect("../mpecwatch_v3.db")
cursor = mpecconn.cursor()

mpccode = '../mpccode.json'
with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)

#prints the contents of a table w/ output limit
def printTableContent(table):
    rows = cursor.execute("SELECT * FROM {} WHERE Object = 'J99M00L' LIMIT 100".format(table)).fetchall()
    print(rows)

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

def calcObs():
    for station in mpccode.keys():
        #initialize dict
        mpec_data[station] = {}
        mpec_data[station]['MPECId'] = {}
        mpec_data[station]['Discovery'] = {}
        mpec_data[station]['Editorial'] = {}
        mpec_data[station]['OrbitUpdate'] = {}
        mpec_data[station]['DOU'] = {}
        mpec_data[station]['ListUpdate'] = {}
        mpec_data[station]['Retraction'] = {}
        mpec_data[station]['Other'] = {}
        mpec_data[station]['Followup'] = {}
        mpec_data[station]['FirstFollowup'] = {}
        for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
            mpec_data[station]['Discovery'][year] = {'total':0}
            mpec_data[station]['Editorial'][year] = {'total':0}
            mpec_data[station]['OrbitUpdate'][year] = {'total':0}
            mpec_data[station]['DOU'][year] = {'total':0}
            mpec_data[station]['ListUpdate'][year] = {'total':0}
            mpec_data[station]['Retraction'][year] = {'total':0}
            mpec_data[station]['Other'][year] = {'total':0}
            mpec_data[station]['Followup'][year] = {'total':0}
            mpec_data[station]['FirstFollowup'][year] = {'total':0}

        mpec_data[station]['MPECs'] = [] #[Name, Date, Discovery?, First Conf?, Object Type, CATCH]
        mpec_data[station]['OBS'] = {} #contains all observers for each station
        mpec_data[station]['MEA'] = {} #contains all measurers for each station
        mpec_data[station]['Facilities'] = {} #contains all facilities for each station

        #store object and mpecid information for catchurl use later
        try:
            for mpc_obj in mpecconn.execute("SELECT MPEC, Object FROM station_{}".format(station)).fetchall():
                mpec_data[station]['MPECId'][mpc_obj[0]] = mpc_obj[1]
        except: 
            pass

        #observers per station
        try:
            for observer in mpecconn.execute("SELECT Observer FROM station_{}".format(station)).fetchall():
                if observer[0] != '':
                    mpec_data[station]['OBS'][observer[0]] = mpec_data[station]['OBS'].get(observer[0],0)+1
        except: 
            pass           

        #measurers per station
        try:
            for measurer in mpecconn.execute("SELECT Measurer FROM station_{}".format(station)).fetchall():
                if measurer[0] != '':
                    mpec_data[station]['MEA'][measurer[0]] = mpec_data[station]['MEA'].get(measurer[0],0)+1
        except:
            pass

        #facilities per station
        try:
            for facility in mpecconn.execute("SELECT Facility FROM station_{}".format(station)).fetchall():
                if facility[0] != '':
                    mpec_data[station]['Facilities'][facility[0]] = mpec_data[station]['Facilities'].get(facility[0],0)+1
        except:
            pass

    for mpec in cursor.execute("select * from MPEC").fetchall():
        year = date.fromtimestamp(mpec[2]).year
        month = date.fromtimestamp(mpec[2]).month

        for station in mpec[3].split(', '):
            if station == '' or station == 'XXX':
                continue

            #MPECType = 'Discovery' and DiscStation != '{}'
            if mpec[6] == 'Discovery' and station != mpec[4]:
                #increment dict value by 1
                mpec_data[station]['Followup'][year]['total'] = mpec_data[station]['Followup'][year].get('total',0)+1
                mpec_data[station]['Followup'][year][month] = mpec_data[station]['Followup'][year].get(month,0)+1

            #MPECType = 'Discovery' and DiscStation != '{}' and "disc_station, station" in stations
            if mpec[6] == 'Discovery' and station not in mpec[4] and mpec[4] + ', ' + station in mpec[3]:
                mpec_data[station]['FirstFollowup'][year]['total'] = mpec_data[station]['FirstFollowup'][year].get('total',0)+1
                mpec_data[station]['FirstFollowup'][year][month] = mpec_data[station]['FirstFollowup'][year].get(month,0)+1

            #if station = discovery station
            if station == mpec[4]:
                mpec_data[station]['Discovery'][year]['total'] = mpec_data[station]['Discovery'][year].get('total',0)+1
                mpec_data[station]['Discovery'][year][month] = mpec_data[station]['Discovery'][year].get(month,0)+1
            
            for mpecType in ["Editorial", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"]:
                if mpec[6] == mpecType:
                    mpec_data[station][mpecType][year]['total'] = mpec_data[station][mpecType][year].get('total',0)+1
                    mpec_data[station][mpecType][year][month] = mpec_data[station][mpecType][year].get(month,0)+1

            #listing all the MPECs from one station: USING TITLE (from MPEC table)
            temp = [] 
            name = mpec[0] + "\t" + mpec[1]
            if name not in mpec_data[station]['MPECs']: #prevents duplication of the same MPEC object
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

                temp.append(mpec_url) #
                temp.append(datetime.datetime.fromtimestamp(mpec[2])) #time: date and time
                #if station = discovery station
                if station == mpec[4]:
                    temp.append("&#x2713") #check mark
                else:
                    temp.append("")
                #if station = FirstFU
                if station == mpec[5]:
                    temp.append("&#x2713") #check mark
                else:
                    temp.append("")
                
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
                temp.append(obj_type)


                if mpec[7]:
                    #obs_code = cursor.execute("SELECT Object FROM station_{} WHERE MPEC = '{}'".format(station, mpec[0])).fetchall()
                    #catch_url = "<a href=https://catch.astro.umd.edu/data?objid={}%20{}>CATCH</a>".format(obs_code[:3], obs_code[3::])
                    catch_url = "<a href=https://catch.astro.umd.edu/data?target={}>CATCH</a>".format(mpec_data[station]['MPECId'][mpec[0]])
                    #catch_url = "<a href=https://catch.astro.umd.edu/data?objid={}%20{}>CATCH</a>".format(mpec[0].split()[1][:4], mpec[0].split()[1][5::])
                    temp.append(catch_url)
                else:
                    temp.append("")

                mpec_data[station]['MPECs'].append((temp))


def createGraph(station_code, includeFirstFU = True):
    df_yearly = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []})
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
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
    <link href="../dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap theme -->
    <link href="../dist/css/bootstrap-theme.min.css" rel="stylesheet">
    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <link href="../assets/css/ie10-viewport-bug-workaround.css" rel="stylesheet">

    <!-- Custom styles for this template -->
    <link href="../theme.css" rel="stylesheet">
    <!-- Table pagination -->
    <link href="https://unpkg.com/bootstrap-table@1.21.4/dist/bootstrap-table.min.css" rel="stylesheet">
    <script src="https://unpkg.com/bootstrap-table@1.21.4/dist/bootstrap-table.min.js"></script>
    
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
            <!-- <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/mpc_stuff.html">MPC Stuff</a></li> -->
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
            <table class="table table-striped table-sm">
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
        """.format(str(station), str(station), str(station), str(station))
        
    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
        df_monthly = pd.DataFrame({"Editorial": [], "Discovery": [], "OrbitUpdate": [], "DOU": [], "ListUpdate": [], "Retraction": [], "Other": [], "Followup": [], "FirstFollowup": []})
        obs_types = ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup"]
        year_counts = list(map(lambda func: func(), [lambda mpecType=x: mpec_data[station[8::]][mpecType][year]['total'] if year in mpec_data[station[8::]][mpecType].keys() else 0 for x in obs_types]))
        #month_counts = 

        if includeFirstFU:
            year_counts[7] -= year_counts[8]
        else:
            year_counts[8] = 0
        
        df_yearly = pd.concat([df_yearly, pd.DataFrame({"Year": [year, year, year, year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup"], "#MPECs": year_counts})])
        
        month_index = 1
        for month in months:
            new_row = []
            for mpecType in obs_types:
                #if year in mpec_data[station[8::]][mpecType].keys():
                if month_index in mpec_data[station[-3:]][mpecType][year].keys():
                    new_row.append(mpec_data[station[-3:]][mpecType][year][month_index])
                else:
                    new_row.append(0)
            month_index+=1
            df_monthly = pd.concat([df_monthly, pd.DataFrame([new_row], index=[month], columns=obs_types)])
        
        #print(df_monthly)
        monthly(station, year, df_monthly)

        o += """
                <tr>
                    <td><a href="monthly/%s_%i.html">%i</a></td>
                    <td>%i</td>
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
        """ % (station, year, year, sum(year_counts), year_counts[0], year_counts[1], year_counts[2], year_counts[3], year_counts[4], year_counts[5], year_counts[6], year_counts[7], year_counts[8])
    try:
        fig = px.bar(df_yearly, x="Year", y="#MPECs", color="MPECType", title= station[-3:] + " " + mpccode[station[-3:]]['name']+" | Number and type of MPECs by year")
        fig.write_html("../www/byStation/Graphs/"+station+".html")
    except Exception as e:
        print(e)
    
    #df_csv = pd.DataFrame({"Year": [], "Editorial": [], "Discovery": [], "OrbitUpdate": [], "DOU": [], "ListUpdate": [], "Retraction": [], "Other": [], "Followup": [], "FirstFollowup": []})
    df_csv = pd.DataFrame()
    df_csv["Year"] = df_yearly["Year"].unique()
    for mpecType in df_yearly["MPECType"].unique():
        df_csv[mpecType] = df_yearly[df_yearly["MPECType"] == mpecType]["#MPECs"].values

    df_csv.to_csv("../www/byStation/csv/{}.csv".format(station), index=False)

    o += """
            </table>
            <a href="csv/{}.csv" download="{}">
                <p style="padding-bottom: 30px;">Download as csv</p>
            </a>
        </div>
        <div class="containter">
            <table id="mpec_table" 
                class="table table-striped table-bordered table-sm"
                data-toggle="table"
                data-height="460"
                data-pagination="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="name">Name</th>
                        <th class="th-sm" data-field="date">Date/Time</th>
                        <th class="th-sm" data-field="ds">Discoverer</th>
                        <th class="th-sm" data-field="fs">First-responding Confirmer</th>
                        <th class="th-sm" data-field="obj">Object Type</th>
                        <th class="th-sm" data-field="catch">Search Archival Image</th>
                    </tr>
                </thead>
                <tbody>
    """.format(str(station), str(station))
    
    for i in reversed(mpec_data[station[-3::]]['MPECs']):
        o += """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
        """.format(i[0],i[1],i[2],i[3],i[4],i[5])

    o += """
                </tbody>
            </table>
            <table id="OBS_table" 
                class="table table-striped table-bordered table-sm"
                data-toggle="table"
                data-height="460"
                data-pagination="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="observer" data-sortable="true">Observers</th>
                        <th class="th-sm" data-field="count" data-sortable="true">Count</th>
                    </tr>
                </thead>
                <tbody>"""
    for observer, count in mpec_data[station[-3::]]['OBS'].items():
        o += """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
    """.format(observer, count)
        
    o += """
                </tbody>
            </table>
            <table id="MEA_table" 
                class="table table-striped table-bordered table-sm"
                data-toggle="table"
                data-height="460"
                data-pagination="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="measurer" data-sortable="true">Measurers</th>
                        <th class="th-sm" data-field="count" data-sortable="true">Count</th>
                    </tr>
                </thead>
                <tbody>"""
    
    for measurer, count in mpec_data[station[-3::]]['MEA'].items():
        o += """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
    """.format(measurer, count)
        
    o += """
                </tbody>
            </table>
            <table id="FAC_table" 
                class="table table-striped table-bordered table-sm"
                data-toggle="table"
                data-height="460"
                data-pagination="true">
                <thead>
                    <tr>
                        <th class="th-sm" data-field="facility" data-sortable="true">Facilities</th>
                        <th class="th-sm" data-field="count" data-sortable="true">Count</th>
                    </tr>
                </thead>
                <tbody>"""
    
    for facility, count in mpec_data[station[-3::]]['Facilities'].items():
        o += """
                <tr>
                    <td>{}</td>
                    <td>{}</td>
                </tr>
    """.format(facility, count)

    o += """
                </tbody>
            </table>
            <script src="https://cdn.jsdelivr.net/npm/jquery/dist/jquery.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
            <script src="https://unpkg.com/bootstrap-table@1.21.4/dist/bootstrap-table.min.js"></script>
            <script>
                function customSort(sortName, sortOrder, data) {
                    var order = sortOrder === 'desc' ? -1 : 1
                    data.sort(function (a, b) {
                        var aa = +((a[sortName] + '').replace(/[^\d]/g, ''))
                        var bb = +((b[sortName] + '').replace(/[^\d]/g, ''))
                        if (aa < bb) {
                            return order * -1
                        }
                        if (aa > bb) {
                            return order
                        }
                        return 0
                    })
                }
            </script>
        </div>"""
    
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
    </div>
  </body>
</html>"""

    with open(page, 'w', encoding='utf-8') as f:
        f.write(o)


def monthly(station, year, df_monthly):
    page = '../www/byStation/monthly/{}.html'.format(station+"_"+str(year))
    o = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MPECWatch: Monthly Summary | {}</title>

        <!-- Bootstrap core CSS -->
        <link href="../../dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- Bootstrap theme -->
        <link href="../../dist/css/bootstrap-theme.min.css" rel="stylesheet">
        <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
        <link href="../../assets/css/ie10-viewport-bug-workaround.css" rel="stylesheet">
    </head>
    <body>
        <div class="container" theme-showcase" role="main">
            <h2>{} {} | {}</h2>
            <table class="table table-striped table-hover table-condensed table-responsive">
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
            </thead>""".format(year, station[-3:], mpccode[station[-3:]]['name'], year)
    
    for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
        o += """
                <tbody>
                    <tr>
                        <td>%s</td>
                        <td>%i</td>
                        <td>%i</td>
                        <td>%i</td>
                        <td>%i</td>
                        <td>%i</td>
                        <td>%i</td>
                        <td>%i</td>
                        <td>%i</td>
                        <td>%i</td>
                    </tr>""" % (month, df_monthly.loc[month, 'Discovery'], df_monthly.loc[month, 'Editorial'], df_monthly.loc[month, 'OrbitUpdate'], df_monthly.loc[month, 'DOU'], df_monthly.loc[month, 'ListUpdate'], df_monthly.loc[month, 'Retraction'], df_monthly.loc[month, 'Other'], df_monthly.loc[month, 'Followup'], df_monthly.loc[month, 'FirstFollowup'])
        
    df_monthly.to_csv("../www/byStation/monthly/csv/{}.csv".format(station+"_"+str(year)))
    o += """      
                </tbody>
            </table>
            <a href="csv/{}.csv" download="{}">
                <p style="padding-bottom: 30px;">Download as csv</p>
            </a>
        </div>
    </body>
</html>""".format(station+"_"+str(year), station+"_"+str(year))
    
    with open(page, 'w', encoding='utf-8') as f:
            f.write(o)    

def main():
    calcObs()
    # for station in mpccode.keys():
    #     if station == 'XXX':
    #         continue
    #     createGraph(station)
    #     print(station)
    createGraph('J95')

main()
mpecconn.close()
print('finished')
