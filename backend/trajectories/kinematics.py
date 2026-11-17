import math
from typing import Tuple, List, Optional
import datetime


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in Nautical Miles."""
    r_nm = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_nm * c


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing in degrees [0, 360)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    init_bearing = math.degrees(math.atan2(x, y))
    return (init_bearing + 360.0) % 360.0


def calculate_course_difference(c1: float, c2: float) -> float:
    """Shortest angular difference in degrees [0, 180]."""
    diff = abs(c1 - c2) % 360.0
    return 360.0 - diff if diff > 180.0 else diff


def derive_point_kinematics(
    pt_prev: dict,
    pt_curr: dict,
) -> dict:
    """
    Computes derived speed, acceleration, and turn rate between two successive AIS points.
    pt_prev and pt_curr must have: latitude, longitude, timestamp, sog, cog.
    """
    t1 = pt_prev["timestamp"]
    t2 = pt_curr["timestamp"]
    if isinstance(t1, str):
        t1 = datetime.datetime.fromisoformat(t1.replace("Z", "+00:00"))
    if isinstance(t2, str):
        t2 = datetime.datetime.fromisoformat(t2.replace("Z", "+00:00"))

    dt_seconds = (t2 - t1).total_seconds()
    if dt_seconds <= 0:
        return {
            "dt_seconds": 0.0,
            "dist_nm": 0.0,
            "derived_speed_knots": pt_curr.get("sog", 0.0),
            "acceleration_ms2": 0.0,
            "turn_rate_deg_per_min": 0.0,
            "calculated_bearing": pt_curr.get("cog", 0.0),
        }

    dist_nm = haversine_distance_nm(
        pt_prev["latitude"], pt_prev["longitude"],
        pt_curr["latitude"], pt_curr["longitude"]
    )
    derived_speed = (dist_nm / dt_seconds) * 3600.0

    # Acceleration in m/s^2 (1 knot = 0.514444 m/s)
    v1_ms = pt_prev.get("sog", 0.0) * 0.514444
    v2_ms = pt_curr.get("sog", 0.0) * 0.514444
    accel_ms2 = (v2_ms - v1_ms) / dt_seconds

    # Turn rate in deg/min
    cog1 = pt_prev.get("cog", 0.0)
    cog2 = pt_curr.get("cog", 0.0)
    cog_diff = calculate_course_difference(cog1, cog2)
    turn_rate_dpm = (cog_diff / dt_seconds) * 60.0

    calc_bearing = calculate_bearing_deg(
        pt_prev["latitude"], pt_prev["longitude"],
        pt_curr["latitude"], pt_curr["longitude"]
    )

    return {
        "dt_seconds": dt_seconds,
        "dist_nm": dist_nm,
        "derived_speed_knots": round(derived_speed, 2),
        "acceleration_ms2": round(accel_ms2, 4),
        "turn_rate_deg_per_min": round(turn_rate_dpm, 2),
        "calculated_bearing": round(calc_bearing, 2),
    }
