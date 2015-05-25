usage: swift_etag.py [-h] [-s] filename segment_size

positional arguments:
  filename      File to segment and calculate hash
  segment_size  Segment Size in Bytes

optional arguments:
  -h, --help    show this help message and exit
  -s            write the individual segments to files on disk (default:
                False)
