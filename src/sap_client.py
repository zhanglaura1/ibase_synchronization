import requests, os
import pandas as pd

class SAPClient:

    def __init__(self):
        self.base_url = os.getenv("SAP_BASE_URL")
        self.api_key = os.getenv("SAP_API_KEY")

    def _get(self, endpoint, params=None):
        response = requests.get(
            f"{self.base_rul}/{endpoint}",
            headers={
                "APIKey": self.api_key,
                "Accept": "application/json",
                "DataServiceVersion": '2.0'
            },
            params=params
        )
    def get_ibase_records(self):
        data = self._get(
            'sap/c4c/odata/v1/c4codataapi/InstalledBaseCollection',
            params={
                "$select": "ObjectID,AddressLine1"
            }
        )
        return pd.DataFrame(data["results"])

    def get_work_reports(self):
        data = self._get(
            'sapassetintelligencenetwork/workorders',
            params={
                "$select": "equipmentId, location"
            }
        )
        return pd.DataFrame(data)

    def update_ibase_location(self):
        # also update LastChangedOn
        pass