import datetime
from typing import List, Dict, Any
from backend.trajectories.kinematics import haversine_distance_nm


def interpolate_short_gaps(
    points: List[Dict[str, Any]],
    min_gap_seconds: float = 120.0,
    max_gap_seconds: float = 600.0,
    step_seconds: float = 60.0,
) -> List[Dict[str, Any]]:
    """
    Interpolates between successive points only for defensible short gaps (e.g. 2 to 10 minutes).
    Adds points with explicit `is_interpolated=True` uncertainty markers.
    Never interpolates across long gaps (> max_gap_seconds).
    """
    if len(points) < 2:
        return points

    interpolated = []

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]

        interpolated.append(p1)

        t1 = p1["timestamp"]
        t2 = p2["timestamp"]
        if isinstance(t1, str):
            t1 = datetime.datetime.fromisoformat(t1.replace("Z", "+00:00"))
        if isinstance(t2, str):
            t2 = datetime.datetime.fromisoformat(t2.replace("Z", "+00:00"))

        gap = (t2 - t1).total_seconds()

        if min_gap_seconds <= gap <= max_gap_seconds:
            # Generate intermediate points
            num_steps = int(gap // step_seconds)
            for step in range(1, num_steps):
                fraction = (step * step_seconds) / gap
                step_time = t1 + datetime.timedelta(seconds=step * step_seconds)
                step_lat = p1["latitude"] + fraction * (p2["latitude"] - p1["latitude"])
                step_lon = p1["longitude"] + fraction * (p2["longitude"] - p1["longitude"])
                step_sog = p1["sog"] + fraction * (p2["sog"] - p1["sog"])
                step_cog = p1["cog"] + fraction * (p2["cog"] - p1["cog"])

                interp_pt = dict(p1)
                interp_pt["timestamp"] = step_time
                interp_pt["latitude"] = step_lat
                interp_pt["longitude"] = step_lon
                interp_pt["sog"] = step_sog
                interp_pt["cog"] = step_cog
                interp_pt["is_interpolated"] = True
                interpolated.append(interp_pt)

    interpolated.append(points[-1])
    return interpolated
