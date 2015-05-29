#!/bin/bash
USER_NAME=$1
VM_ID=$2
VM_NAME=$3
VM_IP=$4
LINK_1=$5
LINK_2=$6

cat << EOF

Attention $USER_NAME,

Your VM: $VM_ID has been detected as being compromised and has been suspended.

Suspended VMs will be deleted after 2 weeks of receiving this notification email. 

The details of the compromised VM are listed below

Compromised VM: 
ID: $VM_ID
NAME: $VM_NAME
IP: $VM_IP 

The root and ephermal disks of the compromised VM have been extracted and can be downloaded using the links below.

If you have any queries regarding this, please contact us by email: support@rc.nectar.org.au
noting the details above.

Root Disk:
$LINK_1

Ephemeral Disk:
$LINK_2

Regards,

The NeCTAR Research Cloud Support Team

EOF
