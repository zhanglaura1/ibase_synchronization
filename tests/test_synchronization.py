import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synchronization import synchronize, normalize


class TestNormalize:
    """Tests for the normalize function"""

    def test_normalize_converts_to_lowercase(self):
        assert normalize("BUILDING A") == "building a"

    def test_normalize_strips_whitespace(self):
        assert normalize("  building a  ") == "building a"

    def test_normalize_handles_none(self):
        assert normalize(None) is None

    def test_normalize_converts_to_string(self):
        assert normalize(123) == "123"

    def test_normalize_empty_string(self):
        assert normalize("") == ""

    def test_normalize_special_characters(self):
        assert normalize("Building-A/123") == "building-a/123"


class TestSynchronize:
    """Tests for the main synchronize function"""

    def setup_method(self):
        """Setup test data before each test"""
        self.ibase_df = pd.DataFrame({
            "ObjectID": ["ASSET001", "ASSET002", "ASSET003"],
            "AddressLine1": ["Building A", "Building B", "Building C"]
        })

        self.work_report_df = pd.DataFrame({
            "equipmentId": ["ASSET001", "ASSET002", "ASSET004"],
            "location": ["Building A", "Building B", "Building D"],
            "lastChangeDateTime": [
                datetime(2026, 8, 21, 10, 0),
                datetime(2026, 8, 21, 11, 0),
                datetime(2026, 8, 21, 12, 0)
            ]
        })

    def test_synchronize_returns_expected_structure(self):
        """Test that synchronize returns correct result structure"""
        result = synchronize(self.ibase_df, self.work_report_df)

        assert "processed" in result
        assert "matches" in result
        assert "discrepancies" in result
        assert "missing_in_ibase" in result
        assert "errors" in result
        assert "audit_records" in result

    def test_synchronize_counts_matches(self):
        """Test that matching locations are counted correctly"""
        result = synchronize(self.ibase_df, self.work_report_df)

        # ASSET001 and ASSET002 should match
        assert result["matches"] == 2

    def test_synchronize_counts_missing_in_ibase(self):
        """Test that equipment missing from iBase is counted"""
        result = synchronize(self.ibase_df, self.work_report_df)

        # ASSET004 is missing in iBase
        assert result["missing_in_ibase"] == 1

    def test_synchronize_creates_match_audit_record(self):
        """Test that matching records create MATCH audit entries"""
        result = synchronize(self.ibase_df, self.work_report_df)

        match_records = [
            r for r in result["audit_records"]
            if r["result"] == "MATCH"
        ]
        assert len(match_records) == 2

    def test_synchronize_creates_missing_audit_record(self):
        """Test that missing equipment creates MISSING_IN_IBASE audit entry"""
        result = synchronize(self.ibase_df, self.work_report_df)

        missing_records = [
            r for r in result["audit_records"]
            if r["result"] == "MISSING_IN_IBASE"
        ]
        assert len(missing_records) == 1
        assert missing_records[0]["equipment_id"] == "ASSET004"

    def test_synchronize_normalizes_location_comparison(self):
        """Test that locations are normalized before comparison"""
        ibase = pd.DataFrame({
            "ObjectID": ["ASSET001"],
            "AddressLine1": ["  BUILDING A  "]
        })
        work_report = pd.DataFrame({
            "equipmentId": ["ASSET001"],
            "location": ["building a"],
            "lastChangeDateTime": [datetime(2026, 8, 21, 10, 0)]
        })

        result = synchronize(ibase, work_report)

        assert result["matches"] == 1

    def test_synchronize_handles_none_sap_location(self):
        """Test that missing SAP location is treated as error"""
        work_report = pd.DataFrame({
            "equipmentId": ["ASSET001"],
            "location": [None],
            "lastChangeDateTime": [datetime(2026, 8, 21, 10, 0)]
        })

        result = synchronize(self.ibase_df, work_report)

        assert result["errors"] == 1
        error_records = [
            r for r in result["audit_records"]
            if r["result"] == "ERROR"
        ]
        assert len(error_records) == 1
        assert "SAP location is missing" in error_records[0].get("error", "")

    @patch('synchronization.sap_client')
    def test_synchronize_updates_discrepancy(self, mock_sap):
        """Test that location discrepancies trigger updates"""
        work_report = pd.DataFrame({
            "equipmentId": ["ASSET001"],
            "location": ["Building X"],
            "lastChangeDateTime": [datetime(2026, 8, 21, 10, 0)]
        })

        result = synchronize(self.ibase_df, work_report)

        # Should have 1 discrepancy and attempt update
        assert result["discrepancies"] == 1
        mock_sap.update_ibase_location.assert_called_once_with(
            "ASSET001", "Building X"
        )

    @patch('synchronization.sap_client')
    def test_synchronize_logs_update_success(self, mock_sap):
        """Test that successful updates are logged"""
        mock_sap.update_ibase_location.return_value = None

        work_report = pd.DataFrame({
            "equipmentId": ["ASSET001"],
            "location": ["Building X"],
            "lastChangeDateTime": [datetime(2026, 8, 21, 10, 0)]
        })

        result = synchronize(self.ibase_df, work_report)

        updated_records = [
            r for r in result["audit_records"]
            if r["result"] == "UPDATED"
        ]
        assert len(updated_records) == 1

    @patch('synchronization.sap_client')
    def test_synchronize_handles_update_error(self, mock_sap):
        """Test that update errors are caught and logged"""
        mock_sap.update_ibase_location.side_effect = Exception("API Error")

        work_report = pd.DataFrame({
            "equipmentId": ["ASSET001"],
            "location": ["Building X"],
            "lastChangeDateTime": [datetime(2026, 8, 21, 10, 0)]
        })

        result = synchronize(self.ibase_df, work_report)

        assert result["errors"] == 1
        error_records = [
            r for r in result["audit_records"]
            if r["result"] == "UPDATE_ERROR"
        ]
        assert len(error_records) == 1
        assert "API Error" in error_records[0].get("error", "")

    def test_synchronize_sorts_by_last_change_datetime(self):
        """Test that work reports are sorted by lastChangeDateTime"""
        work_report = pd.DataFrame({
            "equipmentId": ["ASSET002", "ASSET001"],
            "location": ["Building B", "Building A"],
            "lastChangeDateTime": [
                datetime(2026, 8, 21, 10, 0),
                datetime(2026, 8, 21, 12, 0)
            ]
        })

        result = synchronize(self.ibase_df, work_report)

        # Both should match, order shouldn't affect result
        assert result["matches"] == 2

    def test_synchronize_removes_duplicates(self):
        """Test that duplicate equipmentIds are handled"""
        work_report = pd.DataFrame({
            "equipmentId": ["ASSET001", "ASSET001"],
            "location": ["Building A", "Building A"],
            "lastChangeDateTime": [
                datetime(2026, 8, 21, 10, 0),
                datetime(2026, 8, 21, 12, 0)
            ]
        })

        result = synchronize(self.ibase_df, work_report)

        # Should only process one ASSET001
        assert result["processed"] == 1

    def test_synchronize_empty_work_report(self):
        """Test synchronization with empty work report"""
        empty_work_report = pd.DataFrame({
            "equipmentId": [],
            "location": [],
            "lastChangeDateTime": []
        })

        result = synchronize(self.ibase_df, empty_work_report)

        assert result["processed"] == 0
        assert result["matches"] == 0
        assert result["discrepancies"] == 0

    def test_synchronize_audit_records_contain_location_data(self):
        """Test that audit records contain both SAP and iBase locations"""
        result = synchronize(self.ibase_df, self.work_report_df)

        for record in result["audit_records"]:
            assert "equipment_id" in record
            assert "location_sap" in record
            assert "location_ibase" in record
            assert "result" in record

    def test_synchronize_counts_processed_records(self):
        """Test that processed count matches work report length after dedup"""
        result = synchronize(self.ibase_df, self.work_report_df)

        # 3 unique equipment IDs in work report
        assert result["processed"] == 3

    def test_synchronize_discrepancies_require_update_attempt(self):
        """Test that discrepancies are followed by update attempts"""
        with patch('synchronization.sap_client') as mock_sap:
            work_report = pd.DataFrame({
                "equipmentId": ["ASSET001", "ASSET002"],
                "location": ["Building X", "Building Y"],
                "lastChangeDateTime": [
                    datetime(2026, 8, 21, 10, 0),
                    datetime(2026, 8, 21, 11, 0)
                ]
            })

            result = synchronize(self.ibase_df, work_report)

            # Both are discrepancies
            assert result["discrepancies"] == 2
            # Both should trigger update attempts
            assert mock_sap.update_ibase_location.call_count == 2
