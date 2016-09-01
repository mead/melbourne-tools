#!/bin/bash
# Author: Justin Mammarella
# Date:  Aug/2016
# Description: Script to add hosts to the midonet tunnel-zone

TUNNEL_ZONE=$(midonet-cli -e list tunnel-zone | awk '{ print $2 }')
while read -r line; do
		 hostname_uuid=$(echo $line | awk '{ print $2 }') 
         hostname_name=$(echo $line | awk '{ print $4 }')
         
         #Regex host filter. Edit me.

         if [[ $hostname_name =~ .*qh2.* ]]; then

        ip_temp=$(midonet-cli -e host $hostname_uuid interface list | grep eth2.431 | cut -f2 -d'[' | cut -f1 -d']' | tr -d 'u' | tr -d "\'" | tr -d ',')
        ip_1=$(echo $ip_temp | awk '{print $1}')
        ip_2=$(echo $ip_temp | awk '{print $2}')
        if [[ $ip_1 =~ .*10.* ]]; then
         ip=$ip_1
        fi
        
        if [[ $ip_2 =~ .*10.* ]]; then
         ip=$ip_2
        fi

        echo $hostname_name $hostname_uuid $ip 

        midonet-cli --eval tunnel-zone $TUNNEL_ZONE add member host $hostname_uuid address $ip

   fi
done < <(midonet-cli --eval host list)


