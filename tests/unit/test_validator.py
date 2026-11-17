import datetime
from backend.ingestion.normalization.schema import CanonicalAISPoint
from backend.ingestion.validation.validator import DataQualityValidator


def test_validator_detects_bounds():
    val = DataQualityValidator(max_speed_knots=50.0)
    ts = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

    # Valid point
    p1 = CanonicalAISPoint(mmsi=123456789, timestamp=ts, latitude=50.0, longitude=1.0, sog=12.0, cog=180.0)
    is_valid, reasons = val.validate_point(p1)
    assert is_valid is True
    assert len(reasons) == 0

    # Out of bounds speed
    p2 = CanonicalAISPoint(mmsi=123456789, timestamp=ts, latitude=50.0, longitude=1.0, sog=75.0, cog=180.0)
    is_valid, reasons = val.validate_point(p2)
    assert is_valid is False
    assert any("SOG" in r for r in reasons)


def test_validator_track_consistency():
    val = DataQualityValidator(max_speed_knots=50.0)
    t0 = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    t1 = datetime.datetime(2025, 6, 1, 12, 5, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2025, 6, 1, 12, 6, 0, tzinfo=datetime.timezone.utc)

    # p0 and p1 are normal, p2 is 100nm away in 1 minute (impossible jump)
    p0 = CanonicalAISPoint(mmsi=123456789, timestamp=t0, latitude=50.0, longitude=1.0, sog=10.0, cog=180.0)
    p1 = CanonicalAISPoint(mmsi=123456789, timestamp=t1, latitude=50.01, longitude=1.0, sog=10.0, cog=180.0)
    p2 = CanonicalAISPoint(mmsi=123456789, timestamp=t2, latitude=52.5, longitude=3.0, sog=10.0, cog=180.0)

    validated, report = val.validate_track_consistency([p0, p1, p2])
    assert report["total_points"] == 3
    assert report["speed_jumps"] == 1
    assert validated[2].is_valid is False
