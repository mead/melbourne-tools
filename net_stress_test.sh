#!/bin/bash
#Launches N * VMs on a host and checks to see if they have network
#Useful for determining inconsitent network behaviour or even lack of metadata

HOST=$1
CELL=melbourne-qh2
VMS=10
N=1
IMAGE=ed01445a-792e-4a69-8868-9ffa5e7e0c06
    
counter=0

while [ $counter -lt $N ]; do
    echo Launching VMS
    for i in `seq 1 $VMS`; do 
        
        if [ $i -eq $VMS ]; then
            echo Polling last VM..
            nova boot --key nectar_jm --image $IMAGE --flavor "m1.small" --availability-zone $CELL:$HOST "$HOST $i dpp_net_stress_test" --poll | grep -e "Server building... 100% complete" -e " id " ;     
        else
            nova boot --key nectar_jm --image $IMAGE --flavor "m1.small" --availability-zone $CELL:$HOST "$HOST $i dpp_net_stress_test" | grep -e "Server building... 100% complete" -e " id " ;  
        fi
    done
    #for i in `seq 1 $VMS`; do nova boot --key nectar_jm --image eeedf697-5a41-4d91-a478-01bb21e32cbe --flavor "m1.small" --availability-zone melbourne-qh2:$HOST "$HOST $i dpp_net_stress_test" | grep -e "Server building... 100% complete" -e " id " ; done
    
    echo Wait for VMs to initialise

    while [ $(nova list | grep -e dpp_net_stress_test | grep spawning | wc -l) -gt 0 ]; do
        sleep 1
    done
    
    #Sleep for a bit more to give network time to come up

    sleep 60

    #NMAP scan VMs to determine if network is okay

    echo Checking Bridge
#    for vm in $(nova list | grep "dpp_net_stress_test" | awk '{ print $2 }'); do echo $vm; ./check_bridge.sh $vm; done
#    nova list
    echo Running NMAP
    while read -r ip; do echo checking $ip; nmap $ip | grep "Nmap scan report" -A 1; done < <(nova list | grep "dpp_net_stress_test" | grep ACTIVE | cut -f7 -d'|' | cut -f2 -d'=')

    echo Ping test
    while read -r ip; do echo checking $ip; ping -i .2 -c 10 $ip | grep loss; done < <(nova list | grep "dpp_net_stress_test" | grep ACTIVE | cut -f7 -d'|' | cut -f2 -d'=')
    while read -r ip; do echo checking $ip; ping -i .2 -c 10 $ip | grep loss; done < <(nova list | grep "dpp_net_stress_test" | grep ACTIVE | cut -f7 -d'|' | cut -f2 -d'=')

    #while read -r ip; do nmap $ip; done < <(nova list | grep "dpp_net_stress_test" | cut -f7 -d'|' | cut -f2 -d'=')
    #Delete VMs
    while read -r vm; do nova delete $vm; done < <(nova list | grep "dpp_net_stress_test" | grep -v "deleting" | awk '{print $2}')
    counter+=1
done;
