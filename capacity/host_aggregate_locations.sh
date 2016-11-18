#!/bin/bash
#Author: Justin Mammarella
#Date: June 2016

ZONES="nectar!melbourne!qh2@production nectar!melbourne!np@production nectar!qh2-uom@production nectar!qh2-uom@preprod nectar!qh2-uom@maintenance"

for zone in $ZONES; do
    echo $zone
    for host in $(nova aggregate-details $zone | grep $zone | cut -f5 -d'|' | tr -d ',' | tr -d "\'"); do
        echo $host
    done
done
