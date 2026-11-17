from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import EvaluationRun
from backend.app.schemas.entities import EvaluationRunOut
from backend.worker.queue import worker
from scripts.run_evaluation import run_benchmark_evaluation

router = APIRouter()


@router.get("", response_model=List[EvaluationRunOut])
def list_evaluations(db: Session = Depends(get_db)):
    return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()


@router.get("/{eval_id}", response_model=EvaluationRunOut)
def get_evaluation(eval_id: str, db: Session = Depends(get_db)):
    ev = db.query(EvaluationRun).filter(EvaluationRun.id == eval_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return ev


@router.post("/run")
def trigger_evaluation_run(
    dataset_name: str = "SYNTHETIC_BENCHMARK",
    model_id: str = "model_tcn_autoencoder_v1",
):
    def task(progress_callback=None, **kwargs):
        return run_benchmark_evaluation(dataset_name=dataset_name, model_id=model_id)

    job_id = worker.submit_job(
        "EVALUATION_RUN",
        task,
        parameters={"dataset_name": dataset_name, "model_id": model_id},
    )
    return {"message": "Benchmark evaluation task submitted to worker", "job_id": job_id}
