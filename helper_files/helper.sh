#!/bin/bash

#Justin Mammarella 06/11/2014

#Helper functions called in by other scripts.

#TRAP: Kill background processes, if script is terminated early.

trap "killProcess" SIGHUP SIGINT SIGTERM 

# Reset
NoColor='\e[0m'       # Text Reset

# Regular Colors
Black='\e[0;30m'        # Black
Red='\e[0;31m'          # Red
Green='\e[0;32m'        # Green
Yellow='\e[0;33m'       # Yellow
Blue='\e[0;34m'         # Blue
Purple='\e[0;35m'       # Purple
Cyan='\e[0;36m'         # Cyan
White='\e[0;37m'        # White

#Initialise Process Array

process[0]=-1
processcount=0

addProcess() {
    if [ ! -z $1 ]; then 
    #process+=$1
    process[$processcount]=$1

    echo "Added Process: " ${process[$processcount]}
    processcount=`expr $processcount + 1`
    fi
}

killProcess() {
    if [ "$processcount" -gt "0" ]; then
    for i in "${process[@]}"
        do
                if [ "$i" -gt "0" ]; then
                  echo "Killing PID: " $i 
                  sudo kill -9 $i
        fi
    done
    fi
}


ssh_tunnel() {

        echo -e "\n${Green}Establish Tunnel Link${NoColor}\n"

        tunnel=$1
        destination=$2
        destination_user=$3
        localport=$4
        
        
       (ssh -AL $localport:$destination:22 $tunnel -Nf)  
       # & pid_tmp2=$!
       # addProcess pid_tmp2
        #ssh -i ~/.ssh/nectar_jm $destination_user@localhost -p $localport exit
        ssh  localhost -p $localport exit
        

        addProcess $(ps ax | grep "ssh -AL $localport:$destination:22 $tunnel -Nf" | head -1 | cut -f1 -d' ')
        
        if [ $? -eq 0 ]; then
            echo "Connection to $2 via $tunnel worked!"
        #    echo "Tunnel has been established. Please connect by ssh user_destination@localhost -p $3"
            return 0
        else
            echo -e "${Red}Tunnel Failed to connect${NoColor}"
            cleanUp;
            return 1 
        fi

}

prompt_user() {
    read -n1 -r -p "$1"
}

calc() {
        echo awk \'BEGIN { print "$@" }\' | /bin/bash 
}

get_integer() {
   echo $(echo "$1" | cut -f1 -d'.')
}

#Draw a Progress Bar on screen
#progressbar <a> <b>
#where a is number of items so far.
#b is total items
progressbar() {


 
    #Cut out any decimal places to allow interger comparison

    arg1=$(get_integer "$1")
    arg2=$(get_integer "$2")
   
    #We do not want the progress bar extending over 100%, thus
    #we prevent the first argument from being larger than the second.

    if [ $arg1 -gt $arg2 ]; then
            arg1=$2
    else
            arg1=$1
    fi

    clc=$(calc "$arg1 / $arg2 * 100")
    clc=$(get_integer $clc)
                    
    clc2=$(calc "$clc / 2") 
    clc2=$(get_integer $clc2)
                                
    bar=""
    a=0

    while [ $a -lt $clc2 ]; do
        bar=$bar'='
        a=`expr $a + 1`
    done
    
    a=0
    
    while [ $a -lt $(expr 50 - $clc2) ]; do
        bar=$bar'-'
        a=`expr $a + 1`    
    done


    echo -n "$clc% [ $bar ] " 

}
get_vm_virshname() {
        echo $(nova show $1 | grep "OS-EXT-SRV-ATTR:instance_name" | cut -f3 -d'|' | tr -d ' ')
}
get_vm_name() {
        echo $(nova show $1 | grep ' name ' | cut -f3 -d'|' | tr -d ' ')
}
get_vm_ip() {
        echo $(nova show $1 | grep IPv4 | cut -f3 -d'|' | tr -d ' ')
}

get_user_id() {
        #$1 = VM_ID
        echo $(nova show $1 | grep user_id | cut -f3 -d'|' | tr -d ' ')
}

get_user_email() {
        #$1 = user_id
        echo $(keystone user-get $1 | grep email | cut -f3 -d'|' | tr -d ' ') 
}

get_user_tenant_id() {
        #$1 = user_id
        echo $(keystone user-get $1 | grep tenantId | cut -f3 -d'|' | tr -d ' ') 
}

get_user_name() {
        #$1 = user_id
        tenantid=$(get_user_tenant_id $1) 
        echo $(keystone tenant-get $tenantid | grep description | cut -f3 -d'|' | cut -f1 -d"'") 
}
check_admin_credentials() {
    
        
    if [ "$OS_USERNAME" = "admin-melbourne" ] && [ "$OS_TENANT_ID" = "2" ]; then
            echo "Admin Credentials Supplied"
            return 0
        else
            echo "Admin Credentials Not supplied"        
            return 1
    fi;


}

get_volumes() {
        if [ -z check_admin_credentials ]; then
            return 1
        fi

        if [ -z $1 ]; then
            echo "No VM ID supplied"    
            return 1
        else
            nova show $1 |  grep "OS-EXT-SRV-ATTR:hypervisor_hostname" | cut -f3 -d'|' | tr -d ' ' 
                
        fi

}

getNode() {

        if [ -z check_admin_credentials ]; then
            return 1
        fi
        
        if [ -z $1 ]; then
            echo "No VM ID supplied"    
            return 1
        else
            nova show $1 |  grep "OS-EXT-SRV-ATTR:hypervisor_hostname" | cut -f3 -d'|' | tr -d ' ' 
                
        fi

}

