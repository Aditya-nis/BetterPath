# AI-Based Route Optimization for Travelling Salesman Problem (TSP)

![Project Status](https://img.shields.io/badge/Status-Completed-success)
![Course](https://img.shields.io/badge/Course-Third%20Year%20Computer%20Engineering-blue)
![Subject](https://img.shields.io/badge/Subject-Artificial%20Intelligence%20(AI)-purple)
![Framework](https://img.shields.io/badge/Django-5.0+-green)
![Python](https://img.shields.io/badge/Python-3.11+-yellow)

A full-stack, responsive, and interactive web-based Artificial Intelligence microproject designed to solve the NP-hard **Travelling Salesman Problem (TSP)** using evolutionary **Genetic Algorithms (GA)**, great-circle **Haversine calculations**, and real **OSRM Road-Network routing**.

Built with a futuristic dark navy and electric cyan glassmorphism dashboard, interactive Leaflet.js maps, and real-time Chart.js convergence analytics.

---

## 🌟 Key Features

1. **Genetic Algorithm Engine**:
   - **Representation**: Permutation chromosome encoding with fixed origin/return hub.
   - **Selection**: Tournament Selection ($k=5$) to balance selection pressure and genetic diversity.
   - **Crossover**: Ordered Crossover (**OX1**) ensuring valid TSP cycle permutations without duplicates.
   - **Mutation**: Swap Mutation ($P_m = 0.05$) to break local minima traps.
   - **Elitism**: Top 2 elite individuals are preserved untouched across generations.
   - **Reproducibility**: Optional pseudo-random seed parameter.

2. **Dual Distance Modes**:
   - **Mode A: Geographic Distance**: Vectorized Haversine spherical trigonometric formula (in km).
   - **Mode B: Road Distance**: Live Open Source Routing Machine (**OSRM**) driving network with in-memory caching and graceful fallback.

3. **Mathematical Brute-Force Verification**:
   - Exact combinatorial solver for $\le 9$ cities to evaluate all $(N-1)!$ permutations.
   - Benchmarks whether the Genetic Algorithm heuristic discovers the exact global optimum.

4. **Modern UI/UX Dashboard (Glassmorphism 2.0)**:
   - **Dual Theme Support**: Interactive **Light Mode (Luminous Pearl)** and **Dark Mode (Deep Space Navy)** with 1-click persistent toggle.
   - **Google Places Live Autocomplete**: Search and auto-add any city, town, or landmark across India and globally.
   - **High-Resolution Map**:
     - **Red dashed line**: Initial baseline sequence.
     - **Green solid line**: AI-optimized route.
     - **Yellow pin**: Starting & return hub.
     - **Blue pins**: Intermediate waypoints.
   - Real-time Chart.js Convergence Curves and Distance Comparison bar charts (theme-adaptive).
   - Snapshot export as PNG and dataset export as CSV.
   - Persistent SQLite3 optimization run history.

5. **Docker Containerization**:
   - Multi-stage slim Docker image with automatic migrations and city seeding.
   - Ready for one-command deployment using `docker compose up --build`.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6), Bootstrap 5.3, Bootstrap Icons, Leaflet.js, Chart.js, html2canvas |
| **Backend** | Python 3, Django, Django ORM, RESTful JSON Endpoints |
| **Mathematical / AI** | NumPy, Pure Python Genetic Algorithm, Haversine Spherical Trigonometry, OSRM API |
| **Database** | SQLite3 (Persistent ORM) |

---

## 📁 Project Architecture

```text
AI_TSP_Web/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── optimizer/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    ├── management/
    │   └── commands/
    │       └── seed_cities.py
    ├── services/
    │   ├── __init__.py
    │   ├── distance_calculator.py
    │   ├── routing_service.py
    │   ├── genetic_algorithm.py
    │   └── brute_force.py
    ├── templates/
    │   └── optimizer/
    │       ├── base.html
    │       ├── dashboard.html
    │       ├── optimize.html
    │       ├── history.html
    │       └── about.html
    └── static/
        └── optimizer/
            ├── css/
            │   └── style.css
            └── js/
                ├── main.js
                ├── map.js
                └── charts.js
```

---

## 🚀 Setup & Execution Guide (Windows 11 / VS Code)

Follow these simple steps in your VS Code terminal (PowerShell or Command Prompt):

### 1. Create and Activate Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install Project Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Apply Database Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Predefined Maharashtra Sample Cities
```powershell
python manage.py seed_cities
```
*Seeds: Pune, Mumbai, Nashik, Chhatrapati Sambhajinagar, Kolhapur, Satara, Solapur, Nagpur.*

### 5. Run Automated Test Suite
```powershell
python manage.py test optimizer
```
*Executes all 10 unit and integration tests verifying algorithm correctness, distance symmetry, and API contracts.*

### 6. Start the Development Server
```powershell
python manage.py runserver
```

Open your browser and navigate to:
```text
http://127.0.0.1:8000/
```

---

## 🐳 Docker Deployment Guide

You can also run the entire application using Docker with a single command:

```bash
# Build and run containers
docker compose up --build

# Run in detached mode (background)
docker compose up -d --build

# View container logs
docker compose logs -f

# Stop container
docker compose down
```

The container automatically applies SQLite migrations, seeds default cities, and serves the application at **`http://localhost:8000/`**.

---

## 🧭 Application Walkthrough

1. **Dashboard (`/`)**: View high-level metrics across all runs, latest tour performance, and quick project statistics.
2. **Route Optimizer (`/optimizer/`)**:
   - Click **"Load Sample Cities"** or pick from the dropdown.
   - Choose your origin hub (e.g. Pune).
   - Select distance metric: **Geographic (Haversine)** or **OSRM Road Network**.
   - Click **"Run AI Route Optimization"**.
   - Inspect the red initial route vs the green optimized route on the Leaflet map.
   - Analyze the Genetic Algorithm convergence chart and comparison metrics.
   - Export result to CSV or capture map image to PNG.
3. **History (`/history/`)**: Inspect and search every previous optimization run saved in SQLite.
4. **About Project (`/about/`)**: Academic documentation detailing TSP theory, $O(N!)$ complexity, Genetic Algorithm mechanisms, flowchart, and applications.

---

## 🧪 Testing Verification Summary

The project includes tests covering:
1. City selection validation (minimum 3 cities, valid coordinates).
2. Haversine distance matrix symmetry ($D_{ij} = D_{ji}, D_{ii} = 0$).
3. Route distance calculation accuracy.
4. Intermediate tour visiting each city exactly once.
5. Tour return to the designated starting city.
6. Genetic Algorithm produces valid closed tours.
7. Optimization result is guaranteed no worse than baseline order.
8. Correct percentage improvement formula execution.
9. JSON API payload structure and response formats.
10. Database persistence into SQLite models.

---

## 🎓 Academic Microproject Details
- **Course**: Bachelor of Engineering (Computer Engineering)
- **Subject**: Artificial Intelligence (AI)
- **University**: Savitribai Phule Pune University (SPPU)
