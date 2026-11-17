import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text
from backend.app.db.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(64), nullable=False)  # NOAA, HAWAII_COAST, DANISH_AIS, GENERIC, SYNTHETIC
    format = Column(String(32), nullable=False)  # CSV, PARQUET, GEOPARQUET, ZIP
    file_path = Column(String(512), nullable=False)
    parquet_path = Column(String(512), nullable=True)
    
    row_count = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    vessel_count = Column(Integer, default=0)
    quality_score = Column(Float, default=1.0)
    status = Column(String(32), default="READY")  # PENDING, INGESTING, READY, FAILED
    
    time_range_start = Column(DateTime, nullable=True)
    time_range_end = Column(DateTime, nullable=True)
    bbox_min_lat = Column(Float, nullable=True)
    bbox_min_lon = Column(Float, nullable=True)
    bbox_max_lat = Column(Float, nullable=True)
    bbox_max_lon = Column(Float, nullable=True)
    
    quality_report = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Vessel(Base):
    __tablename__ = "vessels"

    mmsi = Column(Integer, primary_key=True, index=True)
    imo = Column(Integer, nullable=True, index=True)
    name = Column(String(128), nullable=True, index=True)
    vessel_type = Column(String(64), default="Unknown", index=True)  # Cargo, Tanker, Fishing, Passenger, Tug, Other
    flag = Column(String(64), nullable=True, index=True)
    length = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    draught = Column(Float, nullable=True)

    observation_count = Column(Integer, default=0)
    segment_count = Column(Integer, default=0)
    total_distance_nm = Column(Float, default=0.0)
    avg_speed_knots = Column(Float, default=0.0)
    max_speed_knots = Column(Float, default=0.0)

    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    last_lat = Column(Float, nullable=True)
    last_lon = Column(Float, nullable=True)
    last_sog = Column(Float, nullable=True)
    last_cog = Column(Float, nullable=True)
    last_heading = Column(Float, nullable=True)
    last_status = Column(String(64), nullable=True)

    data_quality_score = Column(Float, default=1.0)
    event_count = Column(Integer, default=0)
    historical_profile = Column(JSON, nullable=True)  # Speed dist, heading entropy, typical regions
    is_synthetic = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class TrajectorySegment(Base):
    __tablename__ = "trajectory_segments"

    id = Column(String(64), primary_key=True, index=True)
    mmsi = Column(Integer, index=True, nullable=False)
    segment_index = Column(Integer, default=0)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    duration_seconds = Column(Float, default=0.0)
    point_count = Column(Integer, default=0)
    distance_nm = Column(Float, default=0.0)
    avg_speed = Column(Float, default=0.0)
    max_speed = Column(Float, default=0.0)

    bbox_min_lat = Column(Float, nullable=False)
    bbox_min_lon = Column(Float, nullable=False)
    bbox_max_lat = Column(Float, nullable=False)
    bbox_max_lon = Column(Float, nullable=False)

    # Simplified GeoJSON LineString for efficient map rendering
    geometry_geojson = Column(JSON, nullable=False)
    # Statistical kinematic summary
    kinematics_summary = Column(JSON, nullable=True)
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BehavioralEvent(Base):
    __tablename__ = "behavioral_events"

    id = Column(String(64), primary_key=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    # UNUSUAL_ROUTE_DEVIATION, RENDEZVOUS, LOITERING, PEER_GROUP_DEVIATION,
    # HISTORICAL_INCONSISTENCY, AIS_TRANSMISSION_GAP, IMPLAUSIBLE_MOVEMENT
    
    primary_mmsi = Column(Integer, index=True, nullable=False)
    secondary_mmsi = Column(Integer, index=True, nullable=True)
    
    detector_id = Column(String(64), nullable=False, index=True)
    detector_version = Column(String(32), default="1.0.0")
    deviation_score = Column(Float, nullable=False)  # 0.0 to 1.0
    severity = Column(String(16), default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, default=0.8)

    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, default=0.0)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    bbox_geojson = Column(JSON, nullable=True)

    # Contextual interpretation
    contextual_state = Column(String(32), default="CONTEXT_UNAVAILABLE")
    # EXPECTED_CONTEXT, POTENTIALLY_RELEVANT, CONTEXT_UNAVAILABLE, INSUFFICIENT_DATA
    contextual_explanation = Column(Text, nullable=True)

    # Detailed explainability evidence
    explanation = Column(Text, nullable=False)
    feature_attributions = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)  # Observations, timestamps, speeds, distance metrics
    data_quality_warnings = Column(JSON, nullable=True)

    is_synthetic = Column(Boolean, default=False)
    status = Column(String(32), default="NEW", index=True)  # NEW, UNDER_INVESTIGATION, RESOLVED, FALSE_POSITIVE
    investigation_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ModelRecord(Base):
    __tablename__ = "model_records"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    model_type = Column(String(64), nullable=False)
    # TCN_AUTOENCODER, TRAJECTORY_TRANSFORMER, ISOLATION_FOREST, RULE_ENSEMBLE
    version = Column(String(32), default="1.0.0")
    dataset_id = Column(String(64), nullable=True)
    status = Column(String(32), default="INITIALIZED")  # INITIALIZED, TRAINING, TRAINED, FAILED

    hyperparameters = Column(JSON, nullable=True)
    feature_config = Column(JSON, nullable=True)
    validation_metrics = Column(JSON, nullable=True)
    training_loss_history = Column(JSON, nullable=True)
    artifact_path = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    dataset_name = Column(String(64), nullable=False)  # HAWAII_COAST_GT, DANISH_AIS_ANNOTATED, SYNTHETIC_BENCHMARK
    model_id = Column(String(64), nullable=True)
    split_strategy = Column(String(64), default="VESSEL_GROUPED_TEMPORAL")

    metrics = Column(JSON, nullable=False)  # Precision, Recall, F1, PR-AUC, ROC-AUC, P@K, FalseAlertsPerVesselDay
    class_metrics = Column(JSON, nullable=True)
    confusion_matrix = Column(JSON, nullable=True)
    report_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class JobRecord(Base):
    __tablename__ = "job_records"

    id = Column(String(64), primary_key=True, index=True)
    job_type = Column(String(64), nullable=False)  # INGESTION, DETECTION, MODEL_TRAINING, EVALUATION
    status = Column(String(32), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    progress = Column(Float, default=0.0)
    parameters = Column(JSON, nullable=True)
    log_messages = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
