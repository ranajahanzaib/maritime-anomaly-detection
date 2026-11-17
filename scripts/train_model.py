import sys
from pathlib import Path
from backend.app.db.session import SessionLocal
from backend.app.models.entities import ModelRecord, TrajectorySegment
from backend.ingestion.storage.duckdb_store import DuckDBStore
from backend.ml.training.trainer import TrajectoryModelTrainer


def run_training_experiment(
    model_name: str = "TCN Trajectory Autoencoder v1",
    model_type: str = "TCN_AUTOENCODER",
    dataset_id: str = "synthetic_demo_v1",
    epochs: int = 12,
    batch_size: int = 16,
    lr: float = 0.002,
):
    print(f"Starting training run for {model_name} ({model_type}) on dataset {dataset_id}...")
    store = DuckDBStore()
    points = store.query_points(dataset_id=dataset_id, limit=5000)

    # Group points by vessel
    tracks_by_mmsi = {}
    for p in points:
        tracks_by_mmsi.setdefault(p["mmsi"], []).append(p)

    tracks = list(tracks_by_mmsi.values())
    print(f"Loaded {len(tracks)} vessel tracks for training.")

    trainer = TrajectoryModelTrainer(
        model_type=model_type,
        seq_len=16,
        batch_size=batch_size,
        epochs=epochs,
        learning_rate=lr,
    )

    model_id = f"model_{model_type.lower()}_v1"

    def on_epoch(epoch, total_epochs, t_loss, v_loss):
        print(f"  Epoch [{epoch}/{total_epochs}] Train Loss: {t_loss:.5f} | Val Loss: {v_loss:.5f}")

    res = trainer.train(
        model_id=model_id,
        tracks=tracks,
        dataset_id=dataset_id,
        progress_callback=on_epoch,
    )

    print("Training completed! Validation metrics:", res["validation_metrics"])

    # Persist in DB
    db = SessionLocal()
    try:
        rec = db.query(ModelRecord).filter(ModelRecord.id == model_id).first()
        if not rec:
            rec = ModelRecord(
                id=model_id,
                name=model_name,
                model_type=model_type,
                version="1.0.0",
                dataset_id=dataset_id,
                status="TRAINED",
                hyperparameters={
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "lr": lr,
                    "seq_len": 16,
                    "in_features": 7,
                    "latent_dim": 16,
                },
                feature_config={
                    "features": ["lat_norm", "lon_norm", "sog_norm", "sin_cog", "cos_cog", "turn_rate", "accel"],
                },
                validation_metrics=res["validation_metrics"],
                training_loss_history=res["history"],
                artifact_path=res["artifact_path"],
            )
            db.add(rec)
        else:
            rec.status = "TRAINED"
            rec.validation_metrics = res["validation_metrics"]
            rec.training_loss_history = res["history"]
            rec.artifact_path = res["artifact_path"]
        db.commit()
    finally:
        db.close()

    print(f"Model {model_id} persisted in model registry.")
    return res


if __name__ == "__main__":
    mtype = sys.argv[1] if len(sys.argv) > 1 else "TCN_AUTOENCODER"
    run_training_experiment(model_type=mtype)
