"use client";

import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import {
  Layers,
  Filter,
  Eye,
  EyeOff,
  Navigation,
  Compass,
  AlertTriangle,
  Anchor,
  Clock,
  Ship,
  Search,
} from "lucide-react";
import { api } from "@/lib/api";

interface MaritimeMapViewProps {
  onSelectVessel?: (mmsi: number) => void;
  onSelectEvent?: (eventId: string) => void;
}

export function MaritimeMapView({ onSelectVessel, onSelectEvent }: MaritimeMapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  // Filter states
  const [filterType, setFilterType] = useState<string>("All");
  const [filterBehavior, setFilterBehavior] = useState<string>("All");
  const [searchMmsi, setSearchMmsi] = useState<string>("");
  const [filterPanelOpen, setFilterPanelOpen] = useState<boolean>(true);

  // Layer visibility toggles
  const [showDensity, setShowDensity] = useState<boolean>(true);
  const [showTrajectories, setShowTrajectories] = useState<boolean>(true);
  const [showVessels, setShowVessels] = useState<boolean>(true);
  const [showEvents, setShowEvents] = useState<boolean>(true);
  const [showZones, setShowZones] = useState<boolean>(true);

  // Selected item modal/popover state
  const [selectedEntity, setSelectedEntity] = useState<any>(null);

  // Load zones & data
  const [zones, setZones] = useState<{ ports: any[]; anchorages: any[]; corridors: any[] } | null>(null);
  const [mapVessels, setMapVessels] = useState<any[]>([]);
  const [eventsList, setEventsList] = useState<any[]>([]);

  useEffect(() => {
    api.getMapZones().then(setZones).catch(console.error);
    api.getMapVessels().then((data) => setMapVessels(data.features || [])).catch(console.error);
    api.getEvents({ limit: 100 }).then(setEventsList).catch(console.error);
  }, []);

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Standard dark tile style
    const darkStyle: maplibregl.StyleSpecification = {
      version: 8,
      sources: {
        carto_dark: {
          type: "raster",
          tiles: [
            "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          ],
          tileSize: 256,
          attribution: "© OpenStreetMap, © CARTO",
        },
      },
      layers: [
        {
          id: "carto_dark_layer",
          type: "raster",
          source: "carto_dark",
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    };

    try {
      const m = new maplibregl.Map({
        container: mapContainer.current,
        style: darkStyle,
        center: [1.45, 51.10], // Dover Strait / English Channel default
        zoom: 7.8,
        pitch: 15,
        attributionControl: false,
      });

      m.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");

      m.on("load", async () => {
        // Load trajectories GeoJSON source
        try {
          const trajData = await api.getMapTrajectories(100);
          m.addSource("trajectories_src", {
            type: "geojson",
            data: trajData,
          });

          m.addLayer({
            id: "trajectories_line",
            type: "line",
            source: "trajectories_src",
            paint: {
              "line-color": "#0ea5e9",
              "line-width": 2,
              "line-opacity": 0.65,
              "line-dasharray": [2, 1],
            },
          });
        } catch (e) {
          console.error("Error loading trajectories:", e);
        }

        // Density cells layer
        try {
          const densityData = await api.getMapDensity(0.04);
          const densityGeoJSON: any = {
            type: "FeatureCollection",
            features: densityData.cells.map((c) => ({
              type: "Feature",
              geometry: {
                type: "Point",
                coordinates: [c.lon, c.lat],
              },
              properties: {
                count: c.count,
                avg_sog: c.avg_sog,
              },
            })),
          };

          m.addSource("density_src", {
            type: "geojson",
            data: densityGeoJSON,
          });

          m.addLayer({
            id: "density_heat",
            type: "circle",
            source: "density_src",
            paint: {
              "circle-radius": ["interpolate", ["linear"], ["get", "count"], 1, 6, 50, 18],
              "circle-color": [
                "interpolate",
                ["linear"],
                ["get", "count"],
                1, "rgba(14, 165, 233, 0.25)",
                10, "rgba(16, 185, 129, 0.45)",
                30, "rgba(245, 158, 11, 0.6)",
                60, "rgba(244, 63, 94, 0.75)",
              ],
              "circle-blur": 0.4,
            },
          });
        } catch (e) {
          console.error("Error loading density:", e);
        }
      });

      map.current = m;
    } catch (e) {
      console.warn("MapLibre initialization fallback:", e);
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update layer visibility
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    try {
      if (map.current.getLayer("density_heat")) {
        map.current.setLayoutProperty("density_heat", "visibility", showDensity ? "visible" : "none");
      }
      if (map.current.getLayer("trajectories_line")) {
        map.current.setLayoutProperty("trajectories_line", "visibility", showTrajectories ? "visible" : "none");
      }
    } catch (_) {}
  }, [showDensity, showTrajectories]);

  // Filtered vessel markers
  const filteredVessels = mapVessels.filter((f) => {
    const p = f.properties;
    if (filterType !== "All" && p.vessel_type !== filterType) return false;
    if (filterBehavior === "Deviations" && p.event_count === 0) return false;
    if (searchMmsi && !p.mmsi.toString().includes(searchMmsi) && !p.name.toLowerCase().includes(searchMmsi.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div className="relative w-full h-[calc(100vh-4rem)] flex overflow-hidden bg-slate-950">
      {/* Collapsible Left Filter Panel */}
      <div
        className={`transition-all duration-300 ease-in-out z-10 bg-slate-950/95 backdrop-blur border-r border-slate-800 flex flex-col justify-between ${
          filterPanelOpen ? "w-80 p-4" : "w-10 p-2 items-center"
        }`}
      >
        {filterPanelOpen ? (
          <div className="space-y-4 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center space-x-2 text-slate-200">
                <Filter className="w-4 h-4 text-sky-400" />
                <span className="text-xs font-semibold uppercase tracking-wider">Map Controls</span>
              </div>
              <button
                onClick={() => setFilterPanelOpen(false)}
                className="text-slate-500 hover:text-slate-300 text-xs font-mono"
              >
                Hide ◀
              </button>
            </div>

            {/* MMSI / Vessel Name Search */}
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-slate-400">Search Vessel / MMSI</label>
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="e.g. 244101001 or North Star"
                  value={searchMmsi}
                  onChange={(e) => setSearchMmsi(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 pl-8 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>
            </div>

            {/* Vessel Type Filter */}
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-slate-400">Vessel Category</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
              >
                <option value="All">All Vessel Classes</option>
                <option value="Cargo">Cargo</option>
                <option value="Tanker">Tanker</option>
                <option value="Fishing">Fishing</option>
                <option value="Passenger">Passenger</option>
                <option value="Tug">Tug / Tow</option>
                <option value="Other">Other / Special</option>
              </select>
            </div>

            {/* Behaviour Filter */}
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-slate-400">Behavioural Filter</label>
              <select
                value={filterBehavior}
                onChange={(e) => setFilterBehavior(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
              >
                <option value="All">All Movements</option>
                <option value="Deviations">Active Deviations Only</option>
              </select>
            </div>

            {/* Map Layer Group Toggles */}
            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                  Display Layers
                </span>
                <div className="flex items-center space-x-1.5 text-[10px] font-mono">
                  <button
                    onClick={() => {
                      setShowDensity(true);
                      setShowTrajectories(true);
                      setShowVessels(true);
                      setShowEvents(true);
                      setShowZones(true);
                    }}
                    className="text-sky-400 hover:text-sky-300"
                  >
                    All
                  </button>
                  <span className="text-slate-600">/</span>
                  <button
                    onClick={() => {
                      setShowDensity(false);
                      setShowTrajectories(false);
                      setShowVessels(false);
                      setShowEvents(false);
                      setShowZones(false);
                    }}
                    className="text-slate-500 hover:text-slate-400"
                  >
                    None
                  </button>
                </div>
              </div>

              <div className="space-y-1.5 text-xs font-mono text-slate-400">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showVessels}
                    onChange={(e) => setShowVessels(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0"
                  />
                  <span>Vessel Markers ({filteredVessels.length})</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showTrajectories}
                    onChange={(e) => setShowTrajectories(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0"
                  />
                  <span>Historical Trajectories</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showEvents}
                    onChange={(e) => setShowEvents(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0"
                  />
                  <span>Anomaly / Event Markers ({eventsList.length})</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showDensity}
                    onChange={(e) => setShowDensity(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0"
                  />
                  <span>Traffic Density Heatmap</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showZones}
                    onChange={(e) => setShowZones(e.target.checked)}
                    className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0"
                  />
                  <span>Ports, Anchorages & Fairways</span>
                </label>
              </div>
            </div>

            {/* Quick Context Reference list */}
            {zones && showZones && (
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono space-y-1.5">
                <div className="text-slate-400 font-semibold uppercase text-[10px] flex items-center space-x-1">
                  <Anchor className="w-3 h-3 text-emerald-400" />
                  <span>Monitored Maritime Zones</span>
                </div>
                <div className="space-y-1 text-slate-500">
                  {zones.anchorages.slice(0, 3).map((a, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="truncate">{a.name}</span>
                      <span className="text-emerald-400">Anchor</span>
                    </div>
                  ))}
                  {zones.corridors.slice(0, 2).map((c, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="truncate">{c.name.split("(")[0]}</span>
                      <span className="text-amber-400">TSS</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={() => setFilterPanelOpen(true)}
            className="p-1 rounded bg-slate-900 text-slate-400 hover:text-slate-200 mt-2"
            title="Expand Filters"
          >
            <Filter className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Main Map Container */}
      <div className="relative flex-1 w-full h-full">
        <div ref={mapContainer} className="w-full h-full" />

        {/* Floating In-Map Overlays (HTML Vessel Markers & Event Markers) */}
        {showVessels && (
          <div className="absolute top-4 right-4 z-10 p-2.5 rounded bg-slate-950/90 border border-slate-800 shadow-lg text-xs font-mono space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">
              Live Vessels on Radar
            </div>
            <div className="text-sm font-bold text-sky-400">
              {filteredVessels.length} Active Tracks
            </div>
          </div>
        )}

        {/* Selected Vessel / Event Inspector Drawer */}
        {selectedEntity && (
          <div className="absolute bottom-4 left-6 right-6 md:left-88 md:right-8 z-20 p-4 rounded-lg bg-slate-950/95 border border-sky-900/60 shadow-2xl backdrop-blur max-w-2xl">
            <div className="flex items-start justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center space-x-2">
                <Ship className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  {selectedEntity.name || `MMSI ${selectedEntity.mmsi}`}
                </h3>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-sky-300">
                  {selectedEntity.vessel_type}
                </span>
              </div>
              <button
                onClick={() => setSelectedEntity(null)}
                className="text-slate-400 hover:text-slate-200 text-sm font-mono"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 py-3 text-xs font-mono">
              <div>
                <span className="text-[10px] text-slate-500 block">SOG / COG</span>
                <span className="text-slate-200">
                  {selectedEntity.sog?.toFixed(1) || "0.0"} kts / {selectedEntity.cog?.toFixed(0) || "0"}°
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">Flag</span>
                <span className="text-slate-200">{selectedEntity.flag || "Unknown"}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">Quality Score</span>
                <span className="text-emerald-400">
                  {(selectedEntity.quality_score * 100).toFixed(0)}%
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">Detected Events</span>
                <span
                  className={
                    selectedEntity.event_count > 0 ? "text-amber-400 font-bold" : "text-slate-400"
                  }
                >
                  {selectedEntity.event_count}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800/80">
              {onSelectVessel && (
                <button
                  onClick={() => onSelectVessel(selectedEntity.mmsi)}
                  className="px-3 py-1 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition"
                >
                  Open Vessel Profile
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
