"use client";

import React, { useState } from "react";
import {
  Settings,
  Server,
  Database,
  Download,
  Sliders,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

export function SettingsView() {
  const [apiUrl, setApiUrl] = useState<string>("http://127.0.0.1:8000/api/v1");
  const [maxGap, setMaxGap] = useState<number>(45);
  const [saved, setSaved] = useState<boolean>(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleExport = (format: string) => {
    window.open(`http://127.0.0.1:8000/api/v1/export/events?format=${format}`, "_blank");
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto overflow-y-auto font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center space-x-2 font-sans">
            <Settings className="w-5 h-5 text-sky-400" />
            <span>Platform Configuration & Data Export</span>
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-1">
            System thresholds, data export interfaces, and operational environment settings.
          </p>
        </div>
        {saved && (
          <span className="text-emerald-400 flex items-center space-x-1.5 font-bold">
            <CheckCircle2 className="w-4 h-4" />
            <span>Saved</span>
          </span>
        )}
      </div>

      {/* Export & Reproducibility Section (Section 12) */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
          <Download className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Data Export & Investigation Reproducibility
          </h2>
        </div>
        <p className="text-slate-400 font-sans text-xs">
          Export full behavioural events, quantitative evidence, and trajectory observations for external GIS systems, intelligence reporting, or academic evaluation.
        </p>

        <div className="flex flex-wrap gap-2.5 pt-1">
          <button
            onClick={() => handleExport("json")}
            className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800 hover:border-sky-500 text-sky-300 transition"
          >
            Export Events (JSON)
          </button>
          <button
            onClick={() => handleExport("geojson")}
            className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800 hover:border-emerald-500 text-emerald-300 transition"
          >
            Export Spatial Events (GeoJSON)
          </button>
          <button
            onClick={() => handleExport("csv")}
            className="px-3 py-1.5 rounded bg-slate-950 border border-slate-800 hover:border-amber-500 text-amber-300 transition"
          >
            Export Table (CSV)
          </button>
        </div>
      </div>

      {/* Processing Parameters */}
      <form onSubmit={handleSave} className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
          <Sliders className="w-4 h-4 text-sky-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Processing & Trajectory Segmentation Thresholds
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-slate-300">
          <div>
            <label className="text-slate-500 block text-[10px] uppercase">
              Max Trajectory Time-Gap (Minutes)
            </label>
            <input
              type="number"
              value={maxGap}
              onChange={(e) => setMaxGap(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 mt-1"
            />
            <span className="text-[10px] text-slate-500 mt-0.5 block">
              Gaps exceeding this threshold create separate observed segments.
            </span>
          </div>

          <div>
            <label className="text-slate-500 block text-[10px] uppercase">
              Backend API Base URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 mt-1"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="px-4 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-medium transition"
          >
            Save Parameters
          </button>
        </div>
      </form>

      {/* System Infrastructure Card */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-slate-400">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
          <Server className="w-4 h-4 text-indigo-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Infrastructure & Runtime Stack
          </h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 pt-1 text-[11px]">
          <div>• Python 3.13 / FastAPI</div>
          <div>• Polars & DuckDB Analytics</div>
          <div>• PyTorch TCN Autoencoder</div>
          <div>• PostGIS / SQLite Dual Mode</div>
          <div>• Next.js 15 & MapLibre GL</div>
          <div>• Asynchronous Task Queue</div>
        </div>
      </div>
    </div>
  );
}
