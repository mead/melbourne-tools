#!/bin/bash
#Author: Justin Mammarella
#Function: Checks to see that a specific VM has a valid port mapping on the virtual bridge of the compute node.

#nova list --all-tenants --host qh2-rcc93 | grep ACTIVE | cut -f2 -d' ' | xargs -L 1 ./check_bridge.sh 

function my_ssh {
    while read line; do
        echo $line
    done < <(ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -C $1 $2) 
}

VM=$1
HOST=$(nova show $VM | grep OS-EXT-SRV-ATTR:host | cut -f3 -d'|' | tr -d ' ')
MAC=$(nova interface-list $VM | grep ACTIVE | cut -f6 -d'|' | tr -d ' ')
MAC_TAIL=$(echo $MAC | tail -c 15)
BRIDGE=$(my_ssh $HOST "brctl show | grep brq | awk '{ print \$1}'")
echo $BRIDGE
my_ssh $HOST "brctl showmacs $BRIDGE | sort" | grep $MAC_TAIL
