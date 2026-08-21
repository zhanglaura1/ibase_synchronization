import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
import sys
import os
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synchronization import synchronize
from sap_client import SAPClient
from audit import write_audit_report


class TestIntegration:
    """Integration tests for the complete synchronization workflow"""

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    @patch('sap_client.requests.patch')
    def test_end_to_end_synchronization(self, mock_patch, mock_get):
        """Test complete synchronization workflow from fetch to audit"""
        # Mock iBase records
        ibase_response = MagicMock()
        ibase_response.json.return_value = {
            "results": [
                {"ObjectID": "ASSET001", "AddressLine1": "Building A"},
                {"ObjectID": "ASSET002", "AddressLine1": "Building B"}
            ]
        }

        # Mock work reports
        work_response = MagicMock()
        work_response.json.return_value = [
            {"equipmentId": "ASSET001", "location": "Building A", "lastChangeDateTime": datetime(2026, 8, 21, 10, 0)},
            {"equipmentId": "ASSET002", "location": "Building B", "lastChangeDateTime": datetime(2026, 8, 21, 11, 0)}
        ]

        mock_get.side_effect = [ibase_response, work_response]

        client = SAPClient()
        ibase_df = client.get_ibase_records()
        work_df = client.get_work_reports()

        result = synchronize(ibase_df, work_df)

        assert result["matches"] == 2
        assert result["errors"] == 0

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    @patch('synchronization.sap_client')
    def test_sync_with_discrepancy_and_audit(self, mock_sap, mock_get):
        """Test that discrepancies are logged in audit trail"""
        ibase_response = MagicMock()
        ibase_response.json.return_value = {
            "results": [
                {"ObjectID": "ASSET001", "AddressLine1": "Building A"}
            ]
        }

        work_response = MagicMock()
        work_response.json.return_value = [
            {"equipmentId": "ASSET001", "location": "Building B", "lastChangeDateTime": datetime(2026, 8, 21, 10, 0)}
        ]

        mock_get.side_effect = [ibase_response, work_response]
        mock_sap.update_ibase_location.return_value = None

        client = SAPClient()
        ibase_df = client.get_ibase_records()
        work_df = client.get_work_reports()

        result = synchronize(ibase_df, work_df)

        assert result["discrepancies"] == 1
        assert len(result["audit_records"]) == 1
        assert result["audit_records"][0]["result"] == "UPDATED"

    def test_sync_results_can_be_written_to_audit_file(self):
        """Test that sync results can be written to audit file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = os.path.join(tmpdir, "sync_audit.csv")

            ibase_df = pd.DataFrame({
                "ObjectID": ["ASSET001"],
                "AddressLine1": ["Building A"]
            })

            work_df = pd.DataFrame({
                "equipmentId": ["ASSET001"],
                "location": ["Building A"],
                "lastChangeDateTime": [datetime(2026, 8, 21, 10, 0)]
            })

            result = synchronize(ibase_df, work_df)
            write_audit_report(result["audit_records"], audit_path)

            assert os.path.exists(audit_path)
            audit_df = pd.read_csv(audit_path)
            assert len(audit_df) == 1

    @patch.dict(os.environ, {
        'SAP_BASE_URL': 'https://api.sap.example.com',
        'SAP_API_KEY': 'test-key-123'
    })
    @patch('sap_client.requests.get')
    def test_multiple_sync_runs_can_be_tracked(self, mock_get):
        """Test that multiple sync operations can be tracked separately"""
        # First sync run
        ibase_response1 = MagicMock()
        ibase_response1.json.return_value = {
            "results": [
                {"ObjectID": "ASSET001", "AddressLine1": "Building A"}
            ]
        }

        work_response1 = MagicMock()
        work_response1.json.return_value = [
            {"equipmentId": "ASSET001", "location": "Building A", "lastChangeDateTime": datetime(2026, 8, 21, 10, 0)}
        ]

        # Second sync run with different data
        ibase_response2 = MagicMock()
        ibase_response2.json.return_value = {
            "results": [
                {"ObjectID": "ASSET002", "AddressLine1": "Building B"}
            ]
        }

        work_response2 = MagicMock()
        work_response2.json.return_value = [
            {"equipmentId": "ASSET002", "location": "Building B", "lastChangeDateTime": datetime(2026, 8, 21, 11, 0)}
        ]

        mock_get.side_effect = [
            ibase_response1, work_response1,
            ibase_response2, work_response2
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            client = SAPClient()

            # First sync
            ibase_df1 = client.get_ibase_records()
            work_df1 = client.get_work_reports()
            result1 = synchronize(ibase_df1, work_df1)
            audit_path1 = os.path.join(tmpdir, "audit_1.csv")
            write_audit_report(result1["audit_records"], audit_path1)

            # Second sync
            ibase_df2 = client.get_ibase_records()
            work_df2 = client.get_work_reports()
            result2 = synchronize(ibase_df2, work_df2)
            audit_path2 = os.path.join(tmpdir, "audit_2.csv")
            write_audit_report(result2["audit_records"], audit_path2)

            # Both files should exist and be different
            assert os.path.exists(audit_path1)
            assert os.path.exists(audit_path2)

            audit1 = pd.read_csv(audit_path1)
            audit2 = pd.read_csv(audit_path2)

            assert audit1.iloc[0]["equipment_id"] == "ASSET001"
            assert audit2.iloc[0]["equipment_id"] == "ASSET002"

    def test_sync_handles_large_dataset(self):
        """Test synchronization with large number of records"""
        n_records = 1000

        ibase_data = {
            "ObjectID": [f"ASSET{i:05d}" for i in range(n_records)],
            "AddressLine1": [f"Building {i % 26}" for i in range(n_records)]
        }

        work_data = {
            "equipmentId": [f"ASSET{i:05d}" for i in range(n_records)],
            "location": [f"Building {i % 26}" for i in range(n_records)],
            "lastChangeDateTime": [datetime(2026, 8, 21, 10, 0)] * n_records
        }

        ibase_df = pd.DataFrame(ibase_data)
        work_df = pd.DataFrame(work_data)

        result = synchronize(ibase_df, work_df)

        assert result["processed"] == n_records
        assert result["matches"] == n_records
        assert result["discrepancies"] == 0

    def test_sync_results_summary_is_accurate(self):
        """Test that sync summary statistics are correct"""
        ibase_df = pd.DataFrame({
            "ObjectID": ["ASSET001", "ASSET002", "ASSET003"],
            "AddressLine1": ["Building A", "Building B", "Building C"]
        })

        work_df = pd.DataFrame({
            "equipmentId": ["ASSET001", "ASSET002", "ASSET004"],
            "location": ["Building A", "Building B", "Building D"],
            "lastChangeDateTime": [
                datetime(2026, 8, 21, 10, 0),
                datetime(2026, 8, 21, 11, 0),
                datetime(2026, 8, 21, 12, 0)
            ]
        })

        result = synchronize(ibase_df, work_df)

        # Summary should match audit records
        total_audited = (
            result["matches"] +
            result["discrepancies"] +
            result["missing_in_ibase"] +
            result["errors"]
        )
        assert total_audited == len(result["audit_records"])
