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

You have to provide your client ID and corresponding API key :
- either on the command line
- either in a 'config.local' file located next to this script (see 'config.local.sample' for a sample)

''')
    sys.exit(1)

api_url = 'https://api.digitalocean.com/v1'

credentials  = {}

# Try to load credentials from config.local file
localconfig = os.path.join(os.path.dirname(__file__), 'config.local')
if os.path.exists( localconfig ):
  with open(localconfig) as localconfig_stream:
    credentials.update( json.loads(str(localconfig_stream.read())) )
    if 'client_id' not in credentials or 'api_key' not in credentials:
      print('%s malformed' % (localconfig))
      sys.exit(1)
    else:
      print( 'Successfully loaded credentials from %s' % (localconfig) )

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

if droplet_found:
    sys.exit(0)
else:
    print('Droplet not found: '+ domain)
    sys.exit(1)
