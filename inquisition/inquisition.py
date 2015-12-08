#!/usr/bin/python

#Name: Inquisition

import os
import sys
import argparse
from keystone_functions import *

def config_extract(config_file):
    auth_username = ""
    auth_password = ""
    auth_tenant_id = ""
    auth_tenant_name = ""
    auth_region_name = ""
    auth_url = ""
    with open(config_file, 'r') as f:
        for line in f:
            firstword = line.split(' ')[0]
            if firstword == "export":
                line = line.replace("\n", '').replace('"', '') 
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
    return { 'auth_username': auth_username, 
             'auth_password': auth_password, 
             'auth_tenant_id': auth_tenant_id, 
             'auth_tenant_name': auth_tenant_name, 
             'auth_region_name': auth_region_name, 
             'auth_url': auth_url }

def arg_handling():
   parser = argparse.ArgumentParser(
            prog='swift_checker.py',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='''SwiftChecker:''')
   parser.add_argument('-c1', '--persocred')
   parser.add_argument('-c2', '--admincred')
   return parser

def main():
    args = arg_handling().parse_args()
    print args.persocred
    print args.admincred

    perso_cred = config_extract(args.persocred)
    admin_cred = config_extract(args.admincred)
    keystone_authenticate(perso_cred)
if __name__ == "__main__":
    main()

