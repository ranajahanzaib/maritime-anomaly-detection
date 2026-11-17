"use client";

import React from "react";
import {
  Ship,
  Activity,
  AlertTriangle,
  Route,
  Database,
  Radio,
  ExternalLink,
  ShieldAlert,
  Clock,
  Compass,
} from "lucide-react";
import { OverviewStats } from "@/lib/types";

interface OverviewViewProps {
  stats: OverviewStats | null;
  loading: boolean;
  onNavigateTab: (tab: any, selectedItem?: any) => void;
}

export function OverviewView({ stats, loading, onNavigateTab }: OverviewViewProps) {
  if (loading || !stats) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="flex items-center space-x-3 text-slate-400 font-mono text-sm">
          <div className="w-5 h-5 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
          <span>Loading maritime platform intelligence metrics...</span>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      label: "Imported Vessels",
      value: stats.total_vessels.toLocaleString(),
      subtext: "Tracked MMSI entities",
      icon: Ship,
      color: "text-sky-400",
      border: "border-sky-900/50",
      bg: "bg-sky-950/20",
    },
    {
      label: "Total AIS Observations",
      value: stats.total_observations.toLocaleString(),
      subtext: "Validated position pings",
      icon: Activity,
      color: "text-emerald-400",
      border: "border-emerald-900/50",
      bg: "bg-emerald-950/20",
    },
    {
      label: "Analysed Trajectories",
      value: stats.analyzed_trajectories.toLocaleString(),
      subtext: "Segmented voyage tracks",
      icon: Route,
      color: "text-cyan-400",
      border: "border-cyan-900/50",
      bg: "bg-cyan-950/20",
    },
    {
      label: "Behavioural Events",
      value: stats.behavioral_events.toLocaleString(),
      subtext: "Movement deviations flagged",
      icon: AlertTriangle,
      color: "text-amber-400",
      border: "border-amber-900/50",
      bg: "bg-amber-950/20",
    },
    {
      label: "Data Quality Signals",
      value: stats.data_quality_events.toLocaleString(),
      subtext: "Transmission gaps & jumps",
      icon: Radio,
      color: "text-indigo-400",
      border: "border-indigo-900/50",
      bg: "bg-indigo-950/20",
    },
    {
      label: "Active Datasets",
      value: stats.datasets_count.toLocaleString(),
      subtext: "Registered AIS corpora",
      icon: Database,
      color: "text-teal-400",
      border: "border-teal-900/50",
      bg: "bg-teal-950/20",
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto">
      {/* Banner / Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <span>Operational Maritime Intelligence Dashboard</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Spatial-temporal anomaly detection, route corridor deviation analysis, and contextual operational interpretation.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => onNavigateTab("map")}
            className="flex items-center space-x-2 px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition shadow-sm"
          >
            <Compass className="w-4 h-4" />
            <span>Open Interactive Map</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-3.5 rounded bg-slate-900/80 border ${card.border} flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-slate-400">{card.label}</span>
                <Icon className={`w-4 h-4 ${card.color}`} />
              </div>
              <div className="mt-2">
                <div className="text-xl font-bold font-mono text-slate-100">{card.value}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">{card.subtext}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two Columns: Category Breakdown & Severity Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Detection distribution */}
        <div className="lg:col-span-2 p-4 rounded bg-slate-900/70 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Detections by Behavioral Scenario
            </h2>
            <span className="text-[11px] font-mono text-slate-500">
              {stats.total_events_detected} Total Events
            </span>
          </div>

          <div className="space-y-2.5 pt-1">
            {Object.entries(stats.categories_breakdown).map(([cat, count]) => {
              const pct = stats.total_events_detected > 0
                ? Math.round((count / stats.total_events_detected) * 100)
                : 0;
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-medium">
                      {cat.replace(/_/g, " ")}
                    </span>
                    <span className="font-mono text-slate-400 text-[11px]">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        cat === "UNUSUAL_ROUTE_DEVIATION"
                          ? "bg-amber-500"
                          : cat === "RENDEZVOUS"
                          ? "bg-sky-500"
                          : cat === "LOITERING"
                          ? "bg-emerald-500"
                          : cat === "PEER_GROUP_DEVIATION"
                          ? "bg-purple-500"
                          : "bg-indigo-500"
                      }`}
                      style={{ width: `${Math.max(4, pct)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Severity & Contextual interpretation */}
        <div className="p-4 rounded bg-slate-900/70 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <div className="border-b border-slate-800 pb-2.5">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Severity Tiers
              </h2>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-3">
              {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sev) => {
                const count = stats.severity_breakdown[sev] || 0;
                return (
                  <div
                    key={sev}
                    className="p-2.5 rounded bg-slate-950 border border-slate-800/80 text-center"
                  >
                    <div
                      className={`text-[10px] font-bold uppercase tracking-wider ${
                        sev === "CRITICAL"
                          ? "text-rose-400"
                          : sev === "HIGH"
                          ? "text-amber-400"
                          : sev === "MEDIUM"
                          ? "text-sky-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {sev}
                    </div>
                    <div className="text-lg font-bold font-mono text-slate-200 mt-1">
                      {count}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-3 rounded bg-sky-950/20 border border-sky-900/40 text-[11px] text-slate-400 leading-relaxed font-mono">
            <div className="flex items-center space-x-1.5 text-sky-400 font-semibold mb-1">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Contextual Intelligence Layer</span>
            </div>
            Stationary and low-speed movements inside recognized anchorages or port zones are explicitly tagged as <span className="text-emerald-400">EXPECTED_CONTEXT</span> to avoid false alert congestion.
          </div>
        </div>
      </div>

      {/* Recent Behavioral Events Table */}
      <div className="p-4 rounded bg-slate-900/70 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Recent Detected Behavioural Deviations
            </h2>
          </div>
          <button
            onClick={() => onNavigateTab("events")}
            className="text-xs text-sky-400 hover:text-sky-300 flex items-center space-x-1"
          >
            <span>View All Investigations</span>
            <ExternalLink className="w-3 h-3" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 font-mono text-[11px]">
                <th className="py-2 px-3">Scenario</th>
                <th className="py-2 px-3">Primary Vessel</th>
                <th className="py-2 px-3">Deviation Score</th>
                <th className="py-2 px-3">Severity</th>
                <th className="py-2 px-3">Context State</th>
                <th className="py-2 px-3">Observed Evidence</th>
                <th className="py-2 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {stats.recent_events.map((evt) => (
                <tr key={evt.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-sans font-medium text-slate-200">
                    {evt.category.replace(/_/g, " ")}
                  </td>
                  <td className="py-2.5 px-3 text-sky-400">
                    MMSI {evt.primary_mmsi}
                    {evt.secondary_mmsi && (
                      <span className="text-slate-500"> ↔ {evt.secondary_mmsi}</span>
                    )}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px]">
                      {evt.deviation_score.toFixed(2)}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        evt.severity === "CRITICAL"
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : evt.severity === "HIGH"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : evt.severity === "MEDIUM"
                          ? "bg-sky-950 text-sky-300 border border-sky-800"
                          : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      }`}
                    >
                      {evt.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`text-[11px] ${
                        evt.contextual_state === "EXPECTED_CONTEXT"
                          ? "text-emerald-400"
                          : "text-amber-400"
                      }`}
                    >
                      {evt.contextual_state}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-sans text-slate-400 text-[11px] max-w-md truncate">
                    {evt.explanation}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => onNavigateTab("events", evt)}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] transition"
                    >
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
