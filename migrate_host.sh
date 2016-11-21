#!/bin/bash
#Author: Justin Mammarella:
#Date:   Nov 2016
#Desc:   Migrate all VMs from source_host to destination_host. 
#        If no destination host is provided the global scheduler will select the dest host.
#Usage: ./migrate_hosts source_host <destination_host> <migrate_stopped_vms>
#
#Example: ./migrate_hosts qh2-rcc30 qh2-rcc40
#         Migrate all vms from qh2-rcc30 to qh2-rcc40
#Example: ./migrate_hosts qh2-rcc55 - 1
#         Migrate all vms from qh2-rcc55 to a random host in the az. Stopped VMs will be started, migrated then shutdown

SOURCE=$1
if [ "$2" != "-" ]; then
DEST=$2
fi

EXCLUDE=$3
TMP=tmpfile
spinner="-/|\\"
if [ -z $3 ]; then
nova list --all-tenants --host $SOURCE | grep Running | cut -f2 -d' ' > hosts_to_migrate
else
nova list --all-tenants --host $SOURCE | grep -e Running -e Shutdown | cut -f2 -d' ' > hosts_to_migrate
fi
no_of_vms=$(cat hosts_to_migrate | wc -l)
failed=0
unknown=0
while read -r vm; do
        
    flavor=$(nova show $vm | grep flavor | cut -f3 -d'|' | awk '{ print $1 }')

    echo "Attempting to migrate: $vm from $SOURCE to $DEST"
    turnoff=0
	nova show $vm > $TMP
    vm_state=$(cat $TMP | grep OS-EXT-STS:vm_state | cut -f3 -d '|' | tr -d ' ')
    turnoff=0
	if [ "$vm_state" == "stopped" ]; then
	  echo Starting $vm so that we can live migrate it.
	  nova start $vm
	  turnoff=1
	  sleep 8;
	fi

    nova live-migration $vm $DEST
    complete=0
    
    #if [ "$flavor" != "m1.small" ]; then
    #    echo -e "\Skipping flavor not small"
    #    complete=1
    #fi

    count=0
    migrating=0
    success=0
    while [ $complete -eq 0 ]; do

            spinner=$(echo -n $spinner | tail -c 1)$(echo -n $spinner | head -c 3)                    
    
            timeout=0
            nova show $vm > $TMP
            task_state=$(cat $TMP | grep OS-EXT-STS:task_state | cut -f3 -d '|' | tr -d ' ')
            vm_state=$(cat $TMP | grep OS-EXT-STS:vm_state | cut -f3 -d '|' | tr -d ' ')
			progress=$(cat $TMP | grep progress | cut -f3 -d '|' | tr -d ' ')

            if [ "$vm_state" == "error" ]; then
                echo -e "\nMigration Error"
                nova show $vm
                complete=1
            fi; 

            if [ "$task_state" == "-" ]; then
            
                if [ $migrating -eq 1 ]; then
            
                    complete=1
                    new_host=$(nova show $vm | grep OS-EXT-SRV-ATTR:host | cut -f3 -d '|' | tr -d ' ')
            
                    if [ "$new_host" != "$1" ]; then
                        success=1
                        echo -e "\n$vm succesfully migrated to $new_host"
                    else
                        echo -e "\n$vm failed migrating"
                        success=0
                    fi;
                    if [ $turnoff == 1 ]; then
                        echo Stopping $vm
                        nova stop $vm
                    fi
            
                fi
            fi
            if [ "$success" != "1" ]; then
                if [ "$task_state" == "migrating" ]; then
                    echo -ne "\rmigrating $(echo -n $spinner | head -c 1) $progress%"
                    migrating=1
                fi
                count=$(expr $count + 1) 
                #If the task state of the migrating instance doesn't change within 5 seconds, 
                #then it likely error'd too fast
                if [ $count -gt 5 ] && [ "$task_state" != "migrating" ]; then
                    echo -e "\nInstance migration failed instantaneously, check compute host"
                    failed=`expr $failed + 1`
                    complete=1
                    if [ $turnoff == 1 ]; then
                        echo Stopping $vm
		                nova stop $vm
                	fi
                fi
                if [ $count -gt 300 ]; then
                    echo -e "\nMigration Timed Out: Manually Check $vm"
                    unknown=`expr $unknown + 1`
                    complete=1
					if [ $turnoff == 1 ]; then
                        echo Stopping $vm
						nova stop $vm
					fi
                    
                fi
            fi 
    done

done < <(cat hosts_to_migrate)
echo " "
echo "Migration Complete"
echo "Failed: $failed"
echo "Migrated: $(expr $no_of_vms - $failed - $unknown)"
echo "Unknown State: $unknown"
