"use client";

import React, { useState, useEffect } from "react";
import {
  Ship,
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  Compass,
} from "lucide-react";
import { Vessel } from "@/lib/types";
import { api } from "@/lib/api";

interface VesselExplorerViewProps {
  onSelectVessel: (mmsi: number) => void;
}

export function VesselExplorerView({ onSelectVessel }: VesselExplorerViewProps) {
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedType, setSelectedType] = useState<string>("All");
  const [filterEventsOnly, setFilterEventsOnly] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<"event_count" | "distance" | "observations">("event_count");

  useEffect(() => {
    loadVessels();
  }, [selectedType, filterEventsOnly]);

  const loadVessels = async () => {
    setLoading(true);
    try {
      const data = await api.getVessels({
        vessel_type: selectedType,
        has_events: filterEventsOnly ? true : undefined,
        limit: 100,
      });
      setVessels(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filteredVessels = vessels
    .filter((v) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        v.mmsi.toString().includes(q) ||
        (v.name && v.name.toLowerCase().includes(q)) ||
        (v.flag && v.flag.toLowerCase().includes(q))
      );
    })
    .sort((a, b) => {
      if (sortBy === "event_count") return b.event_count - a.event_count;
      if (sortBy === "distance") return b.total_distance_nm - a.total_distance_nm;
      if (sortBy === "observations") return b.observation_count - a.observation_count;
      return 0;
    });

  return (
    <div className="p-6 space-y-5 max-w-7xl mx-auto overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <Ship className="w-5 h-5 text-sky-400" />
            <span>Vessel Explorer</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Global maritime registry of tracked vessels, kinematic profiles, observed deviations, and telemetry quality.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <span>Showing {filteredVessels.length} vessels</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
        {/* Search Input */}
        <div className="relative md:col-span-2">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by MMSI, vessel name, or flag..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 pl-9 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 font-mono"
          />
        </div>

        {/* Vessel Type Select */}
        <div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
          >
            <option value="All">All Types</option>
            <option value="Cargo">Cargo</option>
            <option value="Tanker">Tanker</option>
            <option value="Fishing">Fishing</option>
            <option value="Passenger">Passenger</option>
            <option value="Tug">Tug</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* Toggle Events Only & Sort */}
        <div className="flex items-center justify-between space-x-2">
          <label className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={filterEventsOnly}
              onChange={(e) => setFilterEventsOnly(e.target.checked)}
              className="rounded bg-slate-950 border-slate-700 text-sky-500 focus:ring-0"
            />
            <span className="font-mono text-[11px]">With Events Only</span>
          </label>

          <select
            value={sortBy}
            onChange={(e: any) => setSortBy(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-xs text-slate-300 font-mono"
          >
            <option value="event_count">Sort: Events</option>
            <option value="distance">Sort: Distance</option>
            <option value="observations">Sort: Observations</option>
          </select>
        </div>
      </div>

      {/* Vessel Directory Table */}
      <div className="rounded-lg bg-slate-900/70 border border-slate-800 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-slate-400">
            Loading vessel database...
          </div>
        ) : filteredVessels.length === 0 ? (
          <div className="p-12 text-center text-xs font-mono text-slate-500">
            No vessels match the specified filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 font-mono text-[11px] bg-slate-950/40">
                  <th className="py-2.5 px-3">MMSI</th>
                  <th className="py-2.5 px-3">Vessel Name</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Flag</th>
                  <th className="py-2.5 px-3">Speed (Avg / Max)</th>
                  <th className="py-2.5 px-3">Total Distance</th>
                  <th className="py-2.5 px-3">Observations</th>
                  <th className="py-2.5 px-3">Data Quality</th>
                  <th className="py-2.5 px-3">Events</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredVessels.map((v) => (
                  <tr
                    key={v.mmsi}
                    onClick={() => onSelectVessel(v.mmsi)}
                    className="hover:bg-slate-800/40 cursor-pointer transition"
                  >
                    <td className="py-2.5 px-3 text-sky-400 font-bold">{v.mmsi}</td>
                    <td className="py-2.5 px-3 font-sans font-medium text-slate-200">
                      {v.name || "—"}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                        {v.vessel_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{v.flag || "—"}</td>
                    <td className="py-2.5 px-3 text-slate-300">
                      {v.avg_speed_knots.toFixed(1)} / {v.max_speed_knots.toFixed(1)} kts
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      {v.total_distance_nm.toFixed(1)} nm
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{v.observation_count}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`text-[11px] ${
                          v.data_quality_score >= 0.95
                            ? "text-emerald-400"
                            : v.data_quality_score >= 0.8
                            ? "text-sky-400"
                            : "text-amber-400"
                        }`}
                      >
                        {(v.data_quality_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      {v.event_count > 0 ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
                          {v.event_count} {v.event_count === 1 ? "Event" : "Events"}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectVessel(v.mmsi);
                        }}
                        className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 text-[11px] transition inline-flex items-center space-x-1"
                      >
                        <span>Profile</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
