import uuid
import datetime
from typing import List, Dict, Any, Tuple
from backend.trajectories.kinematics import haversine_distance_nm, derive_point_kinematics
from backend.trajectories.simplification import simplify_geojson_linestring


class TrajectorySegmenter:
    def __init__(
        self,
        max_time_gap_minutes: float = 45.0,
        min_points_per_segment: int = 5,
        simplification_tolerance: float = 0.0005,
    ):
        self.max_time_gap_seconds = max_time_gap_minutes * 60.0
        self.min_points_per_segment = min_points_per_segment
        self.simplification_tolerance = simplification_tolerance

    def segment_points(
        self,
        mmsi: int,
        points: List[Dict[str, Any]],
        is_synthetic: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Segments a sequence of AIS points for a single vessel.
        Returns:
            - segments: List of segment dicts (matching TrajectorySegment schema)
            - gaps: List of detected transmission gap dicts
        """
        if not points:
            return [], []

        # Ensure sorted by timestamp
        sorted_points = sorted(
            points,
            key=lambda p: p["timestamp"] if isinstance(p["timestamp"], datetime.datetime)
            else datetime.datetime.fromisoformat(str(p["timestamp"]).replace("Z", "+00:00"))
        )

        segments = []
        gaps = []

        current_segment_points: List[Dict[str, Any]] = [sorted_points[0]]
        segment_idx = 0

        for i in range(1, len(sorted_points)):
            prev = sorted_points[i - 1]
            curr = sorted_points[i]

            t1 = prev["timestamp"] if isinstance(prev["timestamp"], datetime.datetime) else datetime.datetime.fromisoformat(str(prev["timestamp"]).replace("Z", "+00:00"))
            t2 = curr["timestamp"] if isinstance(curr["timestamp"], datetime.datetime) else datetime.datetime.fromisoformat(str(curr["timestamp"]).replace("Z", "+00:00"))

            gap_seconds = (t2 - t1).total_seconds()

            if gap_seconds > self.max_time_gap_seconds:
                # We have a long AIS gap!
                gap_dist_nm = haversine_distance_nm(
                    prev["latitude"], prev["longitude"],
                    curr["latitude"], curr["longitude"]
                )
                gaps.append({
                    "mmsi": mmsi,
                    "start_time": t1,
                    "end_time": t2,
                    "duration_seconds": gap_seconds,
                    "duration_hours": round(gap_seconds / 3600.0, 2),
                    "start_lat": prev["latitude"],
                    "start_lon": prev["longitude"],
                    "end_lat": curr["latitude"],
                    "end_lon": curr["longitude"],
                    "displacement_nm": round(gap_dist_nm, 2),
                    "implied_speed_knots": round((gap_dist_nm / gap_seconds) * 3600.0, 2) if gap_seconds > 0 else 0.0,
                })

                # Close current segment if long enough
                if len(current_segment_points) >= self.min_points_per_segment:
                    seg = self._build_segment_dict(
                        mmsi, segment_idx, current_segment_points, is_synthetic
                    )
                    segments.append(seg)
                    segment_idx += 1

                current_segment_points = [curr]
            else:
                current_segment_points.append(curr)

        # Close final segment
        if len(current_segment_points) >= self.min_points_per_segment:
            seg = self._build_segment_dict(
                mmsi, segment_idx, current_segment_points, is_synthetic
            )
            segments.append(seg)

        return segments, gaps

    def _build_segment_dict(
        self,
        mmsi: int,
        segment_index: int,
        points: List[Dict[str, Any]],
        is_synthetic: bool = False,
    ) -> Dict[str, Any]:
        t_start = points[0]["timestamp"] if isinstance(points[0]["timestamp"], datetime.datetime) else datetime.datetime.fromisoformat(str(points[0]["timestamp"]).replace("Z", "+00:00"))
        t_end = points[-1]["timestamp"] if isinstance(points[-1]["timestamp"], datetime.datetime) else datetime.datetime.fromisoformat(str(points[-1]["timestamp"]).replace("Z", "+00:00"))

        duration = (t_end - t_start).total_seconds()

        lats = [float(p["latitude"]) for p in points]
        lons = [float(p["longitude"]) for p in points]
        sogs = [float(p.get("sog", 0.0)) for p in points]

        # Calculate total distance and step kinematics
        total_dist_nm = 0.0
        speeds = []
        turn_rates = []

        for i in range(1, len(points)):
            k = derive_point_kinematics(points[i - 1], points[i])
            total_dist_nm += k["dist_nm"]
            speeds.append(k["derived_speed_knots"])
            turn_rates.append(k["turn_rate_deg_per_min"])

        avg_speed = sum(sogs) / len(sogs) if sogs else 0.0
        max_speed = max(sogs) if sogs else 0.0

        simplified_geo = simplify_geojson_linestring(
            points, tolerance=self.simplification_tolerance
        )

        return {
            "id": f"seg_{mmsi}_{segment_index}_{uuid.uuid4().hex[:8]}",
            "mmsi": mmsi,
            "segment_index": segment_index,
            "start_time": t_start,
            "end_time": t_end,
            "duration_seconds": duration,
            "point_count": len(points),
            "distance_nm": round(total_dist_nm, 2),
            "avg_speed": round(avg_speed, 2),
            "max_speed": round(max_speed, 2),
            "bbox_min_lat": min(lats),
            "bbox_min_lon": min(lons),
            "bbox_max_lat": max(lats),
            "bbox_max_lon": max(lons),
            "geometry_geojson": simplified_geo,
            "kinematics_summary": {
                "avg_derived_speed": round(sum(speeds) / len(speeds), 2) if speeds else 0.0,
                "max_derived_speed": round(max(speeds), 2) if speeds else 0.0,
                "avg_turn_rate_dpm": round(sum(turn_rates) / len(turn_rates), 2) if turn_rates else 0.0,
                "max_turn_rate_dpm": round(max(turn_rates), 2) if turn_rates else 0.0,
            },
            "is_synthetic": is_synthetic,
        }
