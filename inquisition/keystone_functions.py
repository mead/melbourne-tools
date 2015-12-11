#!/usr/bin/python
import pycurl
import json
import requests
from StringIO import StringIO


#Auth using requests

def keystone_authenticate(cred):
    
    rec_buffer = StringIO()
    
    headers = { 'Content-Type': 'application/json' }  
    d = { 
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "name": cred['auth_username'],
                        "password": cred['auth_password'],
                        "domain": {
                            "id": "default"
                        }
                        }
                 }
            }
        }
    }

    data = json.dumps(d)

    r = requests.post("https://keystone.rc.nectar.org.au:5000/v3/auth/tokens", headers=headers, data=data)
    
    n = r.json()
    
    print n
    if "error" in n:
        raise ValueError('Authentication Error')
    else:
        token = n['token']
        return token


#Auth using curl
def keystone_authenticate_V3(cred):
    
    rec_buffer = StringIO()
    
    c = pycurl.Curl()
    c.setopt(pycurl.URL, "https://keystone.rc.nectar.org.au:5000/v3/auth/tokens")
    c.setopt(pycurl.HTTPHEADER, [ 'Content-Type: application/json' ])
    c.setopt(pycurl.WRITEFUNCTION, rec_buffer.write)
    c.setopt(pycurl.POST, 1)
    d = { 
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "name": cred['auth_username'],
                        "password": cred['auth_password'],
                        "domain": {
                            "id": "default"
                        }
                        }
                 }
            }
        }
    }

    
    data = json.dumps(d)
    c.setopt(pycurl.POSTFIELDS, data)
    c.perform()
    c.close()
    content = rec_buffer.getvalue()
    n = json.loads(content)
    print n
    if "error" in n:
        raise ValueError('Authentication Error')
    else:
        token = n['token']
        return token

def keystone_authenticate_v2(cred):
    
    rec_buffer = StringIO()
    
    c = pycurl.Curl()
    c.setopt(pycurl.URL, "https://keystone.rc.nectar.org.au:5000/v2.0/tokens")
    c.setopt(pycurl.HTTPHEADER, [ 'Content-Type: application/json' ])
    c.setopt(pycurl.WRITEFUNCTION, rec_buffer.write)
    c.setopt(pycurl.POST, 1)
    d = { "auth": {
            "tenantName": cred['auth_tenant_name'],
            "passwordCredentials": {
                "username": cred['auth_username'],
                "password": cred['auth_password']
            }
        }
    }
    
    data = json.dumps(d)
    c.setopt(pycurl.POSTFIELDS, data)
    c.perform()
    c.close()
    content = rec_buffer.getvalue()
    n = json.loads(content)
    if "error" in n:
        raise ValueError('Authentication Error')
    else:
        token = n['access']['token']
        return token
    #print content
#def main():
#    json_test()

#if __name__ == "__main__":
#    main()


