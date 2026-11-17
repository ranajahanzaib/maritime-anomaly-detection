from typing import List, Dict, Any, Optional
import datetime
from pydantic import BaseModel, Field


# --- Datasets ---
class DatasetOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    source_type: str
    format: str
    file_path: str
    row_count: int
    valid_count: int
    rejected_count: int
    vessel_count: int
    quality_score: float
    status: str
    time_range_start: Optional[datetime.datetime] = None
    time_range_end: Optional[datetime.datetime] = None
    bbox_min_lat: Optional[float] = None
    bbox_min_lon: Optional[float] = None
    bbox_max_lat: Optional[float] = None
    bbox_max_lon: Optional[float] = None
    is_synthetic: bool = False
    created_at: Optional[datetime.datetime] = None


class DatasetRegisterIn(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str = "GENERIC"  # NOAA, HAWAII_COAST, DANISH_AIS, GENERIC
    file_path: str


# --- Vessels ---
class VesselOut(BaseModel):
    mmsi: int
    imo: Optional[int] = None
    name: Optional[str] = None
    vessel_type: str
    flag: Optional[str] = None
    length: Optional[float] = None
    width: Optional[float] = None
    draught: Optional[float] = None
    observation_count: int
    segment_count: int
    total_distance_nm: float
    avg_speed_knots: float
    max_speed_knots: float
    first_seen: Optional[datetime.datetime] = None
    last_seen: Optional[datetime.datetime] = None
    last_lat: Optional[float] = None
    last_lon: Optional[float] = None
    last_sog: Optional[float] = None
    last_cog: Optional[float] = None
    last_heading: Optional[float] = None
    last_status: Optional[str] = None
    data_quality_score: float
    event_count: int
    historical_profile: Optional[Dict[str, Any]] = None
    is_synthetic: bool = False


# --- Trajectories ---
class TrajectorySegmentOut(BaseModel):
    id: str
    mmsi: int
    segment_index: int
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration_seconds: float
    point_count: int
    distance_nm: float
    avg_speed: float
    max_speed: float
    bbox_min_lat: float
    bbox_min_lon: float
    bbox_max_lat: float
    bbox_max_lon: float
    geometry_geojson: Dict[str, Any]
    kinematics_summary: Optional[Dict[str, Any]] = None
    is_synthetic: bool = False


# --- Events ---
class BehavioralEventOut(BaseModel):
    id: str
    category: str
    primary_mmsi: int
    secondary_mmsi: Optional[int] = None
    detector_id: str
    detector_version: str
    deviation_score: float
    severity: str
    confidence: float
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration_seconds: float
    latitude: float
    longitude: float
    bbox_geojson: Optional[Dict[str, Any]] = None
    contextual_state: str
    contextual_explanation: Optional[str] = None
    explanation: str
    feature_attributions: Optional[Dict[str, Any]] = None
    evidence: Optional[Dict[str, Any]] = None
    data_quality_warnings: Optional[List[str]] = None
    is_synthetic: bool = False
    status: str
    investigation_notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = None


class EventUpdateIn(BaseModel):
    status: Optional[str] = None  # NEW, UNDER_INVESTIGATION, RESOLVED, FALSE_POSITIVE
    investigation_notes: Optional[str] = None


# --- Models ---
class ModelRecordOut(BaseModel):
    id: str
    name: str
    model_type: str
    version: str
    dataset_id: Optional[str] = None
    status: str
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_config: Optional[Dict[str, Any]] = None
    validation_metrics: Optional[Dict[str, Any]] = None
    training_loss_history: Optional[List[Dict[str, Any]]] = None
    artifact_path: Optional[str] = None
    created_at: Optional[datetime.datetime] = None


class ModelTrainIn(BaseModel):
    name: str = "TCN Trajectory Autoencoder"
    model_type: str = "TCN_AUTOENCODER"  # TCN_AUTOENCODER, TRAJECTORY_TRANSFORMER
    dataset_id: str = "synthetic_demo_v1"
    epochs: int = 10
    batch_size: int = 16
    learning_rate: float = 0.002


# --- Evaluation ---
class EvaluationRunOut(BaseModel):
    id: str
    name: str
    dataset_name: str
    model_id: Optional[str] = None
    split_strategy: str
    metrics: Dict[str, Any]
    class_metrics: Optional[Dict[str, Any]] = None
    confusion_matrix: Optional[Dict[str, Any]] = None
    report_text: Optional[str] = None
    created_at: Optional[datetime.datetime] = None


# --- Jobs ---
class JobOut(BaseModel):
    id: str
    job_type: str
    status: str
    progress: float
    parameters: Optional[Dict[str, Any]] = None
    log_messages: Optional[List[str]] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime.datetime] = None
