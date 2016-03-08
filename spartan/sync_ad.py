#!/usr/bin/python
# This script syncs users from AD to Slurm
# It looks up the provided AD accounts and add/deletes users from slurm
# accordingly

import argparse
import subprocess
import os, pdb, sys, traceback

NOOP = False
DEBUG = False

# get list of all slurm accounts
def get_slurm_accounts():
    accounts = {}
    # sample output
    # hpcusers@unimelb.edu.au|
    # hpcusers@unimelb.edu.au|user1@unimelb.edu.au
    # hpcusers@unimelb.edu.au|user2@unimelb.edu.au
    output = subprocess.check_output(['sacctmgr', 'list', 'assoc',
                                        'format=account,user', '--parsable2',
                                        '--noheader'])

    try:
        for line in output.split('\n'):
            account, user = line.split('|')
            if user:
                accounts.setdefault(account, []).append(user)
    except ValueError:
        pass
        
    return accounts


# get a list of users/groups from AD
def get_ad_groups(lookup_groups=[]):
    groups = {}
    for g in lookup_groups:
        # sample output
        # hpcusers@unimelb.edu.au:*:1234567880:user1@unimelb.edu.au,user2@unimelb.edu.au
        try:
            output = subprocess.check_output(['getent', 'group', g])
        except:
            print "ERROR: Can't find AD group %s" % g
            continue
        output = output.rstrip()
        name, passwd, gid, mem = output.split(':')
        if len(mem) == 0:
            # ad group has users, set it to empty list
            groups[g] = []
        else:
            users = mem.split(',')
            for user in users:
                groups.setdefault(name, []).append(user)

    return groups


# get a list of slurm users from account
def get_slurm_users(account):
    accounts = get_slurm_accounts()
    return accounts[account]

# delete all slurm users from account
def clear_slurm_accounts(accounts):
    for account in accounts:
        users = get_slurm_users(account)
        del_slurm_users(account, users)


# add users to slurm account
def add_slurm_users(account, users):
    for user in users:
        args = ['sacctmgr', '--immediate', 'add','user', 'name='+user,
                'account='+account]
        ret = _call(args)

        if ret == 0:
            print "Add %s to %s" % (user, account)
        else:
            print "ERROR! Add %s from %s returns %s" % (user, account, ret)


# delete users from slurm account
def del_slurm_users(account, users):
    for user in users:
        args =['sacctmgr', '--immediate', 'del', 'user', 'name='+user,
                'account='+account]

        ret = _call(args)
        if ret == 0:
            print "Del %s from %s" % (user, account)
        else:
            print "ERROR! Del %s from %s returns %s" % (user, account, ret)


# create slurm account
def add_slurm_account(account):
    print "Creating account %s" % account
    args = ['sacctmgr', '--immediate', 'add', 'account', account]
    ret = _call(args)
    return ret


def add_slurm_account2(account):
    try:
        print "Creating account %s" % account
        args = ['sacctmgr', '--immediate', 'add', 'account', account]
        ret = _call(args)
        if DEBUG:
            print ' '.join(args)
        if not NOOP:
            FNULL = open(os.devnull, 'w')
            subprocess.check_call(args, stdout=FNULL, stderr=subprocess.STDOUT)
        return 0
    except:
        print "Error creating slurm account %s" % account
        return 1


# run subprocess.call quietly
# TODO: Make sacctmgr do things quietly so we don't need this
def _call(args):
    if DEBUG:
        print ' '.join(args)

    if not NOOP:
        FNULL = open(os.devnull, 'w')
        return subprocess.call(args, stdout=FNULL, stderr=subprocess.STDOUT)
    else:
        return 0


def main(ad_groups=[]):
    accounts = get_slurm_accounts()
    groups = get_ad_groups(ad_groups)
    for ad_group in groups:
        ad_users = set(groups[ad_group])
        # sometimes an account might not be created in slurm yet
        if ad_group not in accounts:
            # creates account
            ret = add_slurm_account(ad_group)
            # if there's an error creating account, skip to next
            if ret != 0: continue
            # list of users in this account will be blank
            slurm_users = set([])
        else:
            slurm_users = set(accounts[ad_group])

        not_in_slurm = ad_users - slurm_users
        not_in_ad = slurm_users - ad_users

        add_slurm_users(ad_group, not_in_slurm)
        del_slurm_users(ad_group, not_in_ad)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync AD group to slurm')
    parser.add_argument('groups', metavar='group', nargs='+', help='AD group name')
    parser.add_argument('-c', '--clear',
                        help='Clear the group in slurm',
                        action="store_true")
    parser.add_argument('-d', '--debug',
                        help='Run in debug mode. Print slurm commands executed.',
                        action="store_true")
    parser.add_argument('-n', '--noop',
                        help='Run in noop mode. Do not actually add users',
                        action="store_true")
    args = parser.parse_args()
    ad_groups = args.groups

    if args.debug: DEBUG = True

    if args.noop:
        print "Running in NOOP mode"
        NOOP = True

    try:
        if args.clear:
            clear_slurm_accounts(ad_groups)
        else:
            # main method
            main(ad_groups)
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
