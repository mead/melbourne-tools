#!/bin/bash
#Launches N * VMs on a host and checks to see if they have network
#Useful for determining inconsitant network behaviour or even metadata

HOST=$1
VMS=12
N=1
    
counter=0

while [ $counter -lt $N ]; do
    #Launch VMS
    for i in `seq 1 $VMS`; do 
        
        if [ $i -eq $VMS ]; then
            nova boot --key nectar_jm --image eeedf697-5a41-4d91-a478-01bb21e32cbe --flavor "m1.small" --availability-zone melbourne-qh2:$HOST "$HOST $i dpp_net_stress_test" --poll | grep -e "Server building... 100% complete" -e " id " ;     
        else
            nova boot --key nectar_jm --image eeedf697-5a41-4d91-a478-01bb21e32cbe --flavor "m1.small" --availability-zone melbourne-qh2:$HOST "$HOST $i dpp_net_stress_test" | grep -e "Server building... 100% complete" -e " id " ;  
        fi
    done
    #for i in `seq 1 $VMS`; do nova boot --key nectar_jm --image eeedf697-5a41-4d91-a478-01bb21e32cbe --flavor "m1.small" --availability-zone melbourne-qh2:$HOST "$HOST $i dpp_net_stress_test" | grep -e "Server building... 100% complete" -e " id " ; done
    
    #Wait for VMs to initialise
    echo Sleeping For 10 seconds..
    sleep 10
    #NMAP scan VMs to determine if network is okay
    while read -r ip; do nmap $ip | grep "Nmap scan report" -A 1; done < <(nova list | grep "dpp_net_stress_test" | cut -f7 -d'|' | cut -f2 -d'=')

    #while read -r ip; do nmap $ip; done < <(nova list | grep "dpp_net_stress_test" | cut -f7 -d'|' | cut -f2 -d'=')
    #Delete VMs
    while read -r vm; do nova delete $vm; done < <(nova list | grep "dpp_net_stress_test" | grep -v "deleting" | awk '{print $2}')
    counter+=1
done;
