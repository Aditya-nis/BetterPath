import json
import numpy as np
from django.test import TestCase, Client
from django.urls import reverse
from optimizer.models import City, OptimizationRun
from optimizer.services.distance_calculator import (
    haversine_distance,
    build_haversine_matrix,
    calculate_tour_distance,
)
from optimizer.services.genetic_algorithm import GeneticAlgorithmTSP
from optimizer.services.brute_force import solve_tsp_brute_force


class TSPTestSuite(TestCase):
    def setUp(self):
        self.client = Client()
        self.sample_cities = [
            {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "Nashik", "lat": 19.9975, "lng": 73.7898},
            {"name": "Satara", "lat": 17.6805, "lng": 74.0183},
            {"name": "Kolhapur", "lat": 16.7050, "lng": 74.2433},
        ]
        self.matrix = build_haversine_matrix(self.sample_cities)

    # 1. City selection validation
    def test_city_selection_validation(self):
        # Less than 3 cities should fail
        response = self.client.post(
            reverse('api_optimize'),
            data=json.dumps({
                'cities': [self.sample_cities[0], self.sample_cities[1]],
                'starting_city': 'Pune'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('At least 3 distinct cities', data['error'])

        # Invalid coordinates should fail
        response_invalid_coord = self.client.post(
            reverse('api_optimize'),
            data=json.dumps({
                'cities': [
                    {"name": "CityA", "lat": 105.0, "lng": 73.0}, # Lat > 90
                    {"name": "CityB", "lat": 19.0, "lng": 72.0},
                    {"name": "CityC", "lat": 20.0, "lng": 73.0},
                ],
                'starting_city': 'CityA'
            }),
            content_type='application/json'
        )
        self.assertEqual(response_invalid_coord.status_code, 400)

    # 2. Distance matrix symmetry in Haversine mode
    def test_distance_matrix_symmetry(self):
        n = len(self.sample_cities)
        for i in range(n):
            self.assertAlmostEqual(self.matrix[i, i], 0.0, places=4)
            for j in range(i + 1, n):
                self.assertAlmostEqual(self.matrix[i, j], self.matrix[j, i], places=4)
                self.assertGreater(self.matrix[i, j], 0.0)

    # 3. Correct route distance calculation
    def test_route_distance_calculation(self):
        # Known points: Pune and Mumbai
        pune_lat, pune_lng = 18.5204, 73.8567
        mumbai_lat, mumbai_lng = 19.0760, 72.8777
        dist_pm = haversine_distance(pune_lat, pune_lng, mumbai_lat, mumbai_lng)
        # Pune to Mumbai great-circle distance is approx 115-125 km
        self.assertTrue(110.0 <= dist_pm <= 130.0)

        # Simple 3-city cycle distance
        sub_cities = self.sample_cities[:3]
        sub_matrix = build_haversine_matrix(sub_cities)
        tour = [0, 1, 2, 0]
        expected_dist = (
            sub_matrix[0, 1] + sub_matrix[1, 2] + sub_matrix[2, 0]
        )
        actual_dist = calculate_tour_distance(tour, sub_matrix)
        self.assertAlmostEqual(expected_dist, actual_dist, places=2)

    # 4. Every city is visited exactly once in intermediate sequence
    def test_every_city_visited_exactly_once(self):
        ga = GeneticAlgorithmTSP(
            distance_matrix=self.matrix,
            population_size=40,
            generations=30,
            seed=42
        )
        result = ga.run()
        best_tour = result['best_tour']
        n = len(self.sample_cities)

        # Start and end must be the origin (0)
        self.assertEqual(best_tour[0], 0)
        self.assertEqual(best_tour[-1], 0)
        
        # Intermediate cities must contain each city 1..N-1 exactly once
        intermediate = best_tour[1:-1]
        self.assertEqual(len(intermediate), n - 1)
        self.assertEqual(set(intermediate), set(range(1, n)))

    # 5. Return to the starting city
    def test_return_to_starting_city(self):
        ga = GeneticAlgorithmTSP(
            distance_matrix=self.matrix,
            population_size=30,
            generations=20,
            seed=123
        )
        result = ga.run()
        best_tour = result['best_tour']
        self.assertEqual(best_tour[0], best_tour[-1])
        self.assertEqual(best_tour[0], 0)

    # 6. Genetic Algorithm returns valid routes
    def test_genetic_algorithm_valid_routes(self):
        ga = GeneticAlgorithmTSP(
            distance_matrix=self.matrix,
            population_size=50,
            generations=50,
            mutation_rate=0.08,
            tournament_size=4,
            elitism_count=2,
            seed=999
        )
        result = ga.run()
        self.assertIn('best_tour', result)
        self.assertIn('best_distance', result)
        self.assertIn('convergence_history', result)
        self.assertGreater(result['best_distance'], 0.0)
        self.assertEqual(len(result['convergence_history']), 50)

    # 7. Optimized route is no worse than the chosen initial baseline
    def test_optimized_route_no_worse_than_baseline(self):
        ga = GeneticAlgorithmTSP(
            distance_matrix=self.matrix,
            population_size=60,
            generations=60,
            seed=55
        )
        baseline_order = list(range(len(self.sample_cities)))
        result = ga.run(baseline_order=baseline_order)
        self.assertLessEqual(result['best_distance'], result['baseline_distance'])

    # 8. Correct percentage improvement calculation
    def test_improvement_percentage_calculation(self):
        initial = 1000.0
        optimized = 750.0
        saved = initial - optimized
        pct = (saved / initial) * 100.0
        self.assertEqual(pct, 25.0)

        # In API context
        response = self.client.post(
            reverse('api_optimize'),
            data=json.dumps({
                'cities': self.sample_cities,
                'starting_city': 'Pune',
                'population_size': 40,
                'generations': 40,
                'seed': 42
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        expected_saved = round(data['initial_distance'] - data['optimized_distance'], 2)
        self.assertAlmostEqual(data['distance_saved'], expected_saved, delta=0.05)
        expected_pct = round((expected_saved / data['initial_distance']) * 100.0, 2)
        self.assertAlmostEqual(data['improvement_percentage'], expected_pct, delta=0.05)

    # 9. API returns valid JSON
    def test_api_returns_valid_json(self):
        response = self.client.post(
            reverse('api_optimize'),
            data=json.dumps({
                'cities': self.sample_cities,
                'starting_city': 'Pune',
                'population_size': 30,
                'generations': 20
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('run_id', data)
        self.assertIn('optimized_route', data)
        self.assertIn('initial_distance', data)
        self.assertIn('optimized_distance', data)
        self.assertIn('convergence_history', data)

    # 10. Optimization history is saved correctly in SQLite
    def test_optimization_history_saved_correctly(self):
        initial_count = OptimizationRun.objects.count()
        response = self.client.post(
            reverse('api_optimize'),
            data=json.dumps({
                'cities': self.sample_cities,
                'starting_city': 'Pune',
                'population_size': 30,
                'generations': 20,
                'verify_brute_force': True
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check model persistence in database
        self.assertEqual(OptimizationRun.objects.count(), initial_count + 1)
        latest_run = OptimizationRun.objects.latest('id')
        self.assertEqual(latest_run.starting_city, 'Pune')
        self.assertEqual(len(latest_run.selected_cities), len(self.sample_cities))
        self.assertEqual(latest_run.optimized_distance, data['optimized_distance'])
        self.assertTrue(latest_run.brute_force_verified)
        self.assertIsNotNone(latest_run.brute_force_distance)

    # 11. Presets dataset endpoint returns all curated datasets
    def test_dataset_presets_api(self):
        response = self.client.get(reverse('api_presets'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        presets = data['presets']
        self.assertIn('maharashtra_8', presets)
        self.assertIn('maharashtra_16', presets)
        self.assertIn('india_metros_10', presets)
        self.assertIn('india_grand_20', presets)
        self.assertIn('world_capitals_10', presets)
        self.assertGreaterEqual(len(presets['maharashtra_16']['cities']), 16)
        self.assertGreaterEqual(len(presets['india_grand_20']['cities']), 20)

    # 12. City geocode and autocomplete search endpoint
    def test_geocode_search_api(self):
        # Create a known city in DB
        City.objects.get_or_create(name="Bengaluru", defaults={'latitude': 12.9716, 'longitude': 77.5946})
        response = self.client.get(reverse('api_geocode') + '?q=Bengal')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        names = [r['name'] for r in data['results']]
        self.assertTrue(any('Bengaluru' in name for name in names))

    # 13. Adding custom city via API with validation
    def test_api_add_city_success_and_validation(self):
        # Success case
        res_ok = self.client.post(
            reverse('api_add_city'),
            data=json.dumps({'name': 'Nagapattinam', 'latitude': 10.7656, 'longitude': 79.8427}),
            content_type='application/json'
        )
        self.assertEqual(res_ok.status_code, 200)
        data = res_ok.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['city']['name'], 'Nagapattinam')
        self.assertTrue(City.objects.filter(name='Nagapattinam').exists())

        # Validation error: out of bounds latitude
        res_err = self.client.post(
            reverse('api_add_city'),
            data=json.dumps({'name': 'InvalidCity', 'latitude': 99.0, 'longitude': 40.0}),
            content_type='application/json'
        )
        self.assertEqual(res_err.status_code, 400)
        self.assertFalse(res_err.json()['success'])

    # 14. Ensure preset cities seeding loads multi-region dataset
    def test_ensure_preset_cities_population(self):
        from optimizer.views import _ensure_preset_cities
        _ensure_preset_cities()
        total_cities = City.objects.count()
        self.assertGreaterEqual(total_cities, 30)

    # 15. Genetic algorithm runs correctly on larger tour (16 cities)
    def test_genetic_algorithm_on_larger_dataset(self):
        from optimizer.views import PRESET_DATASETS
        cities_16 = PRESET_DATASETS['maharashtra_16']['cities']
        matrix_16 = build_haversine_matrix(cities_16)
        
        ga = GeneticAlgorithmTSP(
            distance_matrix=matrix_16,
            population_size=60,
            generations=40,
            seed=77
        )
        result = ga.run()
        tour = result['best_tour']
        self.assertEqual(len(tour), 17) # 16 unique cities + origin return at end (N + 1)
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)
        self.assertEqual(len(set(tour[:-1])), 16) # All 16 unique cities visited exactly once

    # 16. Serverless WSGI entrypoint and WhiteNoise static asset delivery
    def test_vercel_wsgi_entrypoint_and_static_files(self):
        from api.index import app
        from django.test import RequestFactory
        factory = RequestFactory()
        
        # Test CSS static asset returns 200 OK
        env_css = factory.get('/static/optimizer/css/style.css').environ
        status_box = []
        headers_box = []
        def start_resp(status, headers):
            status_box.append(status)
            headers_box.append(dict(headers))
        
        app(env_css, start_resp)
        self.assertTrue(status_box[0].startswith('200'))
        content_type = headers_box[0].get('content-type', headers_box[0].get('Content-Type', ''))
        self.assertIn('text/css', content_type)
        
        # Test JS static asset returns 200 OK
        status_box.clear()
        headers_box.clear()
        env_js = factory.get('/static/optimizer/js/map.js').environ
        app(env_js, start_resp)
        self.assertTrue(status_box[0].startswith('200'))
        content_type_js = headers_box[0].get('content-type', headers_box[0].get('Content-Type', ''))
        self.assertIn('javascript', content_type_js)

    # 17. Nearest Neighbor Heuristic Solver
    def test_nearest_neighbor_solver(self):
        from optimizer.services.nearest_neighbor import solve_tsp_nearest_neighbor
        res = solve_tsp_nearest_neighbor(self.matrix, start_idx=0)
        self.assertEqual(res['algorithm_name'], 'Nearest Neighbor')
        tour = res['best_tour']
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)
        self.assertEqual(len(tour), len(self.sample_cities) + 1)
        self.assertEqual(len(set(tour[:-1])), len(self.sample_cities))
        self.assertGreater(res['best_distance'], 0.0)

    # 18. 2-Opt Local Search Heuristic Solver
    def test_two_opt_local_search(self):
        from optimizer.services.two_opt import solve_tsp_2opt
        res = solve_tsp_2opt(self.matrix)
        self.assertEqual(res['algorithm_name'], '2-Opt Local Search')
        tour = res['best_tour']
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)
        self.assertEqual(len(tour), len(self.sample_cities) + 1)
        self.assertEqual(len(set(tour[:-1])), len(self.sample_cities))
        self.assertGreater(res['best_distance'], 0.0)

    # 19. Multi-Algorithm Benchmark Comparison API
    def test_algorithm_benchmark_compare_api(self):
        response = self.client.post(
            reverse('api_compare_algorithms'),
            data=json.dumps({
                'cities': self.sample_cities,
                'starting_city': 'Pune',
                'distance_mode': 'geographic'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['city_count'], 5)
        self.assertTrue(data['proven_optimal'])
        algo_names = [r['algorithm_name'] for r in data['results']]
        self.assertIn('Baseline (Input Order)', algo_names)
        self.assertIn('Nearest Neighbor', algo_names)
        self.assertIn('2-Opt Local Search', algo_names)
        self.assertIn('Genetic Algorithm (OX1)', algo_names)
        self.assertIn('Brute Force (Exact)', algo_names)
        self.assertEqual(len(data['ranking']), 5)

    # 20. Route Itinerary JSON Export API with Watermark
    def test_run_json_export_endpoint(self):
        run = OptimizationRun.objects.create(
            starting_city='Pune',
            selected_cities=self.sample_cities,
            initial_route=self.sample_cities + [self.sample_cities[0]],
            optimized_route=self.sample_cities + [self.sample_cities[0]],
            initial_distance=1000.0,
            optimized_distance=850.0,
            distance_saved=150.0,
            improvement_percentage=15.0,
            execution_time=0.15,
            distance_mode='geographic',
            algorithm_parameters={'population_size': 100, 'generations': 200}
        )
        url = reverse('api_export_run_json', kwargs={'run_id': run.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])
        self.assertIn(f'betterpath_run_{run.id}_report.json', response['Content-Disposition'])
        
        data = json.loads(response.content)
        self.assertEqual(data['watermark'], "developed by Aditya Nisargandh's System")
        self.assertEqual(data['summary']['starting_hub'], 'Pune')
        self.assertEqual(len(data['route_itinerary']), 6) # 5 cities + return to origin

    # 21. Algorithm Lab Web Page View
    def test_algorithm_lab_page_view(self):
        response = self.client.get(reverse('algorithm_lab'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Multi-Algorithm TSP Benchmarking Workbench')
        self.assertContains(response, 'Maharashtra Core (8 Cities)')




