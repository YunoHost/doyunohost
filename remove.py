#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import requests

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

remove.py --client-id <my_client_id>     # DO client ID
          --api-key <my_api_key>         # DO API key
          --domain <mydomain.nohost.me>  # Domain name (used as droplet name)
''')
    sys.exit(1)

api_url = 'https://api.digitalocean.com/v1'

if '--domain' not in sys.argv:
    print('You have to provide a domain name')
    sys.exit(1)
if '--client-id' not in sys.argv:
    print('You have to provide a client ID')
    sys.exit(1)
if '--api-key' not in sys.argv:
    print('You have to provide an API key')
    sys.exit(1)

for key, arg in enumerate(sys.argv):
    if arg == '--domain':
        domain = sys.argv[key+1]
    if arg == '--api-key':
        api_key = sys.argv[key+1]
    if arg == '--client-id':
        client_id = sys.argv[key+1]

credentials = { 'client_id': client_id, 'api_key': api_key }

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
