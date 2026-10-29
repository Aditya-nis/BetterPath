from django.urls import path
from . import views

urlpatterns = [
    # Web Page Views
    path('', views.dashboard_view, name='dashboard'),
    path('optimizer/', views.optimizer_view, name='optimizer'),
    path('history/', views.history_view, name='history'),
    path('about/', views.about_view, name='about'),

    # API Endpoints
    path('api/cities/', views.api_get_cities, name='api_cities'),
    path('api/cities/add/', views.api_add_city, name='api_add_city'),
    path('api/cities/reset-sample/', views.api_reset_cities, name='api_reset_cities'),
    path('api/presets/', views.api_get_presets, name='api_presets'),
    path('api/geocode/', views.api_geocode_city, name='api_geocode'),
    path('api/optimize/', views.api_optimize, name='api_optimize'),
    path('api/history/', views.api_get_history, name='api_history'),
    path('api/history/<int:run_id>/', views.api_get_run_detail, name='api_run_detail'),
    path('api/export-history/', views.api_export_history_csv, name='api_export_history'),
]

