import {
  OverviewStats,
  Vessel,
  TrajectorySegment,
  BehavioralEvent,
  ModelRecord,
  EvaluationRun,
  DatasetItem,
  JobRecord,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errorDetail = "API Error";
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch (_) {}
    throw new Error(`${res.status}: ${errorDetail}`);
  }
  return res.json();
}

export const api = {
  // Overview
  getOverviewStats: () => fetchJson<OverviewStats>("/overview/stats"),

  // Vessels
  getVessels: (params?: { query?: string; vessel_type?: string; flag?: string; has_events?: boolean; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.query) searchParams.set("query", params.query);
    if (params?.vessel_type && params.vessel_type !== "All") searchParams.set("vessel_type", params.vessel_type);
    if (params?.flag) searchParams.set("flag", params.flag);
    if (params?.has_events) searchParams.set("has_events", "true");
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    const qs = searchParams.toString();
    return fetchJson<Vessel[]>(`/vessels${qs ? `?${qs}` : ""}`);
  },

  getVesselDetail: (mmsi: number) => fetchJson<Vessel>(`/vessels/${mmsi}`),
  getVesselTrajectories: (mmsi: number) => fetchJson<TrajectorySegment[]>(`/vessels/${mmsi}/trajectories`),
  getVesselHistory: (mmsi: number, limit: number = 1000) => fetchJson<{ mmsi: number; points: any[] }>(`/vessels/${mmsi}/history?limit=${limit}`),
  getVesselEvents: (mmsi: number) => fetchJson<BehavioralEvent[]>(`/vessels/${mmsi}/events`),

  // Map
  getMapDensity: (gridSize: number = 0.05) => fetchJson<{ cells: Array<{ lat: number; lon: number; count: number; avg_sog: number }> }>(`/map/density?grid_size=${gridSize}`),
  getMapVessels: (params?: { vessel_type?: string; has_events?: boolean }) => {
    const searchParams = new URLSearchParams();
    if (params?.vessel_type && params.vessel_type !== "All") searchParams.set("vessel_type", params.vessel_type);
    if (params?.has_events) searchParams.set("has_events", "true");
    const qs = searchParams.toString();
    return fetchJson<{ type: "FeatureCollection"; features: any[] }>(`/map/vessels${qs ? `?${qs}` : ""}`);
  },
  getMapTrajectories: (limit: number = 50) => fetchJson<{ type: "FeatureCollection"; features: any[] }>(`/map/trajectories?limit=${limit}`),
  getMapZones: () => fetchJson<{ ports: any[]; anchorages: any[]; corridors: any[] }>("/map/zones"),

  // Events
  getEvents: (params?: { category?: string; severity?: string; status?: string; mmsi?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.category && params.category !== "All") searchParams.set("category", params.category);
    if (params?.severity && params.severity !== "All") searchParams.set("severity", params.severity);
    if (params?.status && params.status !== "All") searchParams.set("status", params.status);
    if (params?.mmsi) searchParams.set("mmsi", params.mmsi.toString());
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    const qs = searchParams.toString();
    return fetchJson<BehavioralEvent[]>(`/events${qs ? `?${qs}` : ""}`);
  },
  getEventDetail: (id: string) => fetchJson<BehavioralEvent>(`/events/${id}`),
  updateEvent: (id: string, update: { status?: string; investigation_notes?: string }) =>
    fetchJson<BehavioralEvent>(`/events/${id}`, {
      method: "PATCH",
      body: JSON.stringify(update),
    }),
  triggerDetection: (mmsi?: number) =>
    fetchJson<{ detected_events_count: number }>(`/events/run-detection${mmsi ? `?mmsi=${mmsi}` : ""}`, {
      method: "POST",
    }),

  // Models
  getModels: () => fetchJson<ModelRecord[]>("/models"),
  getModelDetail: (id: string) => fetchJson<ModelRecord>(`/models/${id}`),
  trainModel: (payload: { name: string; model_type: string; epochs: number; batch_size: number; learning_rate: number }) =>
    fetchJson<{ message: string; job_id: string }>("/models/train", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Evaluation
  getEvaluations: () => fetchJson<EvaluationRun[]>("/evaluation"),
  getEvaluationDetail: (id: string) => fetchJson<EvaluationRun>(`/evaluation/${id}`),
  runEvaluation: (payload?: { dataset_name?: string; model_id?: string }) =>
    fetchJson<{ message: string; job_id: string }>(`/evaluation/run?dataset_name=${payload?.dataset_name || "SYNTHETIC_BENCHMARK"}&model_id=${payload?.model_id || "model_tcn_autoencoder_v1"}`, {
      method: "POST",
    }),

  // Datasets
  getDatasets: () => fetchJson<DatasetItem[]>("/datasets"),
  generateSynthetic: () =>
    fetchJson<{ message: string; job_id: string }>("/datasets/generate-synthetic", {
      method: "POST",
    }),

  // Jobs
  getJobs: () => fetchJson<JobRecord[]>("/jobs"),
};
