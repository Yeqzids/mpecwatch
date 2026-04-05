#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		Make a page that contains a summary table of stats by observatories

 (C) Quanzhi Ye
 
"""

import json, numpy as np
from datetime import datetime

stat_file = 'obscode_stat.json'
mpccode_file = '../mpccode.json'

with open(mpccode_file) as f:
    mpccode = json.load(f)
    
with open(stat_file) as f:
    stat = json.load(f)
    
years = [str(y) for y in np.arange(1993, datetime.now().year+1, 1)]

# Generate obs_summary.json
summary = {
    "years": [int(y) for y in years],
    "observatories": {}
}

for s in stat:
    s_years = {}
    total_all_time = stat[s].get('total', 0)
    
    for y in years:
        total = stat[s].get(y, 0)
        disc = stat[s].get('Discovery', {}).get(y, {})
        fu = stat[s].get('Followup', {}).get(y, {})
        ffu = stat[s].get('FirstFollowup', {}).get(y, {})
        prec = stat[s].get('Precovery', {}).get(y, {})
        
        y_total = total
        y_ndisc = disc.get('total', 0) if isinstance(disc, dict) else 0
        y_nfu = fu.get('total', 0) if isinstance(fu, dict) else 0
        y_nffu = ffu.get('total', 0) if isinstance(ffu, dict) else 0
        y_nprecovery = prec.get('total', 0) if isinstance(prec, dict) else 0

        if y_total > 0 or y_ndisc > 0 or y_nfu > 0 or y_nffu > 0 or y_nprecovery > 0:
            s_years[y] = {
                "nmpec": y_total,
                "ndisc": y_ndisc,
                "nNEAd": disc.get('NEA', 0) if isinstance(disc, dict) else 0,
                "nPHAd": disc.get('PHA', 0) if isinstance(disc, dict) else 0,
                "nComd": disc.get('Comet', 0) if isinstance(disc, dict) else 0,
                "nSatd": disc.get('Satellite', 0) if isinstance(disc, dict) else 0,
                "nTNOd": disc.get('TNO', 0) if isinstance(disc, dict) else 0,
                "nund": disc.get('Unusual', 0) if isinstance(disc, dict) else 0,
                "nintd": disc.get('Interstellar', 0) if isinstance(disc, dict) else 0,
                "nunkd": disc.get('Unknown', 0) if isinstance(disc, dict) else 0,
                "nfu": y_nfu,
                "nNEAfu": fu.get('NEA', 0) if isinstance(fu, dict) else 0,
                "nPHAfu": fu.get('PHA', 0) if isinstance(fu, dict) else 0,
                "nComfu": fu.get('Comet', 0) if isinstance(fu, dict) else 0,
                "nSatfu": fu.get('Satellite', 0) if isinstance(fu, dict) else 0,
                "nTNOfu": fu.get('TNO', 0) if isinstance(fu, dict) else 0,
                "nunfu": fu.get('Unusual', 0) if isinstance(fu, dict) else 0,
                "nintfu": fu.get('Interstellar', 0) if isinstance(fu, dict) else 0,
                "nunkfu": fu.get('Unknown', 0) if isinstance(fu, dict) else 0,
                "nffu": y_nffu,
                "nprecovery": y_nprecovery
            }
            
    mc = mpccode.get(s, {})
    if s_years or total_all_time > 0:
        summary["observatories"][s] = {
            "name": mc.get("name", ""),
            "city": mc.get("city", ""),
            "county": mc.get("county", ""),
            "state": mc.get("state", ""),
            "country": mc.get("country", ""),
            "years": s_years,
            "total_all_time": total_all_time
        }

with open('../www/obs_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f)

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

    <title>MPEC Watch | Global Statistics</title>

    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@3.4.1/dist/css/bootstrap.min.css" integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous">
    <!-- Bootstrap theme -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@3.4.1/dist/css/bootstrap-theme.min.css" integrity="sha384-6pzrmJMfsMBPCdGlNi4sNxjws2O40bQh2k93kXErn1rVf11t+1jzXf22uX+i6+p" crossorigin="anonymous">
    <!-- Bootstrap Table CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-table@1.22.5/dist/bootstrap-table.min.css">
    
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
      <div class="page-header">
        <h1>Statistics by Observatory</h1>
        <div class="panel panel-default" style="margin-top: 20px;">
          <div class="panel-body">
            <form class="form-inline" onsubmit="return false;">
              <div class="form-group">
                <label for="startYear">Start Year:</label>
                <select id="startYear" class="form-control"></select>
              </div>
              <div class="form-group" style="margin-left: 15px;">
                <label for="endYear">End Year:</label>
                <select id="endYear" class="form-control"></select>
              </div>
              <button id="filterBtn" class="btn btn-primary" style="margin-left: 15px;">Filter Data</button>
            </form>
          </div>
        </div>
      </div>
      <p>
      Disc. - MPECs associated with discovery made by this station.<br>
      F/U - MPECs associated with follow-up observations made by this station to an object discovered elsewhere.<br>
      1st F/U - MPECs associated with follow-up observations made by this station to an object discovered elsewhere, with this station being the first station to follow-up.<br>
      Prec. - MPECs associated with precovery observations made by this station to an object discovered elsewhere.
      </p>
      <p>
        Last update: UTC %s
      </p>
""" % (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

o += """
      <div class="page-header">
      <table id="obs_table" class="table table-striped">
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

        <script src="https://code.jquery.com/jquery-3.7.1.min.js"
        integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo="
        crossorigin="anonymous"></script>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@3.4.1/dist/js/bootstrap.min.js" integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd" crossorigin="anonymous"></script>
        
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
    $(function() {
        // Initialize Bootstrap Table explicitly so plugins work with dynamic load
        $('#obs_table').bootstrapTable({
            search: true,
            showExport: true,
            pagination: true,
            showColumns: true,
            exportOptions: {
                fileName: 'observatory_statistics'
            }
        });
        
        // Load embedded database JSON into local Javascript variable to bypass CORS file:// restrictions
        var data = """ + json.dumps(summary) + """;
        
        var years = data.years;
        var startSelect = $('#startYear');
        var endSelect = $('#endYear');
        
        years.forEach(function(y) {
            startSelect.append(new Option(y, y));
            endSelect.append(new Option(y, y));
        });
        
        // Default to all years
        startSelect.val(years[0]);
        endSelect.val(years[years.length - 1]);
        
        function updateTable() {
            var sY = parseInt(startSelect.val());
            var eY = parseInt(endSelect.val());
            
            if (sY > eY) {
                alert("Start Year cannot be greater than End Year");
                return;
            }
            
            var tableData = [];
            for (var code in data.observatories) {
                var obs = data.observatories[code];
                var row = {
                    code: code,
                    obs: '<a href="https://sbnmpc.astro.umd.edu/mpecwatch/byStation/station_' + code + '.html">' + obs.name + '</a>',
                    city: obs.city || '',
                    county: obs.county || '',
                    state: obs.state || '',
                    country: obs.country || '',
                    nmpec: 0, ndisc: 0, nNEAd: 0, nPHAd: 0, nComd: 0, nSatd: 0, nTNOd: 0, nund: 0, nintd: 0, nunkd: 0,
                    nfu: 0, nNEAfu: 0, nPHAfu: 0, nComfu: 0, nSatfu: 0, nTNOfu: 0, nunfu: 0, nintfu: 0, nunkfu: 0,
                    nffu: 0, nprecovery: 0
                };
                
                var hasData = false;
                for (var yStr in obs.years) {
                    var y = parseInt(yStr);
                    if (y >= sY && y <= eY) {
                        hasData = true;
                        var yData = obs.years[yStr];
                        row.nmpec += yData.nmpec || 0;
                        row.ndisc += yData.ndisc || 0;
                        row.nNEAd += yData.nNEAd || 0;
                        row.nPHAd += yData.nPHAd || 0;
                        row.nComd += yData.nComd || 0;
                        row.nSatd += yData.nSatd || 0;
                        row.nTNOd += yData.nTNOd || 0;
                        row.nund += yData.nund || 0;
                        row.nintd += yData.nintd || 0;
                        row.nunkd += yData.nunkd || 0;
                        row.nfu += yData.nfu || 0;
                        row.nNEAfu += yData.nNEAfu || 0;
                        row.nPHAfu += yData.nPHAfu || 0;
                        row.nComfu += yData.nComfu || 0;
                        row.nSatfu += yData.nSatfu || 0;
                        row.nTNOfu += yData.nTNOfu || 0;
                        row.nunfu += yData.nunfu || 0;
                        row.nintfu += yData.nintfu || 0;
                        row.nunkfu += yData.nunkfu || 0;
                        row.nffu += yData.nffu || 0;
                        row.nprecovery += yData.nprecovery || 0;
                    }
                }
                
                if (row.nmpec > 0 || row.ndisc > 0 || row.nfu > 0 || row.nffu > 0 || row.nprecovery > 0) {
                    tableData.push(row);
                }
            }
            
            $('#obs_table').bootstrapTable('load', tableData);
        }
        
        $('#filterBtn').click(updateTable);
        
        // Initialize table
        updateTable();
    });
    </script>
  </body>
</html>
"""

with open('../www/obs.html', 'w', encoding='utf-8') as f:
    f.write(o)
