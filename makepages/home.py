#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Make home page

 (C) Quanzhi Ye
 
"""

import sqlite3, plotly.express as px, pandas as pd, datetime, numpy as np

page = '../www/index.html'
dbFile = '../mpecwatch_v3.db'
mpec_count = 'mpec_count.txt'
mpccode = '../mpccode_trim.txt'

def code_to_name(code):			# return observatory name and country/region given an MPC code
	for i in mpccode:
		if i[0:3] == code:
			return i[26:].strip(), i[4:26].strip()

db = sqlite3.connect(dbFile)
cursor = db.cursor()

with open(mpccode) as f:
	mpccode = f.readlines()

o = """
<!doctype html>
<html lang="en">
  <head>
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
            <li class="active"><a href="#">Home</a></li>
            <li><a href="#">Statistics by Year</a></li>
            <li><a href="#">Statistics by Observatory</a></li>
            <li><a href="#">NEA Discovery Statistics</a></li>
            <li><a href="#">Comet Discovery Statistics</a></li>
            <li><a href="#">Service History</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container theme-showcase" role="main">

      <!-- Main jumbotron for a primary marketing message or call to action -->
      <div class="jumbotron">
        <h2>Welcome to MPEC Watch!</h2>
        <p><b>Note: This site is still under development. Currently, none of the links in the top bar work.</b></p>
        <p>MPEC Watch provides various statistical metrics and plots derived from <a href="https://minorplanetcenter.net/">Minor Planet Center</a>'s <a href="https://www.minorplanetcenter.net/mpec/RecentMPECs.html">Minor Planet Electronic Circular</a> service. This website is created and maintained by <a href="https://www.astro.umd.edu/~qye/">Quanzhi Ye</a>. Tables and plots are automatically updated at midnight US Eastern Time.</p>
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
						<td>%s</td>
						<td>%s</td>
					  </tr>
		""" % (str(i+1), s[1].sort_values('count1y', ascending=False).reset_index(drop=True)['cod'][i] + ' ' + code_to_name(s[1].sort_values('count1y', ascending=False).reset_index(drop=True)['cod'][i])[0], s[1].sort_values('count1y', ascending=False).reset_index(drop=True)['count1y'][i])

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
						<td>%s</td>
						<td>%s</td>
					  </tr>
		""" % (str(i+1), s[1].sort_values('count5y', ascending=False).reset_index(drop=True)['cod'][i] + ' ' + code_to_name(s[1].sort_values('count5y', ascending=False).reset_index(drop=True)['cod'][i])[0], s[1].sort_values('count5y', ascending=False).reset_index(drop=True)['count5y'][i])

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
						<td>%s</td>
						<td>%s</td>
					  </tr>
		""" % (str(i+1), s[1].sort_values('countall', ascending=False).reset_index(drop=True)['cod'][i] + ' ' + code_to_name(s[1].sort_values('countall', ascending=False).reset_index(drop=True)['cod'][i])[0], s[1].sort_values('countall', ascending=False).reset_index(drop=True)['countall'][i])

	o += """                
					</tbody>
				  </table>
				</div>
			  </div>
			</div><!-- /.col-sm-4 -->
		  </div> <!-- /container -->"""

o += """
	<footer class="pt-5 my-5 text-muted border-top">
    Script by <a href="https://www.astro.umd.edu/~qye/">Quanzhi Ye</a>. Powered by <a href="https://getbootstrap.com">Bootstrap</a>.
    <a href="https://pdssbn.astro.umd.edu/"><img src="sbn_logo5_v0.png" width="100"></a>
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
