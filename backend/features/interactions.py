import datetime
from typing import List, Dict, Any, Tuple
from backend.trajectories.kinematics import haversine_distance_nm, calculate_course_difference


def compute_pairwise_interaction_timeline(
    track_a: List[Dict[str, Any]],
    track_b: List[Dict[str, Any]],
    time_tolerance_seconds: float = 300.0,
) -> List[Dict[str, Any]]:
    """
    Pairs synchronous observations between two vessels within time_tolerance_seconds.
    Computes distance, relative speed, and course differences over time.
    """
    timeline = []
    
    def to_dt(t):
        if isinstance(t, str):
            return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
        return t

    sorted_b = sorted(track_b, key=lambda p: to_dt(p["timestamp"]))

    for pt_a in track_a:
        t_a = to_dt(pt_a["timestamp"])
        
        # Find nearest point in track_b
        best_b = None
        min_dt = float("inf")
        for pt_b in sorted_b:
            t_b = to_dt(pt_b["timestamp"])
            dt = abs((t_a - t_b).total_seconds())
            if dt < min_dt:
                min_dt = dt
                best_b = pt_b
            elif dt > min_dt:
                # Sorted, so we passed the minimum
                break

        if best_b and min_dt <= time_tolerance_seconds:
            dist_nm = haversine_distance_nm(
                pt_a["latitude"], pt_a["longitude"],
                best_b["latitude"], best_b["longitude"]
            )
            dist_meters = dist_nm * 1852.0
            
            sog_a = float(pt_a.get("sog", 0.0))
            sog_b = float(best_b.get("sog", 0.0))
            rel_speed = abs(sog_a - sog_b)
            
            cog_a = float(pt_a.get("cog", 0.0))
            cog_b = float(best_b.get("cog", 0.0))
            course_diff = calculate_course_difference(cog_a, cog_b)

            timeline.append({
                "timestamp": t_a,
                "distance_nm": round(dist_nm, 3),
                "distance_meters": round(dist_meters, 1),
                "vessel_a_sog": sog_a,
                "vessel_b_sog": sog_b,
                "relative_speed_knots": round(rel_speed, 2),
                "vessel_a_cog": cog_a,
                "vessel_b_cog": cog_b,
                "course_diff_deg": round(course_diff, 1),
                "lat_a": pt_a["latitude"],
                "lon_a": pt_a["longitude"],
                "lat_b": best_b["latitude"],
                "lon_b": best_b["longitude"],
            })

    return timeline
