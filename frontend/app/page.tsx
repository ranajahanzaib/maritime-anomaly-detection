"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, NavTab } from "@/components/Sidebar";
import { OverviewView } from "@/features/dashboard/OverviewView";
import { MaritimeMapView } from "@/features/map/MaritimeMapView";
import { VesselExplorerView } from "@/features/vessel-explorer/VesselExplorerView";
import { VesselProfileView } from "@/features/vessel-profile/VesselProfileView";
import { EventInvestigationView } from "@/features/investigations/EventInvestigationView";
import { ModelLaboratoryView } from "@/features/model-lab/ModelLaboratoryView";
import { DatasetsView } from "@/features/datasets/DatasetsView";
import { SettingsView } from "@/features/settings/SettingsView";
import { OverviewStats } from "@/lib/types";
import { api } from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavTab>("overview");
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loadingStats, setLoadingStats] = useState<boolean>(true);

  // Deep linking states
  const [selectedMmsi, setSelectedMmsi] = useState<number | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | undefined>(undefined);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    setLoadingStats(true);
    try {
      const data = await api.getOverviewStats();
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingStats(false);
    }
  };

  const handleNavigate = (tab: NavTab, item?: any) => {
    if (tab === "events" && item?.id) {
      setSelectedEventId(item.id);
    }
    setActiveTab(tab);
  };

  const handleSelectVessel = (mmsi: number) => {
    setSelectedMmsi(mmsi);
  };

  const handleSelectEvent = (eventId: string) => {
    setSelectedEventId(eventId);
    setActiveTab("events");
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#06090e]">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setSelectedMmsi(null);
          setActiveTab(tab);
        }}
        eventCount={stats?.total_events_detected || 0}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Operational Status Header */}
        <header className="h-12 border-b border-slate-800/80 bg-slate-950/60 px-6 flex items-center justify-between shrink-0 font-mono text-xs">
          <div className="flex items-center space-x-3">
            <span className="text-slate-500 uppercase tracking-wider text-[11px]">
              Active Workspace
            </span>
            <span className="text-slate-600">/</span>
            <span className="text-sky-400 font-semibold uppercase tracking-wider">
              {selectedMmsi ? `Vessel MMSI ${selectedMmsi}` : activeTab.replace(/_/g, " ")}
            </span>
          </div>

          <div className="flex items-center space-x-4 text-[11px] text-slate-400">
            {stats && (
              <div className="flex items-center space-x-3">
                <span>
                  Tracked Vessels: <span className="text-slate-200 font-bold">{stats.total_vessels}</span>
                </span>
                <span>·</span>
                <span>
                  Deviations: <span className="text-amber-400 font-bold">{stats.total_events_detected}</span>
                </span>
              </div>
            )}
          </div>
        </header>

        {/* View Switcher */}
        <div className="flex-1 overflow-hidden">
          {selectedMmsi ? (
            <VesselProfileView
              mmsi={selectedMmsi}
              onBack={() => setSelectedMmsi(null)}
              onSelectEvent={handleSelectEvent}
            />
          ) : activeTab === "overview" ? (
            <OverviewView
              stats={stats}
              loading={loadingStats}
              onNavigateTab={handleNavigate}
            />
          ) : activeTab === "map" ? (
            <MaritimeMapView
              onSelectVessel={handleSelectVessel}
              onSelectEvent={handleSelectEvent}
            />
          ) : activeTab === "vessels" ? (
            <VesselExplorerView onSelectVessel={handleSelectVessel} />
          ) : activeTab === "events" ? (
            <EventInvestigationView
              initialEventId={selectedEventId}
              onSelectVessel={handleSelectVessel}
            />
          ) : activeTab === "models" ? (
            <ModelLaboratoryView />
          ) : activeTab === "datasets" ? (
            <DatasetsView />
          ) : (
            <SettingsView />
          )}
        </div>
      </main>
    </div>
  );
}
