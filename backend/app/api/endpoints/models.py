from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import ModelRecord
from backend.app.schemas.entities import ModelRecordOut, ModelTrainIn
from backend.worker.queue import worker
from scripts.train_model import run_training_experiment

router = APIRouter()


@router.get("", response_model=List[ModelRecordOut])
def list_models(db: Session = Depends(get_db)):
    return db.query(ModelRecord).order_by(ModelRecord.created_at.desc()).all()


@router.get("/{model_id}", response_model=ModelRecordOut)
def get_model(model_id: str, db: Session = Depends(get_db)):
    m = db.query(ModelRecord).filter(ModelRecord.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model record not found")
    return m


@router.post("/train")
def train_model_endpoint(payload: ModelTrainIn):
    """Submits a model training job to the background worker."""
    def task(progress_callback=None, **kwargs):
        return run_training_experiment(
            model_name=payload.name,
            model_type=payload.model_type,
            dataset_id=payload.dataset_id,
            epochs=payload.epochs,
            batch_size=payload.batch_size,
            lr=payload.learning_rate,
        )

    job_id = worker.submit_job(
        "MODEL_TRAINING",
        task,
        parameters=payload.model_dump(),
    )
    return {"message": "Model training task submitted to worker", "job_id": job_id}


@router.post("/compare")
def compare_models(model_ids: List[str], db: Session = Depends(get_db)):
    models = db.query(ModelRecord).filter(ModelRecord.id.in_(model_ids)).all()
    comparison = []
    for m in models:
        metrics = m.validation_metrics or {}
        comparison.append({
            "id": m.id,
            "name": m.name,
            "model_type": m.model_type,
            "status": m.status,
            "final_train_loss": metrics.get("final_train_loss"),
            "final_val_loss": metrics.get("final_val_loss"),
            "anomaly_threshold": metrics.get("anomaly_threshold"),
            "reconstruction_error_mean": metrics.get("reconstruction_error_mean"),
            "epochs": m.hyperparameters.get("epochs") if m.hyperparameters else None,
            "lr": m.hyperparameters.get("lr") if m.hyperparameters else None,
        })
    return {"comparison": comparison}
