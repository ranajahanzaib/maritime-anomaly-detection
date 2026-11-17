import math
import datetime
import random
from typing import List, Dict, Any
from pathlib import Path
import polars as pl

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.models.entities import Dataset, Vessel, TrajectorySegment, BehavioralEvent
from backend.ingestion.normalization.schema import CanonicalAISPoint
from backend.ingestion.storage.parquet_store import ParquetStore
from backend.trajectories.segmenter import TrajectorySegmenter
from backend.detection.pipeline import MaritimeAnomalyDetectionPipeline


def create_synthetic_point(
    mmsi: int,
    ts: datetime.datetime,
    lat: float,
    lon: float,
    sog: float,
    cog: float,
    vessel_name: str,
    vessel_type: str,
    flag: str = "NLD",
    nav_status: str = "Under way using engine",
) -> CanonicalAISPoint:
    return CanonicalAISPoint(
        mmsi=mmsi,
        imo=9000000 + (mmsi % 1000000),
        vessel_name=vessel_name,
        vessel_type=vessel_type,
        flag=flag,
        timestamp=ts,
        latitude=round(lat, 6),
        longitude=round(lon, 6),
        sog=round(max(0.0, sog), 2),
        cog=round(cog % 360.0, 2),
        heading=round(cog % 360.0, 2),
        navigational_status=nav_status,
        source_dataset="SYNTHETIC_DEMO",
        is_interpolated=False,
        is_valid=True,
    )


def generate_demonstration_dataset(seed: int = 42) -> Dict[str, Any]:
    """
    Generates a deterministic synthetic maritime AIS dataset containing 10 scenarios.
    """
    random.seed(seed)
    base_time = datetime.datetime(2025, 6, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)
    all_points: List[CanonicalAISPoint] = []
    vessel_profiles: Dict[int, Dict[str, Any]] = {}

    print("Generating Synthetic Demonstration Scenarios...")

    # ----------------------------------------------------
    # Scenario 1: Route Deviation (Cargo Vessel "MV North Star")
    # ----------------------------------------------------
    # Starts in Dover TSS SW Lane (51.25, 1.80), but turns 65 deg off-course into shallow banks
    mmsi_s1 = 244101001
    lat, lon, sog, cog = 51.25, 1.80, 14.5, 225.0
    for step in range(40):
        t = base_time + datetime.timedelta(minutes=step * 3)
        if step > 12:
            cog = 160.0  # sharp abnormal detour
            sog = 11.2
        d_deg = (sog * (3.0 / 60.0)) / 60.0
        lat += d_deg * math.cos(math.radians(cog))
        lon += d_deg * math.sin(math.radians(cog))
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s1, ts=t, lat=lat, lon=lon, sog=sog, cog=cog,
            vessel_name="MV North Star", vessel_type="Cargo", flag="NLD"
        ))
    vessel_profiles[mmsi_s1] = {"avg_speed_knots": 14.5, "max_speed_knots": 16.0, "observation_count": 40}

    # ----------------------------------------------------
    # Scenario 2: Rendezvous (Tanker "Ocean Trader" & Craft "Sea Hawk")
    # ----------------------------------------------------
    # Both converge in open waters off English Channel, remain 200m apart for 45 minutes
    mmsi_s2_a = 211202002
    mmsi_s2_b = 211202003
    rendezvous_lat, rendezvous_lon = 50.85, 0.90
    for step in range(35):
        t = base_time + datetime.timedelta(minutes=step * 3)
        if 8 <= step <= 23:  # 45 mins stationary together
            lat_a = rendezvous_lat + random.uniform(-0.0008, 0.0008)
            lon_a = rendezvous_lon + random.uniform(-0.0008, 0.0008)
            lat_b = rendezvous_lat + random.uniform(-0.0008, 0.0008)
            lon_b = rendezvous_lon + random.uniform(-0.0008, 0.0008)
            sog_a, sog_b = 0.4, 0.3
            cog_a, cog_b = 40.0, 45.0
        elif step < 8:
            lat_a = rendezvous_lat - (8 - step) * 0.015
            lon_a = rendezvous_lon - (8 - step) * 0.012
            lat_b = rendezvous_lat + (8 - step) * 0.014
            lon_b = rendezvous_lon + (8 - step) * 0.011
            sog_a, sog_b = 11.0, 10.0
            cog_a, cog_b = 45.0, 225.0
        else:
            lat_a = rendezvous_lat + (step - 23) * 0.015
            lon_a = rendezvous_lon + (step - 23) * 0.012
            lat_b = rendezvous_lat - (step - 23) * 0.014
            lon_b = rendezvous_lon - (step - 23) * 0.011
            sog_a, sog_b = 10.5, 9.5
            cog_a, cog_b = 45.0, 225.0

        all_points.append(create_synthetic_point(
            mmsi=mmsi_s2_a, ts=t, lat=lat_a, lon=lon_a, sog=sog_a, cog=cog_a,
            vessel_name="Ocean Trader", vessel_type="Tanker", flag="LBR"
        ))
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s2_b, ts=t, lat=lat_b, lon=lon_b, sog=sog_b, cog=cog_b,
            vessel_name="Sea Hawk", vessel_type="Other", flag="PAN"
        ))
    vessel_profiles[mmsi_s2_a] = {"avg_speed_knots": 11.5, "max_speed_knots": 14.0, "observation_count": 35}
    vessel_profiles[mmsi_s2_b] = {"avg_speed_knots": 9.0, "max_speed_knots": 12.0, "observation_count": 35}

    # ----------------------------------------------------
    # Scenario 3: Loitering in Open Ocean (Container "Ever Bright")
    # ----------------------------------------------------
    # Dwells for 10 hours in open water 35nm away from nearest anchorage at 0.4 kts
    mmsi_s3 = 353303004
    loiter_lat, loiter_lon = 50.40, -0.30  # Open English Channel
    for step in range(50):
        t = base_time + datetime.timedelta(minutes=step * 15)  # 12.5 hours total
        jitter_lat = loiter_lat + math.sin(step * 0.4) * 0.003
        jitter_lon = loiter_lon + math.cos(step * 0.4) * 0.004
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s3, ts=t, lat=jitter_lat, lon=jitter_lon, sog=0.5, cog=180.0,
            vessel_name="Ever Bright", vessel_type="Cargo", flag="PAN", nav_status="Engaged in loitering"
        ))
    vessel_profiles[mmsi_s3] = {"avg_speed_knots": 16.0, "max_speed_knots": 21.0, "observation_count": 50}

    # ----------------------------------------------------
    # Scenario 4: Peer Deviation (High-Speed Cargo "Baltic Runner")
    # ----------------------------------------------------
    # Steams at 28.5 knots (Cargo peer baseline is 13.5 ± 2.8 kts)
    mmsi_s4 = 230404005
    lat, lon, sog, cog = 51.10, 1.40, 28.5, 220.0
    for step in range(30):
        t = base_time + datetime.timedelta(minutes=step * 3)
        d_deg = (sog * (3.0 / 60.0)) / 60.0
        lat += d_deg * math.cos(math.radians(cog))
        lon += d_deg * math.sin(math.radians(cog))
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s4, ts=t, lat=lat, lon=lon, sog=sog, cog=cog,
            vessel_name="Baltic Runner", vessel_type="Cargo", flag="FIN"
        ))
    vessel_profiles[mmsi_s4] = {"avg_speed_knots": 28.0, "max_speed_knots": 30.0, "observation_count": 30}

    # ----------------------------------------------------
    # Scenario 5: Historical Inconsistency (Fishing Vessel "Zeeland 4")
    # ----------------------------------------------------
    # Historically operates in North Sea coastal zone (51.9, 4.0), suddenly found in Dover Strait (50.8, 1.1) at 16 kts
    mmsi_s5 = 244505006
    lat, lon, sog, cog = 50.80, 1.10, 16.0, 230.0
    for step in range(25):
        t = base_time + datetime.timedelta(minutes=step * 4)
        d_deg = (sog * (4.0 / 60.0)) / 60.0
        lat += d_deg * math.cos(math.radians(cog))
        lon += d_deg * math.sin(math.radians(cog))
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s5, ts=t, lat=lat, lon=lon, sog=sog, cog=cog,
            vessel_name="Zeeland 4", vessel_type="Fishing", flag="NLD"
        ))
    # Vessel historical profile has home center at (51.9, 4.0) with typical speed 5 kts
    vessel_profiles[mmsi_s5] = {
        "avg_speed_knots": 5.2,
        "max_speed_knots": 9.0,
        "center_lat": 51.90,
        "center_lon": 4.00,
        "operating_radius_nm": 15.0,
        "observation_count": 85,
    }

    # ----------------------------------------------------
    # Scenario 6: AIS Transmission Gap ("Nordic Pioneer")
    # ----------------------------------------------------
    # Normal transit, goes dark for 4.5 hours, reappears 50nm away
    mmsi_s6 = 257606007
    lat, lon, sog, cog = 51.40, 2.10, 13.0, 220.0
    for step in range(15):
        t = base_time + datetime.timedelta(minutes=step * 4)
        d_deg = (sog * (4.0 / 60.0)) / 60.0
        lat += d_deg * math.cos(math.radians(cog))
        lon += d_deg * math.sin(math.radians(cog))
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s6, ts=t, lat=lat, lon=lon, sog=sog, cog=cog,
            vessel_name="Nordic Pioneer", vessel_type="Cargo", flag="NOR"
        ))
    # Gap of 4.5 hours
    gap_time = base_time + datetime.timedelta(hours=5, minutes=30)
    lat_reappear = 50.70
    lon_reappear = 1.00
    for step in range(15):
        t = gap_time + datetime.timedelta(minutes=step * 4)
        d_deg = (sog * (4.0 / 60.0)) / 60.0
        lat_reappear += d_deg * math.cos(math.radians(cog))
        lon_reappear += d_deg * math.sin(math.radians(cog))
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s6, ts=t, lat=lat_reappear, lon=lon_reappear, sog=sog, cog=cog,
            vessel_name="Nordic Pioneer", vessel_type="Cargo", flag="NOR"
        ))
    vessel_profiles[mmsi_s6] = {"avg_speed_knots": 13.0, "max_speed_knots": 15.0, "observation_count": 30}

    # ----------------------------------------------------
    # Scenario 7: Normal Anchorage (Maasvlakte Anchorage 4E, "Stena Hollandica")
    # ----------------------------------------------------
    # Dwells inside designated anchorage (52.02, 3.90) for 6 hours -> EXPECTED_CONTEXT!
    mmsi_s7 = 244707008
    anch_lat, anch_lon = 52.02, 3.90
    for step in range(36):
        t = base_time + datetime.timedelta(minutes=step * 10)
        j_lat = anch_lat + math.sin(step * 0.3) * 0.002
        j_lon = anch_lon + math.cos(step * 0.3) * 0.003
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s7, ts=t, lat=j_lat, lon=j_lon, sog=0.2, cog=30.0,
            vessel_name="Stena Hollandica", vessel_type="Tanker", flag="NLD", nav_status="At anchor"
        ))
    vessel_profiles[mmsi_s7] = {"avg_speed_knots": 12.0, "max_speed_knots": 16.0, "observation_count": 36}

    # ----------------------------------------------------
    # Scenario 8: Port Congestion Waiting (Dover Port Approaches)
    # ----------------------------------------------------
    # 2 vessels slow-steaming near Dover Port (51.12, 1.34) awaiting berth
    for c_idx, (mmsi_c, name_c) in enumerate([(235808009, "Channel Feeder"), (235808010, "Kent Express")]):
        c_lat = 51.10 + c_idx * 0.015
        c_lon = 1.38 + c_idx * 0.012
        for step in range(25):
            t = base_time + datetime.timedelta(minutes=step * 8)
            d_deg = (1.8 * (8.0 / 60.0)) / 60.0
            c_lat += d_deg * math.sin(step * 0.5)
            c_lon += d_deg * math.cos(step * 0.5)
            all_points.append(create_synthetic_point(
                mmsi=mmsi_c, ts=t, lat=c_lat, lon=c_lon, sog=1.8, cog=90.0,
                vessel_name=name_c, vessel_type="Cargo", flag="GBR", nav_status="Restricted manoeuvrability"
            ))
        vessel_profiles[mmsi_c] = {"avg_speed_knots": 12.5, "max_speed_knots": 15.0, "observation_count": 25}

    # ----------------------------------------------------
    # Scenario 9: Fishing Activity (Trawler "Zeeleeuw")
    # ----------------------------------------------------
    # Low speed zig-zag trawling pattern at 3.5 kts (benign fishing activity!)
    mmsi_s9 = 244909011
    f_lat, f_lon = 51.60, 2.80
    for step in range(35):
        t = base_time + datetime.timedelta(minutes=step * 6)
        cog_trawl = (step % 2) * 180.0 + 45.0  # zig-zag
        d_deg = (3.5 * (6.0 / 60.0)) / 60.0
        f_lat += d_deg * math.cos(math.radians(cog_trawl))
        f_lon += d_deg * math.sin(math.radians(cog_trawl))
        all_points.append(create_synthetic_point(
            mmsi=mmsi_s9, ts=t, lat=f_lat, lon=f_lon, sog=3.5, cog=cog_trawl,
            vessel_name="Zeeleeuw", vessel_type="Fishing", flag="BEL", nav_status="Engaged in fishing"
        ))
    vessel_profiles[mmsi_s9] = {"avg_speed_knots": 4.5, "max_speed_knots": 8.0, "observation_count": 35}

    # ----------------------------------------------------
    # Scenario 10: Normal Transits (10 vessels in lanes)
    # ----------------------------------------------------
    for v_idx in range(10):
        mmsi_norm = 200000000 + v_idx
        v_types = ["Cargo", "Tanker", "Passenger", "Cargo", "Tanker"]
        v_type = v_types[v_idx % len(v_types)]
        v_names = [f"Maersk Line {v_idx+1}", f"CMA CGM {v_idx+1}", f"MSC Marine {v_idx+1}"]
        v_name = v_names[v_idx % len(v_names)]
        
        # Start along SW or NE lane
        is_sw = (v_idx % 2 == 0)
        s_lat = 51.30 - v_idx * 0.04 if is_sw else 50.65 + v_idx * 0.04
        s_lon = 1.85 - v_idx * 0.05 if is_sw else 0.90 + v_idx * 0.05
        cog_norm = 225.0 if is_sw else 45.0
        sog_norm = 13.0 + (v_idx % 4) * 0.8

        for step in range(25):
            t = base_time + datetime.timedelta(minutes=step * 5)
            d_deg = (sog_norm * (5.0 / 60.0)) / 60.0
            s_lat += d_deg * math.cos(math.radians(cog_norm)) + random.uniform(-0.0003, 0.0003)
            s_lon += d_deg * math.sin(math.radians(cog_norm)) + random.uniform(-0.0003, 0.0003)
            all_points.append(create_synthetic_point(
                mmsi=mmsi_norm, ts=t, lat=s_lat, lon=s_lon, sog=sog_norm, cog=cog_norm,
                vessel_name=v_name, vessel_type=v_type, flag="SGP"
            ))
        vessel_profiles[mmsi_norm] = {"avg_speed_knots": sog_norm, "max_speed_knots": sog_norm + 2.0, "observation_count": 25}

    print(f"Total synthetic AIS points generated: {len(all_points)}")

    # Save to Parquet
    dataset_id = "synthetic_demo_v1"
    store = ParquetStore()
    storage_meta = store.write_dataset_points(dataset_id, all_points)
    print("Parquet storage written:", storage_meta["file_path"])

    # Persist in Database
    db = SessionLocal()
    try:
        # Register Dataset record
        ds_rec = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not ds_rec:
            ds_rec = Dataset(
                id=dataset_id,
                name="Synthetic Maritime Demonstration Dataset",
                description="Deterministic synthetic demonstration dataset covering 10 behavioural and operational scenarios in English Channel and North Sea.",
                source_type="SYNTHETIC",
                format="PARQUET",
                file_path=storage_meta["file_path"],
                parquet_path=storage_meta["file_path"],
                row_count=storage_meta["row_count"],
                valid_count=storage_meta["valid_count"],
                rejected_count=storage_meta["rejected_count"],
                vessel_count=storage_meta["vessel_count"],
                quality_score=1.0,
                status="READY",
                bbox_min_lat=storage_meta["bbox_min_lat"],
                bbox_min_lon=storage_meta["bbox_min_lon"],
                bbox_max_lat=storage_meta["bbox_max_lat"],
                bbox_max_lon=storage_meta["bbox_max_lon"],
                time_range_start=storage_meta["time_range_start"],
                time_range_end=storage_meta["time_range_end"],
                is_synthetic=True,
            )
            db.add(ds_rec)
        db.commit()

        # Group by vessel and segment
        segmenter = TrajectorySegmenter()
        pipeline = MaritimeAnomalyDetectionPipeline()

        # Points by MMSI
        pts_by_mmsi: Dict[int, List[Dict[str, Any]]] = {}
        for p in all_points:
            pts_by_mmsi.setdefault(p.mmsi, []).append(p.model_dump())

        total_events_detected = 0

        for mmsi, pts in pts_by_mmsi.items():
            first_pt = pts[0]
            last_pt = pts[-1]
            vtype = first_pt["vessel_type"]
            vname = first_pt["vessel_name"]

            # Trajectory segmentation
            segments, gaps = segmenter.segment_points(mmsi, pts, is_synthetic=True)
            for seg in segments:
                seg_rec = TrajectorySegment(
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
                    kinematics_summary=seg["kinematics_summary"],
                    is_synthetic=True,
                )
                db.merge(seg_rec)

            # Run behavioral detection pipeline
            h_prof = vessel_profiles.get(mmsi)
            events = pipeline.run_trajectory_detection(
                mmsi=mmsi,
                points=pts,
                gaps=gaps,
                vessel_type=vtype,
                historical_profile=h_prof,
                is_synthetic=True,
            )

            # Special case: check rendezvous with pair
            if mmsi == mmsi_s2_a and mmsi_s2_b in pts_by_mmsi:
                rdz_events = pipeline.rendezvous_detector.detect_pair(
                    mmsi_s2_a, pts_by_mmsi[mmsi_s2_a],
                    mmsi_s2_b, pts_by_mmsi[mmsi_s2_b],
                    vessel_a_type="Tanker",
                    vessel_b_type="Other",
                    is_synthetic=True,
                )
                events.extend(rdz_events)

            for evt in events:
                evt_rec = BehavioralEvent(
                    id=evt["id"],
                    category=evt["category"],
                    primary_mmsi=evt["primary_mmsi"],
                    secondary_mmsi=evt.get("secondary_mmsi"),
                    detector_id=evt["detector_id"],
                    detector_version=evt["detector_version"],
                    deviation_score=evt["deviation_score"],
                    severity=evt["severity"],
                    confidence=evt["confidence"],
                    start_time=evt["start_time"],
                    end_time=evt["end_time"],
                    duration_seconds=evt["duration_seconds"],
                    latitude=evt["latitude"],
                    longitude=evt["longitude"],
                    bbox_geojson=evt.get("bbox_geojson"),
                    contextual_state=evt.get("contextual_state", "CONTEXT_UNAVAILABLE"),
                    contextual_explanation=evt.get("contextual_explanation"),
                    explanation=evt["explanation"],
                    feature_attributions=evt.get("feature_attributions"),
                    evidence=evt.get("evidence"),
                    data_quality_warnings=evt.get("data_quality_warnings"),
                    is_synthetic=True,
                    status="NEW",
                )
                db.merge(evt_rec)
                total_events_detected += 1

            # Update/merge Vessel record
            vessel_rec = Vessel(
                mmsi=mmsi,
                name=vname,
                vessel_type=vtype,
                flag=first_pt.get("flag", "NLD"),
                observation_count=len(pts),
                segment_count=len(segments),
                total_distance_nm=sum(s["distance_nm"] for s in segments),
                avg_speed_knots=sum(p["sog"] for p in pts) / len(pts),
                max_speed_knots=max(p["sog"] for p in pts),
                first_seen=first_pt["timestamp"],
                last_seen=last_pt["timestamp"],
                last_lat=last_pt["latitude"],
                last_lon=last_pt["longitude"],
                last_sog=last_pt["sog"],
                last_cog=last_pt["cog"],
                last_heading=last_pt.get("heading"),
                last_status=last_pt.get("navigational_status"),
                data_quality_score=1.0 if not gaps else 0.85,
                event_count=len(events),
                historical_profile=h_prof,
                is_synthetic=True,
            )
            db.merge(vessel_rec)

        db.commit()
        print(f"Database populated: {len(pts_by_mmsi)} vessels, {total_events_detected} behavioural events persisted.")
    finally:
        db.close()

    return {
        "dataset_id": dataset_id,
        "points_count": len(all_points),
        "vessels_count": len(pts_by_mmsi),
        "events_count": total_events_detected,
    }


if __name__ == "__main__":
    init_db()
    res = generate_demonstration_dataset(seed=42)
    print("Demo dataset generation finished:", res)
