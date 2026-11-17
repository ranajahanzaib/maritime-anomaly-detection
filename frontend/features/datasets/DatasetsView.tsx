"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  RotateCw,
  Play,
  FileCheck,
  AlertCircle,
  Clock,
  Sparkles,
  ShieldCheck,
  Radio,
} from "lucide-react";
import { DatasetItem, JobRecord } from "@/lib/types";
import { api } from "@/lib/api";

export function DatasetsView() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");

  useEffect(() => {
    loadDatasetsAndJobs();
  }, []);

  const loadDatasetsAndJobs = async () => {
    setLoading(true);
    try {
      const [dList, jList] = await Promise.all([api.getDatasets(), api.getJobs()]);
      setDatasets(dList);
      setJobs(jList);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSynthetic = async () => {
    setGenerating(true);
    setStatusMessage("Submitting deterministic synthetic generation job...");
    try {
      const res = await api.generateSynthetic();
      setStatusMessage(`Job ${res.job_id} submitted to background worker.`);
      // Poll a few times
      setTimeout(async () => {
        await loadDatasetsAndJobs();
        setGenerating(false);
        setStatusMessage("Synthetic demonstration dataset ready!");
        setTimeout(() => setStatusMessage(""), 5000);
      }, 5000);
    } catch (e: any) {
      console.error(e);
      setStatusMessage(`Error: ${e.message}`);
      setGenerating(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <Database className="w-5 h-5 text-sky-400" />
            <span>Dataset Management & Ingestion Pipelines</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Registered AIS sources, adapters (NOAA, Danish AIS, HawaiiCoast_GT), columnar Parquet stores, and data quality audits.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadDatasetsAndJobs}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs font-mono transition"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            disabled={generating}
            onClick={handleGenerateSynthetic}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white text-xs font-medium transition shadow-sm font-mono"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{generating ? "Generating Demo Data..." : "Regenerate Demo Dataset"}</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 rounded bg-sky-950/40 border border-sky-800 text-xs font-mono text-sky-300 flex items-center space-x-2">
          <Radio className="w-4 h-4 animate-pulse" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Dataset Registry Table */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Registered Datasets ({datasets.length})
          </h2>
          <span className="text-[11px] text-slate-500">Columnar Parquet Backed</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 text-[11px]">
                <th className="py-2.5 px-3">Dataset Name</th>
                <th className="py-2.5 px-3">Source Type</th>
                <th className="py-2.5 px-3">Storage Format</th>
                <th className="py-2.5 px-3">Rows</th>
                <th className="py-2.5 px-3">Vessels</th>
                <th className="py-2.5 px-3">Quality Score</th>
                <th className="py-2.5 px-3">Time Range</th>
                <th className="py-2.5 px-3">Mode</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {datasets.map((d) => (
                <tr key={d.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-3 font-bold text-slate-100">{d.name}</td>
                  <td className="py-2.5 px-3 text-sky-400">{d.source_type}</td>
                  <td className="py-2.5 px-3 text-slate-400">{d.format}</td>
                  <td className="py-2.5 px-3 text-slate-200">{d.row_count.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-slate-200">{d.vessel_count}</td>
                  <td className="py-2.5 px-3">
                    <span className="text-emerald-400 font-bold">
                      {(d.quality_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                    {d.time_range_start ? `${d.time_range_start.substring(0, 10)} → ${d.time_range_end?.substring(0, 10)}` : "—"}
                  </td>
                  <td className="py-2.5 px-3">
                    {d.is_synthetic ? (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-sky-950 text-sky-300 border border-sky-800">
                        Synthetic Demo
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                        External Real
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Supported Adapters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
          <div className="flex items-center space-x-1.5 font-bold text-sky-400">
            <ShieldCheck className="w-4 h-4" />
            <span>NOAA MarineCadastre AIS</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Parses US Coast Guard MarineCadastre CSV & GeoParquet archives, normalizes vessel dimensions, coordinates, SOG, COG, and UTC timestamps.
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
          <div className="flex items-center space-x-1.5 font-bold text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
            <span>HawaiiCoast_GT (Zenodo 8253611)</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Ingests Hawaiian archipelago trajectory benchmark and ground-truth maritime incident annotations under CC-BY 4.0 license.
          </p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
          <div className="flex items-center space-x-1.5 font-bold text-purple-400">
            <ShieldCheck className="w-4 h-4" />
            <span>Danish AIS Trajectories</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Supports Danish Maritime Authority (DMA) trajectory data with abnormal vessel behaviour annotations in the Great Belt and Kattegat.
          </p>
        </div>
      </div>

      {/* Background Ingestion & Processing Worker Queue */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Background Processing Tasks ({jobs.length})
          </h2>
          <span className="text-[11px] text-slate-500">Dedicated Asynchronous Worker</span>
        </div>

        {jobs.length === 0 ? (
          <div className="py-6 text-center text-slate-500">
            No background jobs executed yet.
          </div>
        ) : (
          <div className="space-y-2">
            {jobs.map((j) => (
              <div key={j.id} className="p-2.5 rounded bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center space-x-2">
                    <span className="text-sky-400 font-bold">{j.job_type}</span>
                    <span className="text-slate-500">·</span>
                    <span className="text-slate-300">{j.id}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {j.log_messages && j.log_messages[j.log_messages.length - 1]}
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      j.status === "COMPLETED"
                        ? "bg-emerald-950 text-emerald-300"
                        : j.status === "RUNNING"
                        ? "bg-sky-950 text-sky-300 animate-pulse"
                        : "bg-slate-900 text-slate-400"
                    }`}
                  >
                    {j.status}
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
