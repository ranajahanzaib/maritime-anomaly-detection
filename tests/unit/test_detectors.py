import datetime
from backend.detection.rules.loitering import LoiteringDetector
from backend.detection.rules.rendezvous import RendezvousDetector
from backend.detection.rules.ais_gap import AISTransmissionGapDetector
from backend.detection.statistical.peer_deviation import PeerGroupDeviationDetector


def test_loitering_detector_open_water():
    det = LoiteringDetector(max_loitering_speed_knots=1.5, min_loitering_duration_hours=2.0)
    base_t = datetime.datetime(2025, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    
    # 15 points over 3 hours at low speed in open sea (50.95, 1.20) ~15nm from Dover
    points = []
    for i in range(15):
        t = base_t + datetime.timedelta(minutes=i * 15)
        points.append({
            "latitude": 50.95 + (i % 2) * 0.001,
            "longitude": 1.20 + (i % 2) * 0.001,
            "sog": 0.4,
            "cog": 90.0,
            "timestamp": t,
        })

    events = det.detect(mmsi=999888777, points=points, vessel_type="Cargo")
    assert len(events) == 1
    assert events[0]["category"] == "LOITERING"
    assert events[0]["contextual_state"] == "POTENTIALLY_RELEVANT"
    assert events[0]["primary_mmsi"] == 999888777


def test_rendezvous_detector():
    det = RendezvousDetector(proximity_distance_meters=500.0, min_rendezvous_minutes=15.0)
    base_t = datetime.datetime(2025, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    
    track_a = []
    track_b = []
    for i in range(10):
        t = base_t + datetime.timedelta(minutes=i * 3)  # 30 min duration
        track_a.append({
            "latitude": 50.8500,
            "longitude": 0.9000,
            "sog": 0.5,
            "cog": 45.0,
            "timestamp": t,
        })
        track_b.append({
            "latitude": 50.8505,  # ~50 meters away
            "longitude": 0.9005,
            "sog": 0.4,
            "cog": 40.0,
            "timestamp": t,
        })

    events = det.detect_pair(111111111, track_a, 222222222, track_b)
    assert len(events) == 1
    assert events[0]["category"] == "RENDEZVOUS"
    assert events[0]["primary_mmsi"] == 111111111
    assert events[0]["secondary_mmsi"] == 222222222


def test_ais_gap_detector():
    det = AISTransmissionGapDetector(min_gap_hours=2.0)
    t1 = datetime.datetime(2025, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2025, 6, 1, 14, 30, 0, tzinfo=datetime.timezone.utc)
    
    gaps = [{
        "mmsi": 333333333,
        "start_time": t1,
        "end_time": t2,
        "duration_seconds": 16200.0,
        "duration_hours": 4.5,
        "start_lat": 51.0,
        "start_lon": 1.5,
        "end_lat": 50.5,
        "end_lon": 1.0,
        "displacement_nm": 35.0,
        "implied_speed_knots": 7.7,
    }]

    events = det.detect_from_gaps(333333333, gaps)
    assert len(events) == 1
    assert events[0]["category"] == "AIS_TRANSMISSION_GAP"
    assert "telemetry observability" in events[0]["explanation"]
