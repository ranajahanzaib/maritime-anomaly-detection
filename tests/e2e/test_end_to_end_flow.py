import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.models.entities import Vessel, TrajectorySegment, BehavioralEvent
from backend.ingestion.normalization.schema import CanonicalAISPoint
from backend.ingestion.validation.validator import DataQualityValidator
from backend.ingestion.storage.parquet_store import ParquetStore
from backend.trajectories.segmenter import TrajectorySegmenter
from backend.features.extractor import TrajectoryFeatureExtractor
from backend.detection.pipeline import MaritimeAnomalyDetectionPipeline

client = TestClient(app)


def test_complete_end_to_end_demonstration():
    """
    End-to-end test verifying complete pipeline flow:
    1. Ingestion of raw AIS pings for an anomalous vessel (unusual loitering in open water).
    2. Validation and normalization.
    3. Trajectory segmentation and kinematics derivation.
    4. Feature extraction.
    5. Behavioral anomaly detection and contextual interpretation.
    6. Persistence to database.
    7. Retrieval via FastAPI API endpoints with full explainability evidence.
    """
    init_db()

    # Step 1: Create synthetic vessel exhibiting 3-hour open water loitering
    test_mmsi = 999123456
    base_t = datetime.datetime(2025, 6, 2, 8, 0, 0, tzinfo=datetime.timezone.utc)
    raw_points = []
    
    # 20 points over 3.5 hours with low speed (<1.0 knot) in open water (50.95, 1.20)
    for i in range(20):
        t = base_t + datetime.timedelta(minutes=i * 10)
        raw_points.append(CanonicalAISPoint(
            mmsi=test_mmsi,
            timestamp=t,
            latitude=50.95 + (i % 2) * 0.001,
            longitude=1.20 + (i % 2) * 0.001,
            sog=0.5,
            cog=90.0,
            vessel_name="MV Test Loiterer",
            vessel_type="Cargo",
            flag="NLD",
            source_dataset="E2E_TEST",
        ))

    # Step 2: Validation
    validator = DataQualityValidator()
    validated_pts, val_stats = validator.validate_track_consistency(raw_points)
    assert val_stats["valid_points"] == 20
    assert val_stats["quality_score"] == 1.0

    # Step 3: Trajectory Construction
    pts_dict = [p.model_dump() for p in validated_pts]
    segmenter = TrajectorySegmenter()
    segments, gaps = segmenter.segment_points(test_mmsi, pts_dict, is_synthetic=True)
    assert len(segments) == 1
    assert segments[0]["point_count"] == 20
    assert "geometry_geojson" in segments[0]

    # Step 4: Spatial-Temporal Feature Extraction
    extractor = TrajectoryFeatureExtractor()
    features = extractor.extract_features(pts_dict)
    assert features["speed_mean"] <= 1.0
    assert features["stop_ratio"] == 1.0
    assert "radius_of_gyration_nm" in features

    # Step 5: Behavioral Detection Pipeline
    pipeline = MaritimeAnomalyDetectionPipeline()
    detected_events = pipeline.run_trajectory_detection(
        mmsi=test_mmsi,
        points=pts_dict,
        gaps=gaps,
        vessel_type="Cargo",
        is_synthetic=True,
    )
    assert len(detected_events) >= 1
    loiter_evt = next((e for e in detected_events if e["category"] == "LOITERING"), None)
    assert loiter_evt is not None
    assert loiter_evt["deviation_score"] > 0.4
    assert "Context:" in loiter_evt["explanation"]
    assert loiter_evt["contextual_state"] in ["POTENTIALLY_RELEVANT", "EXPECTED_CONTEXT"]

    # Step 6: Persist in Database
    db = SessionLocal()
    try:
        # Save Segment
        seg = segments[0]
        s_rec = TrajectorySegment(
            id=seg["id"],
            mmsi=seg["mmsi"],
            segment_index=seg["segment_index"],
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            duration_seconds=seg["duration_seconds"],
            point_count=seg["point_count"],
            distance_nm=seg["distance_nm"],
            avg_speed=seg["avg_speed"],
            max_speed=seg["max_speed"],
            bbox_min_lat=seg["bbox_min_lat"],
            bbox_min_lon=seg["bbox_min_lon"],
            bbox_max_lat=seg["bbox_max_lat"],
            bbox_max_lon=seg["bbox_max_lon"],
            geometry_geojson=seg["geometry_geojson"],
            is_synthetic=True,
        )
        db.merge(s_rec)

        # Save Event
        e_rec = BehavioralEvent(
            id=loiter_evt["id"],
            category=loiter_evt["category"],
            primary_mmsi=loiter_evt["primary_mmsi"],
            detector_id=loiter_evt["detector_id"],
            detector_version=loiter_evt["detector_version"],
            deviation_score=loiter_evt["deviation_score"],
            severity=loiter_evt["severity"],
            confidence=loiter_evt["confidence"],
            start_time=loiter_evt["start_time"],
            end_time=loiter_evt["end_time"],
            duration_seconds=loiter_evt["duration_seconds"],
            latitude=loiter_evt["latitude"],
            longitude=loiter_evt["longitude"],
            contextual_state=loiter_evt["contextual_state"],
            contextual_explanation=loiter_evt["contextual_explanation"],
            explanation=loiter_evt["explanation"],
            feature_attributions=loiter_evt["feature_attributions"],
            evidence=loiter_evt["evidence"],
            is_synthetic=True,
            status="NEW",
        )
        db.merge(e_rec)

        # Save Vessel
        v_rec = Vessel(
            mmsi=test_mmsi,
            name="MV Test Loiterer",
            vessel_type="Cargo",
            flag="NLD",
            observation_count=20,
            segment_count=1,
            total_distance_nm=seg["distance_nm"],
            avg_speed_knots=0.5,
            max_speed_knots=0.5,
            data_quality_score=1.0,
            event_count=1,
            is_synthetic=True,
        )
        db.merge(v_rec)
        db.commit()
    finally:
        db.close()

    # Step 7: Retrieve from FastAPI Endpoints and Verify Response
    res_vessel = client.get(f"/api/v1/vessels/{test_mmsi}")
    assert res_vessel.status_code == 200
    assert res_vessel.json()["name"] == "MV Test Loiterer"
    assert res_vessel.json()["event_count"] >= 1

    res_event = client.get(f"/api/v1/events/{loiter_evt['id']}")
    assert res_event.status_code == 200
    event_data = res_event.json()
    assert event_data["category"] == "LOITERING"
    assert event_data["primary_mmsi"] == test_mmsi
    assert "evidence" in event_data
    assert "feature_attributions" in event_data

    res_trajs = client.get(f"/api/v1/vessels/{test_mmsi}/trajectories")
    assert res_trajs.status_code == 200
    assert len(res_trajs.json()) >= 1
    assert res_trajs.json()[0]["geometry_geojson"]["type"] == "LineString"
