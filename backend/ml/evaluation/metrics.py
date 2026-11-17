from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, precision_recall_curve, auc


def compute_binary_classification_metrics(
    y_true: List[int],
    y_scores: List[float],
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Computes precision, recall, F1, ROC-AUC, PR-AUC, and confusion matrix.
    """
    if not y_true or not y_scores:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "roc_auc": 0.0,
            "pr_auc": 0.0,
            "tp": 0, "fp": 0, "tn": 0, "fn": 0,
        }

    y_t = np.array(y_true, dtype=int)
    y_s = np.array(y_scores, dtype=float)
    y_pred = (y_s >= threshold).astype(int)

    # Base counts
    tp = int(np.sum((y_t == 1) & (y_pred == 1)))
    fp = int(np.sum((y_t == 0) & (y_pred == 1)))
    tn = int(np.sum((y_t == 0) & (y_pred == 0)))
    fn = int(np.sum((y_t == 1) & (y_pred == 0)))

    prec = float(precision_score(y_t, y_pred, zero_division=0))
    rec = float(recall_score(y_t, y_pred, zero_division=0))
    f1 = float(f1_score(y_t, y_pred, zero_division=0))

    roc = 0.5
    try:
        if len(np.unique(y_t)) > 1:
            roc = float(roc_auc_score(y_t, y_s))
    except Exception:
        pass

    pr_auc_val = 0.0
    try:
        if len(np.unique(y_t)) > 1:
            p_arr, r_arr, _ = precision_recall_curve(y_t, y_s)
            pr_auc_val = float(auc(r_arr, p_arr))
    except Exception:
        pass

    return {
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc, 4),
        "pr_auc": round(pr_auc_val, 4),
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
        },
    }


def compute_precision_at_k(y_true: List[int], y_scores: List[float], k: int = 10) -> float:
    """Computes Precision@K on top ranked detections."""
    if len(y_scores) == 0:
        return 0.0
    k = min(k, len(y_scores))
    ranked_indices = np.argsort(y_scores)[::-1][:k]
    top_k_labels = np.array(y_true)[ranked_indices]
    return round(float(np.mean(top_k_labels)), 4)


def compute_false_alerts_per_vessel_day(
    false_positives: int, total_vessels: int, total_duration_days: float
) -> float:
    """Calculates false alert rate normalized by operational exposure."""
    vessel_days = max(1.0, total_vessels * max(0.1, total_duration_days))
    return round(float(false_positives / vessel_days), 3)
