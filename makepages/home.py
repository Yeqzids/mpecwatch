#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Make home page

 (C) Quanzhi Ye
 
"""

import sqlite3, pandas as pd, datetime, numpy as np, json

page = '../www/index.html'
dbFile = '../mpecwatch_v3.db'
mpec_count = 'mpec_count.txt'
mpccode = '../mpccode.json'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)

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

    <title>MPEC Watch</title>

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
            <li class="active"><a href="https://sbnmpc.astro.umd.edu/mpecwatch/index.html">Home</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/obs.html">Observatory Browser</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/stats.html">Various Statistics</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu/mpecwatch/mpc_stuff.html">MPC Stuff</a></li>
            <li><a href="https://github.com/Yeqzids/mpecwatch/issues">Issue Tracker</a></li>
            <li><a href="https://sbnmpc.astro.umd.edu">SBN-MPC Annex</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container theme-showcase" role="main">

      <!-- Main jumbotron for a primary marketing message or call to action -->
      <div class="jumbotron">
        <h2>Welcome to MPEC Watch!</h2>
        <p><b>Note: This site is still under active development. Some links do not work.</b></p>
        <p>MPEC Watch provides various statistical metrics and plots derived from <a href="https://minorplanetcenter.net/">Minor Planet Center</a>'s <a href="https://www.minorplanetcenter.net/mpec/RecentMPECs.html">Minor Planet Electronic Circular</a> service. This website is created and maintained by <a href="https://www.astro.umd.edu/~qye/">Quanzhi Ye</a>. Tables and plots are automatically updated at midnight US Eastern Time. </p>
        <p>Last update: UTC %s</p>
      </div>
""" % datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# Table of MPECs by year and type

o += """
      <div class="page-header">
        <h1>At a glance</h1>
      </div>
      <p>
        <iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="MPECTally_ByYear_Fig.html" height="525" width="100%"></iframe>
      </p>
      
      <table class="table table-striped">
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
          </tr>
        </thead>
        <tfoot><tr><td colspan="5">1. P/R/FU - precovery/recovery/follow-up.
        <br>2. DOU - Daily Orbit Update.</td></tr></tfoot>
        <tbody>
"""

for year in list(np.arange(1993, datetime.datetime.now().year+1, 1))[::-1]:
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
	
	o += """
          <tr>
            <td><a href="https://sbnmpc.astro.umd.edu/mpecwatch/byYear/%s.html">%i</a></td>
            <td>%i</td>
            <td>%i</td>
            <td>%i</td>
            <td>%i</td>
            <td>%i</td>
            <td>%i</td>
            <td>%i</td>
            <td>%i</td>
          </tr>
	""" % (str(year), year, sum([editorial, discovery, orbitupdate, dou, listupdate, retraction, other]), editorial, discovery, orbitupdate, dou, listupdate, retraction, other)

o += """
        </tbody>
      </table>
"""

# panels of various statistics

mpec_count = pd.read_fwf('mpec_count.txt')
disc_count = pd.read_fwf('disc_count.txt')
fu_count = pd.read_fwf('fu_count.txt')
fu1_count = pd.read_fwf('fu1_count.txt')
pc_count = pd.read_fwf('pc_count.txt')

for s in [['Top MPEC Contributors', mpec_count], ['Top MPEC-ed Discoverers', disc_count], ['Top MPEC-ed Follow-up Observatories', fu_count], ['Top MPEC-ed First Follow-up Observatories', fu1_count], ['Top MPEC-ed Precoverers', pc_count]]:

	o += """<div class="page-header">
			<h1>%s</h1>
		  </div>
		  <div class="row">
			<div class="col-sm-4">
			  <div class="panel panel-default">
				<div class="panel-heading">""" % s[0]

	o += """
				  <h3 class="panel-title">Last 1 year (%s to %s)</h3>""" % ((datetime.datetime.utcnow() - datetime.timedelta(days=365)).strftime("%Y-%m-%d"), datetime.datetime.utcnow().strftime("%Y-%m-%d"))
				  
	o += """      
				</div>
				<div class="panel-body">
				  <table class="table table-striped">
					<thead>
					  <tr>
						<th>#</th>
						<th>Observatory</th>
						<th>Total MPECs</th>
					  </tr>
					</thead>
					<tbody>"""
					
	for i in list(range(10)):
		o += """
					  <tr>
						<td>%s</td>
						<td><a href="https://sbnmpc.astro.umd.edu/mpecwatch/byStation/station_%s.html">%s</td>
						<td>%s</td>
					  </tr>
		""" % (str(i+1), s[1].sort_values('count1y', ascending=False).reset_index(drop=True)['cod'][i], s[1].sort_values('count1y', ascending=False).reset_index(drop=True)['cod'][i] + ' ' + mpccode[s[1].sort_values('count1y', ascending=False).reset_index(drop=True)['cod'][i]]['name'], s[1].sort_values('count1y', ascending=False).reset_index(drop=True)['count1y'][i])

	o += """                
					</tbody>
				  </table>
				</div>
			  </div>
			</div><!-- /.col-sm-4 -->
			<div class="col-sm-4">
			  <div class="panel panel-default">
				<div class="panel-heading">"""

	o += """
				  <h3 class="panel-title">Last 5 years (%s to %s)</h3>""" % ((datetime.datetime.utcnow() - datetime.timedelta(days=365*5)).strftime("%Y-%m-%d"), datetime.datetime.utcnow().strftime("%Y-%m-%d"))
				  
	o += """      
				</div>
				<div class="panel-body">
				  <table class="table table-striped">
					<thead>
					  <tr>
						<th>#</th>
						<th>Observatory</th>
						<th>Total MPECs</th>
					  </tr>
					</thead>
					<tbody>"""
					
	for i in list(range(10)):
		o += """
					  <tr>
						<td>%s</td>
						<td><a href="https://sbnmpc.astro.umd.edu/mpecwatch/byStation/station_%s.html">%s</td>
						<td>%s</td>
					  </tr>
		""" % (str(i+1), s[1].sort_values('count5y', ascending=False).reset_index(drop=True)['cod'][i], s[1].sort_values('count5y', ascending=False).reset_index(drop=True)['cod'][i] + ' ' + mpccode[s[1].sort_values('count5y', ascending=False).reset_index(drop=True)['cod'][i]]['name'], s[1].sort_values('count5y', ascending=False).reset_index(drop=True)['count5y'][i])

	o += """                
					</tbody>
				  </table>
				</div>
			  </div>
			</div><!-- /.col-sm-4 -->
			<div class="col-sm-4">
			  <div class="panel panel-default">
				<div class="panel-heading">"""
				
	o += """
				  <h3 class="panel-title">All time (since 1993-09-19)</h3>
				</div>
				<div class="panel-body">
				  <table class="table table-striped">
					<thead>
					  <tr>
						<th>#</th>
						<th>Observatory</th>
						<th>Total MPECs</th>
					  </tr>
					</thead>
					<tbody>"""
					
	for i in list(range(10)):
		o += """
					  <tr>
						<td>%s</td>
						<td><a href="https://sbnmpc.astro.umd.edu/mpecwatch/byStation/station_%s.html">%s</td>
						<td>%s</td>
					  </tr>
		""" % (str(i+1), s[1].sort_values('countall', ascending=False).reset_index(drop=True)['cod'][i], s[1].sort_values('countall', ascending=False).reset_index(drop=True)['cod'][i] + ' ' + mpccode[s[1].sort_values('countall', ascending=False).reset_index(drop=True)['cod'][i]]['name'], s[1].sort_values('countall', ascending=False).reset_index(drop=True)['countall'][i])

	o += """                
					</tbody>
				  </table>
				</div>
			  </div>
			</div><!-- /.col-sm-4 -->
		  </div> <!-- /container -->"""

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
    <script src="https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous"></script>
    <script>window.jQuery || document.write('<script src="assets/js/vendor/jquery.min.js"><\/script>')</script>
    <script src="dist/js/bootstrap.min.js"></script>
    <script src="assets/js/docs.min.js"></script>
    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <script src="assets/js/ie10-viewport-bug-workaround.js"></script>
  </body>
</html>"""

with open(page, 'w') as f:
	f.write(o)
