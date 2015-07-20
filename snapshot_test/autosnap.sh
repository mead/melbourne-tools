#!/bin/bash
#Host
HOST=qh2-rcc48
NO_OF_SIMULTANEOUS_SNAPS=4
DATE=`date +"%H%M%S"`
OPENRC=/home/jmammarella/openstack/nectar_tenant-openrc.sh
MAX_NO_OF_SNAPS=10000
REST=60
#LIST RUNNING VMS
source $OPENRC
count=0

echo "AUTOSNAP"
nova list
while [ $count -lt $MAX_NO_OF_SNAPS ]; do
    echo "$count of $MAX_NO_OF_SNAPS" | tee -a log
    nova list --host $HOST | grep ACTIVE | grep -v image_ | cut -f2 -d'|' | tr -d ' ' > running_vms

    if [ $(nova list --host $HOST | grep image_ | wc -l) -lt $NO_OF_SIMULTANEOUS_SNAPS ]; then
        name=bug_test_$DATE_$(head -n 1 running_vms)
        echo $name | tee -a log
        nova image-create $(head -n 1 running_vms) $name | tee -a log
    fi
    echo "RESTING FOR $REST" | tee -a log
    sleep $REST;
    count=`expr $count + 1` 
done
#while read vm; do 
#    echo $vm
#done < <(cat running_vms)


