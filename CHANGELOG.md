# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-17

### Added
- **Data Ingestion & Normalization:**
  - Multi-source canonical AIS parser (`CanonicalAISPoint`) supporting NOAA MarineCadastre, HawaiiCoast_GT, and Danish maritime datasets.
  - Comprehensive `DataQualityValidator` for coordinate bounds, duplicate message timestamps, out-of-order sequencing, and kinematic jump detection.
  - Hybrid storage engine using Apache Parquet for partitioned raw point streams and DuckDB / SQLite / PostgreSQL for analytical querying.
- **Trajectory Processing & Kinematics:**
  - Geodesic trajectory segmentation by configurable time gaps (`MAX_TIME_GAP_MINUTES`).
  - Kinematic metrics computation: Haversine distance, speed over ground (SOG), rate of turn (ROT), course over ground (COG), and acceleration.
  - Trajectory simplification with multi-zoom level-of-detail Ramer-Douglas-Peucker (RDP).
  - Explicit gap marking without silent interpolation.
- **Behavioral Detection Suite:**
  - Rule-based detectors for loitering, rendezvous interactions, corridor route deviation, speed violations, and AIS transmission gap anomalies.
  - Statistical peer-group deviation baselines and historical vessel movement inconsistency profiling.
  - Deep learning anomaly detection models: PyTorch 1D Causal Dilated Temporal Convolutional Network (TCN) Autoencoder and comparative Trajectory Transformer.
  - Operational maritime context interpreter classifying detections into `EXPECTED_CONTEXT`, `POTENTIALLY_RELEVANT`, and `CONTEXT_UNAVAILABLE` based on anchorages, ports, and Traffic Separation Schemes (TSS).
- **Evaluation & Benchmarking Framework:**
  - Vessel-stratified temporal train/test splitting.
  - Evaluation metrics: Precision-Recall AUC (PR-AUC), ROC-AUC, Precision@K, and False Alerts per Vessel-Day.
  - Synthetic benchmark dataset generator (`scripts/generate_demo_data.py`) covering 10 maritime movement scenarios.
- **Full-Stack Application & Interface:**
  - FastAPI backend with 9 API endpoints for overview statistics, datasets, vessels, spatial map layers, behavioral events, models, evaluation runs, async jobs, and GeoJSON/CSV exports.
  - Next.js 15 frontend with Tailwind CSS, MapLibre GL JS interactive maritime map, and Recharts analytical visualizations across 8 navigation views.
- **Infrastructure & Testing:**
  - Containerization with Docker and multi-service `docker-compose.yml`.
  - Comprehensive test suite spanning unit, integration, and end-to-end workflow tests.
  - Full technical documentation in `docs/` with 7 Mermaid architecture diagrams.
