import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Dataset
from backend.app.schemas.entities import DatasetOut, DatasetRegisterIn
from backend.ingestion.adapters.noaa import NOAAAdapter
from backend.ingestion.adapters.hawaii import HawaiiCoastGTAdapter
from backend.ingestion.adapters.danish import DanishAISAdapter
from backend.ingestion.adapters.generic import GenericAISAdapter
from backend.worker.queue import worker
from scripts.generate_demo_data import generate_demonstration_dataset

router = APIRouter()


@router.get("", response_model=List[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/generate-synthetic")
def trigger_synthetic_generation():
    """Triggers deterministic regeneration of the synthetic demonstration dataset in background."""
    def task(progress_callback=None):
        if progress_callback:
            progress_callback(0.2, "Initializing simulation...")
        res = generate_demonstration_dataset(seed=42)
        if progress_callback:
            progress_callback(1.0, "Demonstration dataset generated successfully.")
        return res

    job_id = worker.submit_job("SYNTHETIC_GENERATION", task)
    return {"message": "Synthetic generation job submitted", "job_id": job_id}


@router.post("/preview")
def preview_source_file(file_path: str, source_type: str = "GENERIC"):
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"File not found: {file_path}")

    adapters = {
        "NOAA": NOAAAdapter(),
        "HAWAII_COAST": HawaiiCoastGTAdapter(),
        "DANISH_AIS": DanishAISAdapter(),
        "GENERIC": GenericAISAdapter(),
    }
    adapter = adapters.get(source_type.upper(), GenericAISAdapter())
    schema_info = adapter.inspect_schema(path)
    sample_points = adapter.preview(path, n=5)

    return {
        "schema": schema_info,
        "preview_records": sample_points,
    }
