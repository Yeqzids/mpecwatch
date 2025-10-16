#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Display figures and stats on a number of metrics.

 (C) Quanzhi Ye
 
"""

import sqlite3, datetime, json, numpy as np, plotly.express as px, pandas as pd, calendar, pytz

eastern = pytz.timezone('US/Eastern')

dbFile = '../mpecwatch_v4.db'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

currentYear = datetime.datetime.now().year

list_computer = ['Alexandersen', 'Bell', 'MPC', 'Marsden', 'Pan', 'Pike', 'Spahr', 'Veres', 'Williams', 'Others']
list_issuer = ['A. U. Tomatic', 'Brian G. Marsden', 'Gareth V. Williams', 'Kyle E. Smalley', 'M. P. C. Staff', 'Sonia Keys', 'Timothy B. Spahr', 'Others']

# for computer and issuer: do stat, write to json and make figures

stat_computer = dict()
for i in list_computer:
    stat_computer[i] = {}
    
stat_issuer = dict()
for i in list_issuer:
    stat_issuer[i] = {}
    
df_computer = pd.DataFrame({"Year": [], "Computer": [], "#MPECs": []})
df_issuer = pd.DataFrame({"Year": [], "Issuer": [], "#MPECs": []})

for y in np.arange(1993, currentYear+1, 1):
    y = int(y)
    timestamp_start = calendar.timegm(datetime.date(y,1,1).timetuple())
    timestamp_end = calendar.timegm(datetime.date(y+1,1,1).timetuple())-1
    
    computer_nmpec_thisyear = []
    issuer_nmpec_thisyear = []
    
    for computer in list_computer:
        cursor.execute("select `OrbitComp`, count(*) from MPEC where time >= {} and time <= {} group by `OrbitComp`;".format(timestamp_start, timestamp_end))
        r = cursor.fetchall()
        matched = [(i, el.index(computer)) for i, el in enumerate(r) if computer in el]
        if computer == 'Others':
            total = 0
            none = 0
            for i in r:
                total += i[1]
                if i[0] == None or i[0] == '':
                    none += i[1]

            stat_computer[computer][str(y)] = total - sum(computer_nmpec_thisyear) - none
            computer_nmpec_thisyear.append(stat_computer[computer][str(y)])
        else:
            if len(matched) == 0:
                stat_computer[computer][str(y)] = 0
                computer_nmpec_thisyear.append(0)
            else:
                stat_computer[computer][str(y)] = r[matched[0][0]][1]
                computer_nmpec_thisyear.append(r[matched[0][0]][1])
        
    for issuer in list_issuer:
        cursor.execute("select `Issuer`, count(*) from MPEC where time >= {} and time <= {} group by `Issuer`;".format(timestamp_start, timestamp_end))
        r = cursor.fetchall()
        matched = [(i, el.index(issuer)) for i, el in enumerate(r) if issuer in el]
        if issuer == 'Others':
            total = 0
            none = 0
            for i in r:
                total += i[1]
                if i[0] == None or i[0] == '':
                    none += i[1]
                
            stat_issuer[issuer][str(y)] = total - sum(issuer_nmpec_thisyear) - none
            issuer_nmpec_thisyear.append(stat_issuer[issuer][str(y)])
        else:
            if len(matched) == 0:
                stat_issuer[issuer][str(y)] = 0
                issuer_nmpec_thisyear.append(0)
            else:
                stat_issuer[issuer][str(y)] = r[matched[0][0]][1]
                issuer_nmpec_thisyear.append(r[matched[0][0]][1])

    df_computer = pd.concat([df_computer, pd.DataFrame({"Year": [y]*len(list_computer), "Orbit computer": list_computer, "#MPECs": computer_nmpec_thisyear})], ignore_index = True)
    df_issuer = pd.concat([df_issuer, pd.DataFrame({"Year": [y]*len(list_issuer), "Issuer": list_issuer, "#MPECs": issuer_nmpec_thisyear})], ignore_index = True)
    
fig = px.bar(df_computer, x="Year", y="#MPECs", color="Orbit computer", title="Number MPECs by orbit computers")
fig.write_html("../www/Computer_ByYear_Fig.html")  

fig = px.bar(df_issuer, x="Year", y="#MPECs", color="Issuer", title="Number MPECs by issuers")
fig.write_html("../www/Issuer_ByYear_Fig.html")

with open('../www/computer_stat.json', 'w') as o:
    json.dump(stat_computer, o)
    
with open('../www/issuer_stat.json', 'w') as o:
    json.dump(stat_issuer, o)    
    
# for computer and issuer but for discovery and orbit update MPECs only: do stat, write to json and make figures

for mt in ['Discovery', 'OrbitUpdate']:
    stat_computer = dict()
    for i in list_computer:
        stat_computer[i] = {}
        
    stat_issuer = dict()
    for i in list_issuer:
        stat_issuer[i] = {}
        
    df_computer = pd.DataFrame({"Year": [], "Computer": [], "#MPECs": []})
    df_issuer = pd.DataFrame({"Year": [], "Issuer": [], "#MPECs": []})
    
    for y in np.arange(1993, currentYear+1, 1):
        y = int(y)
        timestamp_start = calendar.timegm(datetime.date(y,1,1).timetuple())
        timestamp_end = calendar.timegm(datetime.date(y+1,1,1).timetuple())-1
        
        computer_nmpec_thisyear = []
        issuer_nmpec_thisyear = []
        
        for computer in list_computer:
            cursor.execute("select `OrbitComp`, count(*) from MPEC where time >= {} and time <= {} and MPECType = '{}' group by `OrbitComp`;".format(timestamp_start, timestamp_end, mt))
            r = cursor.fetchall()
            matched = [(i, el.index(computer)) for i, el in enumerate(r) if computer in el]
            if computer == 'Others':
                total = 0
                none = 0
                for i in r:
                    total += i[1]
                    if i[0] == None or i[0] == '':
                        none += i[1]
    
                stat_computer[computer][str(y)] = total - sum(computer_nmpec_thisyear) - none
                computer_nmpec_thisyear.append(stat_computer[computer][str(y)])
            else:
                if len(matched) == 0:
                    stat_computer[computer][str(y)] = 0
                    computer_nmpec_thisyear.append(0)
                else:
                    stat_computer[computer][str(y)] = r[matched[0][0]][1]
                    computer_nmpec_thisyear.append(r[matched[0][0]][1])
            
        for issuer in list_issuer:
            cursor.execute("select `Issuer`, count(*) from MPEC where time >= {} and time <= {} and MPECType = '{}' group by `Issuer`;".format(timestamp_start, timestamp_end, mt))
            r = cursor.fetchall()
            matched = [(i, el.index(issuer)) for i, el in enumerate(r) if issuer in el]
            if issuer == 'Others':
                total = 0
                none = 0
                for i in r:
                    total += i[1]
                    if i[0] == None or i[0] == '':
                        none += i[1]
                    
                stat_issuer[issuer][str(y)] = total - sum(issuer_nmpec_thisyear) - none
                issuer_nmpec_thisyear.append(stat_issuer[issuer][str(y)])
            else:
                if len(matched) == 0:
                    stat_issuer[issuer][str(y)] = 0
                    issuer_nmpec_thisyear.append(0)
                else:
                    stat_issuer[issuer][str(y)] = r[matched[0][0]][1]
                    issuer_nmpec_thisyear.append(r[matched[0][0]][1])
            
        df_computer = pd.concat([df_computer, pd.DataFrame({"Year": [y]*len(list_computer), "Orbit computer": list_computer, "#MPECs": computer_nmpec_thisyear})], ignore_index = True)
        df_issuer = pd.concat([df_issuer, pd.DataFrame({"Year": [y]*len(list_issuer), "Issuer": list_issuer, "#MPECs": issuer_nmpec_thisyear})], ignore_index = True)

    fig = px.bar(df_computer, x="Year", y="#MPECs", color="Orbit computer", title="Number MPECs by orbit computers")
    fig.write_html("../www/Computer_%s_ByYear_Fig.html" % mt)  
    
    fig = px.bar(df_issuer, x="Year", y="#MPECs", color="Issuer", title="Number MPECs by issuers")
    fig.write_html("../www/Issuer_%s_ByYear_Fig.html" % mt)
    
    with open('../www/computer_%s_stat.json' % mt.lower(), 'w') as o:
        json.dump(stat_computer, o)
        
    with open('../www/issuer_%s_stat.json' % mt.lower(), 'w') as o:
        json.dump(stat_issuer, o)    

# hours, weekdays and types of MPECs from the past year, 2015, 2005 and 1995

## 1995, 2005 and 2015

for y in [1, 1995, 2005, 2015]:

    df_hours = pd.DataFrame({"Hour": [], "MPECType": [], "#MPECs": []}) 
    df_weekdays = pd.DataFrame({"Weekday": [], "MPECType": [], "#MPECs": []}) 
    
    if y == 1:
        t_1y = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        cursor.execute("select Time, MPECType from MPEC where time >= {};".format(t_1y.timestamp()))
        r = cursor.fetchall()
    else:
        timestamp_start = calendar.timegm(datetime.date(y,1,1).timetuple())
        timestamp_end = calendar.timegm(datetime.date(y+1,1,1).timetuple())-1
        cursor.execute("select Time, MPECType from MPEC where time >= {} and time <= {};".format(timestamp_start, timestamp_end))
        r = cursor.fetchall()
    
    tmp = []
    
    for i in r:
        tmp.append([int(pytz.utc.localize(datetime.datetime.utcfromtimestamp(i[0])).astimezone(eastern).strftime('%H')), pytz.utc.localize(datetime.datetime.utcfromtimestamp(i[0])).astimezone(eastern).strftime('%a'), i[1]])
        
    tmp = np.array(tmp)
        
    for h in list(range(24)):
        h = str(h)
        editorial = len(np.where((tmp.T[0] == h) & (tmp.T[2] == 'Editorial'))[0])
        discovery = len(np.where((tmp.T[0] == h) & (tmp.T[2] == 'Discovery'))[0])
        orbitupdate = len(np.where((tmp.T[0] == h) & (tmp.T[2] == 'OrbitUpdate'))[0])
        dou = len(np.where((tmp.T[0] == h) & (tmp.T[2] == 'DOU'))[0])
        listupdate = len(np.where((tmp.T[0] == h) & (tmp.T[2] == 'ListUpdate'))[0])
        retraction = len(np.where((tmp.T[0] == h) & (tmp.T[2] == 'Retraction'))[0])
        other = len(np.where((tmp.T[0] == h) & (tmp.T[2] == 'Other'))[0])
        df_hours = pd.concat([df_hours, pd.DataFrame({"Hour": [h, h, h, h, h, h, h], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, retraction, other]})], ignore_index = True)
        
    for w in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
        editorial = len(np.where((tmp.T[1] == w) & (tmp.T[2] == 'Editorial'))[0])
        discovery = len(np.where((tmp.T[1] == w) & (tmp.T[2] == 'Discovery'))[0])
        orbitupdate = len(np.where((tmp.T[1] == w) & (tmp.T[2] == 'OrbitUpdate'))[0])
        dou = len(np.where((tmp.T[1] == w) & (tmp.T[2] == 'DOU'))[0])
        listupdate = len(np.where((tmp.T[1] == w) & (tmp.T[2] == 'ListUpdate'))[0])
        retraction = len(np.where((tmp.T[1] == w) & (tmp.T[2] == 'Retraction'))[0])
        other = len(np.where((tmp.T[1] == w) & (tmp.T[2] == 'Other'))[0])
        df_weekdays = pd.concat([df_weekdays, pd.DataFrame({"Weekday": [w, w, w, w, w, w, w], "MPECType": ["Editorial", "Discovery", "OrbitUpdate", "DOU", "ListUpdate", "Retraction", "Other"], "#MPECs": [editorial, discovery, orbitupdate, dou, listupdate, retraction, other]})], ignore_index = True)
    
    if y == 1:
        fig = px.bar(df_hours, x="Hour", y="#MPECs", color="MPECType", title="Number and type of MPECs by hours over the past 1-year period")
        fig.write_html("../www/MPECTally_ByHour_Fig_Last1Yr.html")
        fig = px.bar(df_weekdays, x="Weekday", y="#MPECs", color="MPECType", title="Number and type of MPECs by weekdays over the last 1-year period")
        fig.write_html("../www/MPECTally_ByWeekday_Fig_Last1Yr.html")
    else:
        fig = px.bar(df_hours, x="Hour", y="#MPECs", color="MPECType", title="Number and type of MPECs by hours in %s" % str(y))
        fig.write_html("../www/MPECTally_ByHour_Fig_%s.html" % str(y))
        fig = px.bar(df_weekdays, x="Weekday", y="#MPECs", color="MPECType", title="Number and type of MPECs by weekdays in %s" % str(y))
        fig.write_html("../www/MPECTally_ByWeekday_Fig_%s.html" % str(y))
        
# make the page

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

    <title>MPEC Watch | Various Statistics</title>

    <!-- Bootstrap core CSS -->
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
    <link rel="stylesheet" href="https://unpkg.com/bootstrap-table@1.19.1/dist/bootstrap-table.min.css">
    
    <script src="https://unpkg.com/bootstrap-table@1.19.1/dist/bootstrap-table.min.js"></script>
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
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/survey.html">Survey Browser</a></li>
            <li class="active"><a href="https://sbnmpc.astro.umd.edu/mpecwatch/stats.html">Various Statistics</a></li>
            <!-- <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/mpc_stuff.html">MPC Stuff (non-public)</a></li> -->
            <li><a href="https://github.com/Yeqzids/mpecwatch/issues">Issue Tracker</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu">SBN-MPC Annex</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container theme-showcase" role="main">
    <!-- Main jumbotron for a primary marketing message or call to action -->
          <div class="page-header">
            <h1>Various Statistics</h1>
            <p>Various statistics and plots.</p>
          </div>
          <p>
            Last update: UTC %s
          </p>""" % (datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
          
o += """
          <div class="page-header">
          <h2>Fraction of each observer groups among all MPECs</h2>
          <p>
            <iframe id="igraph1" scrolling="no" style="border:none;" seamless="seamless" src="stats/Fraction_of_each_observer_groups_among_all_MPECs+O.html" height="525" width="100%"></iframe>
          </p>
          
          <h2>Fraction of each measurer groups among all MPECs</h2>
          <p>
            <iframe id="igraph2" scrolling="no" style="border:none;" seamless="seamless" src="stats/Fraction_of_each_measurer_groups_among_all_MPECs+O.html" height="525" width="100%"></iframe>
          </p>
          </div>
          
          <h2>Fraction of each observatory code among all MPECs</h2>
          <p>
            <iframe id="igraph3" scrolling="no" style="border:none;" seamless="seamless" src="stats/Fraction_of_each_observatory_code_among_all_MPECs+O.html" height="525" width="100%"></iframe>
          </p>
          
          <h2>Fraction of each observed object among all MPECs</h2>
          <p>
            <iframe id="igraph4" scrolling="no" style="border:none;" seamless="seamless" src="stats/T10Objects+Other.html" height="525" width="100%"></iframe>
          </p>"""
    
o += """
    	<footer class="pt-5 my-5 text-muted border-top">
        Script by <a href="https://www.astro.umd.edu/~qye/">Quanzhi Ye</a> and Taegon Hibbitts, hosted at <a href="https://sbnmpc.astro.umd.edu">SBN-MPC</a>. Powered by <a href="https://getbootstrap.com"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-bootstrap-fill" viewBox="0 0 16 16">
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
        <script src="https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous"></script>
        <script>window.jQuery || document.write('<script src="assets/js/vendor/jquery.min.js"><\/script>')</script>
        <script src="dist/js/bootstrap.min.js"></script>
        <script src="assets/js/docs.min.js"></script>
        <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
        <script src="assets/js/ie10-viewport-bug-workaround.js"></script>
        
        <script src="https://cdn.jsdelivr.net/npm/jquery/dist/jquery.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
        <script src="https://unpkg.com/bootstrap-table@1.19.1/dist/bootstrap-table.min.js"></script>
      </body>
    </html>"""
    
with open('../www/stats.html', 'w') as f:
    f.write(o)
