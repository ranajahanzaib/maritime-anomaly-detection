# Evaluation Framework & Benchmark Metrics

The platform provides a rigorous evaluation framework designed to benchmark anomaly detection algorithms against annotated datasets (e.g. HawaiiCoast_GT and Danish AIS).

---

## 1. Preventing Data Leakage

- **Vessel-Grouped Splitting:** Trajectories from the same vessel are strictly grouped into either the training split or test split. Adjacent sliding windows from the same vessel must never leak between train and evaluation sets.
- **Temporal Splitting:** Historical periods are chronologically partitioned so models only predict on future horizons.

---

## 2. Core Benchmark Metrics

1. **Precision & Recall:**
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
2. **F1 Score:** Harmonic mean of precision and recall.
3. **PR-AUC (Precision-Recall Area Under Curve):** Critical metric under high maritime class imbalance (where anomalies constitute $<5\%$ of total traffic).
4. **ROC-AUC:** Overall diagnostic ranking ability.
5. **Precision at K (P@K):** Precision among the top $K$ most anomalous detections prioritized for human review.
6. **False Alerts per Vessel-Day:**
   $$\text{FAR} = \frac{\text{False Positives}}{\text{Total Vessels} \times \text{Operational Days}}$$

---

## 3. Running Evaluations

```bash
# Execute evaluation benchmark against annotated corpora
python scripts/run_evaluation.py
```

Results are displayed in the UI Model Laboratory with confusion matrices and class-level breakdowns.
