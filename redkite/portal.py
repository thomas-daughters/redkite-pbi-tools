import requests
from pbi.tools import handle_request

class Portal:
    def __init__(self, env, token):
        self.token = token
        self.env = env
        self.api_url = f'https://diageo-eun-orion-datagovernanceapi-{env}.azurewebsites.net'
        self.get_reports()
        self.get_envs()

    def get_headers(self):
        return {'Authorization': f'Bearer {self.token.get_token()}'}

    def get_reports(self):
        r = requests.get(f'{self.api_url}/admin/report-detail', headers=self.get_headers())
        json = handle_request(r)

        self.reports = json
        return self.reports

    def get_report_configs(self):
        r = requests.get(f'{self.api_url}/admin/report-configuration', headers=self.get_headers())
        json = handle_request(r)

        self.report_configs = json
        return self.report_configs
    
    def get_menu_items(self):
        r = requests.get(f'{self.api_url}/admin/menu', headers=self.get_headers())
        json = handle_request(r)

        self.menu_items = json
        return self.menu_items

    def get_envs(self):
        r = requests.get(f'{self.api_url}/admin/report-environment', headers=self.get_headers())
        handle_request(r)

        self.envs = {}
        for e in r.json(): self.envs[e['Name']] = e
        return self.envs

    def sync_report(self, report, stage, tag=None):
        if stage not in self.envs:
            return # Not all PBI environments will surface through Portal

        print(f'*** Updating GPS: {self.env} environment')
        report_name = report.name.rsplit(' -- ', 1)[0] # Remove release name from end
        # TODO: Avoid hard coding delimiter and abstract to allow more generic patterns
        
        payload = {
            "ReportName": report_name,
            "ModelType": 'PBI' if report.dataset.has_rls else 'NoRLS',
            "Tags": tag,
            "PowerBIConfigurations": [{
                "EnvironmentId": self.envs[stage]['Id'],
                "GroupId": report.workspace.id,
                "ReportId": report.id
            }]
        }

        matching_reports = [r for r in self.reports if r['ReportName'] == report_name]
        if len(matching_reports) > 0: # If report exists on Portal, add it to API call (to trigger update rather than insert)
            payload['PowerBIReportId'] = matching_reports[0]['Id']
        else:
            print(f'! Warning: Adding {report_name} to {self.env} Portal')

        r = requests.put(f'{self.api_url}/admin/report-configuration', headers=self.get_headers(), json=payload)
        json = handle_request(r)
        return json

    def delete_report(self, report):
        r = requests.delete(f'{self.api_url}/admin/report-configuration/{report["Id"]}', headers=self.get_headers())
        handle_request(r)

    def get_restriction_types(self):
        r = requests.get(f'{self.api_url}/admin/user-restriction-type', headers=self.get_headers())

        json = handle_request(r)
        return json

    def get_users(self):
        r = requests.get(f'{self.api_url}/admin/user', headers=self.get_headers())

        json = handle_request(r)
        return json

    def get_user(self, id):
        r = requests.get(f'{self.api_url}/admin/user/{id}', headers=self.get_headers())

        json = handle_request(r)
        return json

    def get_old_users(self):
        r = requests.get(f'{self.api_url}/users', headers=self.get_headers())

        json = handle_request(r)
        return json

    def get_user_types(self):
        r = requests.get(f'{self.api_url}/admin/user-type', headers=self.get_headers())

        json = handle_request(r)
        return json

    def get_user_profiles(self):
        r = requests.get(f'{self.api_url}/admin/profile', headers=self.get_headers())

        json = handle_request(r)
        return json

    def create_user(self, email, first, last, type_key, restrictions):
        restrictions_payload = []
        for r in restrictions:
            restrictions_payload.append({
                "RestrictionKey": r['key'],
                "RestrictionValue": r['value'],
            })

        payload = {
            'User': {
                'EmailAddress': email,
                'FirstName': first,
                'SecondName': last,    
                'UserTypeKey': type_key,
            },
            'Restrictions': restrictions_payload
        }

        r = requests.post(f'{self.api_url}/admin/user', headers=self.get_headers(), json=payload)

        json = handle_request(r)
        return json

    def update_user(self, id, email, first, last, type_key, restrictions):
        restrictions_payload = self.get_user(id)
        
        for r in restrictions:
            restrictions_payload.append({
                'UserKey': id,
                "RestrictionKey": r['key'],
                "RestrictionValue": r['value'],
            })

        payload = {
            'User': {
                'UserKey': id,
                'EmailAddress': email,
                'FirstName': first,
                'SecondName': last,    
                'UserTypeKey': type_key,
            },
            'Restrictions': restrictions_payload
        }

        r = requests.put(f'{self.api_url}/admin/user/{id}', headers=self.get_headers(), json=payload)

        json = handle_request(r)
        return json
