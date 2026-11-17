from typing import Dict, Any, Optional
from backend.detection.context.maritime_zones import find_nearest_maritime_zone


class MaritimeContextInterpreter:
    """
    Evaluates whether an observed anomaly is explained by normal maritime operations,
    such as designated anchorages, port waiting, pilotage, or fishing grounds.
    Maintains clean separation between raw behavioural model score and contextual state.
    """

    def interpret_loitering(
        self,
        lat: float,
        lon: float,
        dwell_duration_hours: float,
        vessel_type: str = "Cargo",
    ) -> Dict[str, Any]:
        match = find_nearest_maritime_zone(lat, lon)
        zone = match["zone"]
        dist_nm = match["distance_nm"]
        inside = match["inside_zone"]

        if not zone or dist_nm > 50.0:
            return {
                "contextual_state": "CONTEXT_UNAVAILABLE",
                "contextual_explanation": "No reference ports or designated anchorages within 50nm.",
                "zone_name": None,
                "is_benign_explanation": False,
            }

        if inside:
            if zone["type"] == "ANCHORAGE":
                return {
                    "contextual_state": "EXPECTED_CONTEXT",
                    "contextual_explanation": (
                        f"Dwell of {dwell_duration_hours:.1f}h occurs inside recognized anchorage "
                        f"'{zone['name']}' ({zone['region']}). Dwell is consistent with normal anchorage/waiting."
                    ),
                    "zone_name": zone["name"],
                    "is_benign_explanation": True,
                }
            elif zone["type"] == "PORT":
                return {
                    "contextual_state": "EXPECTED_CONTEXT",
                    "contextual_explanation": (
                        f"Dwell of {dwell_duration_hours:.1f}h occurs within {zone['name']} port limits. "
                        f"Consistent with berthing, cargo operations, or port congestion waiting."
                    ),
                    "zone_name": zone["name"],
                    "is_benign_explanation": True,
                }

        # Outside designated zones
        if vessel_type == "Fishing":
            return {
                "contextual_state": "POTENTIALLY_RELEVANT",
                "contextual_explanation": (
                    f"Low speed loitering/trawling {dist_nm:.1f}nm from {zone['name']}. "
                    "Vessel is registered as Fishing; likely active fishing operations rather than stationary loitering."
                ),
                "zone_name": zone["name"],
                "is_benign_explanation": True,
            }

        return {
            "contextual_state": "POTENTIALLY_RELEVANT",
            "contextual_explanation": (
                f"Stationary dwell of {dwell_duration_hours:.1f}h in open waters, "
                f"{dist_nm:.1f}nm away from the nearest anchorage/port ({zone['name']}). "
                "Unusual open-water loitering warrants review."
            ),
            "zone_name": zone["name"],
            "is_benign_explanation": False,
        }

    def interpret_rendezvous(
        self,
        lat: float,
        lon: float,
        duration_minutes: float,
        vessel_a_type: str = "Cargo",
        vessel_b_type: str = "Tug",
    ) -> Dict[str, Any]:
        match = find_nearest_maritime_zone(lat, lon)
        zone = match["zone"]
        dist_nm = match["distance_nm"]
        inside = match["inside_zone"]

        if inside and zone and zone["type"] == "PORT":
            if "Tug" in (vessel_a_type, vessel_b_type) or "Pilot" in (vessel_a_type, vessel_b_type):
                return {
                    "contextual_state": "EXPECTED_CONTEXT",
                    "contextual_explanation": (
                        f"Close proximity ({duration_minutes:.0f}m) inside {zone['name']} involving a {vessel_b_type}. "
                        "Consistent with routine tug escort or pilot boarding operation."
                    ),
                    "zone_name": zone["name"],
                    "is_benign_explanation": True,
                }

        return {
            "contextual_state": "POTENTIALLY_RELEVANT",
            "contextual_explanation": (
                f"Close proximity rendezvous ({duration_minutes:.0f} min) occurred in open water, "
                f"{dist_nm:.1f}nm from nearest port ({zone['name'] if zone else 'N/A'}). "
                "Candidate ship-to-ship (STS) transfer or unclassified maritime encounter."
            ),
            "zone_name": zone["name"] if zone else None,
            "is_benign_explanation": False,
        }

    def interpret_route_deviation(
        self,
        corridor_deviation_nm: float,
        corridor_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if corridor_deviation_nm < 1.0:
            return {
                "contextual_state": "EXPECTED_CONTEXT",
                "contextual_explanation": "Vessel trajectory lies within normal fairway / traffic separation corridor width.",
                "zone_name": corridor_name,
                "is_benign_explanation": True,
            }
        return {
            "contextual_state": "POTENTIALLY_RELEVANT",
            "contextual_explanation": (
                f"Trajectory deviates {corridor_deviation_nm:.1f}nm from established corridor "
                f"({corridor_name or 'standard fairway'}). Non-standard detour observed."
            ),
            "zone_name": corridor_name,
            "is_benign_explanation": False,
        }
