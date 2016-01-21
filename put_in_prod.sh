#!/bin/bash
#Move host from Maintenance to Production aggregate
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

if [ -z "$(nova aggregate-details $main | grep $main | grep $2)" ]; then
    echo Host $2 is not in Maintenance
else
    echo Moving $2 in to $prod
    nova aggregate-remove-host $main $2
    nova aggregate-add-host $prod $2
fi
