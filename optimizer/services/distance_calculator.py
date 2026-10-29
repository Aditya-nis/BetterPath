import math
import numpy as np
from typing import List, Dict, Any, Tuple

EARTH_RADIUS_KM = 6371.0088  # Mean Earth radius in kilometers

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Result is returned in kilometers.
    """
    if math.isclose(lat1, lat2, abs_tol=1e-9) and math.isclose(lon1, lon2, abs_tol=1e-9):
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clip to avoid floating point precision issues outside [0, 1]
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(EARTH_RADIUS_KM * c, 4)


def build_haversine_matrix(cities: List[Dict[str, Any]]) -> np.ndarray:
    """
    Construct an N x N symmetric distance matrix for the given cities using Haversine formula.
    D[i][j] is the distance from city i to city j in kilometers.
    """
    n = len(cities)
    matrix = np.zeros((n, n), dtype=float)

    for i in range(n):
        lat_i, lng_i = float(cities[i]['lat']), float(cities[i]['lng'])
        for j in range(i + 1, n):
            lat_j, lng_j = float(cities[j]['lat']), float(cities[j]['lng'])
            dist = haversine_distance(lat_i, lng_i, lat_j, lng_j)
            matrix[i, j] = dist
            matrix[j, i] = dist  # Symmetric

    return matrix


def calculate_tour_distance(tour_indices: List[int], distance_matrix: np.ndarray) -> float:
    """
    Calculates the total round-trip distance of a tour.
    Expects tour_indices to form a cycle, e.g., [0, 2, 1, 3, 0].
    If the last element is not the start element, it automatically closes the cycle.
    """
    if len(tour_indices) < 2:
        return 0.0

    total = 0.0
    indices = list(tour_indices)
    if indices[0] != indices[-1]:
        indices.append(indices[0])

    for i in range(len(indices) - 1):
        from_idx = indices[i]
        to_idx = indices[i + 1]
        total += distance_matrix[from_idx, to_idx]

    return round(float(total), 4)
