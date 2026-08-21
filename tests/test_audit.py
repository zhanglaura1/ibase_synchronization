import pytest
import pandas as pd
import os
import sys
from datetime import datetime
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audit import write_audit_report


class TestAuditReport:
    """Tests for the audit reporting functionality"""

    def test_write_audit_report_creates_file(self):
        """Test that write_audit_report creates a CSV file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            records = [
                {
                    "equipment_id": "ASSET001",
                    "location_sap": "Building A",
                    "location_ibase": "Building A",
                    "result": "MATCH"
                }
            ]

            result = write_audit_report(records, filepath)

            assert os.path.exists(filepath)
            assert result == filepath

    def test_write_audit_report_correct_format(self):
        """Test that audit report is written in correct CSV format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            records = [
                {
                    "equipment_id": "ASSET001",
                    "location_sap": "Building A",
                    "location_ibase": "Building A",
                    "result": "MATCH"
                },
                {
                    "equipment_id": "ASSET002",
                    "location_sap": "Building B",
                    "location_ibase": "Building C",
                    "result": "DISCREPANCY"
                }
            ]

            write_audit_report(records, filepath)

            df = pd.read_csv(filepath)
            assert len(df) == 2
            assert list(df.columns) == ["equipment_id", "location_sap", "location_ibase", "result"]

    def test_write_audit_report_with_error_field(self):
        """Test that error field is preserved in audit report"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            records = [
                {
                    "equipment_id": "ASSET001",
                    "location_sap": None,
                    "location_ibase": "Building A",
                    "result": "ERROR",
                    "error": "SAP location is missing"
                }
            ]

            write_audit_report(records, filepath)

            df = pd.read_csv(filepath)
            assert "error" in df.columns
            assert df.iloc[0]["error"] == "SAP location is missing"

    def test_write_audit_report_handles_missing_values(self):
        """Test that None values are handled correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            records = [
                {
                    "equipment_id": "ASSET001",
                    "location_sap": None,
                    "location_ibase": "Building A",
                    "result": "MISSING_IN_SAP"
                }
            ]

            write_audit_report(records, filepath)

            df = pd.read_csv(filepath)
            assert pd.isna(df.iloc[0]["location_sap"])

    def test_write_audit_report_default_filename(self):
        """Test that default filename is audit_report.csv"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                records = [
                    {
                        "equipment_id": "ASSET001",
                        "location_sap": "Building A",
                        "location_ibase": "Building A",
                        "result": "MATCH"
                    }
                ]

                result = write_audit_report(records)

                assert result == "audit_report.csv"
                assert os.path.exists("audit_report.csv")
            finally:
                os.chdir(original_cwd)

    def test_write_audit_report_empty_records(self):
        """Test that empty records list creates empty CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            records = []

            write_audit_report(records, filepath)

            # Empty DataFrame will have no columns when written to CSV
            # Check file exists and is valid CSV
            assert os.path.exists(filepath)
            # Reading empty CSV without columns raises EmptyDataError, which is expected
            try:
                df = pd.read_csv(filepath)
                # If it succeeds, it should have 0 rows
                assert len(df) == 0
            except pd.errors.EmptyDataError:
                # This is expected for completely empty CSVs
                pass

    def test_write_audit_report_multiple_records(self):
        """Test that multiple records are all written"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            records = [
                {
                    "equipment_id": f"ASSET{i:03d}",
                    "location_sap": f"Building {chr(65 + i)}",
                    "location_ibase": f"Building {chr(65 + i)}",
                    "result": "MATCH"
                }
                for i in range(10)
            ]

            write_audit_report(records, filepath)

            df = pd.read_csv(filepath)
            assert len(df) == 10

    def test_write_audit_report_preserves_data_integrity(self):
        """Test that data is not corrupted during write"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            original_records = [
                {
                    "equipment_id": "ASSET001",
                    "location_sap": "Building A (Main)",
                    "location_ibase": "Building A (Main)",
                    "result": "MATCH"
                }
            ]

            write_audit_report(original_records, filepath)

            df = pd.read_csv(filepath)
            assert df.iloc[0]["location_sap"] == "Building A (Main)"

    def test_write_audit_report_overwrites_existing_file(self):
        """Test that existing file is overwritten"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_audit.csv")

            # Write first batch
            records1 = [
                {"equipment_id": "ASSET001", "result": "MATCH"}
            ]
            write_audit_report(records1, filepath)

            # Write second batch
            records2 = [
                {"equipment_id": "ASSET002", "result": "MATCH"},
                {"equipment_id": "ASSET003", "result": "MATCH"}
            ]
            write_audit_report(records2, filepath)

            df = pd.read_csv(filepath)
            # Should only have second batch records
            assert len(df) == 2
            assert "ASSET002" in df["equipment_id"].values
