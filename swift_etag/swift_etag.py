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

#MD5 Chunk size, must be a multiple of 128
#How many bytes are read per itteration.
CHUNK_SIZE=16384

def raise_error(error_msg):
    print error_msg
    exit

def split(filename,segment_size,create_segments):
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
        print "Checksum for segment " + str(segment_count) + " : " + md5_seg
        
        #os.remove(segment_filename)
        segment_count = segment_count + 1
     
    #print "Concatinated Etags: " + hash
    m = hashlib.md5()
    m.update(hash)
    print "Etag of Concatinated Checksums: " + m.hexdigest()

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filename',help='File to segment and calculate hash')
    parser.add_argument('segment_size',help='Segment Size in Bytes', type=int)
    parser.add_argument('-s', action='store_true',help='write the individual segments to files on disk')
    args = parser.parse_args()
    split(args.filename, args.segment_size,args.s)

if __name__ == "__main__":
    main()
