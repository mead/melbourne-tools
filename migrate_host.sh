#!/bin/bash
#Author: Justin Mammarella:
#Date:   Dec 2015
#Desc:   Migrate all VMs from source_host to destination_host. 
#        If no destination host is provided the global scheduler will select the dest host.
#        Third parameter is a VM UUID to exclude (Useful if things get stuck)
#Usage: ./migrate_hosts source_host <destination_host> <exclude_vm>

SOURCE=$1
DEST=$2
EXCLUDE=$3

spinner="-/|\\"

if [ -z $3 ]; then
nova list --all-tenants --host $SOURCE | grep ACTIVE | cut -f2 -d' ' > hosts_to_migrate
else
nova list --all-tenants --host $SOURCE | grep ACTIVE | grep -v $3 | cut -f2 -d' ' > hosts_to_migrate
fi

no_of_vms=$(cat hosts_to_migrate | wc -l)
failed=0
unknown=0
while read -r vm; do
    
    nova live-migration $vm $DEST
    
    complete=0
    count=0
    migrating=0
    success=0

    echo "Attempting to migrate: $vm from $SOURCE to $DEST"
    
    while [ $complete -eq 0 ]; do

            spinner=$(echo -n $spinner | tail -c 1)$(echo -n $spinner | head -c 3)                    
    
            sleep .3
            timeout=0
    
            task_state=$(nova show $vm | grep OS-EXT-STS:task_state | cut -f3 -d '|' | tr -d ' ')
            vm_state=$(nova show $vm | grep OS-EXT-STS:vm_state | cut -f3 -d '|' | tr -d ' ')
    
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
            
                fi
            fi

            if [ "$task_state" == "migrating" ]; then
                echo -ne "\rmigrating $(echo -n $spinner | head -c 1)"
                migrating=1
            fi
            count=$(expr $count + 1) 
            #If the task state of the migrating instance doesn't change within 5 seconds, 
            #then it likely error'd too fast
            if [ $count -gt 5 ] && [ "$task_state" != "migrating" ]; then
                echo -e "\nInstance migration failed instantaneously, check compute host"
                failed=`expr $failed + 1`
                complete=1
            fi
            if [ $count -gt 300 ]; then
                echo -e "\nMigration Timed Out: Manually Check $vm"
                unknown=`expr $unknown + 1`
                complete=1
            fi
    done

done < <(cat hosts_to_migrate)
echo " "
echo "Migration Complete"
echo "Failed: $failed"
echo "Migrated: $(expr $no_of_vms - $failed - $unknown)"
echo "Unknown State: $unknown"
