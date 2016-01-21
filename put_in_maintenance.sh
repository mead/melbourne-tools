#!/bin/bash
#Move host from Production to Maintenance aggregate
#Usage $1 = cell $2 = hostname

if [ "$1" == "np" ]; then
    prod='nectar!melbourne!np@production'
    main='nectar!melbourne!np@maintenance'
fi

if [ "$1" == "qh2" ]; then
    prod='nectar!melbourne!qh2@production'
    main='nectar!melbourne!qh2@maintenance'
fi

if [ "$1" == "qh2-uom" ]; then
    prod='nectar!qh2-uom@production'
    main='nectar!qh2-uom@maintenance'
fi

if [ -z "$(nova aggregate-details $prod | grep $prod | grep $2)" ]; then
    echo Host $2 is not in Prod
else
    echo Moving $2 in to $main
    nova aggregate-remove-host $prod $2
    nova aggregate-add-host $main $2
fi
