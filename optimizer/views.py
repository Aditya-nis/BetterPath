import json
import csv
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.db.models import Avg, Sum, Count, Min, Max

from .models import City, OptimizationRun
from .forms import CityForm
from .services.distance_calculator import build_haversine_matrix, calculate_tour_distance
from .services.routing_service import get_road_distance_matrix, get_road_route_geometry
from .services.genetic_algorithm import GeneticAlgorithmTSP
from .services.brute_force import solve_tsp_brute_force

logger = logging.getLogger(__name__)

PRESET_DATASETS = {
    "maharashtra_8": {
        "id": "maharashtra_8",
        "title": "Maharashtra Core (8 Cities)",
        "region": "Maharashtra",
        "cities": [
            {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "Nashik", "lat": 19.9975, "lng": 73.7898},
            {"name": "Chhatrapati Sambhajinagar", "lat": 19.8762, "lng": 75.3433},
            {"name": "Kolhapur", "lat": 16.7050, "lng": 74.2433},
            {"name": "Satara", "lat": 17.6805, "lng": 74.0183},
            {"name": "Solapur", "lat": 17.6599, "lng": 75.9064},
            {"name": "Nagpur", "lat": 21.1458, "lng": 79.0882},
        ]
    },
    "maharashtra_16": {
        "id": "maharashtra_16",
        "title": "Maharashtra Grand Tour (16 Cities)",
        "region": "Maharashtra",
        "cities": [
            {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "Thane", "lat": 19.2183, "lng": 72.9781},
            {"name": "Navi Mumbai", "lat": 19.0330, "lng": 73.0297},
            {"name": "Nashik", "lat": 19.9975, "lng": 73.7898},
            {"name": "Dhule", "lat": 20.9042, "lng": 74.7749},
            {"name": "Jalgaon", "lat": 21.0077, "lng": 75.5626},
            {"name": "Chhatrapati Sambhajinagar", "lat": 19.8762, "lng": 75.3433},
            {"name": "Ahmednagar", "lat": 19.0948, "lng": 74.7480},
            {"name": "Satara", "lat": 17.6805, "lng": 74.0183},
            {"name": "Sangli", "lat": 16.8524, "lng": 74.5815},
            {"name": "Kolhapur", "lat": 16.7050, "lng": 74.2433},
            {"name": "Solapur", "lat": 17.6599, "lng": 75.9064},
            {"name": "Nanded", "lat": 19.1383, "lng": 77.3210},
            {"name": "Amravati", "lat": 20.9320, "lng": 77.7523},
            {"name": "Nagpur", "lat": 21.1458, "lng": 79.0882},
        ]
    },
    "india_metros_10": {
        "id": "india_metros_10",
        "title": "Top Indian Metros (10 Cities)",
        "region": "India",
        "cities": [
            {"name": "New Delhi", "lat": 28.6139, "lng": 77.2090},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "Bengaluru", "lat": 12.9716, "lng": 77.5946},
            {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867},
            {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
            {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
            {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714},
            {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
            {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873},
            {"name": "Surat", "lat": 21.1702, "lng": 72.8311},
        ]
    },
    "india_grand_20": {
        "id": "india_grand_20",
        "title": "Pan-India Grand Tour (20 Cities)",
        "region": "India",
        "cities": [
            {"name": "New Delhi", "lat": 28.6139, "lng": 77.2090},
            {"name": "Chandigarh", "lat": 30.7333, "lng": 76.7794},
            {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873},
            {"name": "Agra", "lat": 27.1767, "lng": 78.0081},
            {"name": "Lucknow", "lat": 26.8467, "lng": 80.9462},
            {"name": "Varanasi", "lat": 25.3176, "lng": 82.9739},
            {"name": "Patna", "lat": 25.5941, "lng": 85.1376},
            {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
            {"name": "Bhubaneswar", "lat": 20.2961, "lng": 85.8245},
            {"name": "Visakhapatnam", "lat": 17.6868, "lng": 83.2185},
            {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
            {"name": "Bengaluru", "lat": 12.9716, "lng": 77.5946},
            {"name": "Kochi", "lat": 9.9312, "lng": 76.2673},
            {"name": "Goa (Panaji)", "lat": 15.4909, "lng": 73.8278},
            {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "Ahmedabad", "lat": 23.0225, "lng": 72.5714},
            {"name": "Indore", "lat": 22.7196, "lng": 75.8577},
            {"name": "Bhopal", "lat": 23.2599, "lng": 77.4126},
            {"name": "Nagpur", "lat": 21.1458, "lng": 79.0882},
        ]
    },
    "north_india_8": {
        "id": "north_india_8",
        "title": "North India Heritage (8 Cities)",
        "region": "India",
        "cities": [
            {"name": "New Delhi", "lat": 28.6139, "lng": 77.2090},
            {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873},
            {"name": "Agra", "lat": 27.1767, "lng": 78.0081},
            {"name": "Gwalior", "lat": 26.2183, "lng": 78.1828},
            {"name": "Lucknow", "lat": 26.8467, "lng": 80.9462},
            {"name": "Varanasi", "lat": 25.3176, "lng": 82.9739},
            {"name": "Dehradun", "lat": 30.3165, "lng": 78.0322},
            {"name": "Chandigarh", "lat": 30.7333, "lng": 76.7794},
        ]
    },
    "south_india_8": {
        "id": "south_india_8",
        "title": "South India Tech & Coastal (8 Cities)",
        "region": "India",
        "cities": [
            {"name": "Bengaluru", "lat": 12.9716, "lng": 77.5946},
            {"name": "Mysuru", "lat": 12.2958, "lng": 76.6394},
            {"name": "Coimbatore", "lat": 11.0168, "lng": 76.9558},
            {"name": "Kochi", "lat": 9.9312, "lng": 76.2673},
            {"name": "Madurai", "lat": 9.9252, "lng": 78.1198},
            {"name": "Tiruchirappalli", "lat": 10.7905, "lng": 78.7047},
            {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
            {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867},
        ]
    },
    "world_capitals_10": {
        "id": "world_capitals_10",
        "title": "Global Megacities (10 Cities)",
        "region": "Global",
        "cities": [
            {"name": "London", "lat": 51.5074, "lng": -0.1278},
            {"name": "Paris", "lat": 48.8566, "lng": 2.3522},
            {"name": "Berlin", "lat": 52.5200, "lng": 13.4050},
            {"name": "Rome", "lat": 41.9028, "lng": 12.4964},
            {"name": "Dubai", "lat": 25.2048, "lng": 55.2708},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "Singapore", "lat": 1.3521, "lng": 103.8198},
            {"name": "Tokyo", "lat": 35.6762, "lng": 139.6503},
            {"name": "Sydney", "lat": -33.8688, "lng": 151.2093},
            {"name": "New York", "lat": 40.7128, "lng": -74.0060},
        ]
    }
}

PRESET_CITIES = PRESET_DATASETS["maharashtra_8"]["cities"]


def _ensure_preset_cities():
    """Ensure all sample datasets exist in database."""
    for dataset_key, dataset in PRESET_DATASETS.items():
        for c in dataset["cities"]:
            City.objects.get_or_create(
                name=c["name"],
                defaults={
                    "latitude": c["lat"],
                    "longitude": c["lng"],
                    "is_preset": True
                }
            )



@ensure_csrf_cookie
def dashboard_view(request):
    """Home Dashboard view with summary metrics and quick launch."""
    _ensure_preset_cities()
    runs = OptimizationRun.objects.all()
    total_runs = runs.count()
    
    stats = {
        'total_runs': total_runs,
        'avg_improvement': round(runs.aggregate(avg=Avg('improvement_percentage'))['avg'] or 0.0, 2),
        'total_km_saved': round(runs.aggregate(total=Sum('distance_saved'))['total'] or 0.0, 2),
        'best_improvement': round(runs.aggregate(best=Max('improvement_percentage'))['best'] or 0.0, 2),
        'total_cities_in_db': City.objects.count(),
    }
    
    recent_runs = runs[:5]
    latest_run = runs.first()
    
    context = {
        'stats': stats,
        'recent_runs': recent_runs,
        'latest_run': latest_run,
        'preset_cities': PRESET_CITIES,
    }
    return render(request, 'optimizer/dashboard.html', context)


@ensure_csrf_cookie
def optimizer_view(request):
    """Main Route Optimizer interactive view."""
    _ensure_preset_cities()
    all_cities = City.objects.all().order_by('name')
    return render(request, 'optimizer/optimize.html', {
        'cities': all_cities,
        'preset_cities': PRESET_CITIES,
        'preset_datasets': PRESET_DATASETS,
    })


def history_view(request):
    """Optimization History list view."""
    runs = OptimizationRun.objects.all()
    return render(request, 'optimizer/history.html', {'runs': runs})


def about_view(request):
    """About Project theoretical and architecture documentation."""
    return render(request, 'optimizer/about.html')


# ==========================================
# JSON API ENDPOINTS
# ==========================================

def api_get_cities(request):
    """Returns list of all cities and dataset groups."""
    _ensure_preset_cities()
    cities = [c.to_dict() for c in City.objects.all().order_by('name')]
    return JsonResponse({
        'success': True,
        'cities': cities,
        'presets': PRESET_CITIES,
        'preset_datasets': PRESET_DATASETS,
    })


def api_get_presets(request):
    """Returns all curated preset dataset configurations."""
    return JsonResponse({
        'success': True,
        'presets': PRESET_DATASETS
    })


def api_geocode_city(request):
    """
    Search for a city by query string.
    1. Checks local database first (case-insensitive substring match).
    2. Fallbacks to OpenStreetMap Nominatim geocoding service.
    3. Returns list of matching city candidates with name, lat, lng.
    """
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'success': True, 'results': []})

    results = []
    # 1. Local database search
    db_matches = City.objects.filter(name__icontains=query).order_by('name')[:8]
    for c in db_matches:
        results.append({
            'name': c.name,
            'lat': float(c.latitude),
            'lng': float(c.longitude),
            'source': 'Database'
        })

    # 2. OpenStreetMap Nominatim search if needed
    if len(results) < 5:
        try:
            import urllib.request
            import urllib.parse
            encoded = urllib.parse.quote(query)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=6&addressdetails=1"
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'AITSPRouteOptimizer/1.0 (University-AI-Microproject)'}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for item in data:
                    display_name = item.get('display_name', '')
                    parts = [p.strip() for p in display_name.split(',')]
                    short_name = parts[0]
                    label = f"{short_name}, {parts[-1]}" if len(parts) > 1 else short_name
                    
                    if not any(r['name'].lower() == label.lower() or r['name'].lower() == short_name.lower() for r in results):
                        results.append({
                            'name': label,
                            'lat': float(item['lat']),
                            'lng': float(item['lon']),
                            'source': 'OpenStreetMap'
                        })
        except Exception as e:
            logger.warning(f"Geocoding service note: {e}")

    return JsonResponse({'success': True, 'results': results})


@csrf_exempt
def api_add_city(request):
    """Adds a new custom city with coordinate validation or updates existing."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    name = str(data.get('name', '')).strip()
    try:
        lat = float(data.get('latitude', data.get('lat', 0.0)))
        lng = float(data.get('longitude', data.get('lng', 0.0)))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid latitude or longitude numbers.'}, status=400)

    if not name:
        return JsonResponse({'success': False, 'error': 'City name cannot be empty.'}, status=400)
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return JsonResponse({'success': False, 'error': 'Coordinates out of bounds (-90 to 90 lat, -180 to 180 lng).'}, status=400)

    city, created = City.objects.get_or_create(
        name=name,
        defaults={'latitude': lat, 'longitude': lng, 'is_preset': False}
    )
    if not created:
        city.latitude = lat
        city.longitude = lng
        city.save()

    return JsonResponse({
        'success': True,
        'city': city.to_dict(),
        'message': f"City '{city.name}' saved successfully."
    })



@csrf_exempt
def api_reset_cities(request):
    """Resets database cities back to default sample dataset."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    City.objects.filter(is_preset=False).delete()
    for c in PRESET_CITIES:
        City.objects.get_or_create(
            name=c['name'],
            defaults={'latitude': c['lat'], 'longitude': c['lng'], 'is_preset': True}
        )
    return JsonResponse({
        'success': True,
        'message': 'Sample cities reset successfully.',
        'cities': [c.to_dict() for c in City.objects.all()]
    })


@csrf_exempt
def api_optimize(request):
    """
    Main Route Optimization API.
    Runs Genetic Algorithm on selected cities and returns verified results.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)

    try:
        payload = json.loads(request.body)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Invalid JSON payload: {str(e)}'}, status=400)

    # 1. Validation
    raw_cities = payload.get('cities', [])
    if not isinstance(raw_cities, list) or len(raw_cities) < 3:
        return JsonResponse({
            'success': False,
            'error': 'At least 3 distinct cities are required for route optimization.'
        }, status=400)

    # Validate each city structure
    cleaned_cities = []
    seen_names = set()
    for c in raw_cities:
        name = str(c.get('name', '')).strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Every city must have a valid name.'}, status=400)
        if name in seen_names:
            continue  # ignore duplicates
        seen_names.add(name)
        try:
            lat = float(c.get('lat', 0.0))
            lng = float(c.get('lng', 0.0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': f'Invalid coordinates for {name}.'}, status=400)
        
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
            return JsonResponse({'success': False, 'error': f'Coordinates out of bounds for {name}.'}, status=400)
        
        cleaned_cities.append({'name': name, 'lat': lat, 'lng': lng})

    if len(cleaned_cities) < 3:
        return JsonResponse({
            'success': False,
            'error': 'At least 3 distinct unique cities are required.'
        }, status=400)

    # Starting city selection
    starting_city_name = payload.get('starting_city', '').strip()
    start_city_idx = 0
    if starting_city_name:
        for idx, c in enumerate(cleaned_cities):
            if c['name'].lower() == starting_city_name.lower():
                start_city_idx = idx
                break

    # Rearrange cities so starting city is index 0
    selected_cities = [cleaned_cities[start_city_idx]] + [
        c for i, c in enumerate(cleaned_cities) if i != start_city_idx
    ]
    start_city_name = selected_cities[0]['name']

    # Algorithm configuration parameters
    pop_size = int(payload.get('population_size', 100))
    generations = int(payload.get('generations', 300))
    mutation_rate = float(payload.get('mutation_rate', 0.05))
    tournament_size = int(payload.get('tournament_size', 5))
    elitism_count = int(payload.get('elitism_count', 2))
    seed_val = payload.get('seed')
    seed = int(seed_val) if seed_val not in (None, '', 'null') else None
    
    distance_mode = payload.get('distance_mode', 'geographic')
    verify_brute_force = bool(payload.get('verify_brute_force', False))

    # 2. Build Distance Matrix
    is_road_mode = False
    fallback_reason = None
    if distance_mode == 'road':
        dist_matrix, is_road_mode, fallback_reason = get_road_distance_matrix(selected_cities)
    else:
        dist_matrix = build_haversine_matrix(selected_cities)

    # 3. Baseline Route (Natural order: 0 -> 1 -> 2 -> ... -> N-1 -> 0)
    num_cities = len(selected_cities)
    baseline_tour_indices = list(range(num_cities)) + [0]
    initial_distance = calculate_tour_distance(baseline_tour_indices, dist_matrix)
    initial_route_cities = [selected_cities[idx] for idx in baseline_tour_indices]

    # 4. Run Genetic Algorithm
    ga = GeneticAlgorithmTSP(
        distance_matrix=dist_matrix,
        population_size=pop_size,
        generations=generations,
        mutation_rate=mutation_rate,
        tournament_size=tournament_size,
        elitism_count=elitism_count,
        seed=seed
    )
    ga_results = ga.run(baseline_order=list(range(num_cities)))

    best_tour_indices = ga_results['best_tour']
    optimized_distance = ga_results['best_distance']
    optimized_route_cities = [selected_cities[idx] for idx in best_tour_indices]

    # Guarantee distance saved and improvement percentage
    distance_saved = round(max(0.0, initial_distance - optimized_distance), 2)
    if initial_distance > 0:
        improvement_pct = round((distance_saved / initial_distance) * 100.0, 2)
    else:
        improvement_pct = 0.0

    # 5. Optional Brute Force Verification for small datasets (<= 9 cities)
    brute_force_data = None
    if verify_brute_force and num_cities <= 9:
        bf_res = solve_tsp_brute_force(dist_matrix)
        if bf_res.get('supported'):
            bf_indices = bf_res['best_tour']
            bf_route_cities = [selected_cities[idx] for idx in bf_indices]
            brute_force_data = {
                'verified': True,
                'distance': bf_res['best_distance'],
                'tour_cities': bf_route_cities,
                'execution_time': bf_res['execution_time'],
                'permutations_evaluated': bf_res['evaluated_permutations'],
                'ga_matches_optimal': abs(optimized_distance - bf_res['best_distance']) < 0.05
            }
    elif verify_brute_force and num_cities > 9:
        brute_force_data = {
            'verified': False,
            'reason': f"Dataset has {num_cities} cities. Exact search requires ({num_cities}-1)! = "
                      f"{solve_tsp_brute_force(dist_matrix).get('message', '')}"
        }

    # 6. Road Geometry Polyline (if road mode is active and successful)
    route_geometry = None
    if is_road_mode:
        route_geometry = get_road_route_geometry(optimized_route_cities)

    # 7. Persist Optimization Run in SQLite DB
    run_record = OptimizationRun.objects.create(
        starting_city=start_city_name,
        selected_cities=selected_cities,
        initial_route=initial_route_cities,
        optimized_route=optimized_route_cities,
        initial_distance=round(initial_distance, 2),
        optimized_distance=round(optimized_distance, 2),
        distance_saved=distance_saved,
        improvement_percentage=improvement_pct,
        execution_time=ga_results['execution_time'],
        distance_mode='road' if is_road_mode else 'geographic',
        algorithm_parameters={
            'population_size': pop_size,
            'generations': generations,
            'mutation_rate': mutation_rate,
            'tournament_size': tournament_size,
            'elitism_count': elitism_count,
            'seed': seed,
            'city_count': num_cities
        },
        convergence_history=ga_results['convergence_history'],
        brute_force_verified=bool(brute_force_data and brute_force_data.get('verified')),
        brute_force_distance=brute_force_data.get('distance') if brute_force_data else None,
        brute_force_route=brute_force_data.get('tour_cities') if brute_force_data else None,
        route_geometry=route_geometry
    )

    return JsonResponse({
        'success': True,
        'run_id': run_record.id,
        'starting_city': start_city_name,
        'distance_mode': 'road' if is_road_mode else 'geographic',
        'is_road_mode': is_road_mode,
        'fallback_reason': fallback_reason,
        'initial_route': initial_route_cities,
        'initial_distance': round(initial_distance, 2),
        'optimized_route': optimized_route_cities,
        'optimized_distance': round(optimized_distance, 2),
        'distance_saved': distance_saved,
        'improvement_percentage': improvement_pct,
        'execution_time': ga_results['execution_time'],
        'generations_run': ga_results['generations_run'],
        'convergence_history': ga_results['convergence_history'],
        'brute_force': brute_force_data,
        'route_geometry': route_geometry,
        'created_at': run_record.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })


def api_get_history(request):
    """Returns list of recent optimization runs."""
    runs = OptimizationRun.objects.all()[:25]
    data = []
    for r in runs:
        data.append({
            'id': r.id,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'starting_city': r.starting_city,
            'city_count': len(r.selected_cities),
            'distance_mode': r.distance_mode,
            'initial_distance': r.initial_distance,
            'optimized_distance': r.optimized_distance,
            'distance_saved': r.distance_saved,
            'improvement_percentage': r.improvement_percentage,
            'execution_time': r.execution_time,
            'brute_force_verified': r.brute_force_verified,
        })
    return JsonResponse({'success': True, 'runs': data})


def api_get_run_detail(request, run_id):
    """Returns complete details of a specific optimization run."""
    run = get_object_or_404(OptimizationRun, id=run_id)
    return JsonResponse({
        'success': True,
        'run_id': run.id,
        'created_at': run.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'starting_city': run.starting_city,
        'distance_mode': run.distance_mode,
        'selected_cities': run.selected_cities,
        'initial_route': run.initial_route,
        'initial_distance': run.initial_distance,
        'optimized_route': run.optimized_route,
        'optimized_distance': run.optimized_distance,
        'distance_saved': run.distance_saved,
        'improvement_percentage': run.improvement_percentage,
        'execution_time': run.execution_time,
        'algorithm_parameters': run.algorithm_parameters,
        'convergence_history': run.convergence_history,
        'brute_force_verified': run.brute_force_verified,
        'brute_force_distance': run.brute_force_distance,
        'brute_force_route': run.brute_force_route,
        'route_geometry': run.route_geometry,
    })


def api_export_history_csv(request):
    """Exports all optimization runs as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tsp_optimization_history.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Run ID',
        'Date & Time',
        'Starting City',
        'City Count',
        'Distance Mode',
        'Initial Distance (km)',
        'Optimized Distance (km)',
        'Distance Saved (km)',
        'Improvement (%)',
        'Execution Time (s)',
        'Brute Force Verified',
        'Generations',
        'Population Size'
    ])

    for r in OptimizationRun.objects.all():
        params = r.algorithm_parameters or {}
        writer.writerow([
            r.id,
            r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            r.starting_city,
            len(r.selected_cities),
            r.distance_mode,
            r.initial_distance,
            r.optimized_distance,
            r.distance_saved,
            r.improvement_percentage,
            r.execution_time,
            'Yes' if r.brute_force_verified else 'No',
            params.get('generations', 300),
            params.get('population_size', 100),
        ])

    return response
