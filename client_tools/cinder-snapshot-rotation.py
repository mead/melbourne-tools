#!/usr/bin/env python
#
# Cinder Snapshot Rotation Script
# Author: Dylan McCulloch
# Date: 04/09/2016
# Version 0.0.1
#
# Description: Rotate snapshots of a volume that belong to the same snapshot set.
# Creates a new snapshot for the specified volume and adds metadata to the snapshot to indicate
# membership of a specific snapshot set. The number of snapshots belonging to the snapshot set
# is then compared to the rotation number (maximum number of snapshots to keep in the snapshot set)
# and any excess snapshots in the snapshot set are deleted.


import os
import sys
import argparse
import prettytable
import operator
import time

from keystoneclient.v2_0 import client as ks_client
from keystoneclient.exceptions import AuthorizationFailure
from cinderclient.v2 import client as cinder_client
from cinderclient.exceptions import NotFound

def print_snapshot(snapshot):
    pt = prettytable.PrettyTable(['Property', 'Value'])
    pt.add_row(["created_at", snapshot.created_at])
    pt.add_row(["description", snapshot.description])
    pt.add_row(["id", snapshot.id])
    pt.add_row(["metadata", snapshot.metadata])
    pt.add_row(["name", snapshot.name])
    pt.add_row(["size", snapshot.size])
    pt.add_row(["status", snapshot.status])
    pt.add_row(["volume_id", snapshot.volume_id])
    print str(pt)


def get_volume(volume_input):
  volume = get_volume_by_id(volume_input)
  if volume is None:
    volume = get_volume_by_name(volume_input)
  if volume is None:
    print "ERROR: No volume with a name or ID of '{volume_input}' exists".format(volume_input=volume_input)
    sys.exit(1)
  return volume


def get_volume_by_id(id):
  try:
    volume = cc.volumes.get(id)
    return volume
  except:
    pass


def get_volume_by_name(name):
  try:
    volumes = cc.volumes.findall(name=name)
    num_volumes = len(volumes)
    if num_volumes == 1:
      volume = volumes.pop()
      return volume
    elif num_volumes > 1:
      print "Found {num_volumes} volumes with the same name '{name}'. Please specify Volume ID instead.".format(num_volumes=num_volumes,name=name)
      sys.exit(1)
  except:
      raise

def create_snapshot(volume,name,metadata):
  snapshot = cc.volume_snapshots.create(volume_id=volume.id,
    name=name,
    force=True,
    metadata=metadata)
  while (snapshot.status !='available'):
    time.sleep(1)
    snapshot = cc.volume_snapshots.get(snapshot.id)
  print_snapshot(snapshot)
  return snapshot 


def rotate_snapshot_set(volume, snapshot_set_tag, rotation, metadata):
  """Delete excess snapshots within snapshot set associated with a volume.

  Volumes are allowed a fixed number of snapshots (the rotation number) within the snapshot set;
  this method deletes the oldest snapshots that exceed the rotation threshold.

  :param snapshot_set_tag: daily | weekly
  :param rotation: int representing how many snapshots within the snapshot set to keep around;
  """
  snapshot_set = []
  snapshots = cc.volume_snapshots.findall(volume_id=volume.id)

  for snapshot in snapshots:
    if snapshot.metadata.has_key('snapshot_set'):
      if snapshot.metadata['snapshot_set'] == snapshot_set_tag:
        snapshot_set.append(snapshot)
  
  snapshot_set.sort(key=operator.attrgetter('created_at'),reverse=True)
  num_snapshots = len(snapshot_set)
  print "Found {num_snapshots} snapshot/s (rotation: {rotation})".format(num_snapshots=num_snapshots, rotation=rotation)

  if num_snapshots > rotation:
    # NOTE: this deletes all snapshots within the snapshot set that exceed the rotation
    # limit
    excess = len(snapshot_set) - rotation
    print "Rotating out {excess} snapshot/s".format(excess=excess)
    for i in xrange(excess):
      snapshot = snapshot_set.pop()
      print "Deleting snapshot {snapshot_id}".format(snapshot_id=snapshot.id)
      cc.volume_snapshots.delete(snapshot.id)


def get_keystone_client():
  auth_username = os.environ.get('OS_USERNAME')
  auth_password = os.environ.get('OS_PASSWORD')
  auth_tenant = os.environ.get('OS_TENANT_NAME')
  auth_url = os.environ.get('OS_AUTH_URL')

  try:
    kc = ks_client.Client(username=auth_username,
    password=auth_password,
    tenant_name=auth_tenant,
    auth_url=auth_url)
  except AuthorizationFailure as e:
    print e
    print 'Authorization failed, have you sourced your openrc?'
    sys.exit(1)
  return kc


def get_cinder_client():
  auth_username = os.environ.get('OS_USERNAME')
  auth_password = os.environ.get('OS_PASSWORD')
  auth_tenant = os.environ.get('OS_TENANT_NAME')
  auth_url = os.environ.get('OS_AUTH_URL')

  cc = cinder_client.Client(username=auth_username,
  api_key=auth_password,
  project_id=auth_tenant,
  auth_url=auth_url)
  return cc


def collect_args():
  parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
  parser.add_argument('-v', '--volume', dest='volume',
    required=True, help="Name or ID of volume")
  parser.add_argument('-n', '--name', dest='name',
    required=True, help="Snapshot name")
  parser.add_argument('-s', '--set', dest='set',
    required=True, help="Snapshot set. This is a tag that is added to the snapshot metadata to indicate membership of a snapshot set. e.g. Daily or Weekly")
  parser.add_argument('-r', '--rotation', dest='rotation', type=int,
    required=True, help="Int parameter representing how many snapshots within the snapshot set to keep around.")
  return parser

if __name__ == '__main__':
  args = collect_args().parse_args()
  kc = get_keystone_client()
  cc = get_cinder_client()
  volume_input = args.volume
  name = args.name
  snapshot_set_tag = args.set
  rotation = args.rotation
  volume = get_volume(volume_input)
  metadata = {'snapshot_set': snapshot_set_tag}
  create_snapshot(volume,name,metadata)
  rotate_snapshot_set(volume, snapshot_set_tag, rotation, metadata)
