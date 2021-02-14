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

    def sync_report(self, report, stage):
        payload = {
            "ReportName": report.name,
            "ModelType": 'PBI' if report.dataset.has_rls else 'NoRLS',
            "PowerBIConfigurations": [{
                "EnvironmentId": self.envs[stage]['Id'],
                "GroupId": report.workspace.id,
                "ReportId": report.id
            }]
        }

        matching_reports = [r for r in self.reports if r['ReportName'] == report.name]
        if len(matching_reports) > 0: # If report exists on Portal, add it to API call (to trigger update rather than insert)
            payload['PowerBIReportId'] = matching_reports[0]['Id']
        else:
            print(f'Adding {report.name} to {self.env} Portal')

        r = requests.put(f'{self.api_url}/admin/report-configuration', headers=self.get_headers(), json=payload)
        json = handle_request(r)
        return json

    def delete_report(self, report):
        r = requests.delete(f'{self.api_url}/admin/report-configuration/{report["Id"]}', headers=self.get_headers())
        handle_request(r)