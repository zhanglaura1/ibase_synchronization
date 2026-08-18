import requests, os

api_key = os.getenv("SAP_API_KEY")
url = 'https://sandbox.api.sap.com/successfactorsfoundation/odata/v2/User?%24top=20'

headers = {
    'APIKey': api_key,
    'Accept': 'application/json',
    'DataServiceVersion': '2.0',
}

response = requests.get(url, headers=headers)
response.raise_for_status()  # Raise an error for bad responses
data = response.json()

print(data)