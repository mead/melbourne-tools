#!/usr/bin/python
import pycurl
import json
from helper import *
from StringIO import StringIO

def volume_create(cred,token):
   
    endpoint = get_endpoint("volume","public",token)
    print endpoint
    data = {
        "volume": {
            "status": "creating",
            "description": "test",
            "availability_zone": "melbourne-np",
            "source_volid": "null",
            "consistencygroup_id": "null",
            "snapshot_id": "null",
            "source_replica": "null",
            "size": 10,
            "user_id": "null",
            "name": "null",
            "imageRef": "null",
            "attach_status": "detached",
            "volume_type": "null",
            "project_id": "null",
            "metadata": {}
        }
    } 
    api_post(endpoint, token, data)

