#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import requests
import json

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

remove.py --domain <mydomain.nohost.me>  # Domain name (used as droplet name)
          [--client-id <my_client_id>]   # DO client ID
          [--api-key <my_api_key>]       # DO API key
          [--dynette-auth <login:pwd>]   # Credentials to access dynette API

You have to provide your client ID and corresponding API key :
- either on the command line
- either in a 'config.local' file located next to this script (see 'config.local.sample' for a sample)

''')
    sys.exit(1)

api_url = 'https://api.digitalocean.com/v1'

credentials  = {}
dynette_credentials = None

# Try to load credentials from config.local file
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

    if 'dynette_auth' in config:
      dynette_credentials = config["dynette_auth"]
      print( 'Successfully loaded dynette credentials from %s' % (localconfig) )

if '--domain' not in sys.argv:
    print('You have to provide a domain name')
    sys.exit(1)

for key, arg in enumerate(sys.argv):
    if arg == '--domain':
        domain = sys.argv[key+1]
    if arg == '--api-key':
        credentials.update( { "api_key" : sys.argv[key+1] } )
    if arg == '--client-id':
        credentials.update( { "client_id" : sys.argv[key+1] } )
    if arg == '--dynette-auth':
        dynette_credentials = sys.argv[key+1]

if 'client_id' not in credentials or 'api_key' not in credentials:
  print('You have to provide a client ID and an API key')
  sys.exit(1)

params = credentials

print('Getting active droplets...')
r = requests.get(api_url +'/droplets', params=params)
result = r.json()

if len(result['droplets']) == 0:
    print('No droplet found, nothing to remove')
    sys.exit(1)

droplet_found = False
for droplet in result['droplets']:
    if droplet['name'] == domain:
        droplet_found = True
        params.update({ 'scrub_data': False })

        # Destroy droplet
        r = requests.get(api_url +'/droplets/'+ str(droplet['id']) +'/destroy', params=params)
        result = r.json()
        print(domain +' : '+ str(result['status']))
        
        if dynette_credentials:
            # Remove domain from dynette
            command = 'curl  -kL -X POST -u %s http://dynette.yunohost.org/index.php --data-urlencode "domain=%s" > /dev/null 2>&1' % (dynette_credentials, domain)
            print('Removing %s from dynette...' % (domain))
            exit_status = os.system(command)
            if exit_status == 0:
              print('Successfully removed %s from dynette' % (domain))
            else:
              print('Error during removal of domain %s from dynette (%s)' % (domain, exit_status))

if droplet_found:
    sys.exit(0)
else:
    print('Droplet not found: '+ domain)
    sys.exit(1)
