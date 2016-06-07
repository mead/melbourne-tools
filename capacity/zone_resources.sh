#!/bin/bash
#Author: Justin Mammarella
#Date: June 2016
#Usage: ./zone_resources [ use_cpu_overcommit_ratio ]
#Description: For each zone calculate total number Virtual Cpus and Memory available
#Requirements: Source admin credentials

ZONES="nectar!melbourne!qh2@production nectar!melbourne!np@production nectar!qh2-uom@production"

TOTAL_CORES=0
TOTAL_MEM=0

for zone in $ZONES; do
    echo "Counting Resource for: $zone"
    CORES=0
    MEM=0
    for host in $(nova aggregate-details $zone | grep $zone | cut -f5 -d'|' | tr -d ',' | tr -d "\'"); do
            output=$(./count_resources.sh $host $1)
            echo $output
            CORES=$(($(echo $output | awk '{ print $2 }') + $CORES))
            MEM=$(($(echo $output | awk '{ print $3 }') + $MEM))
        done
    TOTAL_CORES=$(($CORES + $TOTAL_CORES))
    TOTAL_MEM=$(($MEM + $TOTAL_MEM))
    echo "Virtual Cores: $CORES"
    echo "Mem (GB): $MEM"
done

echo " "

if [ $1 ]; then
    echo "Total Virtual Cores (Overcommited): $TOTAL_CORES" 
else
    echo "Total Virtual Cores (GB): $TOTAL_CORES" 
fi
echo "Total Mem: $TOTAL_MEM"

