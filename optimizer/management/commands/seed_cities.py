from django.core.management.base import BaseCommand
from optimizer.models import City

PRESET_CITIES = [
    {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567},
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Nashik", "latitude": 19.9975, "longitude": 73.7898},
    {"name": "Chhatrapati Sambhajinagar (Aurangabad)", "latitude": 19.8762, "longitude": 75.3433},
    {"name": "Kolhapur", "latitude": 16.7050, "longitude": 74.2433},
    {"name": "Satara", "latitude": 17.6805, "longitude": 74.0183},
    {"name": "Solapur", "latitude": 17.6599, "longitude": 75.9064},
    {"name": "Nagpur", "latitude": 21.1458, "longitude": 79.0882},
]

class Command(BaseCommand):
    help = "Seeds database with predefined Maharashtra cities for TSP route optimization."

    def handle(self, *args, **options):
        count = 0
        for item in PRESET_CITIES:
            city, created = City.objects.get_or_create(
                name=item['name'],
                defaults={
                    'latitude': item['latitude'],
                    'longitude': item['longitude'],
                    'is_preset': True
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} preset cities (Total: {City.objects.count()})."))
