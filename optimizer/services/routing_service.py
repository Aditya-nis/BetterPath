import requests
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional
from .distance_calculator import build_haversine_matrix

logger = logging.getLogger(__name__)

# In-memory caches to avoid redundant external network requests
_ROAD_MATRIX_CACHE: Dict[str, np.ndarray] = {}
_ROAD_GEOMETRY_CACHE: Dict[str, List[List[float]]] = {}

OSRM_BASE_URL = "https://router.project-osrm.org"
OSRM_TIMEOUT_SECONDS = 6.0


def _cache_key_for_cities(cities: List[Dict[str, Any]]) -> str:
    return ";".join(f"{c['lat']:.5f},{c['lng']:.5f}" for c in cities)


def get_road_distance_matrix(cities: List[Dict[str, Any]]) -> Tuple[np.ndarray, bool, Optional[str]]:
    """
    Retrieves the road distance matrix using OSRM Table API.
    Returns:
        (distance_matrix, is_road_mode, fallback_reason)
    If OSRM fails or times out, safely falls back to Haversine matrix.
    """
    n = len(cities)
    if n < 2:
        return np.zeros((n, n)), True, None

    cache_key = _cache_key_for_cities(cities)
    if cache_key in _ROAD_MATRIX_CACHE:
        return _ROAD_MATRIX_CACHE[cache_key].copy(), True, None

    # OSRM expects: {longitude},{latitude};{longitude},{latitude}
    coords_param = ";".join(f"{c['lng']:.6f},{c['lat']:.6f}" for c in cities)
    table_url = f"{OSRM_BASE_URL}/table/v1/driving/{coords_param}?annotations=distance"

    try:
        response = requests.get(
            table_url,
            headers={"User-Agent": "AI-TSP-Optimizer-Project/1.0"},
            timeout=OSRM_TIMEOUT_SECONDS
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and "distances" in data:
                raw_distances = data["distances"]  # distances are in meters
                matrix = np.zeros((n, n), dtype=float)
                for i in range(n):
                    for j in range(n):
                        val = raw_distances[i][j]
                        if val is not None:
                            matrix[i, j] = round(val / 1000.0, 4)  # convert to km
                        else:
                            # Fallback for null pair
                            from .distance_calculator import haversine_distance
                            matrix[i, j] = haversine_distance(
                                cities[i]['lat'], cities[i]['lng'],
                                cities[j]['lat'], cities[j]['lng']
                            )
                _ROAD_MATRIX_CACHE[cache_key] = matrix
                return matrix, True, None
            else:
                reason = f"OSRM table response status: {data.get('code')}"
        else:
            reason = f"OSRM service returned HTTP {response.status_code}"
    except Exception as e:
        reason = f"OSRM request failed ({str(e)})"

    # Fallback to Haversine
    logger.warning("Falling back to Haversine distance: %s", reason)
    haversine_mat = build_haversine_matrix(cities)
    return haversine_mat, False, reason


def get_road_route_geometry(ordered_cities: List[Dict[str, Any]]) -> Optional[List[List[float]]]:
    """
    Fetches real road driving geometry (polyline coordinates [lat, lng])
    from OSRM for the ordered sequence of cities.
    Closes the loop back to the start city.
    """
    if len(ordered_cities) < 2:
        return None

    # Ensure closed loop
    tour = list(ordered_cities)
    if tour[0]['name'] != tour[-1]['name']:
        tour.append(tour[0])

    cache_key = "geom_" + _cache_key_for_cities(tour)
    if cache_key in _ROAD_GEOMETRY_CACHE:
        return _ROAD_GEOMETRY_CACHE[cache_key]

    # Max waypoints per request for public OSRM is typically 100, our TSP is 3-20
    coords_param = ";".join(f"{c['lng']:.6f},{c['lat']:.6f}" for c in tour)
    route_url = f"{OSRM_BASE_URL}/route/v1/driving/{coords_param}?overview=full&geometries=geojson"

    try:
        response = requests.get(
            route_url,
            headers={"User-Agent": "AI-TSP-Optimizer-Project/1.0"},
            timeout=OSRM_TIMEOUT_SECONDS
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and "routes" in data and len(data["routes"]) > 0:
                # GeoJSON coordinates are [lon, lat] -> convert to Leaflet [lat, lon]
                geojson_coords = data["routes"][0]["geometry"]["coordinates"]
                leaflet_coords = [[pt[1], pt[0]] for pt in geojson_coords]
                _ROAD_GEOMETRY_CACHE[cache_key] = leaflet_coords
                return leaflet_coords
    except Exception as e:
        logger.warning("Could not fetch OSRM road geometry: %s", e)

    return None
