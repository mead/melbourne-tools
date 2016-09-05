#!/bin/bash
# Author: Justin Mammarella
# Date:  Aug/2016
# Description: Script to add hosts to the midonet tunnel-zone

TUNNEL_ZONE=$(midonet-cli -e list tunnel-zone | awk '{ print $2 }')
while read -r line; do
         echo $line
         ip=$(echo $line | awk '{ print $6 }')
         host=$(echo $line | awk '{ print $4 }')

         echo $ip      
         #Regex host filter. Edit me.
         if [[ $ip =~ .*10\.241\.81\..* ]]; then
            echo "Deleting $ip $host"
            midonet-cli --eval tunnel-zone $TUNNEL_ZONE delete member host $host
         fi
 #       echo $hostname_name $hostname_uuid $ip 
  #      fi;        
#        midonet-cli --eval tunnel-zone $TUNNEL_ZONE add member host $hostname_uuid address $ip

done < <(midonet-cli --eval tunnel-zone $TUNNEL_ZONE member list)


