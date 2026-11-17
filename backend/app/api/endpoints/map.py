from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Vessel, TrajectorySegment, BehavioralEvent
from backend.ingestion.storage.duckdb_store import DuckDBStore
from backend.detection.context.maritime_zones import (
    MARITIME_REFERENCE_PORTS,
    MARITIME_REFERENCE_ANCHORAGES,
    MARITIME_SHIPPING_CORRIDORS,
)

router = APIRouter()


@router.get("/density")
def get_traffic_density_grid(
    dataset_id: Optional[str] = None,
    grid_size: float = 0.05,
    min_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
):
    """
    Returns spatial density grid for high-performance traffic heatmap rendering on MapLibre.
    """
    bbox = None
    if min_lat is not None and min_lon is not None and max_lat is not None and max_lon is not None:
        bbox = (min_lat, min_lon, max_lat, max_lon)

    store = DuckDBStore()
    cells = store.compute_density_grid(dataset_id=dataset_id, grid_size_deg=grid_size, bbox=bbox)
    return {"grid_size_deg": grid_size, "cell_count": len(cells), "cells": cells}


@router.get("/vessels")
def get_map_vessels(
    vessel_type: Optional[str] = None,
    has_events: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    Returns latest vessel markers with current coordinates, heading, and status.
    """
    q = db.query(Vessel).filter(Vessel.last_lat.isnot(None), Vessel.last_lon.isnot(None))
    if vessel_type and vessel_type != "All":
        q = q.filter(Vessel.vessel_type == vessel_type)
    if has_events:
        q = q.filter(Vessel.event_count > 0)

    vessels = q.limit(500).all()
    features = []
    for v in vessels:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [v.last_lon, v.last_lat],
            },
            "properties": {
                "mmsi": v.mmsi,
                "name": v.name or f"MMSI {v.mmsi}",
                "vessel_type": v.vessel_type,
                "flag": v.flag,
                "sog": v.last_sog or 0.0,
                "cog": v.last_cog or 0.0,
                "heading": v.last_heading or v.last_cog or 0.0,
                "nav_status": v.last_status,
                "event_count": v.event_count,
                "quality_score": v.data_quality_score,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/trajectories")
def get_map_trajectories(
    mmsi: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Returns simplified GeoJSON FeatureCollection of vessel trajectory lines for map display.
    """
    q = db.query(TrajectorySegment)
    if mmsi:
        q = q.filter(TrajectorySegment.mmsi == mmsi)
    segments = q.limit(limit).all()

    features = []
    for s in segments:
        features.append({
            "type": "Feature",
            "geometry": s.geometry_geojson,
            "properties": {
                "id": s.id,
                "mmsi": s.mmsi,
                "distance_nm": s.distance_nm,
                "avg_speed": s.avg_speed,
                "duration_seconds": s.duration_seconds,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/zones")
def get_maritime_context_zones():
    """Returns reference ports, designated anchorages, and shipping corridors."""
    return {
        "ports": MARITIME_REFERENCE_PORTS,
        "anchorages": MARITIME_REFERENCE_ANCHORAGES,
        "corridors": MARITIME_SHIPPING_CORRIDORS,
    }
