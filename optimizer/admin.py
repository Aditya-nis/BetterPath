from django.contrib import admin
from .models import City, OptimizationRun

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'is_preset', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_preset',)

@admin.register(OptimizationRun)
class OptimizationRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'starting_city', 'initial_distance', 'optimized_distance', 'distance_saved', 'improvement_percentage', 'distance_mode', 'created_at')
    list_filter = ('distance_mode', 'brute_force_verified', 'created_at')
    search_fields = ('starting_city',)
    readonly_fields = ('created_at',)
