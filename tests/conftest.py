import pytest
import pandas as pd
from datetime import datetime
import sys
import os

# Add src directory to path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_ibase_df():
    """Fixture providing sample iBase data"""
    return pd.DataFrame({
        "ObjectID": ["ASSET001", "ASSET002", "ASSET003"],
        "AddressLine1": ["Building A", "Building B", "Building C"]
    })


@pytest.fixture
def sample_work_report_df():
    """Fixture providing sample work report data"""
    return pd.DataFrame({
        "equipmentId": ["ASSET001", "ASSET002", "ASSET004"],
        "location": ["Building A", "Building B", "Building D"],
        "lastChangeDateTime": [
            datetime(2026, 8, 21, 10, 0),
            datetime(2026, 8, 21, 11, 0),
            datetime(2026, 8, 21, 12, 0)
        ]
    })


@pytest.fixture
def matching_ibase_work_report():
    """Fixture providing perfectly matching iBase and work report data"""
    ibase = pd.DataFrame({
        "ObjectID": ["ASSET001", "ASSET002"],
        "AddressLine1": ["Building A", "Building B"]
    })

    work_report = pd.DataFrame({
        "equipmentId": ["ASSET001", "ASSET002"],
        "location": ["Building A", "Building B"],
        "lastChangeDateTime": [
            datetime(2026, 8, 21, 10, 0),
            datetime(2026, 8, 21, 11, 0)
        ]
    })

    return ibase, work_report


@pytest.fixture
def discrepant_ibase_work_report():
    """Fixture providing iBase and work report data with discrepancies"""
    ibase = pd.DataFrame({
        "ObjectID": ["ASSET001", "ASSET002"],
        "AddressLine1": ["Building A", "Building B"]
    })

    work_report = pd.DataFrame({
        "equipmentId": ["ASSET001", "ASSET002"],
        "location": ["Building X", "Building Y"],
        "lastChangeDateTime": [
            datetime(2026, 8, 21, 10, 0),
            datetime(2026, 8, 21, 11, 0)
        ]
    })

    return ibase, work_report


@pytest.fixture
def audit_record_with_match():
    """Fixture providing a sample match audit record"""
    return {
        "equipment_id": "ASSET001",
        "location_sap": "Building A",
        "location_ibase": "Building A",
        "result": "MATCH"
    }


@pytest.fixture
def audit_record_with_error():
    """Fixture providing a sample error audit record"""
    return {
        "equipment_id": "ASSET001",
        "location_sap": None,
        "location_ibase": "Building A",
        "result": "ERROR",
        "error": "SAP location is missing"
    }


@pytest.fixture
def audit_record_with_update():
    """Fixture providing a sample update audit record"""
    return {
        "equipment_id": "ASSET001",
        "location_sap": "Building X",
        "location_ibase": "Building A",
        "result": "UPDATED"
    }
