import os
from .tools import check_file_modified

MODEL_NAME = 'Model.pbix'
DELIMITER = ' -- '

def _name_builder(filepath, **kwargs): # "(branch) -- group -- file -- release"
    filename = os.path.basename(filepath)
    components = [kwargs.get('group'), os.path.splitext(filename)[0], kwargs.get('release')]
    return DELIMITER.join(list(filter(None, components))) # Concatenate components using delimiter, ignoring any empty components

def _name_comparator(a, b):
    a_components = a.split(DELIMITER)
    b_components = b.split(DELIMITER)
    return a_components[:-1] == b_components[:-1] # Compare all except final component (which is the release)

def deploy(pbi_root, workspace, dataset_params=None, credentials=None, force_refresh=False, on_report_success=None, cherry_picks=None, config_workspace=None, release=None):
    error = False
    root, dirs, files = next(os.walk(pbi_root)) # Cycle top level folders only
    for dir in dirs:
        try: # Allow other report groups to deploy, even if others fail
            # 1. Look for model file, check whether it was modified in the last commit (so needs refeshing)
            dataset_file = os.path.join(root, dir, MODEL_NAME) # Expecting exactly one model
            if not os.path.exists(dataset_file):
                print(f'! Warning: No model found in [{dir}]. Skipping folder.')
                continue
            
            force_refresh = force_refresh or check_file_modified(dataset_file)

            # 2. Find report files, including in subfolders (but ignoring model)
            # If cherrypicks are provided, ignore everything else
            report_files = []
            for sub_root, sub_dirs, sub_files in os.walk(os.path.join(root, dir)):
                new_reports = [os.path.join(sub_root, f) for f in sub_files if os.path.splitext(f)[1] == '.pbix' and f != MODEL_NAME and (not cherry_picks or f in cherry_picks or os.path.basename(sub_root) in cherry_picks)]
                report_files.extend(new_reports)

            # 3. Deploy
            print(f'* Deploying {len(report_files)} reports from [{dir}]')
            workspace.deploy(dataset_file, report_files, dataset_params, credentials, force_refresh=force_refresh, on_report_success=on_report_success, name_builder=_name_builder, name_comparator=_name_comparator, group=dir, release=release, config_workspace=config_workspace)

        except SystemExit as e:
            print(f'!! ERROR. Deployment failed for [{root}]. {e}')
            error = True

    return not error