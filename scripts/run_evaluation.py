import uuid
import datetime
from backend.app.db.session import SessionLocal
from backend.app.models.entities import EvaluationRun, BehavioralEvent, TrajectorySegment
from backend.ml.evaluation.evaluator import BenchmarkEvaluator


def run_benchmark_evaluation(dataset_name: str = "SYNTHETIC_BENCHMARK", model_id: str = "model_tcn_autoencoder_v1"):
    print(f"Running benchmark evaluation for {model_id} on {dataset_name}...")
    db = SessionLocal()
    try:
        segments = db.query(TrajectorySegment).all()
        events = db.query(BehavioralEvent).all()

        # Build trajectory labels: if segment overlaps with a behavioural event
        labeled_trajectories = []
        detector_predictions = []

        event_mmsis = {e.primary_mmsi: e for e in events}

        for seg in segments:
            has_anomaly = 1 if seg.mmsi in event_mmsis else 0
            evt = event_mmsis.get(seg.mmsi)
            atype = evt.category if evt else "NORMAL_TRANSIT"
            score = evt.deviation_score if evt else 0.15

            labeled_trajectories.append({
                "id": seg.id,
                "mmsi": seg.mmsi,
                "is_anomalous": has_anomaly,
                "anomaly_type": atype,
            })
            detector_predictions.append({
                "id": seg.id,
                "score": score,
            })

        evaluator = BenchmarkEvaluator()
        eval_results = evaluator.evaluate_trajectories(
            labeled_trajectories, detector_predictions, threshold=0.5
        )

        overall = eval_results["overall"]
        class_m = eval_results["class_metrics"]

        print("Benchmark Results:")
        print(f"  Precision: {overall['precision']:.4f}")
        print(f"  Recall:    {overall['recall']:.4f}")
        print(f"  F1 Score:  {overall['f1']:.4f}")
        print(f"  ROC-AUC:   {overall['roc_auc']:.4f}")
        print(f"  PR-AUC:    {overall['pr_auc']:.4f}")
        print(f"  P@5:       {overall['precision_at_5']:.4f}")
        print(f"  P@10:      {overall['precision_at_10']:.4f}")
        print(f"  False Alerts / Vessel-Day: {overall['false_alerts_per_vessel_day']:.3f}")

        # Save to DB
        eval_id = f"eval_{uuid.uuid4().hex[:8]}"
        eval_rec = EvaluationRun(
            id=eval_id,
            name=f"Evaluation Benchmark - {dataset_name}",
            dataset_name=dataset_name,
            model_id=model_id,
            split_strategy="VESSEL_GROUPED_TEMPORAL",
            metrics=overall,
            class_metrics=class_m,
            confusion_matrix=overall["confusion_matrix"],
            report_text=(
                f"Benchmark evaluation against {dataset_name}. "
                f"Achieved F1: {overall['f1']:.3f}, Precision: {overall['precision']:.3f}, Recall: {overall['recall']:.3f}, "
                f"ROC-AUC: {overall['roc_auc']:.3f}. False alarm rate: {overall['false_alerts_per_vessel_day']} / vessel-day."
            ),
        )
        db.add(eval_rec)
        db.commit()
        print(f"Evaluation record {eval_id} persisted.")
        return eval_results
    finally:
        db.close()


if __name__ == "__main__":
    run_benchmark_evaluation()
