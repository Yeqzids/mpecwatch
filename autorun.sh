cd /home/qye/mpec
python proc.py "$(date +'%Y%m')"
python mpccode.py
cd makepages
python home_stat.py
python MPECTally.py
python home.py
python obscode_stat.py
python browser.py
python mpc_stat.py
python StationPage.py
python Individual_OMF.py
python Overall_OMF.py
python TopObjectsObs_PieChart.py
python stats.py
python survey.py
python ObjectPage.py
cp *.html ../www
cp -r /home/qye/mpec/www/ /an/chiron~4/qye/mpecwatch
