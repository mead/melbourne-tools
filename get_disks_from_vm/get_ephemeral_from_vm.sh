#!/bin/bash
#Author: Justin Mammarella
#Organization: University of Melbourne
#Date: May 2015 

#Summary: Script to backup root and ephemeral storage from OpenStack VMs. Disks are RSYNCED
#         from compute node to the script's host. The disks are then mounted using guestfs.
#         Once the disks are mounted the file system extracted and tar archived.
#         The archived files are uploaded to swift and a tempurl is generated for download
#         An email will be generated, and sent to the user and RT.

#Run cleanup, if script is terminated early.

trap "cleanUp 2" SIGHUP SIGINT SIGTERM  
set -e

display_help() {

echo -e "\nUsage: get_disk_from_vm [-u] [-t] [-s] [-e] [-x] [-h] <id>\n"
#echo "command -t tunnel destination_user tunnel_port -i full_path_to_identity_file VM_ID"
#echome "command -t user@tunnel.com root 5555 -i /home/user/ssh/id_rsa e2xsa3242423411a223423a12 \n"
echo -e "\t-u Generate TempURL only from Swift."
echo -e "\t-t Rsync VM disks using an SSH Tunnel" 
echo -e "\t-s Suspend and Lock the VM with id <id>"
echo -e "\t-e Email the user and generate a support ticket"
echo -e "\t-x Clean up mounts only"
echo -e "\t-h Display this help text.\n"
exit
}

tunnelon=""
clean=""
suspended=""
email=""
if [ $# -eq 0 ]; then
    display_help
    exit 
fi 

while [ $# -gt 0 ]; do
        key="$1"
        case $key in
        -h)
            display_help 
            exit
            ;;
        -t)
            shift
            tunnelon=1
#            user=$2
#            port=$3
#            shift 3 
            ;;
#        -i) shift
#            identity_file=$1
#            ;; 
        -u) shift
            url=1
            ;;   
        -s) shift
            suspended=1
            ;;
        -e) shift
            email=1
            ;;
        -x) shift
            clean=1
            ;;
        *)
            id=$1
            shift
            ;;

        esac


done

#Spinner glyph

spinner="-/|\\"

#CONFIGURATION VARIABLES:

#######################
#Tunnel Configuration
#######################
#Hostname/Ip of tunnel. Leave blank if you do not wish to tunnel into the node.

tunnel="suse" 

user="jmammarella"
port="5555"
identity_file="/home/jmammarella/.ssh/nectar_jm"

#Variables for location of OpenStack credentials.
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

rc_dir="/home/jmammarella/openstack"
admin_rc=$rc_dir/openrc-admin.sh
swift_rc=$rc_dir/nectar_image_quarantine-openrc.sh 

#Storage location of data:

mount_dir_0="/media/jmammarella/ADATANH03/vm_backup/$id"
mount_dir_1="$mount_dir_0/root"
mount_dir_2="$mount_dir_0/ephemeral"

#Instance share on node

disk_image_dir="/var/lib/nova/instances"

#Mount method fues or qemu. Qemu is deprecated.

mount_method="qemu"


#Load Helper Functions and Variables

source ../helper_files/helper.sh

#Create the Directory for the VM if it does not exist

mkdir -p $mount_dir_0 

#Switch in to the VM's directory.

cd $mount_dir_0


echome() {
    echo -e $1 | tee -a $logfile
}

#Function to suspend and lock instance


suspend_lock() {
    echo "Suspending instance $id"
    nova suspend $id
    nova lock $id
    nova meta $id set security=1
}

getdisks() {
    #If the sshtunnel variable is set, then attempt to the node through the tunnel
    if [ ! -z $tunnelon ]; then

        vecho "Creating SSH Tunnel"
        
        ssh_tunnel $tunnel $node $user $port $identity_file 
        
        if [ "$?" -gt "0" ]; then
            cleanUp 5 "SSH Tunnel Failed"
            return 1
        fi 

    #No tunnel specified, attempt to connect to the node directly.


    else

        echo "Connecting directly to node"
        ssh -i $identity_file -A root@$node exit
       
        if [ $? -eq 0 ]; then 
             echo "Direct connnection to root@$node successful."
        else
                    cleanUp 5 "Direct Connection to Node Failed"
             return 1
        fi
    fi



    echome "\nRSYNC: Establish SSH Connection to $node\n"
    echome "   Copy files from root@$node:$disk_image_dir/$id/ \n"
   
    prompt_user "Press space to continue..."
    
    if [ $(ssh root@$node -C "if [ -d $disk_image_dir/$id ]; then echo 1; fi") -eq 1 ]; then
        echo "$disk_image_dir/$id instance directory detected"
        instance_dir="$disk_image_dir/$id"
    elif [ $(ssh root@$node -C "if [ -d $disk_image_dir/$vm_virshname ]; then echo 1; fi") -eq 1 ]; then
        echo "Old VM detected, getting disk from /var/lib/nova/instances/$vm_virshname"
        instance_dir="$disk_image_dir/$vm_virshname"
    else 
        cleanUp 5 "Could not find instance directory"
        return 1
    fi

    #If the tunnel variable is set, rsync using the ssh tunnel.

    if [ ! -z $tunnelon ]; then
  
        echome "\n Using tunnel"
    

        if [ ! -e $mount_dir_0/disk ]; then 
                rsync -Pevv "ssh -A -p $port -i $identity_file" -vz localhost:$instance_dir/disk $mount_dir_0/ 
               # if [ "$?" -eq "0" ]; then
                   # cleanUp 5 'Rsync Failed: sudo rsync -Pe "ssh -p $port -i $identity_file" -vz localhost:$disk_image_dir/$id/disk $mount_dir_0/'
               # fi;
        fi
       
        if [ ! -e $mount_dir_0/disk.local ]; then
                rsync -Pevv "ssh -A -p $port -i $identity_file" -vz localhost:$instance_dir/disk.local $mount_dir_0/
               # if [ "$?" -eq "0" ]; then
                  #  cleanUp 5 'Rsync Failed: sudo rsync -Pe "ssh -p $port -i $identity_file" -vz localhost:$disk_image_dir/$id/disk.local $mount_dir_0/'
               # fi;
        
        fi
        
    else
    
    #rsync directly to node
    echome "Direct transfer"
        if [ ! -e $mount_dir_0/disk ]; then 
                rsync -Pvvz -e "ssh -A -i $identity_file" root@$node:$instance_dir/disk $mount_dir_0/
                #if [ "$?" -eq "0" ]; then
                  #  cleanUp 5 'Rsync Failed: sudo rsync -Pvz -e "ssh -i $identity_file" root@$node:$disk_image_dir/$id/disk $mount_dir_0/'
                #fi;

        fi
        if [ ! -e $mount_dir_0/disk.local ]; then
                rsync -Pvvz -e "ssh -A -i $identity_file" root@$node:$instance_dir/disk.local $mount_dir_0/
                #if [ "$?" -eq "0" ]; then
                  #  cleanUp 5 'Rsync Failed: sudo rsync -Pvz -e "ssh -i $identity_file" root@$node:$disk_image_dir/$id/disk $mount_dir_0/'
                #fi;

                    
        fi
    fi
    
    echome "\n${Green}Stage 0: Get disk data from VM $id${NoColor}\n"
    
    if [ ! -e $mount_dir_0/disk ]; then
        cleanUp 5 "File does not exist.. ssh $mount_dir_0/disk${NoColor}"
        return 1
    fi

    if [ ! -e $mount_dir_0/disk.local ]; then
        cleanUp 5 "File does not exist.. ssh $mount_dir_0/disk.local${NoColor}"
        return 1
    fi


}

mountdisks_fuse() {
    echome "\n${Green}Stage 1: Mount Disks${NoColor}\n"

    #Create the Mount Directories

    echome "Creating Mount Directory: $mount_dir_1"
    mkdir -p $mount_dir_1 
    echome "Creating Mount Directory: $mount_dir_2\n"
    mkdir -p $mount_dir_2

    echome "\nDisk 1, root, disk:"
    echome "guestmount -a disk -i $mount_dir_1 wait"
  
    guestmount -a disk -i $mount_dir_1;  wait
  
    echome "\nDisk 2, ephemeral, disk:"
    echome  "guestmount -a disk.local -m /dev/sda $mount_dir_2 wait" 
    

    guestmount -a disk.local -m /dev/sda $mount_dir_2; wait
#      if $(sudo guestmount -a disk -i $mount_dir_1; wait); then
#       echo "/dev/nbd0 created, disk mounted at $mount_dir_1"
#    else 
#       cleanUp 1 "fusefs failed"
#    fi

#    if $(sudo guestmount -a disk.local -i $mount_dir_2; wait); then
#           echo "/dev/nbd1 created, disk mounted at $mount_dir_2"
#    else 
#           cleanUp 1 "fusefs failed"
#    fi


}

mountdisks_qemu() {

    echome "\n${Green}Stage 1: Mount Disks${NoColor}\n"

    #Create the Mount Directories

    echome "Creating Mount Directory: $mount_dir_1"
    sudo mkdir -p $mount_dir_1 
    echome "Creating Mount Directory: $mount_dir_2\n"
    sudo mkdir -p $mount_dir_2

    #Load the Kernal Module

    if [ `lsmod | grep nbd | wc -l` -gt 0 ]; then

        echo "Qemu Kernal Module already loaded"
        else
        sudo modprobe nbd max_part=63   
        echo "Qemu Kernal Module loaded"
        
    fi

    #Use qemu-nbd to load the first disk image to a device
    
  #  echome "\nDisk 1, root, disk:"
    
  #  if $(sudo qemu-nbd -c /dev/nbd0 disk; wait); then
  #      echo "/dev/nbd0 created"
  #  else 
  #      cleanUp 1 "qemu1 failed"
  #      return 1
  #  fi


    #Add process of previous command to our Process Array (For termination Later)
   # addProcess $(ps ax | grep "qemu-nbd -c /dev/nbd0 disk" | head -1 | cut -f1 -d' ')
 
  #  if $(sudo mount /dev/nbd0p1 $mount_dir_1); then
  #      echome "Mount Successful: $mount_dir_1\n"
  #  elif $(sudo mount /dev/nbd0 $mount_dir_1); then
  #      echome "Mount Successful: $mount_dir_1\n"

  #  else
  #      cleanUp 1 "mount1 failed"
  #      return 1
  #  fi
            
    echo "Disk 2, ephemeral,disk.local"
    if $(sudo qemu-nbd -c /dev/nbd1 disk.local; wait); then
            
        echo "/dev/nbd1"
    else 
        cleanUp 1 "qemu2 failed"
        return 1
    fi

    #Add process of previous command to our Process Array (For termination Later)
    addProcess $(ps ax | grep "qemu-nbd -c /dev/nbd1 disk.local" | head -1 | cut -f1 -d' ')


   if $(sudo mount /dev/nbd1 $mount_dir_2); then
       echome "Mount Successful: $mount_dir_2\n"
   else
       cleanUp 1 "mount2 failed"
       return 1
   fi
    
    df -h
    
    #ps waux | grep ${process[0]}
}


create_tar() {
    
    #Remove the old log file (if it exists)
    if [ -e $1.log ]; then 
        rm $1.log
    fi
    touch $1.log
    #Remove the leading slash from the path
    path_tmp=$(echo $2 | cut -c2-)

    echome "\nCounting Files... "
    
    #Count number of files in mount directory.
    
    num_files=$( find $2 | wc -l)
   
    #Count number of directories in path 
    num_dir=$(echo $2 | grep -o '/' | wc -l)
   

    echo -ne "$num_files\n"

    #Create an archive of the mounted directory by running tar in the background
    cd $2
    #cd $path_tmp
    #echo sudo tar -vzcf $mount_dir_0/$1 --index-file $mount_dir_0/$1.log .

    #exit
   (tar -vzcf $mount_dir_0/$1 --index-file $mount_dir_0/$1.log .) & pid_tmp1=$!
   #(sudo tar -vzcf $1 --index-file $1.log -C / $path_tmp) & pid_tmp1=$!


    #Whilst the tar process is still runnning display progress:

    while [ $(ps -p $pid_tmp1 | wc -l) -gt 1 ] ; do
    #Check progress every 100ms.
        sleep 0.2
    #Count number of files processed so far.
        so_far=$(cat $mount_dir_0/$1.log | wc -l) 
    #Rotate spinner glyph
        spinner=$(echo -n $spinner | tail -c 1)$(echo -n $spinner | head -c 3)                    
      
    #Draw progress bar
        echo -ne "\r $(progressbar $so_far $num_files) $(echo -n $spinner | head -c 1) "
        echo -n "Files: $so_far/$num_files - SizeOf $1: $(du -h $mount_dir_0/$1 | cut -f1 -d$'\t') "      

    done

    #Draw the progress bar one last time to show that the tar completed correctly.

    #Draw progress bar
    echo -ne "\r $(progressbar $so_far $num_files) $(echo -n $spinner | head -c 1) "
    echo -n "Files: $so_far/$num_files - SizeOf $1: $(du -h $mount_dir_0/$1 | cut -f1 -d$'\t') "      


}

tardisks() {

    files=($mount_dir_1/*)
    files2=($mount_dir_2/*)
    
    cd $mount_dir_0

    echome "\n${Green}Stage 2: Create Compressed Archives (TAR) ${NoColor}"

    if [ ${#files[@]} -gt 0 ]; then


        echome "Creating Archive - root.tar.gz"
    
        echome "\n Files were detected in $mount_dir_1"

    #    if [ ! -e root.tar.gz ]; then 

    #    create_tar root.tar.gz $mount_dir_1


     #   else
            echo $mount_dir_0"/root.tar.gz already exists, skipping"
     #   fi
    fi

    if [ ${#files2[@]} -gt 0 ]; then
        echome "\nCreating Archive ephemeral.tar.gz"
        echome "\n Files were detected in $mount_dir_2"
       
        if [ ! -e ephemeral.tar.gz ]; then 
        
                create_tar ephemeral.tar.gz $mount_dir_2
         
        else
            echo $mount_dir_0"/ephemeral.tar.gz already exists, skipping"
        fi   
       

    fi

}


swiftupload() {
    
    if [ -e $2.swift.log ]; then 
        sudo rm $2.swift.log
    fi
    sudo touch $2.swift.log
    sudo chmod 777 $2.swift.log 

    echome "swift -v upload $1 $2 -S $3 > $2.swift.log\n"
    (swift -v upload $1 $2 -S $3 > $2.swift.log) & pid_tmp1=$!


    #Whilst the swift process is still runnning display progress:

    so_far=0
    num_seg=$(du -b $2 | cut -f1 -d$'\t') 
    num_seg=$(expr `expr $num_seg / $3` + 1)
    # num_seg=$(calc "$num_seg / $3")

    while [ $(ps -p $pid_tmp1 | wc -l) -gt 1 ] ; do
  
      #Check progress every 100ms.
        sleep 0.2
    #Count number of files processed so far.
        so_far=$( cat $2.swift.log | wc -l) 
        #Rotate spinner glyph
        spinner=$(echo -n $spinner | tail -c 1)$(echo -n $spinner | head -c 3)                    
      
    #Draw progress bar
      
        echo -ne "\r$(echo -n $spinner | head -c 1) "
        echo -n "Segments: $so_far/$num_seg - SizeOf $(du -h $2 | cut -f1 -d$'\t') "      

    done
}

swift_send() {
    echome "\n${Green}Stage 3: SWIFT Upload ${NoColor}"
    echome "\nUploading mount_dir_0/root.tar.gz to container $id " 
    cd $mount_dir_0
    swift post $id
   # if [ ! $(swift list $id | grep root) ]; then

   # swiftupload $id root.tar.gz 1147483648
   # fi


    echome "\nUploading mount_dir_0/ephemeral.tar.gz to container $id " 
    
    if [ ! $(swift list $id | grep ephemeral) ]; then
    swiftupload $id ephemeral.tar.gz 1147483648
    fi

}

swift_tempurl() {
  echome "\n${Green}Stage 4: Generating Temp URLs: ${NoColor}"

  swift list
  path_tmp=$(echo $mount_dir_0 | cut -c2-)

  authvar=$(swift stat | grep Account: | cut -f2 -d':' | tr -d ' ')
  echo https://swift.rc.nectar.org.au:8888$(swift tempurl GET 604800 /v1/$authvar/$id/"root.tar.gz" waibpobHes) | tee $d_link 
  echo https://swift.rc.nectar.org.au:8888$(swift tempurl GET 604800 /v1/$authvar/$id/"ephemeral.tar.gz" waibpobHes) | tee -a $d_link
    

}

send_email() {
        echome $d_link
        link_1=$(sed -n '1{p;q;}' $d_link)
        link_2=$(sed -n '2{p;q;}' $d_link)
        echo $DIR
        cd $DIR
        /bin/bash ./email_body.sh $user_name $id $vm_name $vm_ip $link_1 $link_2 
}
cleanUp() {

    if [ $1 == 0 ]; then
        echome "\n${Green}Success: Exiting${NoColor}"
    elif [ $1 == 2 ]; then
        echome "\n${Red}User termination.${NoColor}" 
    else
        echome "\n${Red}Error: ${NoColor} $2" 
    fi

    #Kill running processes
    if [ "$mount_method" == "qemu" ]; then

    #Unmount drives
        sudo umount -f /dev/nbd0p1; wait
        sudo umount -f /dev/nbd1; wait
    #Disconnect qemu
        sudo qemu-nbd -d /dev/nbd0
        sudo qemu-nbd -d /dev/nbd1
    
    else
    
        if [ ! -z "$(cat /proc/mounts | grep $mount_dir_1)" ]; then
                echome "Mount directory $mount_dir_1 detected.. unmounting" 
                guestunmount "$mount_dir_1"; wait
        fi
        if [ ! -z "$(cat /proc/mounts | grep $mount_dir_2)" ]; then 
                echome "Mount directory $mount_dir_2 detected.. unmounting"
                guestunmount "$mount_dir_2"; wait
        fi
    fi

      
        #  fi
    return 1
}

#Script Start:


if [ -z $id ]; then
    echome "${Red}Error: Must specify VM ID as argument${NoColor}"
    exit 1
fi 



if [ ! -z $clean ]; then
    cleanUp 0
    exit
fi

logfile="$mount_dir_0/$id.log"
d_link="$mount_dir_0/download_links"

source $admin_rc

node=$(getNode $id) 
if [ "$node" = "1" ] || [ -z $node ] ; then
        cleanUp 1 "Could not find Node"
fi

echome "\n\n"
echome "${Green}--------------------------"
echome "VM Data Backup"
echome "--------------------------\n"
echome "${NoColor}Date: $(date)" 
echome "${NoColor}VM: $id \nHosted on: $node\n"

echome "Logging to: $logfile \n"

user_id=$(get_user_id $id)
user_email=$(get_user_email $user_id)
user_name=$(get_user_name $user_id)
vm_ip=$(get_vm_ip $id)
vm_name=$(get_vm_name $id)
vm_virshname=$(get_vm_virshname $id)

echome "User: $user_name" 
echome "Email: $user_email" 
echome "ID: $user_id\n" 

nova show $id | tee -a $logfile

if [ ! -z $suspended ]; then
    suspend_lock $id
    sleep 10
    nova show $id 
fi

#If local files do not exist... rsync files from node

if [ -z $url ]; then 
    cd $mount_dir_0
   
    if [ ! -e root.tar.gz ] || [ ! -e ephemeral.tar.gz ]; then  
    
        getdisks $node $user $port
        if [ $? -ne 0 ]; then exit; fi


        if [ "$mount_method" == "fuse" ]; then
            if [ -z "$(groups $(whoami) | grep fuse)" ]; then
                cleanUp 1 "Add user to fuse group"
            fi
            mountdisks_fuse
            if [ $? -ne 0 ]; then exit; fi


        else
            mountdisks_qemu 
            if [ $? -ne 0 ]; then exit; fi            
        fi

        sleep 5
        tardisks
        if [ $? -ne 0 ]; then exit; fi

    else
        echome "\n${Orange}Tar files detected in $mount_dir_0\nSkipping Stages 1 and 2${NoColor}"
    fi
    
fi
    source $swift_rc
if [ -z $url ]; then
    swift_send
    if [ $? -ne 0 ]; then exit; fi 
fi

swift_tempurl
if [ $? -ne 0 ]; then exit; fi


if [ -z $email ]; then
    send_email
 
fi

sleep 1
cleanUp 0 
