YunoHost deployment script for Digital Ocean
--------------------------------------------

```bash
Usage:

deploy.py --client-id <my_client_id>     # DO client ID
          --api_key <my_api_key>         # DO API key
          --domain <mydomain.nohost.me>  # Domain name
          [--password <my_password>]     # Admin password (auto-execute post-installation if set)
          [--no-ssh-key-auth]            # Do not use SSH Key based authentatication
          [--test]                       # Install from test repository
          [--no-snapshot]                # Do not snapshot after installation nor recover from snapshot
```
