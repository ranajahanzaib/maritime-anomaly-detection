from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.app.db.session import get_db
from backend.app.models.entities import BehavioralEvent, Vessel
from backend.app.schemas.entities import BehavioralEventOut, EventUpdateIn
from backend.detection.pipeline import MaritimeAnomalyDetectionPipeline
from backend.ingestion.storage.duckdb_store import DuckDBStore

router = APIRouter()


@router.get("", response_model=List[BehavioralEventOut])
def list_behavioral_events(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    mmsi: Optional[int] = None,
    detector_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(BehavioralEvent)
    if category and category != "All":
        q = q.filter(BehavioralEvent.category == category)
    if severity and severity != "All":
        q = q.filter(BehavioralEvent.severity == severity)
    if status and status != "All":
        q = q.filter(BehavioralEvent.status == status)
    if mmsi:
        q = q.filter(or_(BehavioralEvent.primary_mmsi == mmsi, BehavioralEvent.secondary_mmsi == mmsi))
    if detector_id:
        q = q.filter(BehavioralEvent.detector_id == detector_id)

    return q.order_by(BehavioralEvent.deviation_score.desc(), BehavioralEvent.start_time.desc()).offset(skip).limit(limit).all()


@router.get("/categories")
def get_event_category_stats(db: Session = Depends(get_db)):
    rows = db.query(BehavioralEvent.category, func.count(BehavioralEvent.id)).group_by(BehavioralEvent.category).all()
    return [{"category": r[0], "count": r[1]} for r in rows]


@router.get("/{event_id}", response_model=BehavioralEventOut)
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    evt = db.query(BehavioralEvent).filter(BehavioralEvent.id == event_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt


@router.patch("/{event_id}", response_model=BehavioralEventOut)
def update_event_investigation(
    event_id: str,
    update_data: EventUpdateIn,
    db: Session = Depends(get_db),
):
    evt = db.query(BehavioralEvent).filter(BehavioralEvent.id == event_id).first()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")

    if update_data.status:
        evt.status = update_data.status
    if update_data.investigation_notes is not None:
        evt.investigation_notes = update_data.investigation_notes

    db.commit()
    db.refresh(evt)
    return evt


@router.post("/run-detection")
def run_batch_detection(mmsi: Optional[int] = None, db: Session = Depends(get_db)):
    """Runs anomaly detection pipeline across vessels."""
    store = DuckDBStore()
    pts = store.query_points(mmsi=mmsi, limit=5000)
    if not pts:
        return {"detected_events_count": 0, "message": "No points found for detection"}

    pipeline = MaritimeAnomalyDetectionPipeline()
    grouped = {}
    for p in pts:
        grouped.setdefault(p["mmsi"], []).append(p)

    new_events = []
    for v_mmsi, v_pts in grouped.items():
        vessel = db.query(Vessel).filter(Vessel.mmsi == v_mmsi).first()
        v_type = vessel.vessel_type if vessel else "Cargo"
        h_prof = vessel.historical_profile if vessel else None
        evts = pipeline.run_trajectory_detection(
            mmsi=v_mmsi, points=v_pts, vessel_type=v_type, historical_profile=h_prof
        )
        for e in evts:
            rec = BehavioralEvent(
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
                status="NEW",
            )
            db.merge(rec)
            new_events.append(e)

    db.commit()
    return {"detected_events_count": len(new_events), "events": new_events[:10]}
