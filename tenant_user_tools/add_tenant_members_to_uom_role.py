#!/usr/bin/env python

import os
import shutil
import collections
import sys
import argparse

from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.v3 import client as ks_client_v3 
from keystoneclient.v2_0 import client as ks_client_v2 


import subprocess

UOM_ROLE = "78ef989041884cfda970e13b8183ddac"
PREPROD_ROLE = "e6f719ff04d742f4a32402ea4c79f7f7"

#DataStructure containing cloud flavours.

#Ascertain these values from NOVA or database at a later date...

def get_keystone_client_v3():

    url = os.environ.get('OS_AUTH_URL')
    username = os.environ.get('OS_USERNAME')
    password = os.environ.get('OS_PASSWORD')
    tenant = os.environ.get('OS_TENANT_NAME')
    return ks_client_v3.Client(username=username,
                                         password=password,
                                         project_name=tenant,
                                         user_domain_id='default',
                                         auth_url=url.replace('2.0', '3'))

def get_keystone_client_v2():

        url = os.environ.get('OS_AUTH_URL')
        username = os.environ.get('OS_USERNAME')
        password = os.environ.get('OS_PASSWORD')
        tenant = os.environ.get('OS_TENANT_NAME')
        return ks_client_v2.Client(username=username,
                                             password=password,
                                             project_name=tenant,
                                             user_domain_id='default',
                                             auth_url=url)

    

def get_session():
    auth_userid = os.environ.get('OS_ID')
    auth_username = os.environ.get('OS_USERNAME')
    auth_password = os.environ.get('OS_PASSWORD')
    auth_tenant = os.environ.get('OS_TENANT_NAME')
    auth_url = os.environ.get('OS_AUTH_URL')
    
    auth = v3.Password(auth_url=auth_url, username=auth_username, password=auth_password, project_id=auth_tenant)
    sess = session.Session(auth=auth)
    
    return sess

def get_keystone_client():
    auth_username = os.environ.get('OS_USERNAME')
    auth_password = os.environ.get('OS_PASSWORD')
    auth_tenant = os.environ.get('OS_TENANT_NAME')
    auth_url = os.environ.get('OS_AUTH_URL')

    try:
        kc = ks_client.Client(username=auth_username, version=(3, ),
                              password=auth_password,
                              tenant_name=auth_tenant,
                              auth_url=auth_url)
    except AuthorizationFailure as e:
        print e
        print 'Authorization failed, have you sourced your openrc?'
        sys.exit(1)

    return kc


def cmdline(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return out

def user_projects(user):
    keystone = get_keystone_client_v3()
    projects = keystone.projects.list()
    projects = {project.id: project for project in projects}
    roles = keystone.roles.list()
    roles = {role.id: role for role in roles}

    try:
        user = keystone.users.get(user)
    except Exception:
        user = keystone.users.find(name=user)

    if user is None:
        print("Unknown user")
        return

    user_project_roles = collections.defaultdict(list)
    for role in keystone.role_assignments.list(user=user):
        try:
            project_id = role.scope['project']['id']
        except KeyError:
            continue
        role_id = role.role['id']
        user_project_roles[project_id].append(roles[role_id])

    print "Projects and roles for user %s:" % user.name

    for project_id, roles in user_project_roles.items():
        roles = ', '.join(sorted([role.name for role in roles]))
        project = projects[project_id]
        print project.id, project.name, roles

def help():
    print "Usage: [ -a ] <tenant_id>"
    print "-a: Add all users of tenant_id above to UOM roles"
    print "Default Behaviour: Just list tenant member roles, will not add"

def main():

        #scriptname -l <tenant_id>
        #scriptname -a <tenant_id>
    if len(sys.argv) == 1:
        help()
        return
    if sys.argv[1] == '-h':
        help()
        return
    if sys.argv[1] == '-a':
        tenant_id = sys.argv[2]
        add_role = True
    else: 
        tenant_id = sys.argv[1]
        add_role = False

    if not tenant_id:
        help()
        return
    #parser = argparse.ArgumentParser()
    #parser.add_argument('-l','--list')
    #parser.add_argument('-a','--add')
   
   # args = parser.parse_args()
    
  #  if args.list:
  #      print args.list


    
    kc_v2 = get_keystone_client_v2()
    #print kc.users.list(default_project_id=input)
    tenant_obj = kc_v2.tenants.get(tenant_id)
    tenant_members = tenant_obj.list_users()

    for member in tenant_members:
        print "Listing Roles for: " + member.name + " ID:" + member.id + " to role: "
        member_role = kc_v2.roles.roles_for_user(member.id, tenant_id)
        print member_role
            
    if add_role:
        for member in tenant_members:
            role = UOM_ROLE 
            print "Adding: " + member.name + " ID:" + member.id + " to role: " + role
            try: 
                kc_v2.roles.add_user_role(member.id, role, tenant_id)
            except:
                print "Ignoring: User already assigned role"
                pass
            role = PREPROD_ROLE 
            print "Adding: " + member.name + " ID:" + member.id + " to role: " + role
            try: 
                kc_v2.roles.add_user_role(member.id, role, tenant_id)
            except:
                print "Ignoring: User already assigned role"
                pass

#    users = kc.users.list(default_project=input)
#    print users
#    for x in tenants:
#        print x.list_users()
     
   

    





if __name__ == "__main__":
            main()

