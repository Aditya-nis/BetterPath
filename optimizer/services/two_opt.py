import time
import numpy as np
from typing import List, Dict, Any, Optional
from .distance_calculator import calculate_tour_distance


def two_opt_swap(tour: List[int], i: int, k: int) -> List[int]:
    """
    Performs a 2-opt swap by reversing the tour segment between index i and k.
    tour[0..i-1] + reversed(tour[i..k]) + tour[k+1..end]
    """
    return tour[0:i] + tour[i:k + 1][::-1] + tour[k + 1:]


def solve_tsp_2opt(
    distance_matrix: np.ndarray,
    initial_tour: Optional[List[int]] = None,
    max_iterations: int = 500
) -> Dict[str, Any]:
    """
    2-Opt Local Search heuristic for Travelling Salesman Problem.
    Iteratively removes edge crossings by reversing tour segments until local optimum is reached.
    
    Time Complexity: O(iterations * N^2)
    Space Complexity: O(N)
    
    Returns:
        Dict containing:
        - 'best_tour': list of city indices forming the closed loop [0, ..., 0]
        - 'best_distance': total tour distance in km
        - 'swaps_performed': number of 2-opt segment reversals performed
        - 'iterations': number of full passes executed
        - 'execution_time': time taken in seconds
        - 'algorithm_name': '2-Opt Local Search'
        - 'is_exact': False
    """
    start_time = time.perf_counter()
    n = distance_matrix.shape[0]

    if n <= 2:
        tour = list(range(n)) + [0] if n > 0 else []
        dist = calculate_tour_distance(tour, distance_matrix) if tour else 0.0
        return {
            'best_tour': tour,
            'best_distance': round(dist, 2),
            'swaps_performed': 0,
            'iterations': 0,
            'execution_time': 0.0,
            'algorithm_name': '2-Opt Local Search',
            'is_exact': False
        }

    # Initialize tour if not provided (start at 0, visit all cities, return to 0)
    if initial_tour is not None and len(initial_tour) == n + 1:
        current_tour = list(initial_tour)
    else:
        current_tour = list(range(n)) + [0]

    current_dist = calculate_tour_distance(current_tour, distance_matrix)
    swaps_performed = 0
    iteration = 0
    improved = True

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # Check all possible pairs of edges to cut and reconnect
        # Tour is: current_tour[0] -> ... -> current_tour[n] where current_tour[0] == current_tour[n] == 0
        for i in range(1, n - 1):
            for k in range(i + 1, n):
                # Calculate delta in distance without full recalculation for speed
                # Current edges: (i-1 -> i) and (k -> k+1)
                # New edges: (i-1 -> k) and (i -> k+1)
                city_prev = current_tour[i - 1]
                city_i = current_tour[i]
                city_k = current_tour[k]
                city_next = current_tour[k + 1]

                current_edges_len = (
                    distance_matrix[city_prev, city_i] +
                    distance_matrix[city_k, city_next]
                )
                new_edges_len = (
                    distance_matrix[city_prev, city_k] +
                    distance_matrix[city_i, city_next]
                )

                if new_edges_len < current_edges_len - 1e-6:
                    current_tour = two_opt_swap(current_tour, i, k)
                    current_dist = calculate_tour_distance(current_tour, distance_matrix)
                    swaps_performed += 1
                    improved = True
                    break  # First-improvement strategy
            if improved:
                break

    exec_time = round(time.perf_counter() - start_time, 5)

    return {
        'best_tour': current_tour,
        'best_distance': round(current_dist, 2),
        'swaps_performed': swaps_performed,
        'iterations': iteration,
        'execution_time': exec_time,
        'algorithm_name': '2-Opt Local Search',
        'is_exact': False
    }
