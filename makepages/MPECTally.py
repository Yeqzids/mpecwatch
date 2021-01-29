#!/usr/bin/env python3

"""
 PROJECT:		MPEC Watch
 PURPOSE:		generate a static HTML page, powered by plot.ly, that shows a bar chart and a table of all MPECs listed by year

 (C) Quanzhi Ye
 
"""

import sqlite3, plotly.express as px

dbFile = 'mpecwatch.db'

fig =px.scatter(x=range(10), y=range(10))
fig.write_html("path/to/file.html")
