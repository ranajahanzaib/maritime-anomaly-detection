"use client";

import React from "react";
import {
  Compass,
  Ship,
  Map as MapIcon,
  AlertTriangle,
  Cpu,
  Database,
  Settings as SettingsIcon,
  ShieldCheck,
  Radio,
} from "lucide-react";

export type NavTab =
  | "overview"
  | "map"
  | "vessels"
  | "events"
  | "models"
  | "datasets"
  | "settings";

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  eventCount?: number;
}

export function Sidebar({ activeTab, setActiveTab, eventCount = 0 }: SidebarProps) {
  const navItems = [
    { id: "overview" as NavTab, label: "Overview", icon: Compass },
    { id: "map" as NavTab, label: "Maritime Map", icon: MapIcon },
    { id: "vessels" as NavTab, label: "Vessel Explorer", icon: Ship },
    {
      id: "events" as NavTab,
      label: "Behavioural Events",
      icon: AlertTriangle,
      badge: eventCount > 0 ? eventCount : undefined,
    },
    { id: "models" as NavTab, label: "Model Laboratory", icon: Cpu },
    { id: "datasets" as NavTab, label: "Datasets", icon: Database },
    { id: "settings" as NavTab, label: "Settings", icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between select-none shrink-0 z-20">
      <div>
        {/* Brand header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative flex items-center justify-center w-8 h-8 rounded bg-sky-950 border border-sky-800/80 text-sky-400">
              <Compass className="w-5 h-5 animate-spin-slow" />
              <div className="absolute w-2 h-2 rounded-full bg-sky-400 radar-ping" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wider text-slate-100 uppercase">
                Vessel Behavior
              </div>
              <div className="text-[10px] font-mono text-sky-400/80 uppercase tracking-widest">
                Intelligence Platform
              </div>
            </div>
          </div>
        </div>

        {/* Live Status indicator */}
        <div className="px-4 py-2.5 bg-slate-900/60 border-b border-slate-800/60 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-slate-400 font-mono text-[11px]">System Online</span>
          </div>
          <div className="flex items-center space-x-1 text-slate-500 font-mono text-[10px]">
            <Radio className="w-3 h-3 text-sky-400" />
            <span>UTC LIVE</span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-sky-950/70 text-sky-300 border border-sky-800/60 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/80 border border-transparent"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive ? "text-sky-400" : "text-slate-500"
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                      isActive
                        ? "bg-amber-500 text-slate-950"
                        : "bg-amber-950 text-amber-300 border border-amber-800"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer / Provenance info */}
      <div className="p-3 border-t border-slate-800/80 text-[11px] text-slate-500 space-y-1.5 font-mono">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center space-x-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Open Source</span>
          </span>
          <span className="text-[10px] text-slate-500">v1.0.0</span>
        </div>
        <div className="text-[10px] text-slate-600 truncate">
          NOAA · DMA · HawaiiCoast_GT
        </div>
      </div>
    </aside>
  );
}
