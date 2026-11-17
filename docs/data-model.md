# Canonical Data Model & Schema

The platform maps heterogeneous AIS messages into a canonical schema, preserves raw data quality signals, and constructs discrete trajectory segments and behavioral events.

---

## 1. Canonical AIS Schema (`CanonicalAISPoint`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `mmsi` | `int` | Maritime Mobile Service Identity (9-digit identifier) |
| `imo` | `int | None` | International Maritime Organization number |
| `vessel_name` | `str | None` | Cleaned vessel radio name |
| `vessel_type` | `str` | Normalized class: `Cargo`, `Tanker`, `Fishing`, `Passenger`, `Tug`, `Other` |
| `flag` | `str | None` | Country flag identifier |
| `timestamp` | `datetime` | UTC timestamp with ISO-8601 formatting |
| `latitude` | `float` | WGS84 Latitude [-90.0, 90.0] |
| `longitude` | `float` | WGS84 Longitude [-180.0, 180.0] |
| `sog` | `float` | Speed Over Ground in knots [0.0, 60.0] |
| `cog` | `float` | Course Over Ground in degrees [0.0, 360.0] |
| `heading` | `float | None` | True heading in degrees [0.0, 360.0] |
| `navigational_status` | `str | None` | AIS Navigational Status string |
| `length` / `width` / `draught` | `float | None` | Physical vessel dimensions in meters |
| `source_dataset` | `str` | Provenance dataset tag |
| `is_interpolated` | `bool` | True if point was added via defensible short-gap interpolation |
| `is_valid` | `bool` | Data quality validity indicator |
| `rejection_reason` | `str | None` | Explicit reason if flagged as implausible or corrupted |

---

## 2. Trajectory Segment (`TrajectorySegment`)

A segmented sub-track representing continuous vessel movement between long transmission gaps:

- `id`: Segment identifier (`seg_{mmsi}_{index}_{uuid}`)
- `mmsi`: Vessel identifier
- `segment_index`: Incremental index of voyage segment
- `start_time` / `end_time`: Time span
- `duration_seconds`: Total segment duration
- `point_count`: Number of valid observations in segment
- `distance_nm`: Total geodesic distance in nautical miles
- `avg_speed` / `max_speed`: Derived segment velocity in knots
- `geometry_geojson`: Simplified GeoJSON `LineString` for efficient multi-zoom rendering
- `kinematics_summary`: Average derived speed, max speed, turn rate distributions

---

## 3. Behavioral Event (`BehavioralEvent`)

Represents an explainable detection or observability event:

- `id`: Unique event identifier
- `category`:
  - `UNUSUAL_ROUTE_DEVIATION`
  - `RENDEZVOUS`
  - `LOITERING`
  - `PEER_GROUP_DEVIATION`
  - `HISTORICAL_INCONSISTENCY`
  - `AIS_TRANSMISSION_GAP`
  - `IMPLAUSIBLE_MOVEMENT`
- `primary_mmsi` / `secondary_mmsi`: Involved vessels
- `detector_id` & `detector_version`: Originating algorithm
- `deviation_score`: Normalized score [0.0, 1.0]
- `severity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `contextual_state`:
  - `EXPECTED_CONTEXT`: Normal waiting in designated anchorage/port or fishing in designated grounds
  - `POTENTIALLY_RELEVANT`: Significant deviation in open waters away from designated zones
  - `CONTEXT_UNAVAILABLE`: Reference layers not loaded for region
- `explanation`: Human-readable summary of observed deviation
- `feature_attributions`: Dictionary of quantitative contributing factors
- `evidence`: Detailed payload (e.g. pairwise distance timeline, corridor waypoints)
- `status`: `NEW`, `UNDER_INVESTIGATION`, `RESOLVED`, `FALSE_POSITIVE`
- `investigation_notes`: Analyst audit log
