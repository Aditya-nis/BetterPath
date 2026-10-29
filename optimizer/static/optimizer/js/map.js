/**
 * Map Integration Module
 * 1. Primary: High-Res World Street / Satellite Map (Esri ArcGIS - 100% Free, NO 403, NO API Key Required, NO Watermarks)
 * 2. Secondary: Google Maps with Google Places Live Autocomplete
 */

let activeMapEngine = 'leaflet'; // Defaults to reliable Esri/Leaflet map to prevent 403/watermark issues

// Google Maps State
let googleMapInstance = null;
let googleMarkers = [];
let googleInitialPolyline = null;
let googleOptimizedPolyline = null;
let placesAutocompleteInstance = null;

// Leaflet State
let leafletMapInstance = null;
let leafletMarkerGroup = null;
let leafletInitialPolyline = null;
let leafletOptimizedPolyline = null;

// Custom Dark Night Cyberpunk Google Maps Styling
const googleDarkStyles = [
  { elementType: "geometry", stylers: [{ color: "#091224" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#050b14" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#94a3b8" }] },
  {
    featureType: "administrative.locality",
    elementType: "labels.text.fill",
    stylers: [{ color: "#00f0ff" }]
  },
  {
    featureType: "poi",
    elementType: "labels.text.fill",
    stylers: [{ color: "#64748b" }]
  },
  {
    featureType: "poi.park",
    elementType: "geometry",
    stylers: [{ color: "#0d1b33" }]
  },
  {
    featureType: "road",
    elementType: "geometry",
    stylers: [{ color: "#16233b" }]
  },
  {
    featureType: "road",
    elementType: "geometry.stroke",
    stylers: [{ color: "#0c1526" }]
  },
  {
    featureType: "road.highway",
    elementType: "geometry",
    stylers: [{ color: "#0284c7" }]
  },
  {
    featureType: "road.highway",
    elementType: "geometry.stroke",
    stylers: [{ color: "#0369a1" }]
  },
  {
    featureType: "transit",
    elementType: "geometry",
    stylers: [{ color: "#1e293b" }]
  },
  {
    featureType: "water",
    elementType: "geometry",
    stylers: [{ color: "#040812" }]
  },
  {
    featureType: "water",
    elementType: "labels.text.fill",
    stylers: [{ color: "#38bdf8" }]
  }
];

/**
 * Initializes map engines.
 */
function initAllMaps() {
  // 1. Initialize High-Res Esri Street Map (100% Free, NO 403, NO Watermarks)
  initLeafletMap();

  // 2. Initialize Google Maps if ready
  if (window.google && window.google.maps) {
    onGoogleMapsReady();
  }
}

/**
 * Triggered as soon as Google Maps JavaScript finishes loading
 */
window.onGoogleMapsReady = function() {
  if (!googleMapInstance) {
    initGoogleMap();
    initPlacesAutocomplete();
  }
};

/**
 * Triggered if Google Maps reports an authentication / billing failure
 */
window.onGoogleMapsAuthFailed = function() {
  console.warn("Google Maps key has restriction or billing issue. Esri World Streets remains active.");
  switchMapEngine('leaflet');
  
  const gRadio = document.getElementById('engineGoogle');
  if (gRadio) {
    gRadio.disabled = true;
  }
  const lRadio = document.getElementById('engineLeaflet');
  if (lRadio) {
    lRadio.checked = true;
  }
};

/**
 * Initialize Google Maps with dark glass styling
 */
function initGoogleMap(containerId = 'googleMapContainer') {
  const elem = document.getElementById(containerId);
  if (!elem || !window.google || !window.google.maps) return;

  try {
    googleMapInstance = new google.maps.Map(elem, {
      center: { lat: 19.25, lng: 75.25 }, // Centered on Maharashtra
      zoom: 7,
      styles: googleDarkStyles,
      disableDefaultUI: false,
      zoomControl: true,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true
    });

    if (typeof selectedCities !== 'undefined' && selectedCities.length > 0) {
      updateMapMarkers(selectedCities, startingCityName);
    }
  } catch (err) {
    console.error("Failed to initialize Google Maps:", err);
    switchMapEngine('leaflet');
  }
}

/**
 * Initialize Google Places Autocomplete
 */
function initPlacesAutocomplete() {
  const input = document.getElementById('googlePlacesInput');
  if (!input || !window.google || !window.google.maps || !window.google.maps.places) return;

  try {
    placesAutocompleteInstance = new google.maps.places.Autocomplete(input, {
      types: ['geocode', 'establishment'],
      fields: ['place_id', 'geometry', 'name', 'formatted_address']
    });

    placesAutocompleteInstance.addListener('place_changed', () => {
      const place = placesAutocompleteInstance.getPlace();
      if (!place.geometry || !place.geometry.location) {
        if (typeof showToast === 'function') {
          showToast('Please select a valid place from the suggestions list.', 'warning');
        }
        return;
      }

      const lat = place.geometry.location.lat();
      const lng = place.geometry.location.lng();
      let name = place.name;
      if (!name && place.formatted_address) {
        name = place.formatted_address.split(',')[0].trim();
      }
      if (!name) name = 'Selected Place';

      if (typeof handleAddGooglePlaceCity === 'function') {
        handleAddGooglePlaceCity(name, lat, lng);
      }
      input.value = '';
    });
  } catch (e) {
    console.warn("Places Autocomplete init error:", e);
  }
}

/**
 * Initialize Leaflet Map with 100% Free High-Res Esri World Street Tiles
 * ZERO 403 ERRORS - ZERO API KEY REQUIRED - ZERO WATERMARKS!
 */
function initLeafletMap(containerId = 'mapContainer') {
  const elem = document.getElementById(containerId);
  if (!elem || leafletMapInstance) return;

  leafletMapInstance = L.map(containerId, {
    zoomControl: true,
    attributionControl: true
  }).setView([19.25, 75.25], 7);

  // High-Resolution Esri World Street Map Tiles (100% Free, NO 403, NO KEY REQUIRED)
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri &mdash; Street Navigation'
  }).addTo(leafletMapInstance);

  leafletMarkerGroup = L.layerGroup().addTo(leafletMapInstance);

  setTimeout(() => {
    if (leafletMapInstance) {
      leafletMapInstance.invalidateSize();
    }
  }, 300);
}

/**
 * Switch between High-Res Streets and Google Maps
 */
function switchMapEngine(engine) {
  activeMapEngine = engine;
  const gContainer = document.getElementById('googleMapContainer');
  const lContainer = document.getElementById('mapContainer');

  if (engine === 'google' && googleMapInstance) {
    if (gContainer) gContainer.style.display = 'block';
    if (lContainer) lContainer.style.display = 'none';
    if (window.google) {
      google.maps.event.trigger(googleMapInstance, 'resize');
    }
  } else {
    // Default: High-Res Esri Street Map
    activeMapEngine = 'leaflet';
    if (gContainer) gContainer.style.display = 'none';
    if (lContainer) lContainer.style.display = 'block';
    if (leafletMapInstance) {
      leafletMapInstance.invalidateSize();
    }
  }

  // Refresh current markers & routes on switched map
  if (typeof selectedCities !== 'undefined' && selectedCities.length > 0) {
    updateMapMarkers(selectedCities, startingCityName);
    if (typeof lastOptimizationResult !== 'undefined' && lastOptimizationResult) {
      drawInitialRouteMap(lastOptimizationResult.initial_route);
      drawOptimizedRouteMap(lastOptimizationResult.optimized_route, lastOptimizationResult.route_geometry);
    } else {
      fitMapToCities(selectedCities);
    }
  }
}

/**
 * Clear all route layers and markers across both engines
 */
function clearAllMapLayers() {
  // Clear Google Maps
  googleMarkers.forEach(m => m.setMap(null));
  googleMarkers = [];
  if (googleInitialPolyline) {
    googleInitialPolyline.setMap(null);
    googleInitialPolyline = null;
  }
  if (googleOptimizedPolyline) {
    googleOptimizedPolyline.setMap(null);
    googleOptimizedPolyline = null;
  }

  // Clear Leaflet
  if (leafletMarkerGroup) leafletMarkerGroup.clearLayers();
  if (leafletInitialPolyline && leafletMapInstance) {
    leafletMapInstance.removeLayer(leafletInitialPolyline);
    leafletInitialPolyline = null;
  }
  if (leafletOptimizedPolyline && leafletMapInstance) {
    leafletMapInstance.removeLayer(leafletOptimizedPolyline);
    leafletOptimizedPolyline = null;
  }
}

/**
 * Update markers for both map engines
 */
function updateMapMarkers(cities, startingCityName) {
  clearAllMarkersOnly();

  // 1. Google Maps Markers
  if (googleMapInstance && window.google) {
    cities.forEach((city, idx) => {
      const isStart = city.name.toLowerCase() === (startingCityName || '').toLowerCase();
      
      const marker = new google.maps.Marker({
        position: { lat: city.lat, lng: city.lng },
        map: googleMapInstance,
        title: city.name,
        label: {
          text: isStart ? '★' : String(idx + 1),
          color: '#ffffff',
          fontWeight: 'bold',
          fontSize: '11px'
        },
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 13,
          fillColor: isStart ? '#f59e0b' : '#0284c7',
          fillOpacity: 1,
          strokeColor: isStart ? '#fef08a' : '#ffffff',
          strokeWeight: 2.5
        }
      });

      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="font-family: Inter, sans-serif; min-width: 130px; color: #ffffff;">
            <strong style="color: #00f0ff; font-size: 13px;">${city.name}</strong>
            ${isStart ? '<span style="display:block; color: #fbbf24; font-size: 11px; font-weight:600;">★ Starting Hub</span>' : ''}
            <span style="display:block; color: #94a3b8; font-size: 11px;">Lat: ${city.lat.toFixed(4)}, Lng: ${city.lng.toFixed(4)}</span>
          </div>
        `
      });

      marker.addListener('click', () => {
        infoWindow.open(googleMapInstance, marker);
      });

      googleMarkers.push(marker);
    });
  }

  // 2. Leaflet Markers
  if (leafletMapInstance && leafletMarkerGroup) {
    cities.forEach((city, index) => {
      const isStart = city.name.toLowerCase() === (startingCityName || '').toLowerCase();
      const pinClass = isStart ? 'custom-city-pin start-pin' : 'custom-city-pin standard-pin';
      const pinHtml = `<div class="${pinClass}" style="width:26px; height:26px;">${isStart ? '<i class="bi bi-flag-fill"></i>' : index + 1}</div>`;

      const customIcon = L.divIcon({
        html: pinHtml,
        className: 'custom-leaflet-icon',
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const marker = L.marker([city.lat, city.lng], { icon: customIcon });
      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; min-width: 130px;">
          <strong style="color: #0f172a; font-size: 13px;">${city.name}</strong>
          ${isStart ? '<span style="display:block; color: #b45309; font-size: 11px; font-weight:600;">★ Starting Hub</span>' : ''}
          <span style="display:block; color: #64748b; font-size: 11px;">Lat: ${city.lat.toFixed(4)}, Lng: ${city.lng.toFixed(4)}</span>
        </div>
      `);
      leafletMarkerGroup.addLayer(marker);
    });
  }

  fitMapToCities(cities);
}

function clearAllMarkersOnly() {
  googleMarkers.forEach(m => m.setMap(null));
  googleMarkers = [];
  if (leafletMarkerGroup) leafletMarkerGroup.clearLayers();
}

/**
 * Draw Initial Route (Red Polyline)
 */
function drawInitialRouteMap(routeCities) {
  if (!routeCities || routeCities.length < 2) return;

  // 1. Google Maps
  if (googleInitialPolyline) {
    googleInitialPolyline.setMap(null);
    googleInitialPolyline = null;
  }
  if (googleMapInstance && window.google) {
    const path = routeCities.map(c => ({ lat: c.lat, lng: c.lng }));
    googleInitialPolyline = new google.maps.Polyline({
      path: path,
      geodesic: true,
      strokeColor: '#ef4444',
      strokeOpacity: 0.85,
      strokeWeight: 3,
      map: googleMapInstance
    });
  }

  // 2. Leaflet
  if (leafletInitialPolyline && leafletMapInstance) {
    leafletMapInstance.removeLayer(leafletInitialPolyline);
    leafletInitialPolyline = null;
  }
  if (leafletMapInstance) {
    const coords = routeCities.map(c => [c.lat, c.lng]);
    leafletInitialPolyline = L.polyline(coords, {
      color: '#ef4444',
      weight: 3,
      opacity: 0.85,
      dashArray: '8, 8'
    }).addTo(leafletMapInstance);
  }
}

/**
 * Draw AI-Optimized Route (Emerald/Green Polyline)
 */
function drawOptimizedRouteMap(routeCities, roadGeometry = null) {
  if (!routeCities || routeCities.length < 2) return;

  // 1. Google Maps
  if (googleOptimizedPolyline) {
    googleOptimizedPolyline.setMap(null);
    googleOptimizedPolyline = null;
  }
  if (googleMapInstance && window.google) {
    let path;
    if (roadGeometry && roadGeometry.length > 0) {
      path = roadGeometry.map(pt => ({ lat: pt[0], lng: pt[1] }));
    } else {
      path = routeCities.map(c => ({ lat: c.lat, lng: c.lng }));
    }

    googleOptimizedPolyline = new google.maps.Polyline({
      path: path,
      geodesic: true,
      strokeColor: '#10b981',
      strokeOpacity: 0.95,
      strokeWeight: 5,
      map: googleMapInstance
    });
  }

  // 2. Leaflet
  if (leafletOptimizedPolyline && leafletMapInstance) {
    leafletMapInstance.removeLayer(leafletOptimizedPolyline);
    leafletOptimizedPolyline = null;
  }
  if (leafletMapInstance) {
    let coords;
    if (roadGeometry && roadGeometry.length > 0) {
      coords = roadGeometry;
    } else {
      coords = routeCities.map(c => [c.lat, c.lng]);
    }

    leafletOptimizedPolyline = L.polyline(coords, {
      color: '#10b981',
      weight: 5,
      opacity: 0.95
    }).addTo(leafletMapInstance);
  }

  fitMapToCities(routeCities);
}

/**
 * Fit bounds on both Google Maps and Leaflet
 */
function fitMapToCities(cities) {
  if (!cities || cities.length === 0) return;

  // 1. Google Maps Bounds
  if (googleMapInstance && window.google) {
    const bounds = new google.maps.LatLngBounds();
    cities.forEach(c => bounds.extend(new google.maps.LatLng(c.lat, c.lng)));
    googleMapInstance.fitBounds(bounds, 50);
  }

  // 2. Leaflet Bounds
  if (leafletMapInstance) {
    const bounds = L.latLngBounds(cities.map(c => [c.lat, c.lng]));
    if (bounds.isValid()) {
      leafletMapInstance.fitBounds(bounds, { padding: [45, 45], maxZoom: 11 });
    }
  }
}
