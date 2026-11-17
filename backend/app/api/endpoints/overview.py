from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.session import get_db
from backend.app.models.entities import Dataset, Vessel, TrajectorySegment, BehavioralEvent

router = APIRouter()


@router.get("/stats")
def get_overview_statistics(db: Session = Depends(get_db)):
    total_vessels = db.query(func.count(Vessel.mmsi)).scalar() or 0
    total_observations = db.query(func.sum(Vessel.observation_count)).scalar() or 0
    analyzed_trajectories = db.query(func.count(TrajectorySegment.id)).scalar() or 0
    total_events = db.query(func.count(BehavioralEvent.id)).scalar() or 0

    # Data quality events (AIS gaps + implausible jumps)
    dq_events = db.query(func.count(BehavioralEvent.id)).filter(
        BehavioralEvent.category.in_(["AIS_TRANSMISSION_GAP", "IMPLAUSIBLE_MOVEMENT"])
    ).scalar() or 0

    # Behavioral events (excluding pure data quality)
    pure_behavioral_events = total_events - dq_events

    datasets_count = db.query(func.count(Dataset.id)).scalar() or 0

    # Category distribution
    cat_rows = db.query(
        BehavioralEvent.category, func.count(BehavioralEvent.id)
    ).group_by(BehavioralEvent.category).all()
    categories_breakdown = {r[0]: r[1] for r in cat_rows}

    # Severity distribution
    sev_rows = db.query(
        BehavioralEvent.severity, func.count(BehavioralEvent.id)
    ).group_by(BehavioralEvent.severity).all()
    severity_breakdown = {r[0]: r[1] for r in sev_rows}

    # Vessel types distribution
    vtype_rows = db.query(
        Vessel.vessel_type, func.count(Vessel.mmsi)
    ).group_by(Vessel.vessel_type).all()
    vessel_types_breakdown = {r[0]: r[1] for r in vtype_rows}

    # Recent events
    recent_events = db.query(BehavioralEvent).order_by(
        BehavioralEvent.start_time.desc()
    ).limit(8).all()

    return {
        "total_vessels": total_vessels,
        "total_observations": total_observations,
        "analyzed_trajectories": analyzed_trajectories,
        "total_events_detected": total_events,
        "behavioral_events": pure_behavioral_events,
        "data_quality_events": dq_events,
        "datasets_count": datasets_count,
        "categories_breakdown": categories_breakdown,
        "severity_breakdown": severity_breakdown,
        "vessel_types_breakdown": vessel_types_breakdown,
        "recent_events": [
            {
                "id": e.id,
                "category": e.category,
                "primary_mmsi": e.primary_mmsi,
                "secondary_mmsi": e.secondary_mmsi,
                "severity": e.severity,
                "deviation_score": e.deviation_score,
                "start_time": e.start_time.isoformat(),
                "latitude": e.latitude,
                "longitude": e.longitude,
                "explanation": e.explanation,
                "contextual_state": e.contextual_state,
            }
            for e in recent_events
        ],
    }
