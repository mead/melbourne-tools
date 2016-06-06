#!/usr/bin/python

#Name: gluster_mount_test
#Author: Justin Mammarella
#Date: June 2016
#Description: Script to test mounts as specified in mounts.yaml file

import yaml
import os
import subprocess
import argparse

#Mount data in yaml format
CONFIG="mountlist.yaml"

def cmdline(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    out = proc.communicate()
    proc.wait();
    return (out, proc.returncode)

#Custom print function with verbosity level

def my_print(l, text):
  if int(l) < verbosity:
    print(text)

def do_mount(m):
  
  if verbosity > 1: 
    mount_str = "mount -vt "
  else:
    mount_str = "mount -t "

  if 'protocol' not in m:
    my_print(0,"Bad yaml")
    return 1

  if m['protocol'] == 'cifs':
    mount_str+= "cifs "
    if 'host' in m:
      mount_str+= m['host']
    if 'share' in m:
      mount_str+= m['share'] + " "
  
  if m['protocol'] == 'nfs':
    mount_str+= "nfs "
    if 'host' in m:
      mount_str+= m['host']
    if 'share' in m:
      mount_str+= ":/" + m['share'] + " "

  
  if 'mount_point' in m:
    mount_str+= m['mount_point'] + " "
    if not os.path.exists(m['mount_point']):
      my_print(2,"creating directory")
      os.makedirs(m['mount_point'])
  mount_str+= "-o "

  if 'username' in m:
    mount_str+= "username=" + m['username'] + ","

  if 'password' in m:
    mount_str+= "password=" + m['password'] + ","

  if 'domain' in m:
    mount_str+= ",domain=" + m['domain'] + ','

  if 'options' in m:
    mount_str+= m['options']
  
  if 'password' in m:
    my_print(1,"Mounting - " + mount_str.replace(m['password'],"a_real_password"))
  else:
    my_print(1,"Mounting - " + mount_str)

  (out, returncode) = cmdline(mount_str)

  if returncode > 0:
    return 1
    my_print(1, "Fail - Mount")


  my_print(1, "Success - Mount")
  
  return 0

def close_mount(m):
  
  if m['protocol'] == 'cifs':
    (out, err) = cmdline("umount " + m['mount_point'])
  if m['protocol'] == 'nfs':
    (out, err) = cmdline("umount -f " + m['mount_point'])

  if err > 0:
    my_print(1,"Fail - Unmount" + m['mount_point']) 
    return 1;

  my_print(1,"Success - Unmount")
  return 0

def test_mount(m):
  test_dir = m['mount_point'] + "/test/" 
  
  #Create test directory

  if not os.path.exists(test_dir):
    my_print(2,"creating directory")
    os.makedirs(test_dir)

  filename=test_dir + "testfile"

  #Try to touch a file on the mounted share

  try:
    cmdline("touch " + filename)
  except:
    my_print(1,"Fail - Could not touch file: " + filename)
    return 1
  
  #Remove the created file

  try:
    cmdline("rm " + filename)
  except:
    my_print(1,"Fail - Could not remove file: " + filename)

  #Check that the file has been removed
  
  if os.path.isfile(filename):
    my_print(1,"Fail - Mount File Tests") 
    return 1
  
  my_print(1,"Success - Mount File Tests")

  return 0

def arg_handling():
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '-verbosity', help='Verbosity of Output', type=int, default=1)
  return parser

def main():
  args = arg_handling().parse_args()
  
  global verbosity
  
  verbosity = args.v
 
  #Read configuration file containing mount yaml structure.

  stream = open(CONFIG, 'r')
  config = yaml.load(stream)
  fail = 0

  count=0

  #For each mount in config file
  #Perform: Mount, FileTest, CloseMount

  for mount in config['mounts']:

      count += 1
      errors=0

      my_print(1," ")
      my_print(1,"Checking: " + mount)
      
      if do_mount(config['mounts'][str(mount)]) > 0:
        errors += 1

      if test_mount(config['mounts'][str(mount)]) > 0 and errors == 0:
        errors += 1

      if close_mount(config['mounts'][str(mount)]) > 0 and errors == 0:
        errors += 1
      
      if errors > 0:
        fail += 1

  my_print(1," ")

  success = count - fail
  
  if fail > 0:
    my_print(0,"[" + str(success) + "/" + str(count) + "]" + " Error check mounts.")
    return 1

  else:
    my_print(0,"[" + str(success) + "/" + str(count) + "]" + " All mounts are okay") 
    return 0
 
  stream.close()

if __name__ == "__main__":
    main()
