# System Architecture

The **Vessel Behavior Analysis Platform** is an open-source maritime movement intelligence system. Rather than acting as a static AIS viewer, it learns normal maritime movement patterns, detects multidimensional behavioral deviations, and provides human analysts with explainable evidence.

```mermaid
flowchart TD
    subgraph DataIngestion ["1. Data Ingestion & Storage"]
        RawAIS["Raw AIS (CSV / Parquet / ZIP)"] --> Adapters["Source Adapters (NOAA / DMA / HawaiiCoast / Generic)"]
        Adapters --> Validator["Data Quality & Plausibility Validator"]
        Validator --> ParquetStore["Partitioned Parquet Storage (data/storage)"]
        Validator --> DuckDBLayer["DuckDB Analytical Layer"]
    end

    subgraph TrajectoryProcessing ["2. Trajectory Processing"]
        ParquetStore --> Segmenter["Trajectory Segmenter (Max Gap Threshold)"]
        Segmenter --> Kinematics["Kinematic Derivations (Speed, Accel, Turn Rate)"]
        Kinematics --> Simplifier["RDP Simplifier (Multi-zoom GeoJSON)"]
    end

    subgraph FeatureEngineering ["3. Feature Engineering"]
        Kinematics --> MovFeats["Movement Kinematics Features"]
        Kinematics --> SpatFeats["Spatial & Corridor Distance Features"]
        Kinematics --> TempFeats["Temporal & Dwell Features"]
        Kinematics --> InterFeats["Pairwise Interaction Features"]
    end

    subgraph BehavioralIntelligence ["4. Behavioral Intelligence & Models"]
        MovFeats & SpatFeats & TempFeats --> RuleDetectors["Rule Detectors (Loitering, Rendezvous, TSS Deviation, Jumps)"]
        MovFeats & SpatFeats & TempFeats --> StatDetectors["Statistical Detectors (Peer Group, Historical Baseline, Isolation Forest)"]
        MovFeats & SpatFeats & TempFeats --> DLModels["Deep Sequence Models (TCN Autoencoder & Trajectory Transformer)"]
        RuleDetectors & StatDetectors & DLModels --> ContextInterpreter["Maritime Context Interpreter (Ports, Anchorages, TSS)"]
    end

    subgraph PersistenceApplication ["5. Application & Storage"]
        ContextInterpreter --> DB[("PostgreSQL / PostGIS / SQLite")]
        DB --> FastAPI["FastAPI REST Backend (/api/v1)"]
        DuckDBLayer --> FastAPI
        FastAPI --> WebUI["Next.js Dark Analytical Frontend (MapLibre GL)"]
        Worker["Background Job Worker"] --> DB
    end
```

---

## 2. Ingestion Pipeline

```mermaid
flowchart LR
    A["Raw AIS File"] --> B["Adapter (Normalize Schema)"]
    B --> C["Canonical AIS Point Stream"]
    C --> D{"Coordinate & Speed Bounds?"}
    D -- "Invalid" --> E["Flag Rejection Reason (Never Drop Silently)"]
    D -- "Valid" --> F["Chronological Sort by MMSI"]
    F --> G["Kinematic Jump & Duplication Check"]
    G --> H["Partitioned Parquet Writer"]
    H --> I["Dataset Quality Audit Report"]
```

---

## 3. Trajectory Processing Pipeline

```mermaid
flowchart TD
    P["Sorted AIS Points for MMSI"] --> G{"Time Gap > Threshold (45m)?"}
    G -- "Yes" --> Gap["Record Transmission Gap Event"]
    Gap --> NewSeg["Break into Discrete Trajectory Segment"]
    G -- "No" --> ShortGap{"Short Gap (2-10m)?"}
    ShortGap -- "Yes" --> Interp["Linear/Spherical Interpolation with Uncertainty Tag"]
    ShortGap -- "No" --> Normal["Direct Kinematic Derivation"]
    NewSeg & Interp & Normal --> Kin["Compute SOG, Accel, Turn Rate, Bearing"]
    Kin --> RDP["Ramer-Douglas-Peucker Trajectory Simplification"]
    RDP --> SegGeo["Persist Trajectory Segment & GeoJSON"]
```

---

## 4. Behavioural Detection Workflow

```mermaid
flowchart TD
    Track["Vessel Trajectory & Segment Kinematics"] --> D1["Loitering Detector (SOG < 1.5 kts, Dwell > 2h)"]
    Track --> D2["Rendezvous Detector (Inter-vessel < 600m, Relative SOG < 4 kts)"]
    Track --> D3["Route Corridor Deviation (Fairway Centerline Lateral Distance)"]
    Track --> D4["Peer Group Deviation (Class Z-Score > 2.5)"]
    Track --> D5["Historical Inconsistency (Shift from Home Center / Baseline)"]
    Track --> D6["Temporal Deep Sequence Model (Reconstruction MSE > Threshold)"]

    D1 & D2 & D3 & D4 & D5 & D6 --> Context["Maritime Context Engine"]
    Context --> State{"Occurs inside Recognized Zone?"}
    State -- "Anchorage / Port" --> Exp["EXPECTED_CONTEXT (Normal Waiting / Tug Assist)"]
    State -- "Open Water" --> Pot["POTENTIALLY_RELEVANT (Unusual Open Sea Encounter)"]
    State -- "No Zones" --> Unav["CONTEXT_UNAVAILABLE"]

    Exp & Pot & Unav --> Evt["Generate Explainable BehavioralEvent with Evidence Payload"]
```

---

## 5. Model Training & Inference Workflow

```mermaid
flowchart LR
    Parquet["Parquet Trajectory Store"] --> Windows["Sliding Window Slicer (L=16/32 steps)"]
    Windows --> Center["Relative Center Normalization & Kinematics Scaling"]
    Center --> Split["Vessel-Grouped Train / Validation Split"]
    Split --> TCN["Temporal Conv Autoencoder / Transformer"]
    TCN --> Train["Epoch Loop with Adam & MSE Loss"]
    Train --> EvalThresh["Empirical Anomaly Threshold (p95 Validation Error)"]
    EvalThresh --> Registry["Model Store Checkpoint (.pt + metadata.json)"]
    Registry --> Inference["Inference Sequence Scorer"]
```

---

## 6. Event Investigation Flow

```mermaid
sequenceDiagram
    autonumber
    actor Analyst as Maritime Analyst
    participant UI as Map & Event Explorer (Next.js)
    participant API as FastAPI Backend
    participant DuckDB as DuckDB / DB Engine

    Analyst->>UI: Selects Detected Anomaly (e.g. Rendezvous)
    UI->>API: GET /api/v1/events/{id}
    API->>DuckDB: Fetch Event Record & Evidence Payload
    DuckDB-->>API: Evidence (Dual-vessel timeline, corridor waypoints)
    API-->>UI: BehavioralEvent JSON
    UI-->>Analyst: Visualizes Inter-vessel Distance Chart & Context
    Analyst->>UI: Submits Investigation Note & Status (e.g. UNDER_INVESTIGATION)
    UI->>API: PATCH /api/v1/events/{id}
    API->>DuckDB: Persist Audit Status & Notes
    DuckDB-->>API: Success
    API-->>UI: Updated Event
```

---

## 7. Data Storage Architecture

```mermaid
flowchart TD
    subgraph AnalyticalLayer ["Columnar Analytical Layer"]
        Parquet["Partitioned Parquet Files (data/storage/{dataset_id}/data.parquet)"]
        DuckDB["DuckDB In-Memory SQL Engine"]
        Parquet --> DuckDB
        DuckDB --> Density["Spatial Grid Aggregation & Heatmaps"]
        DuckDB --> TrackQueries["Sub-millisecond History Lookups"]
    end

    subgraph RelationalLayer ["Application Metadata Layer (PostgreSQL / SQLite)"]
        Postgres["Datasets · Vessels · Trajectories · Events · Models · Evaluations · Jobs"]
    end

    subgraph ArtifactLayer ["Model Artifact Store"]
        Weights["Torch Checkpoint (.pt)"]
        Meta["Hyperparameters & Loss History (.json)"]
    end
```
