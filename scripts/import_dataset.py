import sys
import argparse
from pathlib import Path
from backend.app.core.logging import logger
from backend.app.db.session import SessionLocal, init_db
from backend.app.models.entities import Dataset, Vessel, TrajectorySegment, BehavioralEvent
from backend.ingestion.adapters.noaa import NOAAAdapter
from backend.ingestion.adapters.hawaii import HawaiiCoastGTAdapter
from backend.ingestion.adapters.danish import DanishAISAdapter
from backend.ingestion.adapters.generic import GenericAISAdapter
from backend.ingestion.validation.validator import DataQualityValidator
from backend.ingestion.storage.parquet_store import ParquetStore
from backend.trajectories.segmenter import TrajectorySegmenter
from backend.detection.pipeline import MaritimeAnomalyDetectionPipeline


def import_dataset(
    file_path: str,
    source_type: str = "GENERIC",
    dataset_name: str | None = None,
    limit: int | None = None,
):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    adapters = {
        "NOAA": NOAAAdapter(),
        "HAWAII_COAST": HawaiiCoastGTAdapter(),
        "DANISH_AIS": DanishAISAdapter(),
        "GENERIC": GenericAISAdapter(),
    }
    adapter = adapters.get(source_type.upper(), GenericAISAdapter())
    name = dataset_name or f"{source_type.capitalize()} Import ({path.name})"
    ds_id = f"ds_{path.stem.lower()[:24]}"

    print(f"Importing {name} using adapter {adapter.source_name}...")

    # 1. Parse raw records
    raw_points = list(adapter.parse(path, limit=limit))
    print(f"Parsed {len(raw_points)} raw points.")

    # 2. Validate
    validator = DataQualityValidator()
    # Group by MMSI
    grouped_raw = {}
    for p in raw_points:
        grouped_raw.setdefault(p.mmsi, []).append(p)

    validated_points = []
    total_val_stats = {"total_points": 0, "valid_points": 0, "rejected_points": 0, "duplicates": 0, "speed_jumps": 0}

    for mmsi, pts in grouped_raw.items():
        v_pts, v_stat = validator.validate_track_consistency(pts)
        validated_points.extend(v_pts)
        for k in total_val_stats:
            total_val_stats[k] += v_stat.get(k, 0)

    # 3. Store Parquet
    p_store = ParquetStore()
    storage_meta = p_store.write_dataset_points(ds_id, validated_points)

    # 4. DB Persistence & Trajectory construction
    init_db()
    db = SessionLocal()
    try:
        ds_rec = Dataset(
            id=ds_id,
            name=name,
            source_type=source_type.upper(),
            format=storage_meta.get("format", "PARQUET"),
            file_path=str(path.resolve()),
            parquet_path=storage_meta["file_path"],
            row_count=storage_meta["row_count"],
            valid_count=storage_meta["valid_count"],
            rejected_count=storage_meta["rejected_count"],
            vessel_count=storage_meta["vessel_count"],
            quality_score=round(storage_meta["valid_count"] / max(1, storage_meta["row_count"]), 4),
            status="READY",
            bbox_min_lat=storage_meta.get("bbox_min_lat"),
            bbox_min_lon=storage_meta.get("bbox_min_lon"),
            bbox_max_lat=storage_meta.get("bbox_max_lat"),
            bbox_max_lon=storage_meta.get("bbox_max_lon"),
            time_range_start=storage_meta.get("time_range_start"),
            time_range_end=storage_meta.get("time_range_end"),
            quality_report=total_val_stats,
            is_synthetic=False,
        )
        db.merge(ds_rec)

        # Segment trajectories and run detection
        segmenter = TrajectorySegmenter()
        pipeline = MaritimeAnomalyDetectionPipeline()

        pts_by_mmsi = {}
        for p in validated_points:
            pts_by_mmsi.setdefault(p.mmsi, []).append(p.model_dump())

        for mmsi, pts in pts_by_mmsi.items():
            segments, gaps = segmenter.segment_points(mmsi, pts)
            for s in segments:
                s_rec = TrajectorySegment(
                    id=s["id"],
                    mmsi=s["mmsi"],
                    segment_index=s["segment_index"],
                    start_time=s["start_time"],
                    end_time=s["end_time"],
                    duration_seconds=s["duration_seconds"],
                    point_count=s["point_count"],
                    distance_nm=s["distance_nm"],
                    avg_speed=s["avg_speed"],
                    max_speed=s["max_speed"],
                    bbox_min_lat=s["bbox_min_lat"],
                    bbox_min_lon=s["bbox_min_lon"],
                    bbox_max_lat=s["bbox_max_lat"],
                    bbox_max_lon=s["bbox_max_lon"],
                    geometry_geojson=s["geometry_geojson"],
                    kinematics_summary=s["kinematics_summary"],
                    is_synthetic=False,
                )
                db.merge(s_rec)

            first_pt = pts[0]
            last_pt = pts[-1]
            events = pipeline.run_trajectory_detection(
                mmsi=mmsi, points=pts, gaps=gaps, vessel_type=first_pt.get("vessel_type", "Other")
            )
            for e in events:
                e_rec = BehavioralEvent(
                    id=e["id"],
                    category=e["category"],
                    primary_mmsi=e["primary_mmsi"],
                    secondary_mmsi=e.get("secondary_mmsi"),
                    detector_id=e["detector_id"],
                    detector_version=e["detector_version"],
                    deviation_score=e["deviation_score"],
                    severity=e["severity"],
                    confidence=e["confidence"],
                    start_time=e["start_time"],
                    end_time=e["end_time"],
                    duration_seconds=e["duration_seconds"],
                    latitude=e["latitude"],
                    longitude=e["longitude"],
                    bbox_geojson=e.get("bbox_geojson"),
                    contextual_state=e.get("contextual_state", "CONTEXT_UNAVAILABLE"),
                    contextual_explanation=e.get("contextual_explanation"),
                    explanation=e["explanation"],
                    feature_attributions=e.get("feature_attributions"),
                    evidence=e.get("evidence"),
                    is_synthetic=False,
                    status="NEW",
                )
                db.merge(e_rec)

            v_rec = Vessel(
                mmsi=mmsi,
                name=first_pt.get("vessel_name"),
                vessel_type=first_pt.get("vessel_type", "Other"),
                flag=first_pt.get("flag"),
                observation_count=len(pts),
                segment_count=len(segments),
                total_distance_nm=sum(s["distance_nm"] for s in segments),
                avg_speed_knots=sum(p.get("sog", 0.0) for p in pts) / len(pts),
                max_speed_knots=max(p.get("sog", 0.0) for p in pts),
                first_seen=first_pt["timestamp"],
                last_seen=last_pt["timestamp"],
                last_lat=last_pt["latitude"],
                last_lon=last_pt["longitude"],
                last_sog=last_pt.get("sog", 0.0),
                last_cog=last_pt.get("cog", 0.0),
                data_quality_score=round(len([p for p in pts if p.get("is_valid", True)]) / len(pts), 3),
                event_count=len(events),
                is_synthetic=False,
            )
            db.merge(v_rec)

        db.commit()
        print(f"Dataset {ds_id} imported successfully: {len(pts_by_mmsi)} vessels.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import AIS datasets")
    parser.add_argument("file_path", help="Path to CSV/Parquet file")
    parser.add_argument("--source", default="GENERIC", choices=["NOAA", "HAWAII_COAST", "DANISH_AIS", "GENERIC"])
    parser.add_argument("--name", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    import_dataset(args.file_path, source_type=args.source, dataset_name=args.name, limit=args.limit)
