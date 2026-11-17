# REST API Reference

The FastAPI backend exposes typed RESTful endpoints documented via OpenAPI at `/api/v1/docs`.

---

## Key Endpoints

### 1. Overview & Statistics
- `GET /api/v1/overview/stats`: Returns aggregated platform metrics (total vessels, observations, trajectory counts, behavioral events, category breakdowns, severity distributions, recent events).

### 2. Vessel Explorer
- `GET /api/v1/vessels`: Search and filter vessels by MMSI, name, vessel type, flag, or event status with pagination.
- `GET /api/v1/vessels/{mmsi}`: Detailed metadata and baseline profile.
- `GET /api/v1/vessels/{mmsi}/trajectories`: Simplified GeoJSON trajectory segments.
- `GET /api/v1/vessels/{mmsi}/history`: Chronological AIS position pings.
- `GET /api/v1/vessels/{mmsi}/events`: Detected behavioral events for vessel.

### 3. Maritime Map
- `GET /api/v1/map/density`: Aggregated spatial density grid cells for traffic heatmap rendering.
- `GET /api/v1/map/vessels`: Latest positions, headings, speeds, and categories as GeoJSON FeatureCollection.
- `GET /api/v1/map/trajectories`: Simplified GeoJSON LineStrings.
- `GET /api/v1/map/zones`: Monitored reference ports, designated anchorages, and shipping corridors.

### 4. Behavioral Events & Investigation
- `GET /api/v1/events`: List events filtered by category, severity, status, or vessel.
- `GET /api/v1/events/{id}`: Full detail including feature attributions and quantitative evidence payloads.
- `PATCH /api/v1/events/{id}`: Update review status (`NEW`, `UNDER_INVESTIGATION`, `RESOLVED`, `FALSE_POSITIVE`) and analyst notes.
- `POST /api/v1/events/run-detection`: Execute anomaly detection pipeline on demand.

### 5. Model Management
- `GET /api/v1/models`: List registered models.
- `GET /api/v1/models/{id}`: Hyperparameters, validation loss history, and metrics.
- `POST /api/v1/models/train`: Submit background training run.

### 6. Evaluation & Benchmarking
- `GET /api/v1/evaluation`: List benchmark evaluation runs.
- `POST /api/v1/evaluation/run`: Launch benchmark evaluation against ground-truth annotations.

### 7. Data Export
- `GET /api/v1/export/events?format=json|csv|geojson`: Export detected events and evidence.
