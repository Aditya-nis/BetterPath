import time
import numpy as np
from typing import List, Dict, Any
from .distance_calculator import calculate_tour_distance


def solve_tsp_nearest_neighbor(distance_matrix: np.ndarray, start_idx: int = 0) -> Dict[str, Any]:
    """
    Greedy Nearest Neighbor heuristic for the Travelling Salesman Problem.
    Constructs a tour by iteratively visiting the closest unvisited city.
    
    Time Complexity: O(N^2)
    Space Complexity: O(N)
    
    Returns:
        Dict containing:
        - 'best_tour': list of city indices forming the closed loop [0, ..., 0]
        - 'best_distance': total tour distance in km
        - 'execution_time': time taken in seconds
        - 'algorithm_name': 'Nearest Neighbor'
    """
    start_time = time.perf_counter()
    n = distance_matrix.shape[0]
    
    if n < 2:
        return {
            'best_tour': [0, 0] if n == 1 else [],
            'best_distance': 0.0,
            'execution_time': 0.0,
            'algorithm_name': 'Nearest Neighbor'
        }

    unvisited = set(range(n))
    unvisited.remove(start_idx)
    tour = [start_idx]
    current = start_idx

    while unvisited:
        next_city = min(unvisited, key=lambda city: distance_matrix[current, city])
        tour.append(next_city)
        unvisited.remove(next_city)
        current = next_city

    # Close the cycle back to start
    tour.append(start_idx)
    total_distance = calculate_tour_distance(tour, distance_matrix)
    exec_time = round(time.perf_counter() - start_time, 5)

    return {
        'best_tour': tour,
        'best_distance': round(total_distance, 2),
        'execution_time': exec_time,
        'algorithm_name': 'Nearest Neighbor',
        'is_exact': False
    }
