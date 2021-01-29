#!/usr/bin/bash

start=2011-01-01
end=2020-07-31

start=$(date -d $start +%Y%m%d)
end=$(date -d $end +%Y%m%d)

while [[ $start -le $end ]]
do
	python proc.py ${start:0:6}
	start=$(date -d"$start + 1 month" +"%Y%m%d")
done
