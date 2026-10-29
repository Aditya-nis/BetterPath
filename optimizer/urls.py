from django.urls import path
from . import views

urlpatterns = [
    # Web Page Views
    path('', views.dashboard_view, name='dashboard'),
    path('optimizer/', views.optimizer_view, name='optimizer'),
    path('lab/', views.algorithm_lab_view, name='algorithm_lab'),
    path('history/', views.history_view, name='history'),
    path('about/', views.about_view, name='about'),

    # API Endpoints
    path('api/cities/', views.api_get_cities, name='api_cities'),
    path('api/cities/add/', views.api_add_city, name='api_add_city'),
    path('api/cities/reset-sample/', views.api_reset_cities, name='api_reset_cities'),
    path('api/presets/', views.api_get_presets, name='api_presets'),
    path('api/geocode/', views.api_geocode_city, name='api_geocode'),
    path('api/optimize/', views.api_optimize, name='api_optimize'),
    path('api/compare/', views.api_compare_algorithms, name='api_compare_algorithms'),
    path('api/history/', views.api_get_history, name='api_history'),
    path('api/history/<int:run_id>/', views.api_get_run_detail, name='api_run_detail'),
    path('api/history/<int:run_id>/export-json/', views.api_export_run_json, name='api_export_run_json'),
    path('api/export-history/', views.api_export_history_csv, name='api_export_history'),
]

