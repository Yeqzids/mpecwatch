#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Make a page that contains a summary table of stats by observatories

 (C) Quanzhi Ye
 
"""

import sqlite3, datetime, json, numpy as np

dbFile = '../mpecwatch_v3.db'
stat = 'obscode_stat.json'
mpccode = '../mpccode.json'

db = sqlite3.connect(dbFile)
cursor = db.cursor()

with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)
    
with open(stat) as stat:
    stat = json.load(stat)
    
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
        
        <!-- Main jumbotron for a primary marketing message or call to action -->
      <div class="jumbotron">
        <p>The pages here are still under active development and testing. Comments, suggestions and bug reports are welcome (via Issue Tracker or by email). Quanzhi 09/02/22</p>
      </div>
    """ % str(p)
    
    # Table of MPECs by year and type
    
    o += """
          <div class="page-header">
            <h1>Statistics by Observatory - %s</h1>
            <p><a href="https://sbnmpc.astro.umd.edu/mpecwatch/obs.html">All time</a> """ % str(p)
            
    for pp in pages[:-1]:
        o += """ | <a href="https://sbnmpc.astro.umd.edu/mpecwatch/obs-%s.html">%s</a>""" % (str(pp), str(pp))
        
    o += """
            </p>
          </div>
          <p>
          Disc. - MPECs associated with discovery made by this station.<br>
          F/U - MPECs associated with follow-up observations made by this station to an object discovered elsewhere.<br>
          1st F/U - MPECs associated with follow-up observations made by this station to an object discovered elsewhere, with this station being the first station to follow-up.<br>
          Prec. - MPECs associated with precovery observations made by this station to an object discovered elsewhere.
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
                  <th data-field="code" data-sortable="true">Code</th>
                  <th data-field="obs" data-sortable="true">Observatory</th>
                  <th data-field="city" data-sortable="true">City</th>
                  <th data-field="county" data-sortable="true">County</th>
                  <th data-field="state" data-sortable="true">State</th>
                  <th data-field="country" data-sortable="true">Country</th>
                  <th data-field="nmpec" data-sortable="true">MPECs</th>
                  <th data-field="ndisc" data-sortable="true">Disc.</th>
                  <th data-field="nNEA" data-sortable="true">NEA</th>
                  <th data-field="nPHA" data-sortable="true">PHA</th>
                  <th data-field="nfu" data-sortable="true">F/U</th>
                  <th data-field="nffu" data-sortable="true">1st F/U</th>
                  <th data-field="nprecovery" data-sortable="true">Prec.</th>
                </tr>
              </thead>
              <tbody>
    """
    
    for s in stat:
        
        try:
            city = mpccode[s]['city']
        except:
            city = ''
            
        try:
            county = mpccode[s]['county']
        except:
            county = ''
            
        try:
            state = mpccode[s]['state']
        except:
            state = ''
            
        try:
            country = mpccode[s]['country']
        except:
            country = ''
            
        o += """
            <tr>
                <td>%s</td>""" % s
                
        #if s in ['244', '245', '247', '248', '249', '250', '258', '270', '274', '275', '500', 'C49', 'C50', 'C51', 'C52', 'C53', 'C54', 'C55', 'C56', 'C57', 'C59']:
        o += """
                <td><a href="https://sbnmpc.astro.umd.edu/mpecwatch/byStation/station_%s.html">%s</a></td>""" % (str(s), mpccode[s]['name'])
                
        o += """
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
        """ % (city, county, state, country)
        
        if p == 'All time':
            o += """
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
            """ % (str(sum(stat[s]['mpec'].values())), str(sum(stat[s]['mpec_discovery'].values())), str(sum(stat[s]['NEA'].values())), str(sum(stat[s]['PHA'].values())), str(sum(stat[s]['mpec_followup'].values())), str(sum(stat[s]['mpec_1st_followup'].values())), str(sum(stat[s]['mpec_precovery'].values())))
        else:
            o += """
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
            """ % (str(stat[s]['mpec'][str(p)]), str(stat[s]['mpec_discovery'][str(p)]), str(stat[s]['NEA'][str(p)]), str(stat[s]['PHA'][str(p)]), str(stat[s]['mpec_followup'][str(p)]), str(stat[s]['mpec_1st_followup'][str(p)]), str(stat[s]['mpec_precovery'][str(p)]))
        
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
        -->

        <script src="https://cdn.jsdelivr.net/npm/jquery/dist/jquery.min.js"></script>
        <script src="dist/js/bootstrap.min.js"></script>
        <script src="assets/js/docs.min.js"></script>
        <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
        <script src="assets/js/ie10-viewport-bug-workaround.js"></script>
        
        <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
        <script src="https://unpkg.com/bootstrap-table@1.19.1/dist/bootstrap-table.min.js"></script>

        <!-- Export table -->
        <script type="text/javascript" src="extensions/export/libs/FileSaver/FileSaver.min.js"></script>
        <script type="text/javascript" src="extensions/export/libs/js-xlsx/xlsx.core.min.js"></script>
        <script type="text/javascript" src="extensions/export/libs/html2canvas/html2canvas.min.js"></script>
        <script src="extensions/export/tableExport.min.js">$('#obs_table').tableExport({type:'csv'});</script>
      </body>
    </html>"""
    
    if p == 'All time':
        with open('../www/obs.html', 'w', encoding='utf-8') as f:
          f.write(o)
    else:
        with open('../www/obs-%s.html' % str(p), 'w', encoding='utf-8') as f:
          f.write(o)
