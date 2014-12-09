Deployment Script
-----------------

Prerequisites
-------------

* A Digital Ocean account
* Some credits owned
* An SSH key configured and added to Digital Ocean (highly recommended)
* An API key and Client ID for APIv1 ( https://www.digitalocean.com/api_access )


Usage
-----

```bash
deploy.py --client-id <my_client_id>     # DO client ID
          --api-key <my_api_key>         # DO API key
          --domain <mydomain.nohost.me>  # Domain name (used as droplet name)
          [--ssh-key-name <ssh_key>]     # Use SSH key based authentication, with the specific key
          [--password <my_password>]     # Admin password (auto-execute post-installation if set)
          [--test]                       # Install from test repository
          [--no-snapshot]                # Do not snapshot after installation nor recover from snapshot
          [--update-snapshot]            # Force fresh install and snapshot
          [--system-upgrade]             # Force system upgrade before YunoHost installation
```

```bash
remove.py --client-id <my_client_id>     # DO client ID
          --api-key <my_api_key>         # DO API key
          --domain <mydomain.nohost.me>  # Domain name (used as droplet name)
```
