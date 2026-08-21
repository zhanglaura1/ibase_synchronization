import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sap_client import SAPClient


class TestSAPClient:
    """Tests for the SAPClient class"""

    def setup_method(self):
        """Setup before each test"""
        self.client = SAPClient()

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    def test_sap_client_initialization(self):
        """Test that SAPClient initializes with environment variables"""
        client = SAPClient()
        assert client.base_url == 'https://api.sap.example.com'
        assert client.api_key == 'test-key-123'

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    def test_get_ibase_records_success(self, mock_get):
        """Test successful retrieval of iBase records"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"ObjectID": "ASSET001", "AddressLine1": "Building A"},
                {"ObjectID": "ASSET002", "AddressLine1": "Building B"}
            ]
        }
        mock_get.return_value = mock_response

        client = SAPClient()
        result = client.get_ibase_records()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "ObjectID" in result.columns
        assert "AddressLine1" in result.columns

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    def test_get_ibase_records_api_error(self, mock_get):
        """Test handling of API errors in get_ibase_records"""
        mock_get.side_effect = Exception("Connection error")

        client = SAPClient()
        with pytest.raises(Exception):
            client.get_ibase_records()

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    def test_get_work_reports_success(self, mock_get):
        """Test successful retrieval of work reports"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"equipmentId": "ASSET001", "location": "Building A"},
            {"equipmentId": "ASSET002", "location": "Building B"}
        ]
        mock_get.return_value = mock_response

        client = SAPClient()
        result = client.get_work_reports()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "equipmentId" in result.columns
        assert "location" in result.columns

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.patch')
    def test_update_ibase_location_success(self, mock_patch):
        """Test successful location update"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_patch.return_value = mock_response

        client = SAPClient()
        client.update_ibase_location("ASSET001", "Building X")

        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        assert "ASSET001" in call_args[0][0]

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.patch')
    def test_update_ibase_location_api_error(self, mock_patch):
        """Test handling of API errors in location update"""
        mock_patch.side_effect = Exception("Update failed")

        client = SAPClient()
        with pytest.raises(Exception):
            client.update_ibase_location("ASSET001", "Building X")

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    def test_get_includes_required_headers(self, mock_get):
        """Test that API calls include required headers"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        client = SAPClient()
        client.get_ibase_records()

        call_headers = mock_get.call_args[1]['headers']
        assert call_headers['APIKey'] == 'test-key-123'
        assert call_headers['Accept'] == 'application/json'
        assert call_headers['DataServiceVersion'] == '2.0'

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.patch')
    def test_update_includes_content_type(self, mock_patch):
        """Test that update requests include Content-Type header"""
        mock_response = MagicMock()
        mock_patch.return_value = mock_response

        client = SAPClient()
        client.update_ibase_location("ASSET001", "Building X")

        call_headers = mock_patch.call_args[1]['headers']
        assert call_headers['Content-Type'] == 'application/json'

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    def test_get_ibase_records_odata_endpoint(self, mock_get):
        """Test that correct OData endpoint is called"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        client = SAPClient()
        client.get_ibase_records()

        call_url = mock_get.call_args[0][0]
        assert 'InstalledBaseCollection' in call_url
