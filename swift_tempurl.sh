#!/bin/bash
#Author: Justin Mammarella
#Date: June 2016
#Description: Generate a TempURL for swift download

if [ -z '$@' ]; then
  echo "Usage:"
  echo "$(basename $0) <CONTAINER> <OBJECT_PATH>"
  exit 1
fi

if [ -z $OS_REGION_NAME ]; then
  echo "OpenStack Credentials must be sourced." 
  exit 1
fi

SECONDS=$((7 * 24 * 60 * 60))
CONTAINER=$1 
OBJECT_PATH=$2

ACCOUNT=$(swift stat | grep Account: | cut -f2 -d':' | tr -d ' ')
KEY=$(swift stat | grep Temp-Url-Key | cut -f2 -d ':' | tr -d ' ')

if [ -z $KEY ]; then
  echo "You need to set a key for decrypting the temp-URL"
  echo "swift post -m 'Temp-URL-Key:<secret>"
  exit 1
fi

if [ $OS_REGION_NAME == "VicNode" ]; then
   url="vicnode"
else
   url="swift"
fi

echo https://$url.rc.nectar.org.au:8888$(swift tempurl GET $SECONDS /v1/$ACCOUNT/$CONTAINER/$OBJECT_PATH $KEY)
