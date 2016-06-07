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

do_ssh $node lscpu > $TMP

SOCKETS=$(cat $TMP | grep 'Socket(s):' | cut -f2 -d ':' | tr -d ' ')
CORES=$(cat $TMP | grep 'Core(s) per socket:' | cut -f2 -d ':' | tr -d ' ')
THREADS=$(cat $TMP | grep 'Thread(s) per core:' | cut -f2 -d ':' | tr -d ' ')
MODEL=$(cat $TMP | grep 'Vendor ID' | cut -f2 -d ':' | sed 's/^ *//g')
MEMTOTAL=$(do_ssh $node free -m | grep Mem: | awk '{ print $2 }')

if [ $2 ]; then
  do_ssh $node "cat /etc/nova/nova.conf" > $TMP
  CPU_RATIO=$(cat $TMP | grep cpu_allocation_ratio | cut -f2 -d '=' | cut -f1 -d '.')
else
  CPU_RATIO=1
fi


echo $1 $(($SOCKETS * $CORES * $THREADS * $CPU_RATIO)) $(($MEMTOTAL / 1000)) $MODEL
