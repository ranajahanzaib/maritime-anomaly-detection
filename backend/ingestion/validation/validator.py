import math
import datetime
from typing import List, Dict, Any, Tuple
from backend.ingestion.normalization.schema import CanonicalAISPoint


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in nautical miles."""
    r_nm = 3440.065  # Earth radius in nautical miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_nm * c


class DataQualityValidator:
    def __init__(
        self,
        max_speed_knots: float = 55.0,
        max_acceleration_ms2: float = 4.0,
    ):
        self.max_speed_knots = max_speed_knots
        self.max_acceleration_ms2 = max_acceleration_ms2

    def validate_point(self, point: CanonicalAISPoint) -> Tuple[bool, List[str]]:
        reasons = []

        # Coordinate bounds
        if not (-90.0 <= point.latitude <= 90.0):
            reasons.append(f"Latitude {point.latitude} out of bounds [-90, 90]")
        if not (-180.0 <= point.longitude <= 180.0):
            reasons.append(f"Longitude {point.longitude} out of bounds [-180, 180]")
        if point.latitude == 0.0 and point.longitude == 0.0:
            reasons.append("Null Island coordinate (0, 0)")

        # Speed bounds
        if point.sog < 0.0 or point.sog > self.max_speed_knots:
            reasons.append(f"SOG {point.sog} knots out of plausible bounds [0, {self.max_speed_knots}]")

        # Course bounds
        if point.cog < 0.0 or point.cog > 360.0:
            reasons.append(f"COG {point.cog} out of bounds [0, 360]")

        # Heading bounds
        if point.heading is not None and (point.heading < 0.0 or point.heading > 360.0):
            reasons.append(f"Heading {point.heading} out of bounds [0, 360]")

        # Timestamp validity
        if point.timestamp.year < 1990 or point.timestamp.year > 2035:
            reasons.append(f"Suspicious timestamp year {point.timestamp.year}")

        # MMSI validity (standard 9-digit MMSI)
        if point.mmsi <= 0 or point.mmsi > 999999999:
            reasons.append(f"Invalid MMSI {point.mmsi}")

        is_valid = len(reasons) == 0
        return is_valid, reasons

    def validate_track_consistency(
        self, points: List[CanonicalAISPoint]
    ) -> Tuple[List[CanonicalAISPoint], Dict[str, Any]]:
        """
        Validates an ordered sequence of points for a single vessel:
        detects duplicates, out-of-order, impossible jumps.
        Does NOT drop points silently; marks them and records quality stats.
        """
        if not points:
            return [], {
                "total_points": 0,
                "valid_points": 0,
                "rejected_points": 0,
                "duplicates": 0,
                "speed_jumps": 0,
                "quality_score": 1.0,
            }

        # Sort chronologically
        sorted_points = sorted(points, key=lambda p: p.timestamp)

        duplicates = 0
        speed_jumps = 0
        point_rejections = 0
        validated = []
        last_valid: CanonicalAISPoint | None = None

        for i, pt in enumerate(sorted_points):
            is_valid, reasons = self.validate_point(pt)
            
            # Check duplicate timestamp
            if last_valid and pt.timestamp == last_valid.timestamp:
                duplicates += 1
                pt.is_valid = False
                reasons.append("Duplicate timestamp")

            # Check kinematic jump from last valid point
            if is_valid and last_valid:
                dt_seconds = (pt.timestamp - last_valid.timestamp).total_seconds()
                if dt_seconds > 0:
                    dist_nm = haversine_distance_nm(
                        last_valid.latitude, last_valid.longitude,
                        pt.latitude, pt.longitude
                    )
                    implied_speed_knots = (dist_nm / dt_seconds) * 3600.0
                    
                    if implied_speed_knots > self.max_speed_knots:
                        speed_jumps += 1
                        pt.is_valid = False
                        reasons.append(
                            f"Implausible kinematic jump: implied speed {implied_speed_knots:.1f} kts > {self.max_speed_knots} kts"
                        )

            if not is_valid or reasons:
                pt.is_valid = False
                pt.rejection_reason = "; ".join(reasons)
                point_rejections += 1
            else:
                last_valid = pt

            validated.append(pt)

        total = len(sorted_points)
        valid_count = total - point_rejections
        quality_score = max(0.0, min(1.0, valid_count / total if total > 0 else 1.0))

        report = {
            "total_points": total,
            "valid_points": valid_count,
            "rejected_points": point_rejections,
            "duplicates": duplicates,
            "speed_jumps": speed_jumps,
            "quality_score": round(quality_score, 4),
        }

        return validated, report
