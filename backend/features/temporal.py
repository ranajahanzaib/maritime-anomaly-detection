import datetime
from typing import List, Dict, Any
import numpy as np


def compute_temporal_features(points: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Computes temporal features: duration, interval statistics, day/night and hour of day.
    """
    if len(points) < 2:
        return {
            "duration_hours": 0.0,
            "sampling_interval_mean_sec": 0.0,
            "sampling_interval_std_sec": 0.0,
            "start_hour": 12.0,
            "day_of_week": 0.0,
        }

    def to_dt(t):
        if isinstance(t, str):
            return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
        return t

    t_start = to_dt(points[0]["timestamp"])
    t_end = to_dt(points[-1]["timestamp"])
    total_seconds = (t_end - t_start).total_seconds()

    intervals = []
    for i in range(1, len(points)):
        t1 = to_dt(points[i - 1]["timestamp"])
        t2 = to_dt(points[i]["timestamp"])
        intervals.append((t2 - t1).total_seconds())

    return {
        "duration_hours": round(total_seconds / 3600.0, 2),
        "sampling_interval_mean_sec": round(float(np.mean(intervals)), 1) if intervals else 0.0,
        "sampling_interval_std_sec": round(float(np.std(intervals)), 1) if intervals else 0.0,
        "start_hour": float(t_start.hour),
        "day_of_week": float(t_start.weekday()),
    }
