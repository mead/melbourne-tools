#!/bin/bash
#Author: Justin Mammarella
#Date: June 2016
#Usage: ./count_resources host-name [ use_overcommit_ratio ]
#Description: For a particular node, output the number of Virtual CPUs and Total Memory available

node=$1


TMP="/tmp/host_resources"

function do_ssh() {
   ssh -q -o StrictHostKeyChecking=no root@$1 ${@:2}
}

TOTAL_USED_RAM=0
TOTAL_USED_CPU=0

do_ssh $node 'virsh list | grep running' > $TMP
if [ $(cat $TMP | wc -l) -gt 0 ]; then
   VMS=$(cat $TMP | awk '{ print $2 }' | xargs echo)
   for domain in $VMS; do        
     #echo virsh dominfo $domain
     CPU=$(do_ssh $node "virsh dominfo $domain" | grep 'CPU(s)' | awk ' { print $2 }' ) 
     RAM=$(do_ssh $node "virsh dominfo $domain" | grep 'Max memory' | awk ' { print $3 }' ) 
     RAM_MB=$(echo "$RAM / 1024" | bc)
     TOTAL_USED_RAM=$(($RAM_MB + $TOTAL_USED_RAM))
     TOTAL_USED_CPU=$(($CPU + $TOTAL_USED_CPU))
   done < <(cat $TMP)
fi  
echo $TOTAL_USED_RAM $TOTAL_USED_CPU
