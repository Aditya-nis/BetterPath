import itertools
import time
import numpy as np
from typing import List, Dict, Any, Optional
from .distance_calculator import calculate_tour_distance

MAX_BRUTE_FORCE_CITIES = 9

def solve_tsp_brute_force(distance_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Computes mathematically proven exact optimal TSP route by evaluating
    all (N-1)! permutations of the intermediate cities.
    Supported up to MAX_BRUTE_FORCE_CITIES (9 cities -> 8! = 40,320 permutations).
    """
    n = distance_matrix.shape[0]
    if n > MAX_BRUTE_FORCE_CITIES:
        return {
            'supported': False,
            'message': f"Brute force exact search is restricted to <= {MAX_BRUTE_FORCE_CITIES} cities "
                       f"due to O(N!) combinatorial explosion. For {n} cities, search space is ({n}-1)! "
                       f"= {math_factorial(n-1):,} permutations."
        }

    start_time = time.perf_counter()
    other_cities = list(range(1, n))
    best_dist = float('inf')
    best_tour: Optional[List[int]] = None
    evaluated_permutations = 0

    for perm in itertools.permutations(other_cities):
        tour = [0] + list(perm) + [0]
        dist = calculate_tour_distance(tour, distance_matrix)
        evaluated_permutations += 1
        if dist < best_dist:
            best_dist = dist
            best_tour = tour

    exec_time = round(time.perf_counter() - start_time, 4)

    return {
        'supported': True,
        'best_tour': best_tour,
        'best_distance': round(best_dist, 2),
        'evaluated_permutations': evaluated_permutations,
        'execution_time': exec_time,
        'is_proven_optimal': True
    }


def math_factorial(n: int) -> int:
    import math
    return math.factorial(n)
