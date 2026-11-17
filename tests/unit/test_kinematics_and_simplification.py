from backend.trajectories.kinematics import (
    haversine_distance_nm,
    calculate_bearing_deg,
    calculate_course_difference,
)
from backend.trajectories.simplification import rdp_simplify, simplify_geojson_linestring


def test_haversine_distance():
    # Dover to Calais (~18-20 NM)
    d = haversine_distance_nm(51.12, 1.32, 50.96, 1.85)
    assert 18.0 <= d <= 23.0


def test_bearing_calculation():
    # Due East
    b_east = calculate_bearing_deg(50.0, 1.0, 50.0, 2.0)
    assert 88.0 <= b_east <= 92.0

    # Due North
    b_north = calculate_bearing_deg(50.0, 1.0, 51.0, 1.0)
    assert abs(b_north - 0.0) < 1.0 or abs(b_north - 360.0) < 1.0


def test_course_difference():
    assert calculate_course_difference(10.0, 20.0) == 10.0
    assert calculate_course_difference(350.0, 10.0) == 20.0
    assert calculate_course_difference(0.0, 180.0) == 180.0


def test_rdp_simplification():
    # 5 collinear points should simplify down to start and end points
    coords = [(1.0, 50.0), (1.1, 50.1), (1.2, 50.2), (1.3, 50.3), (1.4, 50.4)]
    simplified = rdp_simplify(coords, tolerance=0.001)
    assert len(simplified) == 2
    assert simplified[0] == coords[0]
    assert simplified[-1] == coords[-1]
