#!/usr/bin/python

#Name: SwiftChecker
#Author: Justin Mammarella
#Organisation: University of Melbourne
#Date: 01/06/2015
#Description: Compare local files or folders with objects stored in swift containers 
#             SwiftChecker detects whether or not a swift object is stored as a segmented
#             object. If the object is segmented, the local file is segmeneted and 
#             the individual md5 hashes for each segment are calculated. The swift
#             ETag value is also calculated locally, by hashing a concatinated string of 
#             the segement hashes.
#             The ETag and segment hashes are used to compare the local file against the 
#             external swift object
#
#             SwiftChecker supports full directory scanning. Meaning, each file in a specfied
#             directory is compared against objects stored in a swift container.

import hashlib
import sys
import os
import math
import argparse
import textwrap

from swiftclient import client as swiftclient  

#MD5 Chunk size, must be a multiple of 128
#How many bytes are read per itteration.
CHUNK_SIZE=16384
OUTPUT_FORMAT = '{: <5} {: <4} {: >1} {: >32} {: >3} {: <32}' 

class swift_obj:
        def __init__(self, object_name, object_hash, object_bytes):
            self.object_name = object_name
            self.object_hash = object_hash
            self.object_bytes = object_bytes

def raise_error(error_msg):
    print error_msg
    exit
    #sys.exit(1)

def display_break(c):
    width = len(OUTPUT_FORMAT.format("","","","","",""))
    print c * width

def display_header():
    display_break('=')
    display_output("", "", "Local File", "Swift Object")
    display_break('=')
#print header

def display_output(column1,column2,column3,column4):
    print OUTPUT_FORMAT.format(column1, column2, "|",  column3, " | ", column4)

def swift_client(config_file):
    if config_file:
        with open(config_file,'r') as f:
            for line in f:
                firstword = line.split(' ')[0] 
                if firstword == "export":
                    line = line.replace("\n",'').replace('"','')
                    n = line.split(' ')[1].split('=')[0]
                    m = line.split('=')[1] 
                    if n == "OS_USERNAME":
                        auth_username = m
                    if n == "OS_PASSWORD":
                        auth_password = m 
                    if n == "OS_TENANT_ID":
                        auth_tenant_id = m
                    if n == 'OS_TENANT_NAME':
                        auth_tenant_name = m
                    if n == 'OS_REGION_NAME':
                        auth_region_name = m
                    if n == 'OS_AUTH_URL':
                        auth_url = m

        auth_vars = (auth_username, auth_password, auth_tenant_id, auth_tenant_name, auth_region_name, auth_url)

    else: 
        auth_url = os.environ['OS_AUTH_URL']
        auth_region_name = os.environ['OS_REGION_NAME']
        auth_tenant_name = os.environ['OS_TENANT_NAME']
        auth_username = os.environ['OS_USERNAME']
        auth_password = os.environ['OS_PASSWORD']
        auth_tenant_id = os.environ['OS_TENANT_ID']

        auth_vars = (os.environ['OS_AUTH_URL'], os.environ['OS_REGION_NAME'], os.environ['OS_TENANT_NAME'], 
                        os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'], os.environ['OS_TENANT_ID'])
    for var in auth_vars:
        if not var:
            print "Missing openstack environment variables, try sourcing your openrc file, exiting."
            sys.exit(1)

    try: 
        swift_conn = swiftclient.Connection(authurl=auth_url,
                       key=auth_password,
                       user=auth_username,
                       tenant_name=auth_tenant_name,
                       auth_version='2', os_options={'region_name': auth_region_name})
    except:
        error_dict = vars(sys.exc_info()[1])
        print error_dict
        sys.exit(1)

    return swift_conn

def md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()


def split(filename,segment_size, segment_container):
    hash = ""
    try:
        f = open(filename, 'rb')
    except (OSError, IOError), e:
        raise_error("Could not open file")
    
    try:
        filesize = os.path.getsize(filename)
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
        
        md5hash = hashlib.md5();
        
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
            
            #Update number of bytes read/written
            read_bytes = read_bytes + n_bytes
            read_bytes_total = read_bytes + n_bytes

        md5_seg = md5hash.hexdigest()
        hash = hash + md5_seg

        if verbose_mode == 2:
            if md5_seg == segment_container[segment_count].object_hash:
                display_output("Seg: ", segment_count, segment_container[segment_count].object_hash, md5_seg)
                  
            else:
                display_output("Err: ", segment_count, segment_container[segment_count].object_hash, md5_seg)

        #os.remove(segment_filename)
        segment_count = segment_count + 1
     
    #print "Concatinated Etags: " + hash
    m = hashlib.md5()
    m.update(hash)
    
    if verbose_mode == 2:
        display_break('-')
        display_output("MD5:","", filehash.hexdigest(),"")  
    
    return m.hexdigest()

def compare_file_with_object(sc,filename,container, objectname):
        
    #print sc.head_object(args.container, args.object)
    try:
        swift_etag = sc.head_object(container, objectname)['etag']
    #If the object has a manifest, then it is a segmented file
        if 'x-object-manifest' in sc.head_object(container, objectname):           
            if verbose_mode == 2:
                print "Calculating Segments: "
            if verbose_mode != 0:
                display_header()

        #Get thesegment container name so that we can list the segments for the object

            segment_container_name = sc.head_object(container, objectname)['x-object-manifest'].split('/')[0]
            segment_container = []
    #List all the objects in the container and store the assosciated hash, name, bytes in a data structure
            for o in sc.get_container(segment_container_name, full_listing='True')[1]:
                x = swift_obj(o['name'],o['hash'],o['bytes'])
                segment_container.append(x)
    #Begin the segmentation locally, using the segment size obtianed from the first object in the segment container
    #Supply the segment_container data structure such that comparisons can be made between calculated hash and swift value.
            local_hash = split(filename, segment_container[0].object_bytes, segment_container)
    #The object has no manifest, therefore it is not segmented.
            
        else:
    #Calculate the md5hash locally and compare against the ETag.
            local_hash = md5sum(filename)
    
        swift_etag = swift_etag.strip('"')

        if verbose_mode == 1:
            display_output("ETag:","", swift_etag, local_hash)
            display_break("-")
        
        if swift_etag == local_hash:
            return 0
        else:
            return 1

    except:
        print sys.exc_info()
        error_dict = vars(sys.exc_info()[1])
        if error_dict['http_reason'] == 'Not Found':
            print "Swift Error: object not found,", objectname
            return 1
        else:
            print error_dict
            return 1

def arg_handling():
    parser = argparse.ArgumentParser(
        prog='swift_checker.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Swift checker test''',
        epilog=textwrap.dedent('''\
        
        Single File Comparison:

            1: Compare local file with object sharing the same name in swift container
               Example: ./swift_checker.py filename container

            2: Compare local file with object having a different name or path
               Example: ./swift_checker.py filename container object_name
        
        Directory Comparison:

            3: Compare files/folders contained within local directory with objects in swift container
               Example: ./swift_checker.py /absolute_path/to_my_files container 

            4: Compare files/folders contained within path with objects in swift container specifying object prefix
               Example: ./swift_checker.py /path_to_my_files container /my_objects_start_with_this_prefix/

    ''')


)
    parser.add_argument('-c','-credentials',help='Full path to openrc file to read OpenStack/Swift authentication credentials from')
    parser.add_argument('-v',help="Verbose mode: Displays the md5 hashes of each file and object. Display ETag calculation",action='store_true')
    parser.add_argument('-vv',help="Very Verbose mode: Verbose mode + display the md5 hashes of individual segments",action='store_true')

    parser.add_argument('path',help='The full path to a file or directory that you would like to check against a swift object or container')
    parser.add_argument('container',help='Name of the Swift container to check')
    parser.add_argument('object_or_path', help='''Optional: For file comparison this is the specific object name in swift to compare against. 
                For directory comparison, this is an optional prefix/path to append to the beggining of file names during comparison''',nargs='?')

    return parser

def main():

    args = arg_handling().parse_args()
    
    #Determine the output verbosity from the input args.
    global verbose_mode
    
    verbose_mode = 0
    if args.v:
        verbose_mode = 1
    if args.vv:
        verbose_mode = 2
    #Establish a connection to Swift
    try:
        sc = swift_client(args.c)
    except:
        raise_error("Swift connection failed")

    savedPath = os.getcwd()

    #If path is a directory, then scan all files and folders in directory recursively.
    
    errors = 0
    jobs = []
    files_succeeded = []
    files_failed = []

    if os.path.isdir(args.path):
        
        os.chdir(os.path.abspath(args.path))
        print ""    
        print "Checking files in local directory:", os.getcwd()
        for root, dirs, files in os.walk('.', topdown=True):
            for name in files:
     #If a path is specified in the 3rd argument, append it as a path to the start of the swift object name 
                if args.object_or_path:
                    cur_object = os.path.join(args.object_or_path.lstrip('.').lstrip('/').lstrip('\\'),
                                 root.lstrip('.').lstrip('/').lstrip('\\'),name) 
     #Use absolute path as swift object name
                else: 
                    cur_object = os.path.join(root.lstrip('.').lstrip('/').lstrip('\\'),name)
     #Store the job in an array to be processed once directory scanning complete
                j = [sc, os.path.abspath(os.path.join(root,name)), args.container, cur_object]
                jobs.append(j)  
        if os.getcwd() != savedPath: 
            os.chdir(savedPath)
        print "Files in directory:", len(jobs) 
        print " "

        filecount = 0
     #Start processing each job
        for j in jobs:
            filecount=filecount+1
            print "Processing:", filecount, "/", len(jobs)
     #Check the current file with swift object
            print "Local File: ", j[1]
            print "Swift Object: ", j[3]
            print ""   
        
            if compare_file_with_object(j[0],j[1],j[2],j[3]) == 0:
                print "Match: ", j[1]
                files_succeeded.append(j[1])
            else:
                errors = errors + 1 
                print "Fail: ", j[1]
                files_failed.append(j[1])
            print " "

     #Result summary
        print "Summary:"
        print ""
        print "Matches:", len(jobs) - errors, "/", len(jobs)
        for f in files_succeeded:
            print f
        print ""
        print "Fails:", errors, "/", len(jobs)
        for f in files_failed:
            print f
        print ""
        
    #If path is a file then check only the file
    elif os.path.isfile(args.path):
        print "Checking file"
        if verbose_mode > 0:
            display_header()
        if not args.object_or_path:
            if compare_file_with_object(sc, args.path, args.container, os.path.split(args.path)[1]) == 0:
                print "Match: ", args.path
            else:
                print "Fail: ", args.path
                errors = errors + 1
        else:
            if compare_file_with_object(sc, args.path, args.container, args.object_or_path) == 0:
                print "Match: ", args.path
            else:
                errors = errors + 1
                print "Fail: ", args.path

    exit

    #print sc.get_account()[1]

if __name__ == "__main__":
    main()
