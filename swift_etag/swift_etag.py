#!/usr/bin/python
import hashlib
import sys
import os
import math

CHUNK_SIZE=10000

def raise_error(error_msg):
    print error_msg
    exit

def md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()
                    
def split(filename,segment_size):
    global hash
    hash = ""
    try:
        f = open(filename, 'rb')
    except (OSError, IOError), e:
        raise_error("Could not open file")
    
    try:
        filesize = os.path.getsize(filename)
        print filesize
    except (OSError), e:
        raise_error("File size could not be determined")

    segment_count = 0
    read_bytes_total = 0

    #Total number of segments is
    number_of_segments = math.floor(filesize / segment_size) + 1

    while segment_count < number_of_segments:

        read_bytes = 0

        segment_filename = filename + "_segment_" + str(segment_count)
        print "Create segment: " + segment_filename
        
        try:
            f_segment = open(segment_filename, 'wb')
        except (OSError, IOError), e:
            raise_error("unable to create new segment")
        #Adjust segment size if we're near the end of the file

        if ((read_bytes_total + segment_size) > filesize):
            segment_size = filesize - read_bytes_total

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
            except (OSError, IOError), e:
                raise_error("Error reading from file")
            
            #Write the bytes
            try:
                f_segment.write(chunk)
            except (OSError, IOError), e:
                raise_error("Error reading from file")
            

            #Update number of bytes read/written
            read_bytes = read_bytes + n_bytes
            read_bytes_total = read_bytes + n_bytes

        try:
            f_segment.close()
        except (OSError, IOError), e:
            raise_error("Error closing file")
        
        md5 = md5sum(segment_filename)
        hash = hash + md5
        print "Etag for segment: " + md5
        
        #os.remove(segment_filename)
        segment_count = segment_count + 1
     
    print "Concatinated Etags: " + hash
    m = hashlib.md5()
    m.update(hash)
    print "Etag of Concatinated Etags: " + m.hexdigest()

def main():
    filename = sys.argv[1]
    segment_size = int(sys.argv[2])
#    print md5sum(sys.argv[1])
    split(filename, segment_size)
if __name__ == "__main__":
    main()
