#!/bin/bash

# quick hack to open idrac console from the cli, only tested jnlp for c6320's

if [ "$1" = "-h" -o "$1" = "--help" -o "$1" = "-?" -o $# -ne 3 ]
then
  echo "usage: $(basename $0) <ip> <username> <password>"
  exit
fi

# mistyping the ip leaves java hanging around like a lost puppy
ping -c 1 -W 1 $1 &>/dev/null && (
sed -e "s/_IP_/$1/" -e "s/_USER_/$2/" -e "s/_PASS_/$3/" >~/.irac-$$ <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<jnlp codebase="https://_IP_:443" spec="1.0+">
<information>
  <title>Virtual Console Client</title>
  <vendor>Dell Inc.</vendor>
   <icon href="https://_IP_:443/images/logo.gif" kind="splash"/>
   <shortcut online="true"/>
 </information>
 <application-desc main-class="com.avocent.idrac.kvm.Main">
   <argument>ip=_IP_</argument>
   <argument>vm=1</argument>
   <argument>title=idrac+host%3A+_IP_+User%3A+_USER_</argument>
   <argument>user=_USER_</argument>
   <argument>passwd=_PASS_</argument>
   <argument>kmport=5900</argument>
   <argument>vport=5900</argument>
   <argument>apcp=1</argument>
   <argument>reconnect=2</argument>
   <argument>chat=1</argument>
   <argument>F1=1</argument>
   <argument>custom=0</argument>
   <argument>scaling=15</argument>
   <argument>minwinheight=100</argument>
   <argument>minwinwidth=100</argument>
   <argument>videoborder=0</argument>
   <argument>version=2</argument>
 </application-desc>
 <security>
   <all-permissions/>
 </security>
 <resources>
   <j2se version="1.6+"/>
   <jar href="https://_IP_:443/software/avctKVM.jar" download="eager" main="true" />
 </resources>
 <resources os="Windows" arch="x86">
   <nativelib href="https://_IP_:443/software/avctKVMIOWin32.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLWin32.jar" download="eager"/>
 </resources>
 <resources os="Windows" arch="amd64">
   <nativelib href="https://_IP_:443/software/avctKVMIOWin64.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLWin64.jar" download="eager"/>
 </resources>
 <resources os="Windows" arch="x86_64">
   <nativelib href="https://_IP_:443/software/avctKVMIOWin64.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLWin64.jar" download="eager"/>
 </resources>
  <resources os="Linux" arch="x86">
    <nativelib href="https://_IP_:443/software/avctKVMIOLinux32.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLLinux32.jar" download="eager"/>
  </resources>
  <resources os="Linux" arch="i386">
    <nativelib href="https://_IP_:443/software/avctKVMIOLinux32.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLLinux32.jar" download="eager"/>
  </resources>
  <resources os="Linux" arch="i586">
    <nativelib href="https://_IP_:443/software/avctKVMIOLinux32.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLLinux32.jar" download="eager"/>
  </resources>
  <resources os="Linux" arch="i686">
    <nativelib href="https://_IP_:443/software/avctKVMIOLinux32.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLLinux32.jar" download="eager"/>
  </resources>
  <resources os="Linux" arch="amd64">
    <nativelib href="https://_IP_:443/software/avctKVMIOLinux64.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLLinux64.jar" download="eager"/>
  </resources>
  <resources os="Linux" arch="x86_64">
    <nativelib href="https://_IP_:443/software/avctKVMIOLinux64.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLLinux64.jar" download="eager"/>
  </resources>
  <resources os="Mac OS X" arch="x86_64">
    <nativelib href="https://_IP_:443/software/avctKVMIOMac64.jar" download="eager"/>
   <nativelib href="https://_IP_:443/software/avctVMAPI_DLLMac64.jar" download="eager"/>
  </resources>
</jnlp>
EOF
javaws ~/.irac-$$ &>/dev/null &
sleep 3
rm ~/.irac-$$
)

