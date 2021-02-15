import os
from pbi import tools

AID_REPORT_NAME = 'Deployment Aid Report'

def deploy(workspace, dataset_filepath, report_filepaths, dataset_params=None, credentials=None, force_refresh=False, on_report_success=None, name_builder=None, **kwargs):
    # 1. Get dummy connections string from 'aid report'
    aid_report = workspace.find_report(AID_REPORT_NAME) # Find aid report to get new dataset connection string
    if aid_report is None:
        raise SystemExit('ERROR: Cannot find Deployment Aid Report')

    with open(AID_REPORT_NAME, 'wb') as report_file: # Get connection string from aid report
        report_file.write(aid_report.download())
    connection_string = tools.get_connection_string(AID_REPORT_NAME)

    # 2. Publish dataset or get existing dataset (if unchanged and current)
    dataset_name = name_builder(dataset_filepath, **kwargs) if name_builder else os.path.basename(dataset_filepath) # Allow custom name formation, default to filename
    matching_datasets = [d for d in workspace.datasets if d.name == dataset_name] # Look for existing dataset
    dataset_modified = tools.check_file_modified(dataset_filepath)

    if matching_datasets and not dataset_modified and not force_refresh: # Only publish dataset if it's been updated (or override used):
        dataset = matching_datasets.pop() # Get the latest dataset
        print(f'** Using existing dataset [{dataset.name}]')
    
    else:
        print(f'** Publishing dataset [{dataset_filepath}] as [{dataset_name}]...')
        new_datasets, new_reports = workspace.publish_file(dataset_filepath, dataset_name, skipReports=True)
        dataset = new_datasets.pop()

    # 3. Update params and credentials, then refresh (unless current)
    if dataset.get_refresh_state() not in ('Completed', 'Unknown'): # If we're using a valid exising dataset, don't touch it
        dataset.take_ownership() # Publishing does not change ownership, so make sure we own it before continuing

        print('*** Updating parameters...')
        param_keys = [p['name'] for p in dataset.get_params()]
        params = [{'name': k, 'newValue': v} for k, v in dataset_params.items() if k in param_keys] # Only try to update params that are defined for this dataset
        if params: dataset.update_params({'updateDetails': params})

        print('*** Authenticating...')
        dataset.authenticate(credentials)

        print('*** Triggering refresh') # We check back later for completion
        dataset.trigger_refresh()
    
    # 4. Wait for refresh to complete (stop on error)
    refresh_state = dataset.get_refresh_state(wait=True) # Wait for any dataset refreshes to finish before continuing
    if refresh_state != 'Completed':
        raise SystemExit(f'Refresh failed: {refresh_state}')
    
    if not matching_datasets: print('*** Dataset refreshed') # Don't report completed refresh if we used an existing dataset

    # 5. Publish reports (using dummy connection string initially)
    for filepath in report_filepaths: # Import report files
        report_name = name_builder(filepath, **kwargs) if name_builder else os.path.basename(filepath) # Allow custom name formation, default to filename
    
        print(f'** Publishing report [{filepath}] as [{report_name}]...') # Alter PBIX file with dummy dataset, in case dataset used during development has since been deleted (we repoint once on service)
        tools.rebind_report(filepath, connection_string)
        new_datasets, new_reports = workspace.publish_file(filepath, report_name)

        # 6. Repoint to refreshed model and update Portals (if given)
        for report in new_reports:
            report.repoint(dataset) # Once published, repoint from dummy to new dataset
            if on_report_success: on_report_success(report, **kwargs) # Perform any final post-deploy actions

    # 7. Delete old model (old report automatically go too)
    for old_dataset in matching_datasets:
        print(f'** Deleting old dataset [{old_dataset.name}]')
        old_dataset.delete()