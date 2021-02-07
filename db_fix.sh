#!/usr/bin/bash

# fix odd MPEC errors in the MPEC DB file

sqlite3 mpecwatch.db "update MPEC set Title = 'ADES SUBMISSIONS AND THE NEW PROCESSING PIPELINE' where MPECId = 'MPEC 2018-N52'"
