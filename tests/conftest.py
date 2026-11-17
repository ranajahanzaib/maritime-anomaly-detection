import datetime
import pytest
from backend.app.db.init_db import init_db
from backend.app.db.session import SessionLocal
from backend.app.models.entities import ModelRecord, EvaluationRun, Vessel
from scripts.generate_demo_data import generate_demonstration_dataset


@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    """Session-level fixture initializing the test database and seeding baseline records."""
    init_db()
    db = SessionLocal()
    try:
        if db.query(Vessel).count() == 0:
            generate_demonstration_dataset()

        # Ensure at least one ModelRecord exists
        if db.query(ModelRecord).count() == 0:
            m = ModelRecord(
                id="test_model_tcn_v1",
                name="TCN Autoencoder Test",
                model_type="TCN_AUTOENCODER",
                version="v1.0.0",
                status="TRAINED",
                validation_metrics={"final_val_loss": 0.042, "anomaly_threshold": 0.12},
                hyperparameters={"epochs": 5, "lr": 0.001},
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(m)
            db.commit()

        # Ensure at least one EvaluationRun exists
        if db.query(EvaluationRun).count() == 0:
            ev = EvaluationRun(
                id="test_eval_v1",
                name="Synthetic Benchmark Evaluation",
                model_id="test_model_tcn_v1",
                dataset_name="SYNTHETIC_BENCHMARK",
                split_strategy="VESSEL_GROUPED_TEMPORAL",
                metrics={
                    "precision": 0.89,
                    "recall": 0.87,
                    "f1_score": 0.88,
                    "pr_auc": 0.91,
                    "roc_auc": 0.94,
                    "precision_at_5": 1.0,
                    "precision_at_10": 0.90,
                    "false_alerts_per_vessel_day": 0.12,
                },
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(ev)
            db.commit()
    finally:
        db.close()
