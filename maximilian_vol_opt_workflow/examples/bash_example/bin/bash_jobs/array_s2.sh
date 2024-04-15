#!/bin/bash
vol_devs=(-10 -5 -1 1 5 10)

for i in $(seq 0 5)
do
echo $i
sh "../bin/vol_opt_s2.sh" "calc/conc_05/sqs_0" ${vol_devs[$i]}

done