from django import forms
from .models import City

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nashik'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'placeholder': '19.9975'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'placeholder': '73.7898'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError("City name must be at least 2 characters.")
        return name

    def clean_latitude(self):
        lat = self.cleaned_data['latitude']
        if not (-90.0 <= lat <= 90.0):
            raise forms.ValidationError("Latitude must be between -90.0 and 90.0.")
        return lat

    def clean_longitude(self):
        lng = self.cleaned_data['longitude']
        if not (-180.0 <= lng <= 180.0):
            raise forms.ValidationError("Longitude must be between -180.0 and 180.0.")
        return lng
