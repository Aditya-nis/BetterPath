import random
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from .distance_calculator import calculate_tour_distance


class GeneticAlgorithmTSP:
    """
    Genetic Algorithm for solving the Travelling Salesman Problem (TSP).
    
    Configuration:
    - Population size: default 100
    - Maximum generations: default 300
    - Mutation probability: default 0.05
    - Selection method: Tournament Selection
    - Crossover method: Ordered Crossover (OX1)
    - Mutation method: Swap Mutation
    - Elitism: Enabled
    """

    def __init__(
        self,
        distance_matrix: np.ndarray,
        population_size: int = 100,
        generations: int = 300,
        mutation_rate: float = 0.05,
        crossover_rate: float = 0.90,
        tournament_size: int = 5,
        elitism_count: int = 2,
        early_stopping_generations: Optional[int] = None,
        seed: Optional[int] = None
    ):
        self.dist_matrix = distance_matrix
        self.num_cities = distance_matrix.shape[0]
        self.pop_size = max(10, population_size)
        self.generations = max(10, generations)
        self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        self.crossover_rate = max(0.1, min(1.0, crossover_rate))
        self.tournament_size = max(2, min(tournament_size, self.pop_size))
        self.elitism_count = max(1, min(elitism_count, self.pop_size // 2))
        self.early_stopping_generations = early_stopping_generations
        self.seed = seed

        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)

    def _calculate_distance(self, chromosome: List[int]) -> float:
        """Calculate total tour distance: start at 0, visit chromosome, return to 0."""
        tour = [0] + chromosome + [0]
        return calculate_tour_distance(tour, self.dist_matrix)

    def _generate_nearest_neighbor(self) -> List[int]:
        """Greedy heuristic to construct a valid starting permutation."""
        unvisited = set(range(1, self.num_cities))
        current = 0
        route = []
        while unvisited:
            next_city = min(unvisited, key=lambda c: self.dist_matrix[current, c])
            route.append(next_city)
            unvisited.remove(next_city)
            current = next_city
        return route

    def _initialize_population(self, baseline_chromosome: List[int]) -> List[List[int]]:
        """
        Creates initial population ensuring diversity and baseline inclusion.
        Start city (index 0) is excluded from chromosome representation.
        """
        population: List[List[int]] = []

        # 1. Guarantee baseline chromosome is present
        population.append(list(baseline_chromosome))

        # 2. Add Nearest Neighbor greedy candidate if applicable
        if self.num_cities > 2:
            nn_cand = self._generate_nearest_neighbor()
            if nn_cand not in population:
                population.append(nn_cand)

        # 3. Fill the rest with random permutations
        base_indices = list(range(1, self.num_cities))
        while len(population) < self.pop_size:
            ind = list(base_indices)
            random.shuffle(ind)
            population.append(ind)

        return population

    def _tournament_selection(self, population: List[List[int]], scores: List[float]) -> List[int]:
        """Tournament selection: randomly choose k individuals, pick the one with lowest distance."""
        selected_indices = random.sample(range(len(population)), self.tournament_size)
        best_idx = min(selected_indices, key=lambda idx: scores[idx])
        return list(population[best_idx])

    @staticmethod
    def _ordered_crossover(parent1: List[int], parent2: List[int]) -> List[int]:
        """
        Ordered Crossover (OX1):
        Preserves relative ordering and guarantees valid TSP permutation without duplicates.
        """
        size = len(parent1)
        if size <= 1:
            return list(parent1)

        idx1, idx2 = sorted(random.sample(range(size), 2))

        # Copy slice from parent1
        child: List[Optional[int]] = [None] * size
        child[idx1:idx2] = parent1[idx1:idx2]
        copied_set = set(parent1[idx1:idx2])

        # Fill remaining spots from parent2 starting from idx2 wrapping around
        p2_order = parent2[idx2:] + parent2[:idx2]
        fill_items = [item for item in p2_order if item not in copied_set]

        target_positions = list(range(idx2, size)) + list(range(0, idx1))
        for pos, item in zip(target_positions, fill_items):
            child[pos] = item

        return [x for x in child if x is not None]

    def _swap_mutation(self, chromosome: List[int]) -> List[int]:
        """Swap Mutation: with probability mutation_rate, swap two genes."""
        mutated = list(chromosome)
        if len(mutated) < 2:
            return mutated

        if random.random() < self.mutation_rate:
            i, j = random.sample(range(len(mutated)), 2)
            mutated[i], mutated[j] = mutated[j], mutated[i]

        return mutated

    def run(self, baseline_order: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Executes the Genetic Algorithm and tracks convergence history.
        """
        start_time = time.perf_counter()

        # Build baseline permutation (cities 1..N-1)
        if baseline_order is not None and len(baseline_order) == self.num_cities:
            baseline_chrom = [idx for idx in baseline_order if idx != 0]
        else:
            baseline_chrom = list(range(1, self.num_cities))

        baseline_dist = self._calculate_distance(baseline_chrom)

        # Handle trivial case (e.g. 2 or 3 cities total)
        if self.num_cities <= 2:
            exec_time = round(time.perf_counter() - start_time, 4)
            return {
                'best_tour': [0] + baseline_chrom + [0],
                'best_distance': baseline_dist,
                'baseline_tour': [0] + baseline_chrom + [0],
                'baseline_distance': baseline_dist,
                'convergence_history': [{'generation': 1, 'best_distance': baseline_dist}],
                'generations_run': 1,
                'execution_time': exec_time,
            }

        population = self._initialize_population(baseline_chrom)
        best_so_far_chrom = list(baseline_chrom)
        best_so_far_dist = baseline_dist
        convergence_history: List[Dict[str, float]] = []
        gens_without_improvement = 0
        actual_gens_run = 0

        # Generational loop
        for gen in range(1, self.generations + 1):
            actual_gens_run = gen
            # Evaluate fitness (distance) for each individual
            scores = [self._calculate_distance(ind) for ind in population]

            # Rank population
            ranked_pairs = sorted(zip(population, scores), key=lambda x: x[1])
            gen_best_chrom, gen_best_dist = ranked_pairs[0]

            # Update best-so-far
            if gen_best_dist < best_so_far_dist - 1e-6:
                best_so_far_dist = gen_best_dist
                best_so_far_chrom = list(gen_best_chrom)
                gens_without_improvement = 0
            else:
                gens_without_improvement += 1

            # Record convergence stats
            convergence_history.append({
                'generation': gen,
                'best_distance': round(best_so_far_dist, 2),
                'current_gen_best': round(gen_best_dist, 2),
                'average_distance': round(float(np.mean(scores)), 2)
            })

            # Check early stopping condition if configured
            if (self.early_stopping_generations is not None and 
                self.early_stopping_generations > 0 and 
                gens_without_improvement >= self.early_stopping_generations):
                break

            # Elitism: preserve top individuals
            new_population: List[List[int]] = [list(ind) for ind, _ in ranked_pairs[:self.elitism_count]]

            # Reproduction
            while len(new_population) < self.pop_size:
                p1 = self._tournament_selection(population, scores)
                p2 = self._tournament_selection(population, scores)
                if random.random() < self.crossover_rate:
                    child = self._ordered_crossover(p1, p2)
                else:
                    child = list(p1)
                child = self._swap_mutation(child)
                new_population.append(child)

            population = new_population

        # Final evaluation
        final_scores = [self._calculate_distance(ind) for ind in population]
        for ind, score in zip(population, final_scores):
            if score < best_so_far_dist:
                best_so_far_dist = score
                best_so_far_chrom = list(ind)

        # Enforce property: Result is never worse than baseline
        if best_so_far_dist > baseline_dist:
            best_so_far_chrom = list(baseline_chrom)
            best_so_far_dist = baseline_dist

        exec_time = round(time.perf_counter() - start_time, 4)

        return {
            'best_tour': [0] + best_so_far_chrom + [0],
            'best_distance': round(best_so_far_dist, 2),
            'baseline_tour': [0] + baseline_chrom + [0],
            'baseline_distance': round(baseline_dist, 2),
            'convergence_history': convergence_history,
            'generations_run': actual_gens_run,
            'execution_time': exec_time,
        }
