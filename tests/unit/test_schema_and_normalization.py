import datetime
import pytest
from backend.ingestion.normalization.schema import CanonicalAISPoint, normalize_vessel_type


def test_normalize_vessel_type():
    assert normalize_vessel_type("Cargo") == "Cargo"
    assert normalize_vessel_type(70) == "Cargo"
    assert normalize_vessel_type(79) == "Cargo"
    assert normalize_vessel_type(80) == "Tanker"
    assert normalize_vessel_type("crude oil tanker") == "Tanker"
    assert normalize_vessel_type(30) == "Fishing"
    assert normalize_vessel_type("fishing trawler") == "Fishing"
    assert normalize_vessel_type(60) == "Passenger"
    assert normalize_vessel_type("passenger ferry") == "Passenger"
    assert normalize_vessel_type(52) == "Tug"
    assert normalize_vessel_type("tugboat") == "Tug"
    assert normalize_vessel_type(None) == "Other"


def test_canonical_ais_point_valid():
    ts = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    pt = CanonicalAISPoint(
        mmsi=244101001,
        timestamp=ts,
        latitude=51.25,
        longitude=1.80,
        sog=14.5,
        cog=225.0,
    )
    assert pt.mmsi == 244101001
    assert pt.latitude == 51.25
    assert pt.sog == 14.5
    assert pt.vessel_type == "Other"
    assert pt.is_valid is True
