from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import JobRecord
from backend.app.schemas.entities import JobOut

router = APIRouter()


@router.get("", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(JobRecord).order_by(JobRecord.created_at.desc()).limit(50).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    j = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job record not found")
    return j
