import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_overview_stats():
    res = client.get("/api/v1/overview/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_vessels" in data
    assert "total_observations" in data
    assert "categories_breakdown" in data
    assert data["total_vessels"] > 0


def test_list_vessels():
    res = client.get("/api/v1/vessels?limit=10")
    assert res.status_code == 200
    vessels = res.json()
    assert len(vessels) > 0
    assert "mmsi" in vessels[0]
    assert "vessel_type" in vessels[0]


def test_get_vessel_detail_and_trajectories():
    res_list = client.get("/api/v1/vessels?limit=1")
    vessels = res_list.json()
    if vessels:
        mmsi = vessels[0]["mmsi"]
        res_v = client.get(f"/api/v1/vessels/{mmsi}")
        assert res_v.status_code == 200
        assert res_v.json()["mmsi"] == mmsi

        res_trajs = client.get(f"/api/v1/vessels/{mmsi}/trajectories")
        assert res_trajs.status_code == 200
        assert isinstance(res_trajs.json(), list)


def test_list_events_and_detail():
    res = client.get("/api/v1/events?limit=5")
    assert res.status_code == 200
    events = res.json()
    assert len(events) > 0
    evt_id = events[0]["id"]

    res_d = client.get(f"/api/v1/events/{evt_id}")
    assert res_d.status_code == 200
    assert res_d.json()["id"] == evt_id
    assert "explanation" in res_d.json()
    assert "contextual_state" in res_d.json()


def test_map_endpoints():
    res_density = client.get("/api/v1/map/density")
    assert res_density.status_code == 200
    assert "cells" in res_density.json()

    res_vessels = client.get("/api/v1/map/vessels")
    assert res_vessels.status_code == 200
    assert res_vessels.json()["type"] == "FeatureCollection"

    res_zones = client.get("/api/v1/map/zones")
    assert res_zones.status_code == 200
    assert "ports" in res_zones.json()
    assert "anchorages" in res_zones.json()


def test_models_and_evaluation():
    from backend.app.db.session import SessionLocal
    from backend.app.models.entities import ModelRecord, EvaluationRun
    import datetime

    db = SessionLocal()
    try:
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

    res_models = client.get("/api/v1/models")
    assert res_models.status_code == 200
    assert len(res_models.json()) > 0

    res_eval = client.get("/api/v1/evaluation")
    assert res_eval.status_code == 200
    assert len(res_eval.json()) > 0
