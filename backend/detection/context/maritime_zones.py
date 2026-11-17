from typing import List, Dict, Any
from backend.trajectories.kinematics import haversine_distance_nm


MARITIME_REFERENCE_PORTS: List[Dict[str, Any]] = [
    {
        "name": "Port of Rotterdam",
        "country": "NLD",
        "lat": 51.95,
        "lon": 4.15,
        "radius_nm": 6.0,
        "type": "PORT",
    },
    {
        "name": "Port of Dover",
        "country": "GBR",
        "lat": 51.12,
        "lon": 1.32,
        "radius_nm": 4.0,
        "type": "PORT",
    },
    {
        "name": "Port of Singapore",
        "country": "SGP",
        "lat": 1.26,
        "lon": 103.82,
        "radius_nm": 8.0,
        "type": "PORT",
    },
    {
        "name": "Port of Honolulu",
        "country": "USA",
        "lat": 21.31,
        "lon": -157.87,
        "radius_nm": 5.0,
        "type": "PORT",
    },
    {
        "name": "Port of Copenhagen",
        "country": "DNK",
        "lat": 55.70,
        "lon": 12.60,
        "radius_nm": 5.0,
        "type": "PORT",
    },
]

MARITIME_REFERENCE_ANCHORAGES: List[Dict[str, Any]] = [
    {
        "name": "Maasvlakte Anchorage 4E",
        "region": "North Sea / Rotterdam Approaches",
        "lat": 52.02,
        "lon": 3.90,
        "radius_nm": 3.5,
        "type": "ANCHORAGE",
    },
    {
        "name": "Dover Outer Anchorage",
        "region": "English Channel",
        "lat": 51.10,
        "lon": 1.40,
        "radius_nm": 2.5,
        "type": "ANCHORAGE",
    },
    {
        "name": "Singapore Eastern Anchorage",
        "region": "Singapore Strait",
        "lat": 1.28,
        "lon": 103.95,
        "radius_nm": 4.0,
        "type": "ANCHORAGE",
    },
    {
        "name": "Honolulu Barbers Point Anchorage",
        "region": "Oahu South Coast",
        "lat": 21.30,
        "lon": -158.12,
        "radius_nm": 3.0,
        "type": "ANCHORAGE",
    },
    {
        "name": "Kastrup Roads Anchorage",
        "region": "Oresund / Danish Waters",
        "lat": 55.63,
        "lon": 12.70,
        "radius_nm": 2.5,
        "type": "ANCHORAGE",
    },
]

MARITIME_SHIPPING_CORRIDORS: List[Dict[str, Any]] = [
    {
        "name": "English Channel TSS (Dover Strait Southwest Lane)",
        "waypoints": [
            (51.30, 1.80),
            (51.15, 1.50),
            (50.95, 1.20),
            (50.70, 0.80),
        ],
        "width_nm": 3.0,
    },
    {
        "name": "English Channel TSS (Dover Strait Northeast Lane)",
        "waypoints": [
            (50.65, 0.95),
            (50.90, 1.35),
            (51.10, 1.65),
            (51.25, 1.95),
        ],
        "width_nm": 3.0,
    },
    {
        "name": "Danish Great Belt Shipping Route",
        "waypoints": [
            (55.85, 11.00),
            (55.60, 11.00),
            (55.35, 11.10),
            (55.05, 11.15),
        ],
        "width_nm": 2.5,
    },
    {
        "name": "Hawaii Kai Channel Approach",
        "waypoints": [
            (21.20, -157.65),
            (21.25, -157.75),
            (21.30, -157.85),
        ],
        "width_nm": 3.0,
    },
]


def find_nearest_maritime_zone(lat: float, lon: float) -> Dict[str, Any]:
    """Finds nearest port or anchorage and distance in nautical miles."""
    best_zone = None
    min_dist = float("inf")

    all_zones = MARITIME_REFERENCE_PORTS + MARITIME_REFERENCE_ANCHORAGES
    for z in all_zones:
        d = haversine_distance_nm(lat, lon, z["lat"], z["lon"])
        if d < min_dist:
            min_dist = d
            best_zone = z

    return {
        "zone": best_zone,
        "distance_nm": round(min_dist, 2),
        "inside_zone": min_dist <= (best_zone["radius_nm"] if best_zone else 0.0),
    }
