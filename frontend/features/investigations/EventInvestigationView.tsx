"use client";

import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Compass,
  FileText,
  Activity,
  Route,
  Anchor,
  Radio,
  Save,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { BehavioralEvent } from "@/lib/types";
import { api } from "@/lib/api";

interface EventInvestigationViewProps {
  initialEventId?: string;
  onSelectVessel: (mmsi: number) => void;
}

export function EventInvestigationView({
  initialEventId,
  onSelectVessel,
}: EventInvestigationViewProps) {
  const [events, setEvents] = useState<BehavioralEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<BehavioralEvent | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterCategory, setFilterCategory] = useState<string>("All");
  const [filterSeverity, setFilterSeverity] = useState<string>("All");
  const [filterStatus, setFilterStatus] = useState<string>("All");

  // Investigation form state
  const [notes, setNotes] = useState<string>("");
  const [statusVal, setStatusVal] = useState<string>("NEW");
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    loadEvents();
  }, [filterCategory, filterSeverity, filterStatus]);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents({
        category: filterCategory,
        severity: filterSeverity,
        status: filterStatus,
        limit: 100,
      });
      setEvents(data);
      if (initialEventId) {
        const found = data.find((e) => e.id === initialEventId);
        if (found) {
          selectEvent(found);
        } else if (data.length > 0) {
          selectEvent(data[0]);
        }
      } else if (data.length > 0 && !selectedEvent) {
        selectEvent(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const selectEvent = (evt: BehavioralEvent) => {
    setSelectedEvent(evt);
    setNotes(evt.investigation_notes || "");
    setStatusVal(evt.status || "NEW");
    setSaveSuccess(false);
  };

  const handleSaveInvestigation = async () => {
    if (!selectedEvent) return;
    try {
      const updated = await api.updateEvent(selectedEvent.id, {
        status: statusVal,
        investigation_notes: notes,
      });
      setSelectedEvent(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      // Update in local list
      setEvents((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col md:flex-row overflow-hidden bg-slate-950">
      {/* Left List Pane */}
      <div className="w-full md:w-96 border-r border-slate-800 flex flex-col justify-between shrink-0 bg-slate-950/70">
        <div className="p-3.5 border-b border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200 flex items-center space-x-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Event Registry</span>
            </h2>
            <span className="text-[11px] font-mono text-slate-500">
              {events.length} Detections
            </span>
          </div>

          {/* Filter selectors */}
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-300 focus:outline-none"
            >
              <option value="All">All Scenarios</option>
              <option value="UNUSUAL_ROUTE_DEVIATION">Route Deviation</option>
              <option value="RENDEZVOUS">Rendezvous</option>
              <option value="LOITERING">Loitering</option>
              <option value="PEER_GROUP_DEVIATION">Peer Deviation</option>
              <option value="HISTORICAL_INCONSISTENCY">Historical Inconsistency</option>
              <option value="AIS_TRANSMISSION_GAP">AIS Gap</option>
              <option value="IMPLAUSIBLE_MOVEMENT">Implausible Jump</option>
            </select>

            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-300 focus:outline-none"
            >
              <option value="All">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        {/* Scrollable Event Cards */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 font-mono">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500">
              Loading events...
            </div>
          ) : events.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No events found matching filters.
            </div>
          ) : (
            events.map((evt) => {
              const isSelected = selectedEvent?.id === evt.id;
              return (
                <div
                  key={evt.id}
                  onClick={() => selectEvent(evt)}
                  className={`p-3 cursor-pointer transition flex flex-col space-y-1.5 ${
                    isSelected
                      ? "bg-sky-950/40 border-l-2 border-sky-400"
                      : "hover:bg-slate-900/60 border-l-2 border-transparent"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-sans font-semibold text-slate-200">
                      {evt.category.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                        evt.severity === "CRITICAL"
                          ? "bg-rose-950 text-rose-300"
                          : evt.severity === "HIGH"
                          ? "bg-amber-950 text-amber-300"
                          : "bg-sky-950 text-sky-300"
                      }`}
                    >
                      {evt.severity}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="text-sky-400">MMSI {evt.primary_mmsi}</span>
                    <span>Score: {evt.deviation_score.toFixed(2)}</span>
                  </div>

                  <div className="text-[10px] text-slate-500 truncate font-sans">
                    {evt.explanation}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Detail & Evidence Inspector Workspace */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {selectedEvent ? (
          <div className="space-y-6 max-w-4xl mx-auto">
            {/* Event Header Card */}
            <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <h1 className="text-lg font-bold font-sans text-slate-100">
                      {selectedEvent.category.replace(/_/g, " ")}
                    </h1>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                        selectedEvent.severity === "CRITICAL"
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : selectedEvent.severity === "HIGH"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-sky-950 text-sky-300 border border-sky-800"
                      }`}
                    >
                      {selectedEvent.severity}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-slate-300">
                      Deviation: {selectedEvent.deviation_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-slate-400 mt-1 flex items-center space-x-3">
                    <span>
                      Detector: <span className="text-slate-200">{selectedEvent.detector_id} (v{selectedEvent.detector_version})</span>
                    </span>
                    <span>·</span>
                    <span>Confidence: {(selectedEvent.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onSelectVessel(selectedEvent.primary_mmsi)}
                    className="px-3 py-1.5 rounded bg-sky-950 border border-sky-800 hover:bg-sky-900 text-sky-300 text-xs font-mono transition"
                  >
                    View Vessel {selectedEvent.primary_mmsi} →
                  </button>
                  {selectedEvent.secondary_mmsi && (
                    <button
                      onClick={() => onSelectVessel(selectedEvent.secondary_mmsi!)}
                      className="px-3 py-1.5 rounded bg-sky-950 border border-sky-800 hover:bg-sky-900 text-sky-300 text-xs font-mono transition"
                    >
                      View Partner {selectedEvent.secondary_mmsi} →
                    </button>
                  )}
                </div>
              </div>

              {/* Explanation Text */}
              <div className="text-xs text-slate-300 font-sans leading-relaxed">
                {selectedEvent.explanation}
              </div>

              {/* Contextual Intelligence Banner */}
              <div
                className={`p-3 rounded border text-xs font-mono space-y-1 ${
                  selectedEvent.contextual_state === "EXPECTED_CONTEXT"
                    ? "bg-emerald-950/20 border-emerald-900/40 text-emerald-300"
                    : "bg-amber-950/20 border-amber-900/40 text-amber-300"
                }`}
              >
                <div className="flex items-center space-x-1.5 font-bold">
                  <Anchor className="w-3.5 h-3.5" />
                  <span>Context State: {selectedEvent.contextual_state}</span>
                </div>
                <div className="text-[11px] font-sans text-slate-300">
                  {selectedEvent.contextual_explanation || "No contextual reference layer mapped."}
                </div>
              </div>
            </div>

            {/* Feature Attributions Grid */}
            {selectedEvent.feature_attributions && (
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
                  Quantitative Feature Attributions
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-1 font-mono text-xs">
                  {Object.entries(selectedEvent.feature_attributions).map(([k, v]) => (
                    <div key={k} className="p-2 rounded bg-slate-950 border border-slate-800/60">
                      <span className="text-[10px] text-slate-500 block truncate">{k}</span>
                      <span className="text-slate-200 font-bold">
                        {typeof v === "boolean" ? (v ? "True" : "False") : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Scenario-Specific Evidence Visualizations */}

            {/* 1. Rendezvous Pairwise Distance Timeline */}
            {selectedEvent.category === "RENDEZVOUS" &&
              selectedEvent.evidence?.interaction_timeline && (
                <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center space-x-2">
                      <Activity className="w-4 h-4 text-sky-400" />
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                        Pairwise Proximity & Relative Speed Over Time
                      </h3>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500">
                      Distance (m) vs Time
                    </span>
                  </div>

                  <div className="h-56 w-full pt-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={selectedEvent.evidence.interaction_timeline}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis
                          dataKey="timestamp"
                          stroke="#64748b"
                          tick={{ fontSize: 9, fill: "#64748b" }}
                          tickFormatter={(t) => t.substring(11, 16)}
                        />
                        <YAxis
                          stroke="#38bdf8"
                          tick={{ fontSize: 10, fill: "#38bdf8" }}
                          domain={[0, "auto"]}
                          unit="m"
                        />
                        <Tooltip
                          contentStyle={{ backgroundColor: "#0b111a", borderColor: "#1e293b", fontSize: 11, fontFamily: "monospace" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="distance_meters"
                          stroke="#f43f5e"
                          strokeWidth={2}
                          dot={{ r: 2 }}
                          name="Inter-vessel Distance (m)"
                        />
                        <Line
                          type="monotone"
                          dataKey="relative_speed"
                          stroke="#38bdf8"
                          strokeWidth={1.5}
                          dot={false}
                          name="Relative Speed (kts)"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

            {/* 2. Route Corridor Deviation Evidence */}
            {selectedEvent.category === "UNUSUAL_ROUTE_DEVIATION" &&
              selectedEvent.evidence?.expected_corridor_waypoints && (
                <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
                  <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                    <Route className="w-4 h-4 text-amber-400" />
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
                      Route Corridor Conformance Evidence
                    </h3>
                  </div>
                  <div className="space-y-2 text-slate-300">
                    <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase">
                        Expected Fairway Centerline Waypoints
                      </span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {selectedEvent.evidence.expected_corridor_waypoints.map((wp, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px] text-sky-400">
                            WP{i + 1}: {wp.lat.toFixed(2)}°N, {wp.lon.toFixed(2)}°E
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

            {/* 3. AIS Transmission Gap Observability Evidence */}
            {selectedEvent.category === "AIS_TRANSMISSION_GAP" && (
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 font-mono text-xs">
                <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                  <Radio className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
                    Transmission Gap Observability Evidence
                  </h3>
                </div>
                <div className="grid grid-cols-2 gap-3 text-slate-300">
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Last Reported Position</span>
                    <span className="text-sky-400 font-bold">
                      {selectedEvent.latitude.toFixed(4)}°N, {selectedEvent.longitude.toFixed(4)}°E
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Silence Duration</span>
                    <span className="text-amber-400 font-bold">
                      {(selectedEvent.duration_seconds / 3600).toFixed(1)} Hours
                    </span>
                  </div>
                </div>
                {selectedEvent.data_quality_warnings && (
                  <div className="mt-2 p-2 rounded bg-indigo-950/20 border border-indigo-900/40 text-[11px] text-indigo-300">
                    {selectedEvent.data_quality_warnings.map((w, i) => (
                      <div key={i}>• {w}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Investigation Status & Analyst Notes Form */}
            <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
                    Investigation Status & Case Notes
                  </h3>
                </div>
                {saveSuccess && (
                  <span className="text-emerald-400 flex items-center space-x-1 text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Saved</span>
                  </span>
                )}
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-4">
                  <span className="text-slate-400">Review Status:</span>
                  <div className="flex items-center space-x-2">
                    {["NEW", "UNDER_INVESTIGATION", "RESOLVED", "FALSE_POSITIVE"].map((st) => (
                      <button
                        key={st}
                        onClick={() => setStatusVal(st)}
                        className={`px-2.5 py-1 rounded text-[11px] font-bold transition ${
                          statusVal === st
                            ? "bg-sky-600 text-white"
                            : "bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {st.replace(/_/g, " ")}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400 block">Analyst Assessment Notes:</label>
                  <textarea
                    rows={3}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Document operational context, port authority communications, pilot confirmation, or meteorological rationale..."
                    className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-sans"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleSaveInvestigation}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Investigation Case</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-xs font-mono text-slate-500">
            Select an event from the registry to inspect evidence and begin investigation.
          </div>
        )}
      </div>
    </div>
  );
}
