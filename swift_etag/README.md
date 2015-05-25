usage: swift_etag.py [-h] [-s] filename segment_size

Description: Segment a local file and calculate MD5 checksums of each segment.
             Calculate OpenStack Swift Etag Checksum for segments.
             Useful for validating uploaded segmented objects with original file.

positional arguments:
*  filename      File to segment and calculate hash
*  segment_size  Segment Size in Bytes

optional arguments:
*  -h, --help    show this help message and exit
*  -s            write the individual segments to files on disk (default:
False)
