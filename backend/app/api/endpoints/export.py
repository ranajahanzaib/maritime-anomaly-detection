import json
from typing import Optional
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import BehavioralEvent, TrajectorySegment, Vessel
from backend.ingestion.storage.duckdb_store import DuckDBStore

router = APIRouter()


@router.get("/events")
def export_events(
    format: str = "json",
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(BehavioralEvent)
    if category and category != "All":
        q = q.filter(BehavioralEvent.category == category)
    events = q.all()

    if format == "csv":
        # Build CSV string
        header = "id,category,primary_mmsi,secondary_mmsi,severity,deviation_score,start_time,end_time,latitude,longitude,contextual_state,explanation\n"
        lines = [header]
        for e in events:
            lines.append(
                f'"{e.id}","{e.category}",{e.primary_mmsi},{e.secondary_mmsi or ""},"{e.severity}",{e.deviation_score},"{e.start_time}","{e.end_time}",{e.latitude},{e.longitude},"{e.contextual_state}","{e.explanation.replace(chr(34), chr(39))}"\n'
            )
        csv_data = "".join(lines)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=behavioral_events.csv"})

    elif format == "geojson":
        features = []
        for e in events:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [e.longitude, e.latitude],
                },
                "properties": {
                    "id": e.id,
                    "category": e.category,
                    "primary_mmsi": e.primary_mmsi,
                    "severity": e.severity,
                    "deviation_score": e.deviation_score,
                    "explanation": e.explanation,
                    "contextual_state": e.contextual_state,
                },
            })
        geo_data = json.dumps({"type": "FeatureCollection", "features": features}, indent=2)
        return Response(content=geo_data, media_type="application/geo+json", headers={"Content-Disposition": "attachment; filename=events.geojson"})

    # Default JSON
    event_dicts = [
        {
            "id": e.id,
            "category": e.category,
            "primary_mmsi": e.primary_mmsi,
            "secondary_mmsi": e.secondary_mmsi,
            "severity": e.severity,
            "deviation_score": e.deviation_score,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "latitude": e.latitude,
            "longitude": e.longitude,
            "explanation": e.explanation,
            "contextual_state": e.contextual_state,
            "evidence": e.evidence,
            "feature_attributions": e.feature_attributions,
        }
        for e in events
    ]
    return Response(content=json.dumps(event_dicts, indent=2), media_type="application/json", headers={"Content-Disposition": "attachment; filename=events.json"})
