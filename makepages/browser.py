#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Make a page that contains a summary table of stats by observatories

 (C) Quanzhi Ye
 
"""

import json, numpy as np
from datetime import datetime

stat = '../obscode_stat.json'
mpccode = '../mpccode.json'

with open(mpccode) as mpccode:
    mpccode = json.load(mpccode)
    
with open(stat) as stat:
    stat = json.load(stat)
    
pages = list(np.arange(1993, datetime.now().year+1, 1))
pages = [str(p) for p in pages]
pages.append('All time')
years = pages[:-1]

for p in pages:
    # test only all time
    if p != 'All time':
        continue
    
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
          </p>""" % (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Year range filter card
    o += """
          <div class="card mb-4">
              <div class="card-header">
                  <h5><i class="fas fa-calendar-alt"></i> Filter by Year Range</h5>
              </div>
              <div class="card-body">
                  <div class="row align-items-end">
                      <div class="col-md-3">
                          <label for="startYear">Start Year:</label>
                          <select id="startYear" class="form-control">
                              <!-- Populated by JavaScript -->
                          </select>
                      </div>
                      <div class="col-md-3">
                          <label for="endYear">End Year:</label>
                          <select id="endYear" class="form-control">
                              <!-- Populated by JavaScript -->
                          </select>
                      </div>
                      <div class="col-md-3">
                          <button onclick="applyYearFilter()" class="btn btn-primary">Apply Filter</button>
                          <button onclick="clearYearFilter()" class="btn btn-secondary">Show All</button>
                      </div>
                      <div class="col-md-3">
                          <div id="filterStatus" class="text-muted small"></div>
                      </div>
                  </div>
                  <div class="row mt-2">
                      <div class="col-12">
                          <small class="text-muted">Quick filters:</small>
                          <div class="btn-group btn-group-sm" role="group">
                              <button type="button" class="btn btn-outline-secondary" onclick="applyPresetFilter('recent5')">Last 5 Years</button>
                              <button type="button" class="btn btn-outline-secondary" onclick="applyPresetFilter('recent10')">Last 10 Years</button>
                              <button type="button" class="btn btn-outline-secondary" onclick="applyPresetFilter('2020s')">2020s</button>
                              <button type="button" class="btn btn-outline-secondary" onclick="applyPresetFilter('2010s')">2010s</button>
                              <button type="button" class="btn btn-outline-secondary" onclick="applyPresetFilter('2000s')">2000s</button>
                          </div>
                      </div>
                  </div>
              </div>
          </div>

          <!-- Summary Statistics Cards -->
          <div class="row mb-3" id="summaryStats" style="display: none;">
              <div class="col-md-2">
                  <div class="card text-center">
                      <div class="card-body p-2">
                          <h6 class="card-title mb-1" id="total-observatories">-</h6>
                          <small class="text-muted">Observatories</small>
                      </div>
                  </div>
              </div>
              <div class="col-md-2">
                  <div class="card text-center">
                      <div class="card-body p-2">
                          <h6 class="card-title mb-1" id="total-mpecs">-</h6>
                          <small class="text-muted">Total MPECs</small>
                      </div>
                  </div>
              </div>
              <div class="col-md-2">
                  <div class="card text-center">
                      <div class="card-body p-2">
                          <h6 class="card-title mb-1" id="total-discoveries">-</h6>
                          <small class="text-muted">Discoveries</small>
                      </div>
                  </div>
              </div>
              <div class="col-md-2">
                  <div class="card text-center">
                      <div class="card-body p-2">
                          <h6 class="card-title mb-1" id="total-followups">-</h6>
                          <small class="text-muted">Follow-ups</small>
                      </div>
                  </div>
              </div>
              <div class="col-md-2">
                  <div class="card text-center">
                      <div class="card-body p-2">
                          <h6 class="card-title mb-1" id="total-firstfollowups">-</h6>
                          <small class="text-muted">1st Follow-ups</small>
                      </div>
                  </div>
              </div>
              <div class="col-md-2">
                  <div class="card text-center">
                      <div class="card-body p-2">
                          <h6 class="card-title mb-1" id="total-precoveries">-</h6>
                          <small class="text-muted">Precoveries</small>
                      </div>
                  </div>
              </div>
          </div>
          """
          
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
            
        # Create data attributes for JavaScript filtering
        data_attrs = 'data-observatory="%s" class="observatory-row"' % s
        if p == 'All time':
            data_attrs += ' data-mpecs="%s" data-discoveries="%s" data-followups="%s" data-firstfollowups="%s" data-precoveries="%s"' % (
                str(stat[s]['total']), 
                str(stat[s]['Discovery']['total']), 
                str(stat[s]['Followup']['total']),
                str(stat[s]['FirstFollowup']['total']),
                str(stat[s]['Precovery']['total'])
            )
        
        o += """
            <tr %s>
                <td>%s</td>""" % (data_attrs, s)
                
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
            """ % (str(stat[s]['total']), 
                   str(stat[s]['Discovery']['total']), 
                   str(sum(stat[s]['Discovery'][year]['NEA'] for year in years)),
                   str(sum(stat[s]['Discovery'][year]['PHA'] for year in years)),
                   str(sum(stat[s]['Discovery'][year]['Comet'] for year in years)),
                   str(sum(stat[s]['Discovery'][year]['Satellite'] for year in years)),
                   str(sum(stat[s]['Discovery'][year]['TNO'] for year in years)),
                   str(sum(stat[s]['Discovery'][year]['Unusual'] for year in years)),
                   str(sum(stat[s]['Discovery'][year]['Interstellar'] for year in years)),
                   str(sum(stat[s]['Discovery'][year]['Unknown'] for year in years)),
                   str(stat[s]['Followup']['total']),
                   str(sum(stat[s]['Followup'][year]['NEA'] for year in years)),
                   str(sum(stat[s]['Followup'][year]['PHA'] for year in years)),
                   str(sum(stat[s]['Followup'][year]['Comet'] for year in years)),
                   str(sum(stat[s]['Followup'][year]['Satellite'] for year in years)),
                   str(sum(stat[s]['Followup'][year]['TNO'] for year in years)),
                   str(sum(stat[s]['Followup'][year]['Unusual'] for year in years)),
                   str(sum(stat[s]['Followup'][year]['Interstellar'] for year in years)),
                   str(sum(stat[s]['Followup'][year]['Unknown'] for year in years)),
                   str(stat[s]['FirstFollowup']['total']),
                   str(stat[s]['Precovery']['total']))
    
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
                </tr>
            """ % (str(stat[s][str(p)]), 
                   str(stat[s]['Discovery'][str(p)]['total']), 
                   str(stat[s]['Discovery'][str(p)]['NEA']), 
                   str(stat[s]['Discovery'][str(p)]['PHA']), 
                   str(stat[s]['Discovery'][str(p)]['Comet']), 
                   str(stat[s]['Discovery'][str(p)]['Satellite']),
                   str(stat[s]['Discovery'][str(p)]['TNO']),
                   str(stat[s]['Discovery'][str(p)]['Unusual']), 
                   str(stat[s]['Discovery'][str(p)]['Interstellar']), 
                   str(stat[s]['Discovery'][str(p)]['Unknown']),
                   str(stat[s]['Followup'][str(p)]['total']), 
                   str(stat[s]['Followup'][str(p)]['NEA']), 
                   str(stat[s]['Followup'][str(p)]['PHA']), 
                   str(stat[s]['Followup'][str(p)]['Comet']), 
                   str(stat[s]['Followup'][str(p)]['Satellite']), 
                   str(stat[s]['Followup'][str(p)]['TNO']), 
                   str(stat[s]['Followup'][str(p)]['Unusual']), 
                   str(stat[s]['Followup'][str(p)]['Interstellar']), 
                   str(stat[s]['Followup'][str(p)]['Unknown']), 
                   str(stat[s]['FirstFollowup'][str(p)]['total']), 
                   str(stat[s]['Precovery'][str(p)]['total']))
        
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

        <script>
// MPEC Watch Observatory Browser Year Range Filtering
let observatoryData = {};
let currentlyFilteredYears = null;
let statDataUrl = 'obscode_stat.json'; // Load data from separate file

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeObservatoryBrowser();
});

function initializeObservatoryBrowser() {
    /**
     * Initialize observatory browser with year range controls
     */
    populateYearDropdowns();
    loadObservatoryData();
    setupBootstrapTableFiltering();
}

function populateYearDropdowns() {
    /**
     * Populate year dropdown controls with available years
     */
    const years = Array.from({length: %d - 1993 + 1}, (_, i) => 1993 + i);
    const startYearSelect = document.getElementById('startYear');
    const endYearSelect = document.getElementById('endYear');
    
    years.forEach(year => {
        startYearSelect.innerHTML += `<option value="${year}">${year}</option>`;
        endYearSelect.innerHTML += `<option value="${year}">${year}</option>`;
    });
    
    // Set default values
    startYearSelect.value = years[0];
    endYearSelect.value = years[years.length - 1];
}

function loadObservatoryData() {
    /**
     * Load observatory data from JSON file
     */
    fetch(statDataUrl)
        .then(response => response.json())
        .then(data => {
            storeObservatoryData(data);
        })
        .catch(error => {
            console.error('Error loading observatory data:', error);
            // Fallback: Extract data from existing table
            storeObservatoryDataFromTable();
        });
}

function storeObservatoryData(statData) {
    /**
     * Store observatory data for filtering calculations
     */
    const observatoryRows = document.querySelectorAll('tr.observatory-row');
    
    observatoryRows.forEach(row => {
        const code = row.dataset.observatory;
        observatoryData[code] = {
            element: row,
            allTime: {
                mpecs: parseInt(row.dataset.mpecs || 0),
                discoveries: parseInt(row.dataset.discoveries || 0),
                followups: parseInt(row.dataset.followups || 0),
                firstFollowups: parseInt(row.dataset.firstfollowups || 0),
                precoveries: parseInt(row.dataset.precoveries || 0)
            },
            byYear: statData[code] || {}
        };
    });
}

function storeObservatoryDataFromTable() {
    /**
     * Fallback: Extract data from existing table when JSON loading fails
     */
    const observatoryRows = document.querySelectorAll('tr.observatory-row');
    
    observatoryRows.forEach(row => {
        const code = row.dataset.observatory;
        observatoryData[code] = {
            element: row,
            allTime: {
                mpecs: parseInt(row.dataset.mpecs || 0),
                discoveries: parseInt(row.dataset.discoveries || 0),
                followups: parseInt(row.dataset.followups || 0),
                firstFollowups: parseInt(row.dataset.firstfollowups || 0),
                precoveries: parseInt(row.dataset.precoveries || 0)
            },
            byYear: {} // Limited functionality without full data
        };
    });
}

function applyYearFilter() {
    /**
     * Apply year range filter to observatory browser
     */
    const startYear = parseInt(document.getElementById('startYear').value);
    const endYear = parseInt(document.getElementById('endYear').value);
    
    if (startYear > endYear) {
        alert('Start year must be less than or equal to end year');
        return;
    }
    
    currentlyFilteredYears = {start: startYear, end: endYear};
    
    // Update table data
    updateObservatoryTable(startYear, endYear);
    
    // Update summary statistics
    updateSummaryStatistics(startYear, endYear);
    
    // Update filter status
    updateFilterStatus(startYear, endYear);
    
    // Refresh Bootstrap Table
    $('#obs_table').bootstrapTable('refresh');
}

function updateObservatoryTable(startYear, endYear) {
    /**
     * Update observatory table with year range data
     */
    Object.keys(observatoryData).forEach(code => {
        const obsData = observatoryData[code];
        const row = obsData.element;
        
        // Calculate totals for year range
        let mpecs = 0, discoveries = 0, followups = 0, firstFollowups = 0, precoveries = 0;
        let neaDisc = 0, phaDisc = 0, cometDisc = 0, satDisc = 0, tnoDisc = 0;
        let unusualDisc = 0, interDisc = 0, unkDisc = 0;
        let neaFu = 0, phaFu = 0, cometFu = 0, satFu = 0, tnoFu = 0;
        let unusualFu = 0, interFu = 0, unkFu = 0;
        
        for (let year = startYear; year <= endYear; year++) {
            const yearStr = year.toString();
            if (obsData.byYear[yearStr]) {
                mpecs += obsData.byYear[yearStr] || 0;
            }
            
            // Aggregate discovery types
            if (obsData.byYear.Discovery && obsData.byYear.Discovery[yearStr]) {
                const discYear = obsData.byYear.Discovery[yearStr];
                discoveries += discYear.total || 0;
                neaDisc += discYear.NEA || 0;
                phaDisc += discYear.PHA || 0;
                cometDisc += discYear.Comet || 0;
                satDisc += discYear.Satellite || 0;
                tnoDisc += discYear.TNO || 0;
                unusualDisc += discYear.Unusual || 0;
                interDisc += discYear.Interstellar || 0;
                unkDisc += discYear.Unknown || 0;
            }
            
            // Aggregate followup types
            if (obsData.byYear.Followup && obsData.byYear.Followup[yearStr]) {
                const fuYear = obsData.byYear.Followup[yearStr];
                followups += fuYear.total || 0;
                neaFu += fuYear.NEA || 0;
                phaFu += fuYear.PHA || 0;
                cometFu += fuYear.Comet || 0;
                satFu += fuYear.Satellite || 0;
                tnoFu += fuYear.TNO || 0;
                unusualFu += fuYear.Unusual || 0;
                interFu += fuYear.Interstellar || 0;
                unkFu += fuYear.Unknown || 0;
            }
            
            // Aggregate first followups and precoveries
            if (obsData.byYear.FirstFollowup && obsData.byYear.FirstFollowup[yearStr]) {
                firstFollowups += obsData.byYear.FirstFollowup[yearStr].total || 0;
            }
            
            if (obsData.byYear.Precovery && obsData.byYear.Precovery[yearStr]) {
                precoveries += obsData.byYear.Precovery[yearStr].total || 0;
            }
        }
        
        // Update table cells
        const cells = row.querySelectorAll('td');
        if (cells.length >= 27) {
            cells[6].textContent = mpecs;
            cells[7].textContent = discoveries;
            cells[8].textContent = neaDisc;
            cells[9].textContent = phaDisc;
            cells[10].textContent = cometDisc;
            cells[11].textContent = satDisc;
            cells[12].textContent = tnoDisc;
            cells[13].textContent = unusualDisc;
            cells[14].textContent = interDisc;
            cells[15].textContent = unkDisc;
            cells[16].textContent = followups;
            cells[17].textContent = neaFu;
            cells[18].textContent = phaFu;
            cells[19].textContent = cometFu;
            cells[20].textContent = satFu;
            cells[21].textContent = tnoFu;
            cells[22].textContent = unusualFu;
            cells[23].textContent = interFu;
            cells[24].textContent = unkFu;
            cells[25].textContent = firstFollowups;
            cells[26].textContent = precoveries;
        }
    });
}

function updateSummaryStatistics(startYear, endYear) {
    /**
     * Update summary statistics for filtered year range
     */
    let totalObs = 0, totalMpecs = 0, totalDisc = 0, totalFu = 0, totalFirstFu = 0, totalPrec = 0;
    
    Object.keys(observatoryData).forEach(code => {
        const obsData = observatoryData[code];
        
        // Count active observatories in this range
        let hasActivity = false;
        for (let year = startYear; year <= endYear; year++) {
            if (obsData.byYear[year.toString()] && obsData.byYear[year.toString()] > 0) {
                hasActivity = true;
                break;
            }
        }
        if (hasActivity) totalObs++;
        
        // Sum up statistics from current table values
        const row = obsData.element;
        const cells = row.querySelectorAll('td');
        if (cells.length >= 27) {
            totalMpecs += parseInt(cells[6].textContent || 0);
            totalDisc += parseInt(cells[7].textContent || 0);
            totalFu += parseInt(cells[16].textContent || 0);
            totalFirstFu += parseInt(cells[25].textContent || 0);
            totalPrec += parseInt(cells[26].textContent || 0);
        }
    });
    
    // Update summary cards
    document.getElementById('total-observatories').textContent = totalObs.toLocaleString();
    document.getElementById('total-mpecs').textContent = totalMpecs.toLocaleString();
    document.getElementById('total-discoveries').textContent = totalDisc.toLocaleString();
    document.getElementById('total-followups').textContent = totalFu.toLocaleString();
    document.getElementById('total-firstfollowups').textContent = totalFirstFu.toLocaleString();
    document.getElementById('total-precoveries').textContent = totalPrec.toLocaleString();
    
    // Show summary stats
    document.getElementById('summaryStats').style.display = 'flex';
}

function updateFilterStatus(startYear, endYear) {
    /**
     * Update filter status message
     */
    const statusElement = document.getElementById('filterStatus');
    const yearCount = endYear - startYear + 1;
    statusElement.innerHTML = `<i class="fas fa-filter"></i> Showing ${yearCount} years (${startYear}-${endYear})`;
}

function clearYearFilter() {
    /**
     * Clear year filter and restore all-time data
     */
    currentlyFilteredYears = null;
    
    // Restore original all-time data
    Object.keys(observatoryData).forEach(code => {
        const obsData = observatoryData[code];
        const row = obsData.element;
        const cells = row.querySelectorAll('td');
        
        // Get all-time values by summing across all years
        let mpecs = 0, discoveries = 0, followups = 0, firstFollowups = 0, precoveries = 0;
        let neaDisc = 0, phaDisc = 0, cometDisc = 0, satDisc = 0, tnoDisc = 0;
        let unusualDisc = 0, interDisc = 0, unkDisc = 0;
        let neaFu = 0, phaFu = 0, cometFu = 0, satFu = 0, tnoFu = 0;
        let unusualFu = 0, interFu = 0, unkFu = 0;
        
        // Use totals from the data structure
        if (obsData.byYear.total !== undefined) mpecs = obsData.byYear.total;
        if (obsData.byYear.Discovery && obsData.byYear.Discovery.total !== undefined) {
            discoveries = obsData.byYear.Discovery.total;
        }
        if (obsData.byYear.Followup && obsData.byYear.Followup.total !== undefined) {
            followups = obsData.byYear.Followup.total;
        }
        if (obsData.byYear.FirstFollowup && obsData.byYear.FirstFollowup.total !== undefined) {
            firstFollowups = obsData.byYear.FirstFollowup.total;
        }
        if (obsData.byYear.Precovery && obsData.byYear.Precovery.total !== undefined) {
            precoveries = obsData.byYear.Precovery.total;
        }
        
        // Calculate aggregated discovery and followup types across all years
        const years = %s;
        for (const year of years) {
            if (obsData.byYear.Discovery && obsData.byYear.Discovery[year]) {
                const discYear = obsData.byYear.Discovery[year];
                neaDisc += discYear.NEA || 0;
                phaDisc += discYear.PHA || 0;
                cometDisc += discYear.Comet || 0;
                satDisc += discYear.Satellite || 0;
                tnoDisc += discYear.TNO || 0;
                unusualDisc += discYear.Unusual || 0;
                interDisc += discYear.Interstellar || 0;
                unkDisc += discYear.Unknown || 0;
            }
            
            if (obsData.byYear.Followup && obsData.byYear.Followup[year]) {
                const fuYear = obsData.byYear.Followup[year];
                neaFu += fuYear.NEA || 0;
                phaFu += fuYear.PHA || 0;
                cometFu += fuYear.Comet || 0;
                satFu += fuYear.Satellite || 0;
                tnoFu += fuYear.TNO || 0;
                unusualFu += fuYear.Unusual || 0;
                interFu += fuYear.Interstellar || 0;
                unkFu += fuYear.Unknown || 0;
            }
        }
        
        // Restore values
        if (cells.length >= 27) {
            cells[6].textContent = mpecs;
            cells[7].textContent = discoveries;
            cells[8].textContent = neaDisc;
            cells[9].textContent = phaDisc;
            cells[10].textContent = cometDisc;
            cells[11].textContent = satDisc;
            cells[12].textContent = tnoDisc;
            cells[13].textContent = unusualDisc;
            cells[14].textContent = interDisc;
            cells[15].textContent = unkDisc;
            cells[16].textContent = followups;
            cells[17].textContent = neaFu;
            cells[18].textContent = phaFu;
            cells[19].textContent = cometFu;
            cells[20].textContent = satFu;
            cells[21].textContent = tnoFu;
            cells[22].textContent = unusualFu;
            cells[23].textContent = interFu;
            cells[24].textContent = unkFu;
            cells[25].textContent = firstFollowups;
            cells[26].textContent = precoveries;
        }
    });
    
    // Reset dropdowns
    const years = Array.from({length: %d - 1993 + 1}, (_, i) => 1993 + i);
    document.getElementById('startYear').value = years[0];
    document.getElementById('endYear').value = years[years.length - 1];
    
    // Hide summary stats
    document.getElementById('summaryStats').style.display = 'none';
    
    // Clear status
    document.getElementById('filterStatus').innerHTML = '<i class="fas fa-list"></i> Showing all years';
    
    // Refresh Bootstrap Table
    $('#obs_table').bootstrapTable('refresh');
}

function applyPresetFilter(preset) {
    /**
     * Apply preset year range filters
     */
    const currentYear = new Date().getFullYear();
    let startYear, endYear;
    
    switch(preset) {
        case 'recent5':
            startYear = currentYear - 4;
            endYear = currentYear;
            break;
        case 'recent10':
            startYear = currentYear - 9;
            endYear = currentYear;
            break;
        case '2020s':
            startYear = 2020;
            endYear = currentYear;
            break;
        case '2010s':
            startYear = 2010;
            endYear = 2019;
            break;
        case '2000s':
            startYear = 2000;
            endYear = 2009;
            break;
        default:
            return;
    }
    
    document.getElementById('startYear').value = startYear;
    document.getElementById('endYear').value = endYear;
    applyYearFilter();
}

function setupBootstrapTableFiltering() {
    /**
     * Integrate with Bootstrap Table's existing functionality
     */
    $('#obs_table').on('refresh.bs.table', function() {
        // Reapply year filter after table refresh if one is active
        if (currentlyFilteredYears) {
            setTimeout(() => {
                updateObservatoryTable(currentlyFilteredYears.start, currentlyFilteredYears.end);
            }, 100);
        }
    });
}
</script>

      </body>
    </html>""" % (datetime.now().year, years, datetime.now().year)
    
    if p == 'All time':
        with open('../www/obs.html', 'w', encoding='utf-8') as f:
          f.write(o)
    else:
        with open('../www/obs-%s.html' % str(p), 'w', encoding='utf-8') as f:
          f.write(o)
