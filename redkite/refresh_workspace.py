import json

def refresh_workspace(workspace, credentials):
    for dataset in workspace.datasets:
        if dataset.get_refresh_state() == 'Unknown': # Don't trigger refresh if model is already refreshing
            print(f'** [{dataset.name}] is already refreshing')
        else:
            print(f'** Reconfiguring [{dataset.name}]')
            dataset.take_ownership() # In case someone manually took control post deployment

            print(f'*** Reauthenticating data sources...') # Reauthenticate as tokens obtained during deployment will have expired
            for datasource in dataset.get_datasources():
                server = json.loads(datasource.connection_details).get('server')
                if cred = credentials.get(server):
                    print(f'*** Updating credentials for {server}')
                    if token in cred:
                        datasource.update_credentials(cred['token'])
                    elif username in cred:
                        datasource.update_credentials(cred['username'], cred['password'])

                else:
                    print(f'*** No credentials provided for {server}')

            print(f'*** Starting refresh...') # We check back later for completion
            dataset.trigger_refresh()

    print('* Waiting for models to finish refreshing...')
    for dataset in workspace.datasets:
        try:
            refresh_status = dataset.get_refresh_state(wait=True) # Wait for each refresh to complete
            if refresh_status == 'Completed':
                print(f'** Refresh complete for [{dataset.name}]')
            else:
                raise SystemExit(refresh_status)

        except SystemExit as e:
            print(f'!! ERROR. Refresh failed for [{dataset.name}]. {e}')