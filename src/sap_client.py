import requests, os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class SAPClient:

    def __init__(self):
        self.base_url = os.getenv("SAP_BASE_URL")
        self.api_key = os.getenv("SAP_API_KEY")

    def _get(self, endpoint, params=None):
        response = requests.get(
            f"{self.base_url}/{endpoint}",
            headers={
                "APIKey": self.api_key,
                "Accept": "application/json",
                "DataServiceVersion": '2.0'
            },
            params=params
        )

        response.raise_for_status()
        return response.json()

    def get_ibase_records(self):
        data = self._get(
            'sap/c4c/odata/v1/c4codataapi/InstalledBaseCollection',
            params={
                "$select": "ObjectID,AddressLine1"
            }
        )
        return pd.DataFrame(data["d"]["results"])

    def get_work_reports(self):
        data = self._get(
            'sapassetintelligencenetwork/workorders',
            params={
                "$select": "equipmentId,location,lastChangeDateTime"
            }
        )
        return pd.DataFrame(data)

    def update_ibase_location(self, ObjectID, location):
        endpoint = (
            f"sap/c4c/odata/v1/c4codataapi/InstalledBaseCollection"
            f"('\''{ObjectID}'\'')"
        )

        response = requests.patch(
            f"{self.base_url}/{endpoint}",
            headers={
                "APIKey": self.api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "DataServiceVersion": '2.0'
            },
            json={
                "AddressLine1": location
            }
        )

        response.raise_for_status()