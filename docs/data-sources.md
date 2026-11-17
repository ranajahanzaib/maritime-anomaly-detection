# Supported Data Sources & Provenance

The platform integrates configurable adapters for primary open-source and benchmark maritime AIS datasets.

---

## 1. NOAA MarineCadastre AIS

- **Source:** US Bureau of Ocean Energy Management (BOEM) and National Oceanic and Atmospheric Administration (NOAA).
- **URL:** https://github.com/NOAA-OCM/ocm-marinecadastre-ais-vessel-traffic
- **Formats Supported:** CSV and GeoParquet.
- **Fields Mapped:**
  - `MMSI` → `mmsi`
  - `BaseDateTime` → `timestamp` (normalized to UTC)
  - `LAT` / `LON` → `latitude` / `longitude`
  - `SOG` / `COG` / `Heading` → `sog` / `cog` / `heading`
  - `VesselName` / `IMO` / `VesselType` / `Status` → Canonical attributes
  - `Length` / `Width` / `Draft` → Vessel physical dimensions
- **Terms:** Public domain (US Government work).

---

## 2. HawaiiCoast_GT Benchmark Dataset

- **Source:** Zenodo Record 8253611.
- **URL:** https://zenodo.org/records/8253611
- **Description:** Ground truth incident benchmark dataset containing vessel trajectories surrounding the Hawaiian archipelago with curated incident annotations (search and rescue, mechanical breakdown, groundings, abnormal route deviations).
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Implementation Note:** Preserves original incident classifications and links observations without claiming regulatory illegality.

---

## 3. Danish AIS Trajectory Datasets

- **Source:** Danish Maritime Authority (DMA) and Kristoffer Olesen's trajectory benchmarks.
- **URL:** https://github.com/KristofferOlesen/Datasets-of-AIS-Trajectories-from-Danish-Waters
- **Description:** High-density AIS trajectories from Danish waters (Great Belt, Kattegat, Oresund) with annotated abnormal behaviours.
- **Format:** Comma-delimited CSV containing `# Timestamp`, `MMSI`, `Latitude`, `Longitude`, `SOG`, `COG`, `Heading`, `Ship type`.
- **License:** Open data under Danish Maritime Authority terms.

---

## 4. Synthetic Demonstration Dataset

- **Deterministic Generator:** Located at `scripts/generate_demo_data.py`.
- **Purpose:** Standalone, deterministic testbed providing immediate working functionality without multi-gigabyte external downloads.
- **Scenarios Modeled:**
  1. Route deviation (Cargo vessel off Dover SW TSS Lane)
  2. Rendezvous (Tanker and small vessel drifting together in open sea)
  3. Loitering (Container vessel dwelling in open ocean for 12 hours)
  4. Peer deviation (Cargo vessel steaming at 28.5 kts vs 13.5 kt baseline)
  5. Historical inconsistency (Fishing vessel operating 50 NM from home operating zone)
  6. AIS transmission gap (Nordic Pioneer missing reports for 4.5 hours)
  7. Normal anchorage (Vessel waiting at Maasvlakte Anchorage 4E, Rotterdam)
  8. Port congestion (Multiple vessels queuing near Dover Port approaches)
  9. Legitimate fishing pattern (Trawler doing zig-zag trawling pattern at 3.5 kts)
  10. Normal transits (10 vessels maintaining standard separation in shipping fairways)
- **Labeling Policy:** Explicitly tagged with `is_synthetic=True`. Never conflated with real incidents.
