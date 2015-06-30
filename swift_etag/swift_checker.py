#!/usr/bin/python

#Author: Justin Mammarella
#Organisation: University of Melbourne
#Date: 25/05/2015
#Description: Segment a local file and calculate MD5 checksums of each segment.
#             Calculate OpenStack Swift Etag Checksum for segments
#             Useful for validating uploaded segmented objects with original file.

import hashlib
import sys
import os
import math
import argparse

from swiftclient import client as swiftclient  

#MD5 Chunk size, must be a multiple of 128
#How many bytes are read per itteration.
CHUNK_SIZE=16384

class swift_obj:
        def __init__(self, object_name, object_hash, object_bytes):
            self.object_name = object_name
            self.object_hash = object_hash
            self.object_bytes = object_bytes

def raise_error(error_msg):
    print error_msg
    exit

def swift_client():

    
    auth_vars = (os.environ['OS_AUTH_URL'], os.environ['OS_REGION_NAME'], os.environ['OS_TENANT_NAME'], os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'], os.environ['OS_TENANT_ID'])
    
    for var in auth_vars:
        if not var:
            print "Missing nova environment variables, exiting."
            sys.exit(1)

    auth_url = os.environ['OS_AUTH_URL']
    auth_region_name = os.environ['OS_REGION_NAME']
    auth_tenant_name = os.environ['OS_TENANT_NAME']
    auth_username = os.environ['OS_USERNAME']
    auth_password = os.environ['OS_PASSWORD']
    auth_tenant_id = os.environ['OS_TENANT_ID']


    swift_conn = swiftclient.Connection(authurl=auth_url,
                   key=auth_password,
                   user=auth_username,
                   tenant_name=auth_tenant_name,
                   auth_version='2', os_options={'region_name': auth_region_name})
    #auth_version='2', os_options={'tenant_id': 'auth_tenant_id', 'region_name': 'auth_region_name'})

    return swift_conn

def split(filename,segment_size,create_segments, segment_container, swift_etag):
    global hash
    hash = ""
    try:
        f = open(filename, 'rb')
    except (OSError, IOError), e:
        raise_error("Could not open file")
    
    try:
        filesize = os.path.getsize(filename)
        print ""
        print "Processing: " + filename
        print "File Size (Bytes): " + str(filesize)
    except (OSError), e:
        raise_error("File size could not be determined")

    segment_count = 0
    read_bytes_total = 0

    #Total number of segments is
    number_of_segments = math.floor(filesize / segment_size) + 1

    #Hash for the complete file

    filehash = hashlib.md5();

    while segment_count < number_of_segments:

        read_bytes = 0

        segment_filename = filename + "_segment_" + str(segment_count)
        
        if create_segments:
            print "Create segment: " + segment_filename
        md5hash = hashlib.md5();
        
        #If create_segments then open a file to store current segment
        if create_segments:
            try:
                f_segment = open(segment_filename, 'wb')
            except (OSError, IOError), e:
                raise_error("unable to create new segment")
        #Adjust segment size if we're near the end of the file

        #if ((read_bytes_total + segment_size) > filesize):
        #    segment_size = filesize - read_bytes_total

        #Read and write data to each segment

        while read_bytes < segment_size:
    
            #Adjust the number of bytes to read if we're near the end of the segment
            if ((read_bytes + CHUNK_SIZE) > segment_size):
                n_bytes = segment_size - read_bytes
            else:
                n_bytes = CHUNK_SIZE
            
            #Read the bytes
            try:
                chunk = f.read(n_bytes)
                md5hash.update(chunk)
                filehash.update(chunk)
            except (OSError, IOError), e:
                raise_error("Error reading from file")
            
            if create_segments:
                #Write the bytes to segment
                try:
                    f_segment.write(chunk)
                except (OSError, IOError), e:
                    raise_error("Error writing to file")
            

            #Update number of bytes read/written
            read_bytes = read_bytes + n_bytes
            read_bytes_total = read_bytes + n_bytes

        if create_segments:
            try:
                f_segment.close()
            except (OSError, IOError), e:
                raise_error("Error closing file")
        
        md5_seg = md5hash.hexdigest()
        hash = hash + md5_seg

        if md5_seg == segment_container[segment_count].object_hash:
                print "Match: " + segment_container[segment_count].object_hash + " || " + md5_seg
                  
        else:
            print "Error: " + segment_container[segment_count].object_hash + " || " + md5_seg

        #os.remove(segment_filename)
        segment_count = segment_count + 1
     
    #print "Concatinated Etags: " + hash
    m = hashlib.md5()
    m.update(hash)
    print "Calculated MD5 Checksum: " + filehash.hexdigest()
    print " "
    print "Calculated ETag: " + m.hexdigest()
    print "Swift ETag: " + swift_etag

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filename',help='File to segment and calculate hash')
    parser.add_argument('container',help='Swift container to check')
    parser.add_argument('object',help='Object within container to compare')
    parser.add_argument('segment_size',help='Segment Size in Bytes', type=int)
    parser.add_argument('-s', action='store_true',help='write the individual segments to files on disk')
    args = parser.parse_args()
    #split(args.filename, args.segment_size,args.s)
    sc = swift_client()
    print sc.get_account()[1]
    swift_etag = sc.head_object(args.container, args.object)['etag']
    print sc.head_object(args.container, args.object)
    if 'x-object-manifest' in sc.head_object(args.container, args.object):
        print "We got a segmented object here"
        print sc.head_object(args.container, args.object)['x-object-manifest'].split('/')[0]
        segment_container_name = sc.head_object(args.container, args.object)['x-object-manifest'].split('/')[0]
        segment_container = []
        for o in sc.get_container(segment_container_name, full_listing='True')[1]:
            print o
            x = swift_obj(o['name'],o['hash'],o['bytes'])
            print x
            segment_container.append(x)
        split(args.filename, segment_container[0].object_bytes,args.s, segment_container, swift_etag)



if __name__ == "__main__":
    main()
