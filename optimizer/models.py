from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class City(models.Model):
    name = models.CharField(max_length=120, unique=True)
    latitude = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Latitude between -90 and 90 degrees"
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Longitude between -180 and 180 degrees"
    )
    is_preset = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.latitude:.4f}, {self.longitude:.4f})"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'lat': float(self.latitude),
            'lng': float(self.longitude),
            'is_preset': self.is_preset,
        }


class OptimizationRun(models.Model):
    DISTANCE_MODE_CHOICES = [
        ('geographic', 'Geographic (Haversine Distance)'),
        ('road', 'Road Network (OSRM Distance)'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    starting_city = models.CharField(max_length=120)
    selected_cities = models.JSONField(help_text="List of cities involved in optimization")
    
    initial_route = models.JSONField(help_text="Ordered list of cities in the baseline route")
    optimized_route = models.JSONField(help_text="Ordered list of cities in the AI-optimized route")
    
    initial_distance = models.FloatField(help_text="Initial total distance in km")
    optimized_distance = models.FloatField(help_text="Optimized total distance in km")
    distance_saved = models.FloatField(help_text="Kilometers saved")
    improvement_percentage = models.FloatField(help_text="Improvement percentage")
    execution_time = models.FloatField(help_text="Execution time in seconds")
    
    distance_mode = models.CharField(max_length=20, choices=DISTANCE_MODE_CHOICES, default='geographic')
    algorithm_parameters = models.JSONField(default=dict, help_text="GA parameters used")
    convergence_history = models.JSONField(default=list, help_text="History of best distance per generation")
    
    # Optional verification for small datasets (<= 9 cities)
    brute_force_verified = models.BooleanField(default=False)
    brute_force_distance = models.FloatField(null=True, blank=True)
    brute_force_route = models.JSONField(null=True, blank=True)
    
    # Optional road polyline/geometry data for rendering
    route_geometry = models.JSONField(null=True, blank=True, help_text="GeoJSON coordinates for road routing")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Run #{self.id} - {self.starting_city} ({len(self.selected_cities)} cities) - {self.optimized_distance:.2f} km"
