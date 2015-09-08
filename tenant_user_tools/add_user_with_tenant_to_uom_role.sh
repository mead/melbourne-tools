#!/bin/bash

UOM_ROLE="78ef989041884cfda970e13b8183ddac"
PREPROD_ROLE="e6f719ff04d742f4a32402ea4c79f7f7"

keystone user-role-add --user $1 --tenant $2 --role $UOM_ROLE
sleep 1
keystone user-role-add --user $1 --tenant $2 --role $PREPROD_ROLE

