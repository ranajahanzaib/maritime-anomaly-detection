import math
from typing import List, Dict, Any, Tuple
import numpy as np
from backend.trajectories.kinematics import haversine_distance_nm


def compute_spatial_features(
    points: List[Dict[str, Any]],
    reference_corridors: List[List[Tuple[float, float]]] | None = None,
) -> Dict[str, float]:
    """
    Computes spatial features: bounding box, centroid, radius of gyration,
    and minimum distance to known reference shipping corridors.
    """
    if not points:
        return {
            "centroid_lat": 0.0,
            "centroid_lon": 0.0,
            "bbox_area_deg2": 0.0,
            "radius_of_gyration_nm": 0.0,
            "min_corridor_dist_nm": 0.0,
        }

    lats = [float(p["latitude"]) for p in points]
    lons = [float(p["longitude"]) for p in points]

    c_lat = float(np.mean(lats))
    c_lon = float(np.mean(lons))

    d_lat = max(lats) - min(lats)
    d_lon = max(lons) - min(lons)
    bbox_area = d_lat * d_lon

    # Radius of gyration (spatial spread from centroid in NM)
    sq_dists = [
        haversine_distance_nm(c_lat, c_lon, lat, lon) ** 2
        for lat, lon in zip(lats, lons)
    ]
    rg = math.sqrt(np.mean(sq_dists)) if sq_dists else 0.0

    # Minimum distance to any point along reference corridors
    min_corr_dist = 0.0
    if reference_corridors:
        corr_dists = []
        for corridor in reference_corridors:
            for c_pt in corridor:
                for p in points:
                    corr_dists.append(haversine_distance_nm(p["latitude"], p["longitude"], c_pt[0], c_pt[1]))
        if corr_dists:
            min_corr_dist = min(corr_dists)

    return {
        "centroid_lat": round(c_lat, 5),
        "centroid_lon": round(c_lon, 5),
        "bbox_area_deg2": round(bbox_area, 6),
        "radius_of_gyration_nm": round(rg, 2),
        "min_corridor_dist_nm": round(min_corr_dist, 2),
    }
