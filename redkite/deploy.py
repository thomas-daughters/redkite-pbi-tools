import os
from .tools import check_file_modified

MODEL_NAME = 'Model.pbix'
DELIMITER = ' -- '

def _name_builder(filepath, **kwargs): # "(branch) -- group -- file -- release"
    filename = os.path.basename(filepath)
    components = [kwargs.get('group'), os.path.splitext(filename)[0], kwargs.get('release')]
    return DELIMITER.join(list(filter(None, components))) # Concatenate components using delimiter, ignoring any empty components

def _name_comparator(a, b, overwrite_reports=False):
    if overwrite_reports: return a == b # If overwriting reports the names will share the same structure
    a_components = a.split(DELIMITER)
    b_components = b.split(DELIMITER)
    return a_components[:-1] == b_components[:-1] # Compare all except final component (which is the release)

def deploy(pbi_root, workspace, dataset_params=None, credentials=None, force_refresh=None, on_report_success=None, cherry_picks=None, config_workspace=None, release=None, overwrite_reports=False):
    error = False
    root, dirs, files = next(os.walk(pbi_root)) # Cycle top level folders only
    for dir in dirs:
        try: # Allow other report groups to deploy, even if others fail
            # 1. Look for model file
            dataset_file = os.path.join(root, dir, MODEL_NAME) # Expecting exactly one model
            if not os.path.exists(dataset_file):
                print(f'! Warning: No model found in [{dir}]. Skipping folder.')
                continue
            
            # Respect 'refresh override' value if given, otherwise check the latest commit to see whether the model was changed
            local_force_refresh = check_file_modified(dataset_file) if force_refresh is None else force_refresh

            # 2. Find report files, including in subfolders (but ignoring model)
            # If cherrypicks are provided, ignore everything else
            report_files = []
            for sub_root, sub_dirs, sub_files in os.walk(os.path.join(root, dir)):
                new_reports = [os.path.join(sub_root, f) for f in sub_files if os.path.splitext(f)[1] == '.pbix' and f != MODEL_NAME and (not cherry_picks or f in cherry_picks or os.path.basename(sub_root) in cherry_picks)]
                report_files.extend(new_reports)

            # 3. Deploy
            print(f'* Deploying {len(report_files)} reports from [{dir}]')
            workspace.deploy(dataset_file, report_files, dataset_params, credentials, force_refresh=local_force_refresh, on_report_success=on_report_success, name_builder=_name_builder, name_comparator=_name_comparator, group=dir, release=release, config_workspace=config_workspace, overwrite_reports=overwrite_reports)

        except SystemExit as e:
            print(f'!! ERROR. Deployment failed for [{root}]. {e}')
            error = True

    return not error
