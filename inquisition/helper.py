import pycurl
import json
from StringIO import StringIO

def debug(msg):
    if DEBUG == True:
        print msg

def get_endpoint(endpoint_type, interface, token):
    for endpoint_group in token['catalog']:
        if endpoint_group['type'] == endpoint_type:
            #print endpoint_group
            for subgroup in endpoint_group['endpoints']:
                    if subgroup['interface'] == 'public':
                         return subgroup['url']
       # print endpoint_group['type']
def api_post(url, token, data):
    rec_buffer = StringIO()
    c = pycurl.Curl()
    print "blah"
    print token
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.HTTPHEADER, [ 'Content-Type: application/json', 'X-Auth-Token: ' + token['token']['id'] ])

    c.setopt(pycurl.WRITEFUNCTION, rec_buffer.write)
    c.setopt(pycurl.POST, 1)

    json_data = json.dumps(data)
    c.setopt(pycurl.POSTFIELDS, json_data)
    c.perform()
    c.close()
    content = rec_buffer.getvalue()
    print content 
    n = json.loads(content)
    return n
