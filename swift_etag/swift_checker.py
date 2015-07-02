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

def md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()


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

def compare_file_with_object(sc,filename,container,segments, objectname):

   swift_etag = sc.head_object(container, objectname)['etag']
    #print sc.head_object(args.container, args.object)

   #If the object has a manifest, then it is a segmented file
   if 'x-object-manifest' in sc.head_object(container, objectname):
       #Get the segment container name so that we can list the segments for the object
       segment_container_name = sc.head_object(container, objectname)['x-object-manifest'].split('/')[0]
       segment_container = []
       #List all the objects in the container and store the assosciated hash, name, bytes in a data structure
       for o in sc.get_container(segment_container_name, full_listing='True')[1]:
           x = swift_obj(o['name'],o['hash'],o['bytes'])
           segment_container.append(x)
       #Begin the segmentation locally, using the segment size obtianed from the first object in the segment container
       #Supply the segment_container data structure such that comparisons can be made between calculated hash and swift value.
       split(filename, segment_container[0].object_bytes,segments, segment_container, swift_etag)
   #The object has no manifest, therefore it is not segmented.
   else:
   #Calculate the md5hash locally and compare against the ETag.
       md5hash = md5sum(filename)
       if swift_etag == md5hash:
           print "Test: ", objectname, " || ", filename
           print "Match: " + swift_etag + " || " + md5hash
                 
       else:
           print "Error: " + swift_etag + " || " + md5hash            


def main():

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

       
    parser.add_argument('path',help='The full path to a file or directory that you would like to check against a swift object or container')
    parser.add_argument('container',help='Swift container to check')
    parser.add_argument('object_or_path', help='For file comparison this is the object name in swift to compare against. For directory comparison, this is an optional root path to append to file names during comparison',nargs='?')
    
    #group = parser.add_mutually_exclusive_group(required=True)    
    #group.add_argument('object_name',help='For file comparison this is object name. For directory comparison this ',nargs='?')
    #group.add_argument('root_path',help='For file comparison this is object name. For directory comparison this ',nargs='?')
    
    parser.add_argument('-s', action='store_true',help='write the individual segments to files on disk')
    args = parser.parse_args()
    
    try:
        sc = swift_client()
    except:
        raise_error("Swift connection failed")

    savedPath = os.getcwd()

    #If path is a directory, then scan all files and folders in directory recursively.
    head_dir = os.path.basename(os.path.normpath(args.path))
    
    
    if os.path.isdir(args.path):
        
        if not os.path.isabs(args.path):
            #Change directory to one level above search directory
            os.chdir(os.path.split(os.path.abspath(args.path))[0])
       # else:
        
        #If path is absolute path, then assume the user wants to use the absolute path as the prefix for the container object name"
        #if os.abspath(args.path):
            
        search_dir = args.path
        
        
        print "Checking directory"
        for root, dirs, files in os.walk(search_dir, topdown=True):
                #print root, "Blah root"
            #print os.path.split(root)[1], "blah2"
            print "root", root
            for name in files:
                    #print head_dir
                #cur_object = os.path.join(args.object_or_path, root.lstrip('/'), name)
                #print os.path.split(root)[1], name
                #print "THIS root", root
                
                print "blahhhhh", root, args.path, root.strip(args.path)
                 
                #If absolute path, use full path name for swift object name
                #if os.path.isabs(args.path):
                cur_object = os.path.join(root.lstrip('.').lstrip('/').lstrip('\\'),name)
                compare_file_with_object(sc, os.path.join(root,name), args.container,args.s, cur_object)
                #If relative path, use only the 
              #  else:
              #      cur_object = os.path.join(root.lstrip('/').lstrip('\\'),name)
              #      compare_file_with_object(sc, os.path.join(root,name), args.container,args.s, cur_object)

                #if args.object_or_path:
              #      compare_file_with_object(sc, os.path.join(root,name), args.container,args.s, os.path.join(args.object_or_path.strip("/"),root.lstrip('./'),name))
              #  else:
              #      compare_file_with_object(sc, os.path.join(root,name), args.container,args.s, cur_object)
        
        #If our current working directory does not equal our saved/original path, then cd back to the saved path
        if os.getcwd() != savedPath: 
            os.chdir(savedPath)
      
        
        #os.chdir(args.path)

                
            #print name
            #for name in dirs:
                #print(os.path.join(root, name))
                #print name
        
        
    #If path is a file then check only the file
    elif os.path.isfile(args.path):
        print "Checking file"
        if not args.arg3:
            raise_error("No swift object specified")
        compare_file_with_object(sc, args.path, args.container,args.s, args.object_or_path)

    
    exit

    #print sc.get_account()[1]

if __name__ == "__main__":
    main()
