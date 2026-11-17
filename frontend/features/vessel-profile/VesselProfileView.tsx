"use client";

import React, { useState, useEffect } from "react";
import {
  Ship,
  ArrowLeft,
  Activity,
  Compass,
  AlertTriangle,
  Route,
  Radio,
  Clock,
  ShieldCheck,
  TrendingUp,
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
import { Vessel, TrajectorySegment, BehavioralEvent } from "@/lib/types";
import { api } from "@/lib/api";

interface VesselProfileViewProps {
  mmsi: number;
  onBack: () => void;
  onSelectEvent: (eventId: string) => void;
}

export function VesselProfileView({ mmsi, onBack, onSelectEvent }: VesselProfileViewProps) {
  const [vessel, setVessel] = useState<Vessel | null>(null);
  const [trajectories, setTrajectories] = useState<TrajectorySegment[]>([]);
  const [events, setEvents] = useState<BehavioralEvent[]>([]);
  const [historyPoints, setHistoryPoints] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadVesselData();
  }, [mmsi]);

  const loadVesselData = async () => {
    setLoading(true);
    try {
      const [vData, tData, eData, hData] = await Promise.all([
        api.getVesselDetail(mmsi),
        api.getVesselTrajectories(mmsi),
        api.getVesselEvents(mmsi),
        api.getVesselHistory(mmsi, 500),
      ]);
      setVessel(vData);
      setTrajectories(tData);
      setEvents(eData);
      setHistoryPoints(hData.points || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !vessel) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="flex items-center space-x-3 text-slate-400 font-mono text-sm">
          <div className="w-5 h-5 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
          <span>Loading vessel profile for MMSI {mmsi}...</span>
        </div>
      </div>
    );
  }

  // Prepare chart series from history points
  const chartData = historyPoints.map((pt, i) => ({
    time: pt.timestamp ? new Date(pt.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : `#${i}`,
    sog: pt.sog,
    cog: pt.cog,
  }));

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto">
      {/* Navigation & Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-100 font-mono">
                {vessel.name || `MMSI ${vessel.mmsi}`}
              </h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-sky-950 text-sky-300 border border-sky-800">
                {vessel.vessel_type}
              </span>
              {vessel.flag && (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-900 text-slate-400 border border-slate-800">
                  {vessel.flag}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              MMSI: {vessel.mmsi} · IMO: {vessel.imo || "N/A"} · Last Seen:{" "}
              {vessel.last_seen ? new Date(vessel.last_seen).toUTCString() : "Unknown"}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {events.length > 0 && (
            <span className="px-2.5 py-1 rounded bg-amber-950 text-amber-300 border border-amber-800 text-xs font-mono font-bold flex items-center space-x-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{events.length} Active Deviations</span>
            </span>
          )}
        </div>
      </div>

      {/* Identity & Historical Baseline Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Speed Regime</span>
          <div className="text-lg font-bold font-mono text-slate-200 mt-1">
            {vessel.avg_speed_knots.toFixed(1)} <span className="text-xs text-slate-500 font-normal">avg</span> /{" "}
            {vessel.max_speed_knots.toFixed(1)} <span className="text-xs text-slate-500 font-normal">max kts</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-1">Observed kinematics</div>
        </div>

        <div className="p-3.5 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Total Distance</span>
          <div className="text-lg font-bold font-mono text-slate-200 mt-1">
            {vessel.total_distance_nm.toFixed(1)} <span className="text-xs text-slate-500 font-normal">NM</span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-1">Across {vessel.segment_count} trajectory segments</div>
        </div>

        <div className="p-3.5 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Telemetry Quality</span>
          <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
            {(vessel.data_quality_score * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-1">Plausibility & completeness</div>
        </div>

        <div className="p-3.5 rounded bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Observations</span>
          <div className="text-lg font-bold font-mono text-sky-400 mt-1">
            {vessel.observation_count}
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-1">Normalized AIS messages</div>
        </div>
      </div>

      {/* Speed & Course Kinematics Timeline Chart */}
      <div className="p-4 rounded bg-slate-900/70 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-sky-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Movement Kinematics (Speed & Course Over Time)
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-500">
            {chartData.length} Time Steps
          </span>
        </div>

        {chartData.length > 0 ? (
          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis yAxisId="left" stroke="#38bdf8" tick={{ fontSize: 10, fill: "#38bdf8" }} domain={[0, "auto"]} />
                <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" tick={{ fontSize: 10, fill: "#f59e0b" }} domain={[0, 360]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0b111a", borderColor: "#1e293b", fontSize: 11, fontFamily: "monospace" }}
                />
                <Line yAxisId="left" type="monotone" dataKey="sog" stroke="#38bdf8" strokeWidth={2} dot={false} name="Speed (SOG kts)" />
                <Line yAxisId="right" type="monotone" dataKey="cog" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="Course (COG °)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="py-8 text-center text-xs font-mono text-slate-500">
            No kinematics timeline available.
          </div>
        )}
      </div>

      {/* Historical Baseline vs Fleet Peer Comparison */}
      <div className="p-4 rounded bg-slate-900/70 border border-slate-800 space-y-3">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-2.5">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Learned Historical Baseline vs Fleet Peer Group
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-3 rounded bg-slate-950 border border-slate-800/80 space-y-2">
            <span className="text-sky-400 font-bold block uppercase text-[11px]">
              Vessel Historical Profile
            </span>
            {vessel.historical_profile ? (
              <div className="space-y-1.5 text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-500">Typical Speed:</span>
                  <span>{vessel.historical_profile.avg_speed_knots || vessel.avg_speed_knots.toFixed(1)} kts</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Max Historical Speed:</span>
                  <span>{vessel.historical_profile.max_speed_knots || vessel.max_speed_knots.toFixed(1)} kts</span>
                </div>
                {vessel.historical_profile.center_lat && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Home Region:</span>
                    <span>{vessel.historical_profile.center_lat.toFixed(2)}°N, {vessel.historical_profile.center_lon.toFixed(2)}°E</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-slate-500">Confidence:</span>
                  <span className="text-emerald-400">Established ({vessel.historical_profile.observation_count || vessel.observation_count} obs)</span>
                </div>
              </div>
            ) : (
              <div className="text-slate-500 italic">
                Insufficient history to synthesize distinct vessel baseline profile. Fleet peer group used.
              </div>
            )}
          </div>

          <div className="p-3 rounded bg-slate-950 border border-slate-800/80 space-y-2">
            <span className="text-amber-400 font-bold block uppercase text-[11px]">
              {vessel.vessel_type} Fleet Baseline
            </span>
            <div className="space-y-1.5 text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Peer Mean Speed:</span>
                <span>
                  {vessel.vessel_type === "Cargo" ? "13.5 ± 2.8 kts" :
                   vessel.vessel_type === "Tanker" ? "12.0 ± 2.5 kts" :
                   vessel.vessel_type === "Fishing" ? "4.5 ± 3.0 kts" : "10.0 ± 4.0 kts"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Speed Z-Score:</span>
                <span className={Math.abs(vessel.avg_speed_knots - 13.5) / 2.8 > 2.5 ? "text-amber-400 font-bold" : "text-emerald-400"}>
                  {((vessel.avg_speed_knots - 13.5) / 2.8).toFixed(2)} σ
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Corridor Conformance:</span>
                <span className="text-slate-300">Monitored</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detected Events on this Vessel */}
      <div className="p-4 rounded bg-slate-900/70 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Detected Events & Deviations ({events.length})
            </h2>
          </div>
        </div>

        {events.length === 0 ? (
          <div className="py-8 text-center text-xs font-mono text-slate-500">
            No behavioural deviations or data quality anomalies detected for this vessel.
          </div>
        ) : (
          <div className="space-y-2 font-mono text-xs">
            {events.map((evt) => (
              <div
                key={evt.id}
                onClick={() => onSelectEvent(evt.id)}
                className="p-3 rounded bg-slate-950 border border-slate-800/80 hover:border-sky-800 transition cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-2"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-200">{evt.category.replace(/_/g, " ")}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        evt.severity === "CRITICAL"
                          ? "bg-rose-950 text-rose-300"
                          : evt.severity === "HIGH"
                          ? "bg-amber-950 text-amber-300"
                          : "bg-sky-950 text-sky-300"
                      }`}
                    >
                      {evt.severity}
                    </span>
                    <span className="text-slate-500 text-[11px]">
                      Score: {evt.deviation_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 font-sans max-w-2xl">
                    {evt.explanation}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-sky-400 hover:text-sky-300 text-[11px] underline">
                    Investigate Evidence →
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
