#!/usr/bin/python
import pycurl
import json
from StringIO import StringIO

def keystone_authenticate(cred):
    storage = StringIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, "https://keystone.rc.nectar.org.au:5000/v2.0/tokens")
    c.setopt(pycurl.HTTPHEADER, [ 'Content-Type: application/json' ])
    c.setopt(pycurl.WRITEFUNCTION, storage.write)
    c.setopt(pycurl.POST, 1)
    d = { "auth": {
            "tenantId": cred['auth_tenant_name'],
            "passwordCredentials": {
                "userId": cred['auth_username'],
                "password": cred['auth_password']
            }
        }
    }
    #d = { "auth": {
    #    "identity": {
    #    "methods": ["password"],
    #    "password": {
    #        "user": {
    #        "name": cred['auth_username'],
    #        "domain": { "id": "default" },
    #        "password": cred['auth_password']
    #        }
    #    }
    #    }
    #}
    #}
    data = json.dumps(d)
    print data
    c.setopt(pycurl.POSTFIELDS, data)
    c.perform()
    c.close()
    content = storage.getvalue()
    print content
#def main():
#    json_test()

#if __name__ == "__main__":
#    main()


