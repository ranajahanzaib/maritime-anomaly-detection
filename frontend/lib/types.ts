export interface OverviewStats {
  total_vessels: number;
  total_observations: number;
  analyzed_trajectories: number;
  total_events_detected: number;
  behavioral_events: number;
  data_quality_events: number;
  datasets_count: number;
  categories_breakdown: Record<string, number>;
  severity_breakdown: Record<string, number>;
  vessel_types_breakdown: Record<string, number>;
  recent_events: Array<{
    id: string;
    category: string;
    primary_mmsi: number;
    secondary_mmsi?: number;
    severity: string;
    deviation_score: number;
    start_time: string;
    latitude: number;
    longitude: number;
    explanation: string;
    contextual_state: string;
  }>;
}

export interface Vessel {
  mmsi: number;
  imo?: number;
  name?: string;
  vessel_type: string;
  flag?: string;
  length?: number;
  width?: number;
  draught?: number;
  observation_count: number;
  segment_count: number;
  total_distance_nm: number;
  avg_speed_knots: number;
  max_speed_knots: number;
  first_seen?: string;
  last_seen?: string;
  last_lat?: number;
  last_lon?: number;
  last_sog?: number;
  last_cog?: number;
  last_heading?: number;
  last_status?: string;
  data_quality_score: number;
  event_count: number;
  historical_profile?: Record<string, any>;
  is_synthetic: boolean;
}

export interface TrajectorySegment {
  id: string;
  mmsi: number;
  segment_index: number;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  point_count: number;
  distance_nm: number;
  avg_speed: number;
  max_speed: number;
  bbox_min_lat: number;
  bbox_min_lon: number;
  bbox_max_lat: number;
  bbox_max_lon: number;
  geometry_geojson: {
    type: "LineString";
    coordinates: [number, number][];
  };
  kinematics_summary?: Record<string, any>;
  is_synthetic: boolean;
}

export interface BehavioralEvent {
  id: string;
  category: string;
  primary_mmsi: number;
  secondary_mmsi?: number;
  detector_id: string;
  detector_version: string;
  deviation_score: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  latitude: number;
  longitude: number;
  bbox_geojson?: any;
  contextual_state: "EXPECTED_CONTEXT" | "POTENTIALLY_RELEVANT" | "CONTEXT_UNAVAILABLE" | "INSUFFICIENT_DATA";
  contextual_explanation?: string;
  explanation: string;
  feature_attributions?: Record<string, any>;
  evidence?: {
    interaction_timeline?: Array<{
      timestamp: string;
      distance_meters: number;
      vessel_a_sog: number;
      vessel_b_sog: number;
      relative_speed: number;
      course_diff_deg: number;
    }>;
    expected_corridor_waypoints?: Array<{ lat: number; lon: number }>;
    actual_peak_deviation_coords?: [number, number];
    last_reported_position?: [number, number];
    reappearance_position?: [number, number];
    center_coordinates?: [number, number];
    radius_meters?: number;
    cluster_point_count?: number;
    gap_duration_seconds?: number;
    observed_distribution?: Record<string, any>;
    peer_baseline?: Record<string, any>;
    feature_vector_summary?: Record<string, any>;
  };
  data_quality_warnings?: string[];
  is_synthetic: boolean;
  status: "NEW" | "UNDER_INVESTIGATION" | "RESOLVED" | "FALSE_POSITIVE";
  investigation_notes?: string;
  created_at?: string;
}

export interface ModelRecord {
  id: string;
  name: string;
  model_type: string;
  version: string;
  dataset_id?: string;
  status: string;
  hyperparameters?: Record<string, any>;
  feature_config?: Record<string, any>;
  validation_metrics?: Record<string, any>;
  training_loss_history?: Array<{
    epoch: number;
    train_loss: number;
    val_loss: number;
  }>;
  artifact_path?: string;
  created_at?: string;
}

export interface EvaluationRun {
  id: string;
  name: string;
  dataset_name: string;
  model_id?: string;
  split_strategy: string;
  metrics: {
    precision: number;
    recall: number;
    f1: number;
    roc_auc: number;
    pr_auc: number;
    precision_at_5: number;
    precision_at_10: number;
    false_alerts_per_vessel_day: number;
    total_evaluated_trajectories: number;
    confusion_matrix: {
      tp: number;
      fp: number;
      tn: number;
      fn: number;
    };
  };
  class_metrics?: Record<string, any>;
  report_text?: string;
  created_at?: string;
}

export interface DatasetItem {
  id: string;
  name: string;
  description?: string;
  source_type: string;
  format: string;
  row_count: number;
  valid_count: number;
  rejected_count: number;
  vessel_count: number;
  quality_score: number;
  status: string;
  time_range_start?: string;
  time_range_end?: string;
  is_synthetic: boolean;
  created_at?: string;
}

export interface JobRecord {
  id: string;
  job_type: string;
  status: string;
  progress: number;
  parameters?: Record<string, any>;
  log_messages?: string[];
  error_message?: string;
  result?: any;
  created_at?: string;
}
