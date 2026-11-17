from typing import List, Dict, Any, Tuple
import numpy as np
from backend.ml.evaluation.metrics import (
    compute_binary_classification_metrics,
    compute_precision_at_k,
    compute_false_alerts_per_vessel_day,
)


class BenchmarkEvaluator:
    """
    Evaluates anomaly detectors against ground-truth annotations (Danish AIS, HawaiiCoast_GT, Synthetic).
    Prevents data leakage by splitting at vessel-level or strict temporal boundaries.
    """

    def split_vessel_grouped(
        self,
        vessel_ids: List[int],
        test_ratio: float = 0.3,
        random_seed: int = 42,
    ) -> Tuple[List[int], List[int]]:
        unique_vessels = np.array(list(set(vessel_ids)))
        rng = np.random.default_rng(random_seed)
        rng.shuffle(unique_vessels)

        n_test = max(1, int(len(unique_vessels) * test_ratio))
        test_vessels = list(unique_vessels[:n_test])
        train_vessels = list(unique_vessels[n_test:])
        return train_vessels, test_vessels

    def evaluate_trajectories(
        self,
        labeled_trajectories: List[Dict[str, Any]],
        detector_predictions: List[Dict[str, Any]],
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        labeled_trajectories: list of dicts with 'id', 'mmsi', 'is_anomalous' (0 or 1), 'anomaly_type'
        detector_predictions: list of dicts with 'id', 'score' (0.0 to 1.0)
        """
        pred_map = {p["id"]: p["score"] for p in detector_predictions}

        y_true = []
        y_scores = []
        class_true = {}
        class_scores = {}

        for item in labeled_trajectories:
            tid = item["id"]
            label = int(item.get("is_anomalous", 0))
            score = float(pred_map.get(tid, 0.0))
            atype = item.get("anomaly_type", "GENERAL")

            y_true.append(label)
            y_scores.append(score)

            if atype not in class_true:
                class_true[atype] = []
                class_scores[atype] = []
            class_true[atype].append(label)
            class_scores[atype].append(score)

        overall_metrics = compute_binary_classification_metrics(y_true, y_scores, threshold=threshold)
        p_at_5 = compute_precision_at_k(y_true, y_scores, k=5)
        p_at_10 = compute_precision_at_k(y_true, y_scores, k=10)

        fp_count = overall_metrics["confusion_matrix"]["fp"]
        unique_vessels = len(set(t["mmsi"] for t in labeled_trajectories))
        fa_rate = compute_false_alerts_per_vessel_day(
            false_positives=fp_count,
            total_vessels=unique_vessels,
            total_duration_days=3.0,
        )

        # Class-level metrics
        class_metrics = {}
        for cname in class_true:
            c_m = compute_binary_classification_metrics(class_true[cname], class_scores[cname], threshold=threshold)
            class_metrics[cname] = {
                "support": len(class_true[cname]),
                "precision": c_m["precision"],
                "recall": c_m["recall"],
                "f1": c_m["f1"],
            }

        return {
            "overall": {
                **overall_metrics,
                "precision_at_5": p_at_5,
                "precision_at_10": p_at_10,
                "false_alerts_per_vessel_day": fa_rate,
                "total_evaluated_trajectories": len(labeled_trajectories),
            },
            "class_metrics": class_metrics,
        }
