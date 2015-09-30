#!/bin/bash
SOURCE=$1
DEST=$2

nova list --all-tenants --host $SOURCE | grep ACTIVE | cut -f2 -d' ' > hosts_to_migrate

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
            
            if [ "$task_state" == "-" ]; then
            
                if [ $migrating -eq 1 ]; then
            
                    complete=1
                    new_host=$(nova show $vm | grep OS-EXT-SRV-ATTR:host | cut -f3 -d '|' | tr -d ' ')
            
                    if [ "$new_host" != "$1" ]; then
                        success=1
                        echo "$vm succesfully migrated to $new_host" 
                    else
                        echo "vm failed migrating"
                        success=0
                    fi;
            
                fi
            fi

            if [ "$task_state" == "migrating" ]; then
                echo migrating
                migrating=1
            fi
            count=$(expr $count + 1) 
            if [ $count -gt 120 ]; then
                echo "Struggletown"
                exit
            fi
    done
    echo "Migrated: $vm from $SOURCE to $DEST"

done < <(cat hosts_to_migrate)

