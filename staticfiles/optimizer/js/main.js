/**
 * Main application coordinator for Route Optimizer.
 * Handles UI interactions, API calls, state management, and visual updates.
 */

let availableCities = [];
let selectedCities = [];
let startingCityName = '';
let lastOptimizationResult = null;
let presetDatasets = {};

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Map Engines (Google Maps primary + Leaflet fallback)
  initAllMaps();

  // 2. Fetch available cities and initialize presets
  fetchAvailableCities();

  // 3. Register Event Listeners & Live Search
  setupEventListeners();
  setupCitySearch();
});

function setupEventListeners() {
  // Add city from dropdown
  const btnAddDropdown = document.getElementById('btnAddDropdownCity');
  if (btnAddDropdown) {
    btnAddDropdown.addEventListener('click', handleAddCityFromDropdown);
  }

  // Load sample cities preset (fallback if button present)
  const btnLoadPresets = document.getElementById('btnLoadPresets');
  if (btnLoadPresets) {
    btnLoadPresets.addEventListener('click', handleLoadPresetCities);
  }

  // Preset Dataset Menu items
  document.querySelectorAll('.preset-option-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const presetId = btn.getAttribute('data-preset-id');
      handleSelectPreset(presetId);
    });
  });

  // Reset cities selection
  const btnReset = document.getElementById('btnResetCities');
  if (btnReset) {
    btnReset.addEventListener('click', handleResetSelection);
  }

  // Quick Demo button
  const btnQuickDemo = document.getElementById('btnQuickDemo');
  if (btnQuickDemo) {
    btnQuickDemo.addEventListener('click', handleQuickDemo);
  }

  // Starting city dropdown change
  const startSelect = document.getElementById('startCitySelect');
  if (startSelect) {
    startSelect.addEventListener('change', (e) => {
      startingCityName = e.target.value;
      renderSelectedCityTags();
      updateMapMarkers(selectedCities, startingCityName);
    });
  }

  // Save custom city from modal
  const btnSaveCustom = document.getElementById('btnSaveCustomCity');
  if (btnSaveCustom) {
    btnSaveCustom.addEventListener('click', handleSaveCustomCity);
  }

  // Run Optimization button
  const btnOptimize = document.getElementById('btnRunOptimizer');
  if (btnOptimize) {
    btnOptimize.addEventListener('click', handleRunOptimization);
  }

  // Fit map button
  const btnFitMap = document.getElementById('btnFitMap');
  if (btnFitMap) {
    btnFitMap.addEventListener('click', () => {
      fitMapToCities(selectedCities);
    });
  }

  // Distance mode radio switcher
  const modeRadios = document.querySelectorAll('input[name="distanceModeRadio"]');
  modeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      const label = document.getElementById('activeDistanceModeLabel');
      if (label) {
        if (e.target.value === 'road') {
          label.innerText = 'Mode: Road Network (OSRM)';
          label.className = 'badge badge-ai badge-emerald';
        } else {
          label.innerText = 'Mode: Geographic (Haversine)';
          label.className = 'badge badge-ai badge-cyan';
        }
      }
    });
  });

  // Map engine switcher (Google Maps vs Leaflet)
  const engineRadios = document.querySelectorAll('input[name="mapEngineRadio"]');
  engineRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      switchMapEngine(e.target.value);
    });
  });

  // Export PNG button
  const btnExportPng = document.getElementById('btnExportPng');
  if (btnExportPng) {
    btnExportPng.addEventListener('click', handleExportDashboardPng);
  }

  // Export CSV button
  const btnExportCsv = document.getElementById('btnExportResultCsv');
  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', handleExportCurrentResultCsv);
  }

  // Export JSON button
  const btnExportJson = document.getElementById('btnExportResultJson');
  if (btnExportJson) {
    btnExportJson.addEventListener('click', handleExportCurrentResultJson);
  }
}

/**
 * Setup live city search with instant suggestions, OpenStreetMap geocoding fallback, and enter-key add
 */
function setupCitySearch() {
  const searchInput = document.getElementById('googlePlacesInput');
  const suggestionsBox = document.getElementById('searchSuggestionsBox');
  const btnAddSearch = document.getElementById('btnAddCityBySearch');
  if (!searchInput) return;

  let debounceTimer = null;

  // Search input typing handler
  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.trim();
    clearTimeout(debounceTimer);
    if (q.length < 2) {
      if (suggestionsBox) suggestionsBox.style.display = 'none';
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/geocode/?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (data.success && data.results && data.results.length > 0) {
          renderSuggestions(data.results, suggestionsBox, searchInput);
        } else {
          if (suggestionsBox) suggestionsBox.style.display = 'none';
        }
      } catch (err) {
        console.warn('Geocoding search failed:', err);
      }
    }, 220);
  });

  // Enter key in input field
  searchInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      await triggerCitySearchAndAdd(searchInput.value.trim());
    }
  });

  // Add button click
  if (btnAddSearch) {
    btnAddSearch.addEventListener('click', async () => {
      await triggerCitySearchAndAdd(searchInput.value.trim());
    });
  }

  // Close suggestions when clicking outside
  document.addEventListener('click', (e) => {
    if (suggestionsBox && !searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
      suggestionsBox.style.display = 'none';
    }
  });
}

function renderSuggestions(results, box, input) {
  if (!box) return;
  box.innerHTML = '';
  results.forEach(item => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'list-group-item list-group-item-action py-2 px-3 d-flex justify-content-between align-items-center text-start border-bottom';
    btn.style.background = 'rgba(11, 20, 38, 0.98)';
    btn.style.color = '#f8fafc';
    btn.style.borderColor = 'rgba(56, 189, 248, 0.2)';

    const sourceBadge = item.source === 'Database' 
      ? '<span class="badge badge-ai badge-emerald" style="font-size: 0.68rem;">Database</span>'
      : '<span class="badge badge-ai badge-cyan" style="font-size: 0.68rem;">OpenStreetMap</span>';

    btn.innerHTML = `
      <div>
        <strong class="d-block text-white fs-7">${item.name}</strong>
        <small class="text-subtle fs-8">Lat: ${item.lat.toFixed(4)}, Lng: ${item.lng.toFixed(4)}</small>
      </div>
      <div>${sourceBadge}</div>
    `;

    btn.addEventListener('click', () => {
      addCityToSelection({
        name: item.name,
        lat: parseFloat(item.lat),
        lng: parseFloat(item.lng)
      });
      showToast(`Added '${item.name}'!`, 'success');
      input.value = '';
      box.style.display = 'none';
    });

    box.appendChild(btn);
  });
  box.style.display = 'block';
}

async function triggerCitySearchAndAdd(query) {
  if (!query) {
    showToast('Please type a city name to search and add.', 'warning');
    return;
  }

  const searchInput = document.getElementById('googlePlacesInput');
  const suggestionsBox = document.getElementById('searchSuggestionsBox');
  if (suggestionsBox) suggestionsBox.style.display = 'none';

  // 1. Check if query matches an existing city in availableCities (case-insensitive substring or exact)
  const exact = availableCities.find(c => c.name.toLowerCase() === query.toLowerCase());
  if (exact) {
    addCityToSelection(exact);
    showToast(`Added '${exact.name}' from database!`, 'success');
    if (searchInput) searchInput.value = '';
    return;
  }

  const partial = availableCities.find(c => c.name.toLowerCase().includes(query.toLowerCase()));
  if (partial && query.length >= 3) {
    addCityToSelection(partial);
    showToast(`Added '${partial.name}' from database!`, 'success');
    if (searchInput) searchInput.value = '';
    return;
  }

  // 2. Geocode via /api/geocode/
  showToast(`Searching coordinates for '${query}'...`, 'info');
  try {
    const res = await fetch(`/api/geocode/?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (data.success && data.results && data.results.length > 0) {
      const topMatch = data.results[0];
      const cityObj = {
        name: topMatch.name,
        lat: parseFloat(topMatch.lat),
        lng: parseFloat(topMatch.lng)
      };
      addCityToSelection(cityObj);
      showToast(`Added '${cityObj.name}' (${cityObj.lat.toFixed(2)}, ${cityObj.lng.toFixed(2)})!`, 'success');
      if (searchInput) searchInput.value = '';

      // Persist in DB in background
      fetch('/api/cities/add/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') || ''
        },
        body: JSON.stringify({ name: cityObj.name, latitude: cityObj.lat, longitude: cityObj.lng })
      }).then(r => r.json()).then(d => {
        if (d.success && d.city) {
          if (!availableCities.some(c => c.name.toLowerCase() === d.city.name.toLowerCase())) {
            availableCities.push(d.city);
            populateCityDropdown();
          }
        }
      }).catch(e => console.log('City background save:', e));
    } else {
      showToast(`Could not find coordinates for '${query}'. Use "Add Lat/Lng" for custom coordinates.`, 'error');
    }
  } catch (err) {
    showToast(`Search error: ${err.message}`, 'error');
  }
}

async function handleAddGooglePlaceCity(name, lat, lng) {
  const cityObj = {
    name: name,
    lat: parseFloat(lat),
    lng: parseFloat(lng)
  };
  addCityToSelection(cityObj);
  showToast(`Added '${name}' from Google Places!`, 'success');

  // Automatically save to database in background
  try {
    await fetch('/api/cities/add/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ name, latitude: lat, longitude: lng })
    });
  } catch (e) {
    console.log('Background city persist:', e);
  }
}

async function fetchAvailableCities() {
  try {
    const res = await fetch('/api/cities/');
    const data = await res.json();
    if (data.success) {
      availableCities = data.cities;
      if (data.preset_datasets) {
        presetDatasets = data.preset_datasets;
      }
      populateCityDropdown();

      // Automatically load Maharashtra presets on initial empty load
      if (selectedCities.length === 0) {
        if (data.presets && data.presets.length > 0) {
          loadPresetArray(data.presets);
        } else if (presetDatasets['maharashtra_8']) {
          loadPresetArray(presetDatasets['maharashtra_8'].cities);
        }
      }
    }
  } catch (err) {
    showToast('Failed to load cities: ' + err.message, 'error');
  }
}

function populateCityDropdown() {
  const dropdown = document.getElementById('cityDropdown');
  if (!dropdown) return;

  const countLabel = document.getElementById('dbCityCountLabel');
  if (countLabel) {
    countLabel.innerText = `${availableCities.length} Cities in DB`;
  }

  dropdown.innerHTML = `<option value="" disabled selected>Choose a city from database (${availableCities.length} available)...</option>`;
  
  // Sort alphabetically
  const sorted = [...availableCities].sort((a, b) => a.name.localeCompare(b.name));

  sorted.forEach(c => {
    const isSelected = selectedCities.some(sc => sc.name.toLowerCase() === c.name.toLowerCase());
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = isSelected 
      ? `✓ ${c.name} (${c.lat.toFixed(2)}, ${c.lng.toFixed(2)}) [Added]`
      : `${c.name} (${c.lat.toFixed(2)}, ${c.lng.toFixed(2)})`;
    if (isSelected) {
      opt.disabled = true;
      opt.style.color = '#94a3b8';
    }
    dropdown.appendChild(opt);
  });
}

function handleAddCityFromDropdown() {
  const dropdown = document.getElementById('cityDropdown');
  if (!dropdown || !dropdown.value) {
    showToast('Please select a city from the dropdown first.', 'warning');
    return;
  }

  const cityName = dropdown.value;
  const found = availableCities.find(c => c.name.toLowerCase() === cityName.toLowerCase());
  if (found) {
    addCityToSelection(found);
    showToast(`Added '${found.name}'!`, 'success');
  }
}

function addCityToSelection(cityObj) {
  if (selectedCities.some(c => c.name.toLowerCase() === cityObj.name.toLowerCase())) {
    showToast(`'${cityObj.name}' is already in the tour.`, 'warning');
    return;
  }

  selectedCities.push({
    name: cityObj.name,
    lat: parseFloat(cityObj.lat),
    lng: parseFloat(cityObj.lng)
  });

  // If no starting city set, default to first city
  if (!startingCityName || !selectedCities.some(c => c.name === startingCityName)) {
    startingCityName = selectedCities[0].name;
  }

  renderSelectedCityTags();
  updateStartingCityDropdown();
  populateCityDropdown();
  updateMapMarkers(selectedCities, startingCityName);
}

function removeCityFromSelection(cityName) {
  selectedCities = selectedCities.filter(c => c.name.toLowerCase() !== cityName.toLowerCase());
  
  if (startingCityName.toLowerCase() === cityName.toLowerCase()) {
    startingCityName = selectedCities.length > 0 ? selectedCities[0].name : '';
  }

  renderSelectedCityTags();
  updateStartingCityDropdown();
  populateCityDropdown();
  updateMapMarkers(selectedCities, startingCityName);
}

function handleResetSelection() {
  selectedCities = [];
  startingCityName = '';
  renderSelectedCityTags();
  updateStartingCityDropdown();
  populateCityDropdown();
  clearAllMapLayers();

  const resultsCard = document.getElementById('resultsCard');
  if (resultsCard) resultsCard.style.display = 'none';
  const chartsContainer = document.getElementById('chartsContainer');
  if (chartsContainer) chartsContainer.style.display = 'none';

  showToast('City selection reset.', 'info');
}

function handleSelectPreset(presetId) {
  if (presetDatasets && presetDatasets[presetId]) {
    const dataset = presetDatasets[presetId];
    loadPresetArray(dataset.cities);
    showToast(`Loaded '${dataset.title}' (${dataset.cities.length} cities).`, 'success');
  } else {
    fetch('/api/presets/')
      .then(r => r.json())
      .then(data => {
        if (data.presets && data.presets[presetId]) {
          presetDatasets = data.presets;
          loadPresetArray(data.presets[presetId].cities);
          showToast(`Loaded '${data.presets[presetId].title}'.`, 'success');
        }
      });
  }
}

function handleLoadPresetCities() {
  handleSelectPreset('maharashtra_8');
}

function loadPresetArray(presetList) {
  selectedCities = presetList.map(c => ({
    name: c.name,
    lat: parseFloat(c.lat),
    lng: parseFloat(c.lng)
  }));

  startingCityName = selectedCities[0].name;
  renderSelectedCityTags();
  updateStartingCityDropdown();
  populateCityDropdown();
  updateMapMarkers(selectedCities, startingCityName);
  fitMapToCities(selectedCities);
}


function renderSelectedCityTags() {
  const container = document.getElementById('selectedCitiesContainer');
  const countBadge = document.getElementById('selectedCountBadge');
  if (!container) return;

  if (countBadge) {
    countBadge.innerText = `${selectedCities.length} Cities`;
    countBadge.className = selectedCities.length >= 3 ? 'badge badge-ai badge-emerald' : 'badge badge-ai badge-amber';
  }

  if (selectedCities.length === 0) {
    container.innerHTML = '<span class="text-subtle fs-7 p-2 d-block">No cities selected. Choose from dropdown or load sample dataset.</span>';
    return;
  }

  container.innerHTML = '';
  selectedCities.forEach((city, index) => {
    const isStart = city.name.toLowerCase() === (startingCityName || '').toLowerCase();
    const tag = document.createElement('div');
    tag.className = `city-tag ${isStart ? 'is-start' : ''}`;
    tag.innerHTML = `
      <span class="fw-semibold me-1">${isStart ? '★ ' : ''}${city.name}</span>
      <small class="text-subtle fs-8">(${city.lat.toFixed(2)}, ${city.lng.toFixed(2)})</small>
      <button type="button" class="btn-remove" title="Remove city" onclick="removeCityFromSelection('${city.name}')">
        <i class="bi bi-x-circle-fill"></i>
      </button>
    `;
    container.appendChild(tag);
  });
}

function updateStartingCityDropdown() {
  const select = document.getElementById('startCitySelect');
  if (!select) return;

  select.innerHTML = '';
  if (selectedCities.length === 0) {
    select.innerHTML = '<option value="" disabled selected>No cities selected...</option>';
    return;
  }

  selectedCities.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = c.name;
    if (c.name.toLowerCase() === (startingCityName || '').toLowerCase()) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });
}

async function handleSaveCustomCity() {
  const nameInput = document.getElementById('customCityName');
  const latInput = document.getElementById('customCityLat');
  const lngInput = document.getElementById('customCityLng');

  const name = nameInput.value.trim();
  const lat = parseFloat(latInput.value);
  const lng = parseFloat(lngInput.value);

  if (!name) {
    showToast('Please enter a valid city name.', 'warning');
    return;
  }
  if (isNaN(lat) || lat < -90 || lat > 90) {
    showToast('Latitude must be a valid number between -90 and 90.', 'warning');
    return;
  }
  if (isNaN(lng) || lng < -180 || lng > 180) {
    showToast('Longitude must be a valid number between -180 and 180.', 'warning');
    return;
  }

  try {
    const res = await fetch('/api/cities/add/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ name, latitude: lat, longitude: lng })
    });

    const data = await res.json();
    if (data.success) {
      availableCities.push(data.city);
      addCityToSelection(data.city);

      // Close modal & reset inputs
      const modalEl = document.getElementById('customCityModal');
      const bsModal = bootstrap.Modal.getInstance(modalEl);
      if (bsModal) bsModal.hide();
      nameInput.value = '';
      latInput.value = '';
      lngInput.value = '';

      showToast(`City '${data.city.name}' added successfully.`, 'success');
    } else {
      showToast(data.error || 'Failed to add custom city.', 'error');
    }
  } catch (err) {
    showToast('Error saving custom city: ' + err.message, 'error');
  }
}

async function handleRunOptimization() {
  if (selectedCities.length < 3) {
    showToast('At least 3 distinct cities are required for TSP route optimization.', 'warning');
    return;
  }

  const spinner = document.getElementById('optimizationSpinner');
  const spinnerText = document.getElementById('spinnerText');
  if (spinner) {
    spinner.style.display = 'flex';
    if (spinnerText) spinnerText.innerText = 'Calculating distance matrix & running Genetic Algorithm...';
  }

  // Gather config parameters
  const popSize = parseInt(document.getElementById('inputPopSize')?.value || 100);
  const generations = parseInt(document.getElementById('inputGenerations')?.value || 300);
  const mutationRate = parseFloat(document.getElementById('inputMutationRate')?.value || 0.05);
  const crossoverRate = parseFloat(document.getElementById('inputCrossoverRate')?.value || 0.90);
  const earlyStopInput = document.getElementById('inputEarlyStop')?.value;
  const earlyStopVal = earlyStopInput ? parseInt(earlyStopInput) : 50;
  const seedVal = document.getElementById('inputSeed')?.value;
  const seed = seedVal ? parseInt(seedVal) : null;
  
  const distanceMode = document.querySelector('input[name="distanceModeRadio"]:checked')?.value || 'geographic';
  const verifyBruteForce = document.getElementById('checkBruteForce')?.checked || false;

  const payload = {
    cities: selectedCities,
    starting_city: startingCityName || selectedCities[0].name,
    distance_mode: distanceMode,
    population_size: popSize,
    generations: generations,
    mutation_rate: mutationRate,
    crossover_rate: crossoverRate,
    early_stopping_generations: earlyStopVal,
    seed: seed,
    verify_brute_force: verifyBruteForce
  };

  try {
    const res = await fetch('/api/optimize/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (spinner) spinner.style.display = 'none';

    if (data.success) {
      lastOptimizationResult = data;
      displayOptimizationResults(data);
      showToast(`Optimization complete! Saved ${data.distance_saved} km (${data.improvement_percentage}%).`, 'success');

      if (data.fallback_reason) {
        showToast(`OSRM Road Service fallback: ${data.fallback_reason}. Using Haversine distance.`, 'warning');
      }
    } else {
      showToast(data.error || 'Optimization failed.', 'error');
    }
  } catch (err) {
    if (spinner) spinner.style.display = 'none';
    showToast('Optimization request error: ' + err.message, 'error');
  }
}

function displayOptimizationResults(result) {
  // 1. Reveal results & charts cards
  const resultsCard = document.getElementById('resultsCard');
  if (resultsCard) resultsCard.style.display = 'block';

  const chartsContainer = document.getElementById('chartsContainer');
  if (chartsContainer) chartsContainer.style.display = 'block';

  // 2. Metrics summary
  document.getElementById('resInitialDistance').innerText = `${result.initial_distance} km`;
  document.getElementById('resOptimizedDistance').innerText = `${result.optimized_distance} km`;
  document.getElementById('resDistanceSaved').innerText = `${result.distance_saved} km`;
  document.getElementById('resImprovementPct').innerText = `+${result.improvement_percentage}%`;
  document.getElementById('resExecTime').innerText = `Time: ${result.execution_time}s (${result.generations_run} gens)`;

  // 3. Format Route Sequences
  const initSeqBox = document.getElementById('resInitialRouteSeq');
  if (initSeqBox) {
    initSeqBox.innerHTML = result.initial_route.map((c, i) => {
      const isStart = i === 0 || i === result.initial_route.length - 1;
      const badge = `<span class="route-step ${isStart ? 'text-amber fw-bold' : 'text-white'}">${c.name}</span>`;
      return i < result.initial_route.length - 1 ? `${badge}<span class="route-arrow">&rarr;</span>` : badge;
    }).join(' ');
  }

  const optSeqBox = document.getElementById('resOptimizedRouteSeq');
  if (optSeqBox) {
    optSeqBox.innerHTML = result.optimized_route.map((c, i) => {
      const isStart = i === 0 || i === result.optimized_route.length - 1;
      const badge = `<span class="route-step ${isStart ? 'text-amber fw-bold' : 'text-emerald fw-semibold'}">${c.name}</span>`;
      return i < result.optimized_route.length - 1 ? `${badge}<span class="route-arrow">&rarr;</span>` : badge;
    }).join(' ');
  }

  // 4. Update Map with both initial (red) and optimized (green) routes
  updateMapMarkers(selectedCities, result.starting_city);
  drawInitialRouteMap(result.initial_route);
  drawOptimizedRouteMap(result.optimized_route, result.route_geometry);

  // 5. Update Visual Charts
  if (result.convergence_history) {
    renderConvergenceChart(result.convergence_history);
  }
  renderComparisonChart(result.initial_distance, result.optimized_distance, result.distance_saved);

  // 6. Brute Force Verification Card
  const bfCard = document.getElementById('bruteForceCard');
  const bfDetails = document.getElementById('bruteForceDetails');
  if (bfCard && bfDetails) {
    if (result.brute_force && result.brute_force.verified) {
      bfCard.style.display = 'block';
      const bf = result.brute_force;
      bfDetails.innerHTML = `
        <div class="row g-2">
          <div class="col-sm-4"><strong>Proven Global Optimum:</strong> ${bf.distance} km</div>
          <div class="col-sm-4"><strong>Permutations Checked:</strong> ${bf.permutations_evaluated.toLocaleString()}</div>
          <div class="col-sm-4"><strong>Exact Search Time:</strong> ${bf.execution_time}s</div>
        </div>
        <div class="mt-2">
          ${bf.ga_matches_optimal 
            ? '<span class="badge badge-ai badge-emerald"><i class="bi bi-check-circle me-1"></i> GA achieved 100% true mathematically proven global optimal tour!</span>' 
            : `<span class="badge badge-ai badge-amber"><i class="bi bi-info-circle me-1"></i> GA was within ${(Math.abs(result.optimized_distance - bf.distance)).toFixed(2)} km of mathematical optimum.</span>`}
        </div>
      `;
    } else if (result.brute_force && result.brute_force.reason) {
      bfCard.style.display = 'block';
      bfDetails.innerHTML = `<span><i class="bi bi-info-circle text-amber me-1"></i> ${result.brute_force.reason}</span>`;
    } else {
      bfCard.style.display = 'none';
    }
  }

  // Smooth scroll to results
  resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleExportCurrentResultCsv() {
  if (!lastOptimizationResult) {
    showToast('No active optimization result to export.', 'warning');
    return;
  }

  const r = lastOptimizationResult;
  const rows = [
    ['Metric', 'Value'],
    ['Run ID', r.run_id],
    ['Starting City', r.starting_city],
    ['Distance Mode', r.distance_mode],
    ['Initial Distance (km)', r.initial_distance],
    ['Optimized Distance (km)', r.optimized_distance],
    ['Distance Saved (km)', r.distance_saved],
    ['Improvement (%)', r.improvement_percentage],
    ['Execution Time (s)', r.execution_time],
    ['Generations', r.generations_run],
    ['Initial Route Order', r.initial_route.map(c => c.name).join(' -> ')],
    ['Optimized Route Order', r.optimized_route.map(c => c.name).join(' -> ')]
  ];

  let csvContent = 'data:text/csv;charset=utf-8,' + rows.map(e => e.map(val => `"${val}"`).join(',')).join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `tsp_route_result_run_${r.run_id}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function handleExportDashboardPng() {
  const target = document.querySelector('.map-viewport-wrapper') || document.getElementById('googleMapContainer') || document.getElementById('mapContainer');
  if (!target) return;

  showToast('Generating snapshot image...', 'info');

  html2canvas(target, {
    useCORS: true,
    backgroundColor: '#070d19'
  }).then(canvas => {
    const link = document.createElement('a');
    link.download = 'tsp_optimized_route_map.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
    showToast('Route map image downloaded successfully.', 'success');
  }).catch(err => {
    showToast('Could not export image: ' + err.message, 'error');
  });
}

function handleExportCurrentResultJson() {
  if (!lastOptimizationResult) {
    showToast('No active optimization result to export.', 'warning');
    return;
  }

  const r = lastOptimizationResult;
  if (r.run_id) {
    window.location.href = `/api/history/${r.run_id}/export-json/`;
    showToast('Downloading route report JSON...', 'success');
  } else {
    const blob = new Blob([JSON.stringify(r, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `betterpath_optimization_result.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast('Exported JSON successfully.', 'success');
  }
}

function handleQuickDemo() {
  showToast('Launching instant demo with Maharashtra Core dataset...', 'info');
  handleSelectPreset('maharashtra_8');
  setTimeout(() => {
    handleRunOptimization();
  }, 350);
}
