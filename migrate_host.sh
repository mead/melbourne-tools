#!/bin/bash
SOURCE=$1
DEST=$2
EXCLUDE=$3

if [ -z $3 ]; then
nova list --all-tenants --host $SOURCE | grep ACTIVE | cut -f2 -d' ' > hosts_to_migrate
else
nova list --all-tenants --host $SOURCE | grep ACTIVE | grep -v $3 | cut -f2 -d' ' > hosts_to_migrate
fi

while read -r vm; do
    nova live-migration $vm $DEST
    complete=0
    count=0
    migrating=0
    success=0
    echo "Attempting to migrate: $vm from $SOURCE to $DEST"
    while [ $complete -eq 0 ]; do
            sleep 1

            task_state=$(nova show $vm | grep OS-EXT-STS:task_state | cut -f3 -d '|' | tr -d ' ')
            vm_state=$(nova show $vm | grep OS-EXT-STS:vm_state | cut -f3 -d '|' | tr -d ' ')
            if [ "$vm_state" == "error" ]; then
                echo Migration Error
                nova show $vm
                complete=1
            fi; 
            if [ "$task_state" == "-" ]; then
            
                if [ $migrating -eq 1 ]; then
            
                    complete=1
                    new_host=$(nova show $vm | grep OS-EXT-SRV-ATTR:host | cut -f3 -d '|' | tr -d ' ')
            
                    if [ "$new_host" != "$1" ]; then
                        success=1
                        echo "$vm succesfully migrated to $new_host" 
                    else
                        echo "$vm failed migrating"
                        success=0
                    fi;
            
                fi
            fi

            if [ "$task_state" == "migrating" ]; then
                echo migrating
                migrating=1
            fi
            count=$(expr $count + 1) 
            #If the task state of the migrating instance doesn't change within 5 seconds, 
            #then it likely error'd too fast
            if [ $count -gt 5 ] && [ "$task_state" != "migrating" ]; then
                echo "Instance migration failed instantaneously, check compute host"
                complete=1
            fi
            if [ $count -gt 120 ]; then
                echo "Struggletown"
                exit
            fi
    done

done < <(cat hosts_to_migrate)

