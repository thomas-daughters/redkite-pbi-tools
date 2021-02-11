import json

def refresh_workspace(workspace, credentials):
    error = False
    
    for dataset in workspace.datasets:
        if 'Deployment Aid' in dataset.name: continue # Skip deployment aid
        try:
            if dataset.get_refresh_state() == 'Unknown': # Don't trigger refresh if model is already refreshing
                print(f'** [{dataset.name}] is already refreshing')
            else:
                print(f'** Reconfiguring [{dataset.name}]')
                dataset.take_ownership() # In case someone manually took control post deployment

                print(f'*** Reauthenticating data sources...') # Reauthenticate as tokens obtained during deployment will have expired
                for datasource in dataset.get_datasources():
                    server = json.loads(datasource.connection_details).get('server')
                    if server in credentials:
                        cred = credentials.get(server)
                        print(f'*** Updating credentials for {server}')
                        if 'token' in cred:
                            datasource.update_credentials(cred['token'])
                        elif 'username' in cred:
                            datasource.update_credentials(cred['username'], cred['password'])

                    else:
                        print(f'*** No credentials provided for {server}')

                print(f'*** Starting refresh...') # We check back later for completion
                dataset.trigger_refresh()

        except SystemExit as e:
            print(f'!! ERROR. Triggering refresh failed for [{dataset.name}]. {e}')
            error = True

    print('* Waiting for models to finish refreshing...')
    for dataset in workspace.datasets:
        if 'Deployment Aid' in dataset.name: continue # Skip deployment aid
        try:
            refresh_status = dataset.get_refresh_state(wait=True) # Wait for each refresh to complete
            if refresh_status == 'Completed':
                print(f'** Refresh complete for [{dataset.name}]')
            else:
                raise SystemExit(refresh_status)

        except SystemExit as e:
            print(f'!! ERROR. Refresh failed for [{dataset.name}]. {e}')
            error = True

    return not error