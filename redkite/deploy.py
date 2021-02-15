import os
from os.path import basename

MODEL_NAME = 'Model.pbix'
DELIMITER = ' -- '

def name_builder(filepath, **kwargs): # "group -- filename"
    group = kwargs.get('group')
    filename = os.path.basename(filepath)
    return DELIMITER.join([group, filename])

def deploy(pbi_root, workspace, dataset_params=None, credentials=None, force_refresh=False, on_report_success=None, exclusions=[]):
    root, dirs, files = next(os.walk(pbi_root)) # Cycle top level folders only
    for dir in dirs:
        try: # Allow other report groups to deploy, even if others fail
            # 1. Look for model file
            dataset_file = os.path.join(root, dir, MODEL_NAME) # Expecting exactly one model
            if not os.path.exists(dataset_file):
                print(f'! Warning: No model found in [{dir}]. Skipping folder.')
                continue

            # 2. Find report files, including in subfolders (but ignoring model and any file/folder exclusions)
            report_files = []
            for sub_root, sub_dirs, sub_files in os.walk(os.path.join(root, dir)):
                new_reports = [os.path.join(sub_root, f) for f in sub_files if os.path.splitext(f)[1] == '.pbix' and f != MODEL_NAME and f not in exclusions and os.path.basename(sub_root) not in exclusions]
                report_files.extend(new_reports)

            # 3. Deploy
            print(f'* Deploying {len(report_files)} reports from [{dir}]')
            workspace.deploy(dataset_file, report_files, dataset_params, credentials, force_refresh, on_report_success=on_report_success, name_builder=name_builder, group=dir)

        except SystemExit as e:
            print(f'!! ERROR. Deployment failed for [{root}]. {e}')
            error = True

    return not error