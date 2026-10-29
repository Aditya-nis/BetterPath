"""
URL configuration for AI_TSP_Web project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('optimizer.urls')),
]
