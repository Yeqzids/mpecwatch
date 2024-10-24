#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Make a page that contains a summary table of stats by observatories

 (C) Quanzhi Ye
 
"""

import sqlite3, datetime, json, numpy as np, pandas as pd, plotly.express as px

survey_data = {}
mpec_data = {}
with open('../mpec_data.json') as file:
    mpec_data = json.load(file)

mpecconn = sqlite3.connect("../mpecwatch_v3.db")
cursor = mpecconn.cursor()

obs_types = ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup"]
obj_types = ["NEA", "Comet", "Satellite", "TNO", "Unusual", "Interstellar", "unk"]

def merge_mpec_dicts(*dicts):
    merged_dict = {}
    for d in dicts:
        merged_dict = merge_dictionaries(merged_dict, d)
    return merged_dict

def merge_dictionaries(dict1, dict2):
    merged_dict = {}
    for key in dict1:
        if key == 'MPECId':
            merged_dict['MPECId'] = dict1['MPECId'] | dict2['MPECId']
            continue
        if key in dict2:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                # Recursive merging for nested dictionaries
                merged_dict[key] = merge_dictionaries(dict1[key], dict2[key])
            elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                # Concatenate lists
                merged_dict[key] = dict1[key] + dict2[key]
            elif isinstance(dict1[key], (int, float)) and isinstance(dict2[key], (int, float)):
                # Sum numbers
                merged_dict[key] = dict1[key] + dict2[key]
            else:
                # Handle other types or raise an error
                raise ValueError(f"Unsupported value type for key '{key}'")
        else:
            merged_dict[key] = dict1[key]
    # Add keys that are only in dict2
    for key in dict2:
        if key not in merged_dict:
            merged_dict[key] = dict2[key]
    return merged_dict

# Creates a sruvey page by combining the stats of all stations in the survey
def createSurveyPage(surveyName, surveyNameAbbv, codes):
  survey_data[surveyName] = {}
  survey_data[surveyName]['MPECId'] = {} # single 'MPECId' key: {MPECId: Object designation in packed form}
  survey_data[surveyName]['Discovery'] = {} 
  survey_data[surveyName]['Editorial'] = {}
  survey_data[surveyName]['OrbitUpdate'] = {}
  survey_data[surveyName]['DOU'] = {}
  survey_data[surveyName]['ListUpdate'] = {}
  survey_data[surveyName]['Retraction'] = {}
  survey_data[surveyName]['Other'] = {}
  survey_data[surveyName]['Followup'] = {}
  survey_data[surveyName]['FirstFollowup'] = {}
  for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
      year = int(year)
      survey_data[surveyName]['Discovery'][year] = {'total':0} 
      for obj in obj_types:
          survey_data[surveyName]['Discovery'][year][obj] = 0 #object type count
      survey_data[surveyName]['Editorial'][year] = {'total':0}
      survey_data[surveyName]['OrbitUpdate'][year] = {'total':0} 
      for obj in obj_types:
          survey_data[surveyName]['OrbitUpdate'][year][obj] = 0 #object type count
      survey_data[surveyName]['DOU'][year] = {'total':0}
      survey_data[surveyName]['ListUpdate'][year] = {'total':0}
      survey_data[surveyName]['Retraction'][year] = {'total':0}
      survey_data[surveyName]['Other'][year] = {'total':0}
      survey_data[surveyName]['Followup'][year] = {'total':0}
      survey_data[surveyName]['FirstFollowup'][year] = {'total':0}
      for month in range(1, 13):
          survey_data[surveyName]['Discovery'][year][month] = 0
          survey_data[surveyName]['Editorial'][year][month] = 0
          survey_data[surveyName]['OrbitUpdate'][year][month] = 0
          survey_data[surveyName]['DOU'][year][month] = 0
          survey_data[surveyName]['ListUpdate'][year][month] = 0
          survey_data[surveyName]['Retraction'][year][month] = 0
          survey_data[surveyName]['Other'][year][month] = 0
          survey_data[surveyName]['Followup'][year][month] = 0
          survey_data[surveyName]['FirstFollowup'][year][month] = 0
  survey_data[surveyName]['MPECs'] = set() #[[Name, unix timestamp, Discovery?, First Conf?, Object Type, CATCH], ...]
  survey_data[surveyName]['OBS'] = {} #contains all observers for each surveyName
  survey_data[surveyName]['MEA'] = {} #contains all measurers for each station
  survey_data[surveyName]['Facilities'] = {} #contains all facilities for each station

  for code in codes:
      #combine object and mpecid information for each station in the survey
      survey_data[surveyName]['MPECId'] = survey_data[surveyName]['MPECId'] | mpec_data[code]['MPECId']

      #combine observers for each station in the survey
      survey_data[surveyName]['OBS'] = merge_mpec_dicts(survey_data[surveyName]['OBS'], mpec_data[code]['OBS'])

      #combine measurers for each station in the survey
      survey_data[surveyName]['MEA'] = merge_mpec_dicts(survey_data[surveyName]['MEA'], mpec_data[code]['MEA'])

      #combine facilities for each station in the survey
      survey_data[surveyName]['Facilities'] = merge_mpec_dicts(survey_data[surveyName]['Facilities'], mpec_data[code]['Facilities'])

      #combine MPECs for each station in the survey (skip duplicates)
      for MPEC in mpec_data[code]['MPECs']:
        survey_data[surveyName]['MPECs'].add(tuple(MPEC))

      # need to fix this part
      for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
          # Note that mpec_data stores the year as a string while survey_data stores it as an int (json limitation)
          survey_data[surveyName]['Discovery'][year]['total'] += mpec_data[code]['Discovery'][str(year)]['total']
          for obj in obj_types:
              survey_data[surveyName]['Discovery'][year][obj] += mpec_data[code]['Discovery'][str(year)][obj]
          survey_data[surveyName]['Editorial'][year]['total'] += mpec_data[code]['Editorial'][str(year)]['total']
          survey_data[surveyName]['OrbitUpdate'][year]['total'] += mpec_data[code]['OrbitUpdate'][str(year)]['total']
          for obj in obj_types:
              survey_data[surveyName]['OrbitUpdate'][year][obj] += mpec_data[code]['OrbitUpdate'][str(year)][obj]
          survey_data[surveyName]['DOU'][year]['total'] += mpec_data[code]['DOU'][str(year)]['total']
          survey_data[surveyName]['ListUpdate'][year]['total'] += mpec_data[code]['ListUpdate'][str(year)]['total']
          survey_data[surveyName]['Retraction'][year]['total'] += mpec_data[code]['Retraction'][str(year)]['total']
          survey_data[surveyName]['Other'][year]['total'] += mpec_data[code]['Other'][str(year)]['total']
          survey_data[surveyName]['Followup'][year]['total'] += mpec_data[code]['Followup'][str(year)]['total']
          survey_data[surveyName]['FirstFollowup'][year]['total'] += mpec_data[code]['FirstFollowup'][str(year)]['total']
          # Note that mpec_data stores the month as a string while survey_data stores it as an int (json limitation)
          for month in range(1, 13):
              survey_data[surveyName]['Discovery'][year][month] += mpec_data[code]['Discovery'][str(year)][str(month)]
              survey_data[surveyName]['Editorial'][year][month] += mpec_data[code]['Editorial'][str(year)][str(month)]
              survey_data[surveyName]['OrbitUpdate'][year][month] += mpec_data[code]['OrbitUpdate'][str(year)][str(month)]
              survey_data[surveyName]['DOU'][year][month] += mpec_data[code]['DOU'][str(year)][str(month)]
              survey_data[surveyName]['ListUpdate'][year][month] += mpec_data[code]['ListUpdate'][str(year)][str(month)]
              survey_data[surveyName]['Retraction'][year][month] += mpec_data[code]['Retraction'][str(year)][str(month)]
              survey_data[surveyName]['Other'][year][month] += mpec_data[code]['Other'][str(year)][str(month)]
              survey_data[surveyName]['Followup'][year][month] += mpec_data[code]['Followup'][str(year)][str(month)]
              survey_data[surveyName]['FirstFollowup'][year][month] += mpec_data[code]['FirstFollowup'][str(year)][str(month)]
      

  # to convert the set back to a list
  survey_data[surveyName]['MPECs'] = [list(mpec) for mpec in survey_data[surveyName]['MPECs']]
  
  # Potential improvement: make dictionary local to function and pass it to createGraph
  createGraph(surveyName, surveyNameAbbv, codes)

def createGraph(surveyName, surveyNameAbbv, codes, includeFirstFU = True):
    df_yearly = pd.DataFrame({"Year": [], "MPECType": [], "#MPECs": []})
    disc_obj = pd.DataFrame({"Year": [], "ObjType": [], "#MPECs": []})
    OU_obj = pd.DataFrame({"Year": [], "ObjType": [], "#MPECs": []})
    survey = 'survey'+surveyName
    page = "../www/bySurvey/" + surveyNameAbbv + ".html"
    #list of codes in the corresponding survey

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

    <title>MPEC Watch | Survey Statistics %s</title>

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

      <!-- Main jumbotron for a primary marketing message or call to action -->""" % str(surveyName)
    o += """<div class="row">
            <h2>{}</h2>""".format(surveyName)
    for code in codes:
        o += """<h3>{}</h3>""".format(code)
              
        if str(code) not in ['244', '245', '247', '248', '249', '250', '258', '270', '273', '274', '275', '500', 'C49', 'C50', 'C51', 'C52', 'C53', 'C54', 'C55', 'C56', 'C57', 'C58', 'C59']:
            #print(code)
            #print(mpccode[code])
            if mpccode[code]['lon'] > 180:
                lon = mpccode[code]['lon'] - 360
            else:
                lon = mpccode[code]['lon']
            o += """<p><a href="https://geohack.toolforge.org/geohack.php?params={};{}">Where is this observatory?</a></p>""".format(mpccode[code]['lat'], lon)
              
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
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="graphs/{}.html" height="525" width="100%"></iframe>
              <h4>Yearly Breakdown of Discovery Object Types</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="graphs/{}_disc_obj.html" height="525" width="100%"></iframe>
              <h4>Yearly Breakdown of Orbit Update Object Types</h4>
              <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="graphs/{}_OU_obj.html" height="525" width="100%"></iframe>
              
              <!-- NOT IMPLEMENTED YET
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
              -->

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
        """.format(surveyName, surveyName, surveyName, surveyName, surveyName, surveyName, surveyName, surveyName, surveyName, surveyName) 
        
    for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
        year = int(year)
        year_counts = []
        for mpecType in obs_types:
            if year in survey_data[surveyName][mpecType].keys():
                total = survey_data[surveyName][mpecType][year]['total']
            else:
                total = 0
            year_counts.append(total)
        if includeFirstFU:
            year_counts[7] -= year_counts[8]
        else:
            year_counts[8] = 0

        #for objType in obj_types:
        
        df_yearly = pd.concat([df_yearly, pd.DataFrame({"Year": [year, year, year, year, year, year, year, year, year], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup"], "#MPECs": year_counts})])
        disc_obj = pd.concat([disc_obj, pd.DataFrame({"Year": [year, year, year, year, year, year, year], "ObjType": ["NEA", "Comet", "Satellite", "TNO", "Unusual", "Interstellar", "Unknown"], "#MPECs": [survey_data[surveyName]['Discovery'][year]['NEA'], survey_data[surveyName]['Discovery'][year]['Comet'], survey_data[surveyName]['Discovery'][year]['Satellite'], survey_data[surveyName]['Discovery'][year]['TNO'], survey_data[surveyName]['Discovery'][year]['Unusual'], survey_data[surveyName]['Discovery'][year]['Interstellar'], survey_data[surveyName]['Discovery'][year]['unk']]})])
        OU_obj = pd.concat([OU_obj, pd.DataFrame({"Year": [year, year, year, year, year, year, year], "ObjType": ["NEA", "Comet", "Satellite", "TNO", "Unusual", "Interstellar", "Unknown"], "#MPECs": [survey_data[surveyName]['OrbitUpdate'][year]['NEA'], survey_data[surveyName]['OrbitUpdate'][year]['Comet'], survey_data[surveyName]['OrbitUpdate'][year]['Satellite'], survey_data[surveyName]['OrbitUpdate'][year]['TNO'], survey_data[surveyName]['OrbitUpdate'][year]['Unusual'], survey_data[surveyName]['OrbitUpdate'][year]['Interstellar'], survey_data[surveyName]['OrbitUpdate'][year]['unk']]})])
        
        df_monthly_graph = pd.DataFrame({"Month": [], "MPECType": [], "#MPECs": []})
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_index = 1
        for month in months:
            month_counts = []
            for mpecType in obs_types:
                month_counts.append(survey_data[surveyName][mpecType][year][month_index])
            df_monthly_graph = pd.concat([df_monthly_graph, pd.DataFrame({"Month": [month, month, month, month, month, month, month, month, month], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other", "Followup", "FirstFollowup"], "#MPECs": month_counts})])
            month_index += 1
        monthly(surveyName, surveyNameAbbv, year, df_monthly_graph)

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
        """ % (survey, year, year, sum(year_counts), year_counts[0], year_counts[1], year_counts[2], year_counts[3], year_counts[4], year_counts[5], year_counts[6], year_counts[7], year_counts[8])
    try:
        fig = px.bar(df_yearly, x="Year", y="#MPECs", color="MPECType", title= surveyName+" | Number and type of MPECs by year")
        fig.write_html("../www/bySurvey/graphs/"+surveyNameAbbv+".html")
    except Exception as e:
        print(e)

    try:
        fig = px.bar(disc_obj, x="Year", y="#MPECs", color="ObjType", title= surveyName+" | Discovery: Number and type of Object by year")
        fig.write_html("../www/bySurvey/graphs/"+surveyNameAbbv+"_disc_obj.html")
    except Exception as e:
        print(e)

    try:
        fig = px.bar(OU_obj, x="Year", y="#MPECs", color="ObjType", title= surveyName+" | Orbit Update: Number and type of Object by year")
        fig.write_html("../www/bySurvey/graphs/"+surveyNameAbbv+"_OU_obj.html")
    except Exception as e:
        print(e)
    
    o += """
            </table>
        </div>
        <div class="containter">
            <h4>List of Individual MPECs</h4>
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
    """.format(str(survey), str(survey))
    
    index = 1
    for i in reversed(survey_data[surveyName]['MPECs']):
        o += """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
        """.format(index,i[0],datetime.datetime.fromtimestamp(i[1]),i[2],i[3],i[4],i[5])
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
    for observer, count in survey_data[surveyName]['OBS'].items():
        o += """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
    """.format(observer, count)
        
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
    
    for measurer, count in survey_data[surveyName]['MEA'].items():
        o += """
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
    """.format(measurer, count)
        
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
    
    for facility, count in survey_data[surveyName]['Facilities'].items():
        o += """
                <tr>
                    <td>{}</td>
                    <td>{}</td>
                </tr>
    """.format(facility, count)

    o += """
                </tbody>
            </table>
        
        <!--
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@3.4.1/dist/js/bootstrap.min.js" integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd" crossorigin="anonymous"></script>
        -->

        <script src="../dist/js/custom_sort.js"></script>
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

        <!-- Bootstrap Table -->
        <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/tableExport.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/libs/jsPDF/jspdf.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.22.5/dist/bootstrap-table.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.22.5/dist/extensions/export/bootstrap-table-export.min.js"></script>
    </div>
  </body>
</html>"""

    #print(survey)
    with open(page, 'w', encoding='utf-8') as f:
        f.write(o)      

def monthly(surveyName, surveyNameAbbv, year, df_month_graph):
    fig = px.bar(df_month_graph, x="Month", y="#MPECs", color="MPECType")
    fig.write_html("../www/bySurvey/monthly/graphs/"+surveyNameAbbv+"_"+str(year)+".html")

    df_monthly = pd.DataFrame({"Editorial": [], "Discovery": [], "OrbitUpdate": [], "DOU": [], "ListUpdate": [], "Retraction": [], "Other": [], "Followup": [], "FirstFollowup": []})
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_index = 1
    for month in months:
        new_row = []
        for mpecType in obs_types:
            new_row.append(survey_data[surveyName][mpecType][year][month_index])
        month_index+=1
        df_monthly = pd.concat([df_monthly, pd.DataFrame([new_row], index=[month], columns=obs_types)])
    
    page = '../www/bySurvey/monthly/{}.html'.format(surveyNameAbbv+"_"+str(year))
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
            <h2>{} {}</h2>
            <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="graphs/{}.html" height="525" width="100%"></iframe>
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
            </thead>""".format(year, surveyName, year, surveyName+"_"+str(year))
    
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
                    </tr>""" % (month, df_monthly.loc[month, 'Editorial'], df_monthly.loc[month, 'Discovery'], df_monthly.loc[month, 'OrbitUpdate'], df_monthly.loc[month, 'DOU'], df_monthly.loc[month, 'ListUpdate'], df_monthly.loc[month, 'Retraction'], df_monthly.loc[month, 'Other'], df_monthly.loc[month, 'Followup'], df_monthly.loc[month, 'FirstFollowup'])
        
    df_monthly.to_csv("../www/bySurvey/monthly/csv/{}.csv".format(surveyNameAbbv+"_"+str(year)))
    o += """      
                </tbody>
            </table>
            <a href="csv/{}.csv" download="{}">
                <p style="padding-bottom: 30px;">Download as csv</p>
            </a>
        </div>
    </body>
</html>""".format(surveyNameAbbv+"_"+str(year), surveyNameAbbv+"_"+str(year))
    
    with open(page, 'w', encoding='utf-8') as f:
            f.write(o)
      
survey_def_table = [['Lincoln Near Earth Asteroid Research (LINEAR)', ['704'], 'linear'], \
                    ['Space Surveillance Telescope (SST)', ['G45', 'P07'], 'sst'], \
                    ['Near-Earth Asteroid Tracking (NEAT)', ['566', '608', '644'], 'neat'], \
                    ['Spacewatch', ['291', '691'], 'spacewatch'], \
                    ['Lowell Observatory Near-Earth-Object Search (LONEOS)', ['699'], 'loneos'], \
                    ['Catalina Sky Survey (CSS)', ['703', 'E12', 'G96', 'I52', 'V06'], 'css'], \
                    ['Panoramic Survey Telescope and Rapid Response System (Pan-STARRS)', ['F51', 'F52'], 'panstarrs'], \
                    ['Wide-field Infrared Survey Explorer (WISE_NEOWISE)', ['C51'], 'wise'], \
                    ['Asteroid Terrestrial-impact Last Alert System (ATLAS)', ['T05', 'T08', 'M22', 'W68'], 'atlas']]

dbFile = '../mpecwatch_v3.db'
stat = 'obscode_stat.json'
mpccode = '../mpccode.json'
#survey_data = '../survey_data.json'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)
    
with open(stat) as stat:
    stat = json.load(stat)

# with open(survey_data) as survey_data:
#     survey_data = json.load(survey_data)
    
    
pages = list(np.arange(1993, 2025, 1))
pages.append('All time')

for p in pages:

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
        <link rel="icon" href="favicon.ico">
    
        <title>MPEC Watch | Global Statistics %s</title>
    
        <!-- Bootstrap core CSS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-table@1.22.5/dist/bootstrap-table.min.css">
        <link href="dist/css/bootstrap.min.css" rel="stylesheet">
        <!-- Bootstrap theme -->
        <link href="dist/css/bootstrap-theme.min.css" rel="stylesheet">
        <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
        <link href="assets/css/ie10-viewport-bug-workaround.css" rel="stylesheet">
    
        <!-- Custom styles for this template -->
        <link href="theme.css" rel="stylesheet">
    
        <!-- Just for debugging purposes. Don't actually copy these 2 lines! -->
        <!--[if lt IE 9]><script src="assets/js/ie8-responsive-file-warning.js"></script><![endif]-->
        <script src="assets/js/ie-emulation-modes-warning.js"></script>
    
        <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
        <!--[if lt IE 9]>
          <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
          <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
        <![endif]-->
        
        <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.6.3/css/all.css" integrity="sha384-UHRtZLI+pbxtHCWp1t77Bi1L4ZtiqrqD80Kn4Z8NTSRyMA2Fd33n5dQ8lWUE00s/" crossorigin="anonymous">
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
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/obs.html">Observatory Browser</a></li>
            <li class="active"><a href="https://sbnmpc.astro.umd.edu/mpecwatch/survey.html">Survey Browser</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/stats.html">Various Statistics</a></li>
            <!-- <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/mpc_stuff.html">MPC Stuff (non-public)</a></li> -->
            <li><a href="https://github.com/Yeqzids/mpecwatch/issues">Issue Tracker</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu">SBN-MPC Annex</a></li>
              </ul>
            </div><!--/.nav-collapse -->
          </div>
        </nav>
    
        <div class="container theme-showcase" role="main">
        
        <!-- Main jumbotron for a primary marketing message or call to action -->
      <div class="jumbotron">
        <p>This page is still under active development and testing. Comments, suggestions and bug reports are welcome (via Issue Tracker or by email). Quanzhi 05/31/24</p>
      </div>
    """ % str(p)
    
    # Table of MPECs by year and type
    
    o += """
          <div class="page-header">
            <h1>Statistics by Survey - %s</h1>
            <p><a href="https://sbnmpc.astro.umd.edu/mpecwatch/survey.html">All time</a> """ % str(p)
            
    for pp in pages[:-1]:
        o += """ | <a href="https://sbnmpc.astro.umd.edu/mpecwatch/survey-%s.html">%s</a>""" % (str(pp), str(pp))
        
    o += """
            </p>
          </div>
          <p>
          Disc. - MPECs associated with discovery made by this station.<br>
          F/U - MPECs associated with follow-up observations made by this station to an object discovered elsewhere.<br>
          1st F/U - MPECs associated with follow-up observations made by this station to an object discovered elsewhere, with this station being the first station to follow-up.<br>
          Prec. - MPECs associated with precovery observations made by this station to an object discovered elsewhere.<br>
          Recvy. - MPECs associated with recovery of single-opposition objects.<br>
          1st Recvy. - MPECs associated with recovery of single-opposition objects with this station being the first station in time to detect the object.
          </p>
          <p>
            Last update: UTC %s
          </p>""" % (datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
          
    o += """
          <div class="page-header">
          <table id="obs_table" class="table table-striped"
              data-toggle="table"
              data-search="true"
              data-show-export="true"
              data-pagination="true"
              data-show-columns="true">
              <thead>
                <tr class="tr-class-1">
                  <th data-field="survey" data-sortable="true">Survey</th>
                  <th data-field="obs" data-sortable="true">Observatory</th>
                  <th data-field="nmpec" data-sortable="true">MPECs</th>
                  <th data-field="ndisc" data-sortable="true">Disc.</th>
                  <th data-field="nNEAd" data-sortable="true">NEA Disc.</th>
                  <th data-field="nPHAd" data-sortable="true">PHA Disc.</th>
                  <th data-field="nComd" data-sortable="true">Comet Disc.</th>
                  <th data-field="nSatd" data-sortable="true">Sat Disc.</th>
                  <th data-field="nTNOd" data-sortable="true">TNO Disc.</th>
                  <th data-field="nund" data-sortable="true">Unusual Disc.</th>
                  <th data-field="nintd" data-sortable="true">Inter Disc.</th>
                  <th data-field="nunkd" data-sortable="true">Unk Disc.</th>
                  <th data-field="nfu" data-sortable="true">F/U</th>
                  <th data-field="nNEAfu" data-sortable="true">NEA FU</th>
                  <th data-field="nPHAfu" data-sortable="true">PHA FU</th>
                  <th data-field="nComfu" data-sortable="true">Comet FU</th>
                  <th data-field="nSatfu" data-sortable="true">Sat FU</th>
                  <th data-field="nTNOfu" data-sortable="true">TNO FU</th>
                  <th data-field="nunfu" data-sortable="true">Unusual FU</th>
                  <th data-field="nintfu" data-sortable="true">Inter FU</th>
                  <th data-field="nunkfu" data-sortable="true">Unk FU</th>
                  <th data-field="nffu" data-sortable="true">1st F/U</th>
                  <th data-field="nprecovery" data-sortable="true">Prec.</th>
                  <th data-field="nrecovery" data-sortable="true">Recvy.</th>
                  <th data-field="nfrecovery" data-sortable="true">1st Recvy.</th>
                </tr>
              </thead>
              <tbody>
    """
    print("Year: ", p)
    for s in survey_def_table:
        
        survey = s[0]
        data = [stat[i] for i in s[1]]
        survey_abbv = s[2]
        
        
        print(survey)
        createSurveyPage(survey, survey_abbv, s[1])
        if p == 'All time':
            o += """
            <tr>
                <td>
                    <a href="../www/bySurvey/%s.html">%s</a>
                </td> 
                <td> """ % (survey_abbv, survey)
        else:
            o += """
                <tr>
                    <td>
                        <a href="../www/bySurvey/monthly/%s.html">%s</a>
                    </td> 
                    <td> """ % (survey_abbv, survey)
        
        for codi in s[1]:
            o += """<a href="https://sbnmpc.astro.umd.edu/mpecwatch/byStation/station_%s.html">%s %s</a><br>""" % (codi, codi, mpccode[codi]['name'])

        o += """</td>"""

        if p == 'All time':
            o += """
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
            """ % (str(sum([sum(stat[i]['mpec'].values()) for i in s[1]])), str(sum([sum(stat[i]['mpec_discovery'].values()) for i in s[1]])), str(sum([sum(stat[i]['NEA_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['PHA_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['Comet_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['Satellite_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['TNO_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['Unusual_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['Interstellar_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['Unknown_Disc'].values()) for i in s[1]])), str(sum([sum(stat[i]['mpec_followup'].values()) for i in s[1]])), str(sum([sum(stat[i]['NEA_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['PHA_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['Comet_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['Satellite_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['TNO_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['Unusual_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['Interstellar_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['Unknown_FU'].values()) for i in s[1]])), str(sum([sum(stat[i]['mpec_1st_followup'].values()) for i in s[1]])), str(sum([sum(stat[i]['mpec_precovery'].values()) for i in s[1]])), str(sum([sum(stat[i]['mpec_recovery'].values()) for i in s[1]])), str(sum([sum(stat[i]['mpec_1st_recovery'].values()) for i in s[1]])))
        else:
            o += """
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
            """ % (str(sum(stat[i]['mpec'][str(p)] for i in s[1])), str(sum(stat[i]['mpec_discovery'][str(p)] for i in s[1])), str(sum(stat[i]['NEA_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['PHA_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['Comet_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['Satellite_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['TNO_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['Unusual_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['Interstellar_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['Unknown_Disc'][str(p)] for i in s[1])), str(sum(stat[i]['mpec_followup'][str(p)] for i in s[1])), str(sum(stat[i]['NEA_FU'][str(p)] for i in s[1])), str(sum(stat[i]['PHA_FU'][str(p)] for i in s[1])), str(sum(stat[i]['Comet_FU'][str(p)] for i in s[1])), str(sum(stat[i]['Satellite_FU'][str(p)] for i in s[1])), str(sum(stat[i]['TNO_FU'][str(p)] for i in s[1])), str(sum(stat[i]['Unusual_FU'][str(p)] for i in s[1])), str(sum(stat[i]['Interstellar_FU'][str(p)] for i in s[1])), str(sum(stat[i]['Unknown_FU'][str(p)] for i in s[1])), str(sum(stat[i]['mpec_1st_followup'][str(p)] for i in s[1])), str(sum(stat[i]['mpec_precovery'][str(p)] for i in s[1])), str(sum(stat[i]['mpec_recovery'][str(p)] for i in s[1])), str(sum(stat[i]['mpec_1st_recovery'][str(p)] for i in s[1])))
        
    o += """
        </tbody>
    </table>
    </div>
    """
    
    o += """
    	<footer class="pt-5 my-5 text-muted border-top">
        Script by <a href="https://www.astro.umd.edu/~qye/">Quanzhi Ye</a>, hosted at <a href="https://sbnmpc.astro.umd.edu">SBN-MPC</a>. Powered by <a href="https://getbootstrap.com"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-bootstrap-fill" viewBox="0 0 16 16">
  <path d="M6.375 7.125V4.658h1.78c.973 0 1.542.457 1.542 1.237 0 .802-.604 1.23-1.764 1.23H6.375zm0 3.762h1.898c1.184 0 1.81-.48 1.81-1.377 0-.885-.65-1.348-1.886-1.348H6.375v2.725z"/>
  <path d="M4.002 0a4 4 0 0 0-4 4v8a4 4 0 0 0 4 4h8a4 4 0 0 0 4-4V4a4 4 0 0 0-4-4h-8zm1.06 12V3.545h3.399c1.587 0 2.543.809 2.543 2.11 0 .884-.65 1.675-1.483 1.816v.1c1.143.117 1.904.931 1.904 2.033 0 1.488-1.084 2.396-2.888 2.396H5.062z"/>
</svg> Bootstrap</a> and <a href="https://bootstrap-table.com">Bootstrap Table</a>.
        <a href="https://pdssbn.astro.umd.edu/"><img src="sbn_logo5_v0.png" width="100" style="vertical-align:bottom"></a>
        <a href="https://github.com/Small-Bodies-Node/mpecwatch"><svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" fill="currentColor" class="bi bi-github" viewBox="0 0 16 16">
  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
</svg></a>
      </footer>
    
        <!-- Bootstrap core JavaScript
        ================================================== -->
        <!-- Placed at the end of the document so the pages load faster -->
        <!--
        <script src="https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous"></script>
        <script>window.jQuery || document.write('<script src="assets/js/vendor/jquery.min.js"><\/script>')</script>

        <script src="https://cdn.jsdelivr.net/npm/jquery/dist/jquery.min.js"></script>
        -->

        <script
        src="https://code.jquery.com/jquery-3.7.1.min.js"
        integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo="
        crossorigin="anonymous"></script>

        <script src="dist/js/bootstrap.min.js"></script>
        <script src="assets/js/docs.min.js"></script>
        <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
        <script src="assets/js/ie10-viewport-bug-workaround.js"></script>
        
        <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js"></script>

        <!-- Export table
        <script type="text/javascript" src="extensions/export/libs/FileSaver/FileSaver.min.js"></script>
        <script type="text/javascript" src="extensions/export/libs/js-xlsx/xlsx.core.min.js"></script>
        <script type="text/javascript" src="extensions/export/libs/html2canvas/html2canvas.min.js"></script>
        <script src="extensions/export/tableExport.min.js">$('#obs_table').tableExport({type:'csv'});</script>
        -->

        <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/tableExport.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/tableexport.jquery.plugin@1.29.0/libs/jsPDF/jspdf.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.22.5/dist/bootstrap-table.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap-table@1.22.5/dist/extensions/export/bootstrap-table-export.min.js"></script>

      </body>
    </html>"""
    
    if p == 'All time':
        with open('../www/survey.html', 'w', encoding='utf-8') as f:
          f.write(o)
    else:
        with open('../www/survey-%s.html' % str(p), 'w', encoding='utf-8') as f:
          f.write(o)
