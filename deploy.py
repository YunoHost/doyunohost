#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import requests
import time
import json

image_id_Debian_7_0_x64 = 10322059

size_id = 66                         # 512MB RAM
region_id = 9                        # AMS 3
image_id = image_id_Debian_7_0_x64   # Debian 7.0 x64

if len(sys.argv) == 1:
    print(
'''
Deployment Script
-----------------

Prerequisites
-------------

* A Digital Ocean account
* Some credits owned
* An SSH key configured and added to Digital Ocean (highly recommended)
* An API key and Client ID for APIv1 ( https://cloud.digitalocean.com/api_access )


Usage
-----

deploy.py --domain <mydomain.nohost.me>  # Domain name (used as droplet name)
          [--client-id <my_client_id>]   # DO client ID
          [--api-key <my_api_key>]       # DO API key
          [--ssh-key-name <ssh_key>]     # Use SSH key based authentication, with the specific key
          [--password <my_password>]     # Admin password (auto-execute post-installation if set)
          [--test]                       # Install from test repository
          [--no-snapshot]                # Do not snapshot after installation nor recover from snapshot
          [--update-snapshot]            # Force fresh install and snapshot
          [--branch <stable|testing|unstable>] # Which Yunohost flavor to install (default : stable)

You have to provide your client ID and corresponding API key :
- either on the command line
- either in a 'config.local' file located next to this script (see 'config.local.sample' for a sample)

''')
    sys.exit(1)

api_url = 'https://api.digitalocean.com/v1'
test = '--test' in sys.argv
snapshot = '--no-snapshot' not in sys.argv
update_snapshot = '--update-snapshot' in sys.argv
postinstall = False
branch = 'stable'

if '--domain' not in sys.argv:
    print('You have to provide a domain name')
    sys.exit(1)

credentials  = {}

# Try to load credentials & ssh-key from config.local file
localconfig = os.path.join(os.path.dirname(__file__), 'config.local')
if os.path.exists( localconfig ):
  with open(localconfig) as localconfig_stream:
    config = {}
    config.update( json.loads(str(localconfig_stream.read())) )
    if 'client_id' not in config or 'api_key' not in config:
      print('%s malformed' % (localconfig))
      sys.exit(1)

    credentials["client_id"] = config["client_id"]
    credentials["api_key"] = config["api_key"]
    print( 'Successfully loaded credentials from %s' % (localconfig) )
    
    if 'ssh_key' in config:
      ssh_key_name = config["ssh_key"]
      print( 'Successfully loaded SSH key %s from %s' % (ssh_key_name, localconfig) )

# Parse command line arguments
for key, arg in enumerate(sys.argv):
    if arg == '--domain':
        domain = sys.argv[key+1]
    if arg == '--password':
        postinstall = True
        password = sys.argv[key+1]
    if arg == '--api-key':
        credentials.update( { "api_key" : sys.argv[key+1] } )
    if arg == '--client-id':
        credentials.update( { "client_id" : sys.argv[key+1] } )
    if arg == '--ssh-key-name':
        ssh_key_name = sys.argv[key+1]
    if arg == '--branch':
        branch = sys.argv[key+1]

if 'client_id' not in credentials or 'api_key' not in credentials:
  print('You have to provide a client ID and an API key')
  sys.exit(1)

start = time.time()

# Check if YunoHost snapshot exists
if snapshot or update_snapshot:
    params = credentials
    params['filter'] = 'my_images'
    print('Getting snapshots...')
    r = requests.get(api_url +'/images', params=params)
    snapshot_name = 'YunoHost'
    if branch is not "stable":
        snapshot_name = 'YunoHost-%s' % branch
    result = r.json()
    print result
    for image in result['images']:
        if image['name'] == snapshot_name:
            print('Snapshot found: '+ snapshot_name)
            if update_snapshot:
                r = requests.get(api_url +'/images/'+ str(image['id']) + '/destroy', params=params)
                result = r.json()
                if result['status'] == 'ERROR':
                    print('Failed to remove "'+ snapshot_name +'" snapshot')
                    sys.exit(1)
                else:
                    print('Snapshot removed: '+ snapshot_name)
            else:
                image_id = image['id']

params = credentials

# Check if SSH key auth
if ssh_key_name:
    print('Getting SSH keys...')
    r = requests.get(api_url +'/ssh_keys', params=params)
    result = r.json()
    if len(result['ssh_keys']) > 0:
        for key in result['ssh_keys']:
            if key['name'] == ssh_key_name:
                params['ssh_key_ids'] = key['id']
        if 'ssh_key_ids' not in params:
            print('SSH key not found: '+ ssh_key_name)
            sys.exit(1)
    else:
        print('No SSH key found')
        sys.exit(1)

params.update({
    'name': domain,
    'image_id': image_id,   # Debian 7.0 x64 by default
    'size_id': size_id,     # 512MB by default
    'region_id': region_id  # AMS3 by default
})

sys.stdout.write('Creating your droplet, it may take a while...')
sys.stdout.flush()
r = requests.get(api_url +'/droplets/new', params=params)
result = r.json()
if result['status'] == 'ERROR':
    print('Failed to create droplet: '+ result['error_message'])
    sys.exit(1)

droplet = str(result['droplet']['id'])

# Display a dot every 10 seconds
while True:
    time.sleep(10)
    sys.stdout.write('.')
    sys.stdout.flush()
    params = credentials
    r = requests.get(api_url +'/droplets/'+ droplet, params=params)
    result = r.json()
    if result['droplet']['status'] == 'active':
        ip = result['droplet']['ip_address']
        time.sleep(20)
        if "ssh_key_ids" in params:
            # wait another 30 sec
            time.sleep(30)
        break

print(' Droplet IP: '+ ip)

if os.path.exists( os.path.join(os.environ['HOME'], ".ssh", "known_hosts") ):
  os.system('ssh-keygen -R '+ ip)

if image_id == image_id_Debian_7_0_x64:
    command_list = [
            'echo "root:M3ryOPF.AfR2E" | chpasswd -e', # Change root password to "yunohost"
            'git clone http://github.com/YunoHost/install_script /root/install_script',
            'cd /root/install_script && git checkout update-repo-url'
    ]
    command_list.append('apt-get update && apt-get upgrade -qq -y')
    command_list.append('cd /root/install_script && ./autoinstall_yunohostv2 branch')
    
    print('Installing YunoHost on your droplet, it WILL take a while')
    for command in command_list:
        command_result = os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "root@'+ ip +'" "export TERM=linux; '+ command +'"')
        if command_result != 0:
            print('Error during install command: '+ command)
            print('Result: '+ str(command_result))
            #sys.exit(1)

if snapshot and image_id == image_id_Debian_7_0_x64:
    sys.stdout.write('Shutting your droplet down, it may take a while...')
    sys.stdout.flush()
    requests.get(api_url +'/droplets/'+ droplet +'/power_off', params=credentials)
    while True:
        time.sleep(10)
        sys.stdout.write('.')
        sys.stdout.flush()
        r = requests.get(api_url +'/droplets/'+ droplet, params=credentials)
        result = r.json()
        if result['droplet']['status'] == 'off':
            break

    print(' Droplet off')
    params = credentials
    params['name'] = 'YunoHost'
    if test:
        params['name'] = 'YunoHostest'
    sys.stdout.write('Snapshooting your droplet, it may take a while...')
    sys.stdout.flush()
    requests.get(api_url +'/droplets/'+ droplet +'/snapshot', params=params)
    while True:
        time.sleep(10)
        sys.stdout.write('.')
        sys.stdout.flush()
        r = requests.get(api_url +'/droplets/'+ droplet, params=credentials)
        result = r.json()
        if result['droplet']['status'] == 'active':
            time.sleep(20)
            break

    print(' Snapshot created: YunoHost')

postinst_command_list = []

if postinstall:
    print(' Proceeding with YunoHost postinstall...')
    
    postinst_command_list.append('apt-get update && apt-get upgrade -qq -y')
    postinst_command_list.append('yunohost tools postinstall --domain '+ domain +' --password '+ password)

    for command in postinst_command_list:
        command_result = os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "root@'+ ip +'" "export TERM=linux; '+ command +'"')
        if command_result != 0:
            print('Error during postinst command: ' + command)

print('')
print('Successfully installed in '+ str(time.time() - start) +' s')
print('')
print('Connect to your droplet with "ssh root@'+ ip +'"')
sys.exit(0)

