from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.db.session import get_db
from backend.app.models.entities import Vessel, TrajectorySegment, BehavioralEvent
from backend.app.schemas.entities import VesselOut, TrajectorySegmentOut, BehavioralEventOut
from backend.ingestion.storage.duckdb_store import DuckDBStore

router = APIRouter()


@router.get("", response_model=List[VesselOut])
def search_vessels(
    query: Optional[str] = None,
    vessel_type: Optional[str] = None,
    flag: Optional[str] = None,
    has_events: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Vessel)
    if query:
        search_filter = or_(
            Vessel.name.ilike(f"%{query}%"),
            Vessel.mmsi.cast(db.bind.dialect.type_compiler.process(Vessel.mmsi.type)).ilike(f"%{query}%")
            if hasattr(db.bind.dialect, "name") and db.bind.dialect.name == "postgresql"
            else Vessel.name.ilike(f"%{query}%")  # SQLite handled below
        )
        try:
            mmsi_val = int(query)
            q = q.filter(or_(Vessel.mmsi == mmsi_val, Vessel.name.ilike(f"%{query}%")))
        except ValueError:
            q = q.filter(Vessel.name.ilike(f"%{query}%"))

    if vessel_type and vessel_type != "All":
        q = q.filter(Vessel.vessel_type == vessel_type)
    if flag:
        q = q.filter(Vessel.flag == flag)
    if has_events is True:
        q = q.filter(Vessel.event_count > 0)

    return q.order_by(Vessel.event_count.desc(), Vessel.mmsi.asc()).offset(skip).limit(limit).all()


@router.get("/{mmsi}", response_model=VesselOut)
def get_vessel(mmsi: int, db: Session = Depends(get_db)):
    v = db.query(Vessel).filter(Vessel.mmsi == mmsi).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return v


@router.get("/{mmsi}/trajectories", response_model=List[TrajectorySegmentOut])
def get_vessel_trajectories(mmsi: int, db: Session = Depends(get_db)):
    return db.query(TrajectorySegment).filter(TrajectorySegment.mmsi == mmsi).order_by(TrajectorySegment.start_time.asc()).all()


@router.get("/{mmsi}/events", response_model=List[BehavioralEventOut])
def get_vessel_events(mmsi: int, db: Session = Depends(get_db)):
    return db.query(BehavioralEvent).filter(
        or_(BehavioralEvent.primary_mmsi == mmsi, BehavioralEvent.secondary_mmsi == mmsi)
    ).order_by(BehavioralEvent.start_time.desc()).all()


@router.get("/{mmsi}/history")
def get_vessel_history_points(mmsi: int, limit: int = 1000):
    store = DuckDBStore()
    pts = store.query_points(mmsi=mmsi, limit=limit)
    return {"mmsi": mmsi, "points_count": len(pts), "points": pts}
