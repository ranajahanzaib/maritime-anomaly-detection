import math
from typing import List, Tuple, Dict, Any


def perpendicular_distance(
    pt: Tuple[float, float], line_start: Tuple[float, float], line_end: Tuple[float, float]
) -> float:
    """Calculates perpendicular distance from point to line in degrees (approximate for simplification)."""
    x, y = pt[0], pt[1]
    x1, y1 = line_start[0], line_start[1]
    x2, y2 = line_end[0], line_end[1]

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)

    # Calculate the projection of the point onto the line segment
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return math.hypot(x - proj_x, y - proj_y)


def rdp_simplify(
    coords: List[Tuple[float, float]], tolerance: float = 0.0005
) -> List[Tuple[float, float]]:
    """
    Ramer-Douglas-Peucker trajectory simplification.
    coords is list of (lon, lat) tuples.
    """
    if len(coords) <= 2:
        return coords

    # Find point with maximum distance
    dmax = 0.0
    index = 0
    end = len(coords) - 1

    for i in range(1, end):
        d = perpendicular_distance(coords[i], coords[0], coords[end])
        if d > dmax:
            index = i
            dmax = d

    if dmax > tolerance:
        rec_results1 = rdp_simplify(coords[: index + 1], tolerance)
        rec_results2 = rdp_simplify(coords[index:], tolerance)
        return rec_results1[:-1] + rec_results2
    else:
        return [coords[0], coords[end]]


def simplify_geojson_linestring(
    points: List[Dict[str, Any]], tolerance: float = 0.0005
) -> Dict[str, Any]:
    """
    Converts a list of dicts with latitude/longitude to a simplified GeoJSON LineString.
    Returns GeoJSON feature geometry.
    """
    if not points:
        return {"type": "LineString", "coordinates": []}

    raw_coords = [(float(p["longitude"]), float(p["latitude"])) for p in points]
    simplified = rdp_simplify(raw_coords, tolerance=tolerance)

    return {
        "type": "LineString",
        "coordinates": [[round(c[0], 6), round(c[1], 6)] for c in simplified],
    }
