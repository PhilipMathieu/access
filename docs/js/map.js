// MapLibre GL JS Map Initialization with PMTiles
// PMTiles file URLs (relative to GitHub Pages)
const BLOCKS_PMTILES = './data/blocks.pmtiles';
const CONSERVED_LANDS_PMTILES = './data/conserved_lands.pmtiles';
const CEJST_PMTILES = './data/cejst.pmtiles';

// Initialize PMTiles protocol
// PMTiles library should be loaded before this script
if (typeof pmtiles === 'undefined') {
    console.error('PMTiles library not loaded. Ensure pmtiles.js is loaded before map.js');
}

// Register PMTiles protocol with MapLibre
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

// Create PMTiles instances and register with protocol
const blocksPmtiles = new pmtiles.PMTiles(BLOCKS_PMTILES);
const conservedLandsPmtiles = new pmtiles.PMTiles(CONSERVED_LANDS_PMTILES);
const cejstPmtiles = new pmtiles.PMTiles(CEJST_PMTILES);

protocol.add(blocksPmtiles);
protocol.add(conservedLandsPmtiles);
protocol.add(cejstPmtiles);

// Initialize map with Positron basemap from OpenMapTiles
const map = new maplibregl.Map({
    container: 'map',
    style: 'https://tiles.openfreemap.org/styles/positron',
    center: [-69.0, 44.5], // Maine state center
    zoom: 6.5,
    hash: true // Enable URL hash for sharing map state
});

// Add navigation controls
map.addControl(new maplibregl.NavigationControl(), 'top-right');

// Create legend control with full walk time spectrum and integrated layer toggles
const legend = document.createElement('div');
legend.id = 'map-legend';
legend.className = 'map-legend';
legend.innerHTML = `
    <h5>Map Legend</h5>
    <div class="legend-section">
        <strong>Walk Time to Conserved Land:</strong>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #508142; opacity: 1.0;"></div>
            <span>&lt;5 min walk</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #508142; opacity: 0.8;"></div>
            <span>5-10 min walk</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #508142; opacity: 0.6;"></div>
            <span>10-15 min walk</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #508142; opacity: 0.5;"></div>
            <span>15-20 min walk</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #508142; opacity: 0.3;"></div>
            <span>20-30 min walk</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #508142; opacity: 0.15;"></div>
            <span>30-45 min walk</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #508142; opacity: 0.0;"></div>
            <span>45-60 min walk</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: transparent; border: 1px solid #ccc;"></div>
            <span>60+ min walk / No access</span>
        </div>
    </div>
    <div class="legend-section">
        <strong>Other Layers:</strong>
        <div class="legend-item legend-item-with-toggle">
            <div class="legend-item-content">
                <div class="legend-color" style="background-color: #508142; opacity: 0.6;"></div>
                <span>Conserved Lands</span>
            </div>
            <button class="layer-toggle-btn" id="toggle-conserved" aria-label="Toggle conserved lands layer" title="Show/hide conserved lands">
                <i class="fas fa-eye"></i>
            </button>
        </div>
        <div class="legend-item legend-item-with-toggle">
            <div class="legend-item-content">
                <div class="legend-color" style="background-color: #d54400; opacity: 0.4;"></div>
                <span>CEJST Disadvantaged Communities</span>
            </div>
            <button class="layer-toggle-btn" id="toggle-cejst" aria-label="Toggle CEJST layer" title="Show/hide CEJST disadvantaged communities">
                <i class="fas fa-eye"></i>
            </button>
        </div>
    </div>
`;


// Create search control (positioned to avoid overlap)
const searchControl = document.createElement('div');
searchControl.id = 'search-control';
searchControl.className = 'search-control';
searchControl.innerHTML = `
    <div class="search-box">
        <input type="text" id="search-input" placeholder="Search address or location..." aria-label="Search address or location">
        <button id="search-button" aria-label="Search"><i class="fas fa-search"></i></button>
        <button id="locate-button" aria-label="Use current location"><i class="fas fa-crosshairs"></i></button>
    </div>
    <div id="search-results" class="search-results"></div>
`;

// Add legend and layer toggle to map when it loads
let controlsAdded = false;

// Function to re-add map layers (used when base map changes)
function reAddMapLayers() {
    // Add PMTiles sources
    if (!map.getSource('blocks')) {
        map.addSource('blocks', {
            type: 'vector',
            url: 'pmtiles://./data/blocks.pmtiles',
            attribution: '© US Census Bureau',
            buffer: 256
        });
    }
    
    if (!map.getSource('conserved-lands')) {
        map.addSource('conserved-lands', {
            type: 'vector',
            url: 'pmtiles://./data/conserved_lands.pmtiles',
            attribution: '© Maine GeoLibrary',
            buffer: 256
        });
    }
    
    if (!map.getSource('cejst')) {
        map.addSource('cejst', {
            type: 'vector',
            url: 'pmtiles://./data/cejst.pmtiles',
            attribution: '© Climate Equity and Justice Screening Tool',
            buffer: 256
        });
    }
    
    // Add layers
    if (!map.getLayer('blocks-fill')) {
        map.addLayer({
            id: 'blocks-fill',
            type: 'fill',
            source: 'blocks',
            'source-layer': 'blocks',
            paint: {
                'fill-color': '#508142',
                'fill-opacity': [
                    'case',
                    ['>', ['get', 'AC_5'], 0], 1.0,
                    ['>', ['get', 'AC_10'], 0], 0.8,
                    ['>', ['get', 'AC_15'], 0], 0.6,
                    ['>', ['get', 'AC_20'], 0], 0.5,
                    ['>', ['get', 'AC_30'], 0], 0.3,
                    ['>', ['get', 'AC_45'], 0], 0.15,
                    ['>', ['get', 'AC_60'], 0], 0.0,
                    0.0
                ]
            }
        });
    }
    
    if (!map.getLayer('conserved-lands-fill')) {
        map.addLayer({
            id: 'conserved-lands-fill',
            type: 'fill',
            source: 'conserved-lands',
            'source-layer': 'conserved_lands',
            paint: {
                'fill-color': '#508142',
                'fill-opacity': 0.6
            }
        });
        
        map.addLayer({
            id: 'conserved-lands-outline',
            type: 'line',
            source: 'conserved-lands',
            'source-layer': 'conserved_lands',
            paint: {
                'line-color': '#508142',
                'line-width': 1,
                'line-opacity': 0.8
            }
        });
    }
    
    // Add CEJST hatching pattern
    const svgPattern = `<svg width="8" height="8" viewBox="0 0 8 8" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <pattern id="hatch" patternUnits="userSpaceOnUse" width="8" height="8">
                <path d="M-1,1 L9,-7 M-1,9 L9,1" stroke="#d54400" stroke-width="1.5" stroke-opacity="0.6"/>
            </pattern>
        </defs>
        <rect width="8" height="8" fill="url(#hatch)"/>
    </svg>`;
    
    const img = new Image(8, 8);
    img.onload = () => {
        if (!map.hasImage('hatch-red')) {
            map.addImage('hatch-red', img);
        }
        
        if (!map.getLayer('cejst-hatching')) {
            map.addLayer({
                id: 'cejst-hatching',
                type: 'fill',
                source: 'cejst',
                'source-layer': 'cejst',
                filter: ['>', ['get', 'TC'], 0],
                paint: {
                    'fill-pattern': 'hatch-red',
                    'fill-opacity': 0.6
                }
            });
        }
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(svgPattern);
}

// Wait for map to load before adding sources and layers
map.on('load', () => {
    // Add legend and search control only once
    if (!controlsAdded) {
        const mapContainer = document.getElementById('map');
        if (!mapContainer) {
            console.error('Map container not found');
            return;
        }
        
        mapContainer.appendChild(legend);
        mapContainer.appendChild(searchControl);
        
        // Wait a moment for DOM to update, then add event listeners
        setTimeout(() => {
            // Add toggle handlers for conserved lands
            const toggleConservedBtn = document.getElementById('toggle-conserved');
            if (!toggleConservedBtn) {
                console.warn('Toggle conserved button not found');
            } else {
                const updateConservedIcon = () => {
                    const icon = toggleConservedBtn.querySelector('i');
                    if (!icon) return;
                    
                    // Check if layer exists before checking visibility
                    if (!map.getLayer('conserved-lands-fill')) {
                        // Layer doesn't exist yet, default to visible (open eye)
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                        return;
                    }
                    
                    const isVisible = map.getLayoutProperty('conserved-lands-fill', 'visibility') === 'visible';
                    if (isVisible) {
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                        toggleConservedBtn.setAttribute('aria-label', 'Hide conserved lands layer');
                        toggleConservedBtn.setAttribute('title', 'Hide conserved lands');
                    } else {
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                        toggleConservedBtn.setAttribute('aria-label', 'Show conserved lands layer');
                        toggleConservedBtn.setAttribute('title', 'Show conserved lands');
                    }
                };
                
                toggleConservedBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (!map.getLayer('conserved-lands-fill')) return;
                    
                    const isVisible = map.getLayoutProperty('conserved-lands-fill', 'visibility') === 'visible';
                    const visibility = isVisible ? 'none' : 'visible';
                    map.setLayoutProperty('conserved-lands-fill', 'visibility', visibility);
                    map.setLayoutProperty('conserved-lands-outline', 'visibility', visibility);
                    updateConservedIcon();
                });
                
                // Initialize icon state after layers are added
                map.once('idle', () => {
                    updateConservedIcon();
                });
            }
            
            // Add toggle handlers for CEJST
            const toggleCejstBtn = document.getElementById('toggle-cejst');
            if (!toggleCejstBtn) {
                console.warn('Toggle CEJST button not found');
            } else {
                const updateCejstIcon = () => {
                    const icon = toggleCejstBtn.querySelector('i');
                    if (!icon) return;
                    
                    // Check if layer exists before checking visibility
                    if (!map.getLayer('cejst-hatching')) {
                        // Layer doesn't exist yet, default to visible (open eye)
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                        return;
                    }
                    
                    const isVisible = map.getLayoutProperty('cejst-hatching', 'visibility') === 'visible';
                    if (isVisible) {
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                        toggleCejstBtn.setAttribute('aria-label', 'Hide CEJST layer');
                        toggleCejstBtn.setAttribute('title', 'Hide CEJST disadvantaged communities');
                    } else {
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                        toggleCejstBtn.setAttribute('aria-label', 'Show CEJST layer');
                        toggleCejstBtn.setAttribute('title', 'Show CEJST disadvantaged communities');
                    }
                };
                
                toggleCejstBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (!map.getLayer('cejst-hatching')) return;
                    
                    const isVisible = map.getLayoutProperty('cejst-hatching', 'visibility') === 'visible';
                    const visibility = isVisible ? 'none' : 'visible';
                    map.setLayoutProperty('cejst-hatching', 'visibility', visibility);
                    updateCejstIcon();
                });
                
                // Initialize icon state after layers are added
                map.once('idle', () => {
                    updateCejstIcon();
                });
            }
            
            // Add search functionality
            setupSearch();
        }, 10);
        
        controlsAdded = true;
    }
    
    // Add PMTiles sources and layers
    reAddMapLayers();

    // Add popup for blocks
    const popup = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: false
    });

    // Enhanced click handler for blocks with comprehensive neighborhood data
    map.on('click', 'blocks-fill', (e) => {
        const feature = e.features[0];
        const props = feature.properties;
        
        let html = '<div class="popup-content compact">';
        html += `<div class="popup-header"><strong>Census Block</strong>`;
        if (props.POP20 !== undefined && props.POP20 !== null) {
            html += ` <span class="popup-meta">Pop: ${props.POP20.toLocaleString()}</span>`;
        }
        html += `</div>`;
        
        // Walk time and access metrics
        let minWalkTime = null;
        if (props.AC_5 && props.AC_5 > 0) {
            minWalkTime = 5;
        } else if (props.AC_10 && props.AC_10 > 0) {
            minWalkTime = 10;
        } else if (props.AC_15 && props.AC_15 > 0) {
            minWalkTime = 15;
        } else if (props.AC_20 && props.AC_20 > 0) {
            minWalkTime = 20;
        } else if (props.AC_30 && props.AC_30 > 0) {
            minWalkTime = 30;
        } else if (props.AC_45 && props.AC_45 > 0) {
            minWalkTime = 45;
        } else if (props.AC_60 && props.AC_60 > 0) {
            minWalkTime = 60;
        }
        
        if (minWalkTime !== null) {
            html += `<div class="popup-row"><strong>Walk Time:</strong> ${minWalkTime} min</div>`;
            // Show only the most relevant acres accessible
            if (props.AC_5) {
                html += `<div class="popup-row"><strong>Acres (5 min):</strong> ${props.AC_5.toFixed(1)}</div>`;
            }
            if (props.AC_10) {
                html += `<div class="popup-row"><strong>Acres (10 min):</strong> ${props.AC_10.toFixed(1)}</div>`;
            }
        } else {
            html += `<div class="popup-row"><strong>Walk Time:</strong> >60 min (no access)</div>`;
        }
        
        // CEJST status if available
        if (props.TC !== undefined && props.TC !== null && props.TC > 0) {
            html += `<div class="popup-row"><strong>CEJST:</strong> Disadvantaged (TC: ${props.TC})</div>`;
        }
        
        html += '</div>';
        
        popup.setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map);
    });

    // Simple hover effect - just change cursor
    map.on('mouseenter', 'blocks-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'blocks-fill', () => {
        map.getCanvas().style.cursor = '';
    });

    // Conserved lands - no click handler, just visual layer

    // CEJST - no click handler, just visual layer

    console.log('Map loaded successfully');
});

// Error handling
map.on('error', (e) => {
    console.error('Map error:', e);
    const mapContainer = document.getElementById('map');
    if (mapContainer) {
        mapContainer.innerHTML = '<div class="alert alert-danger p-5 text-center"><h4>Error Loading Map</h4><p>There was an error loading the map. Please refresh the page or contact support if the problem persists.</p></div>';
    }
});

// Handle PMTiles load errors with user-friendly messages
let pmtilesErrors = [];

// Check PMTiles headers for errors
blocksPmtiles.getHeader().catch((error) => {
    console.error('Error loading blocks PMTiles:', error);
    pmtilesErrors.push('Census blocks data');
    showPmtilesError();
});

conservedLandsPmtiles.getHeader().catch((error) => {
    console.error('Error loading conserved lands PMTiles:', error);
    pmtilesErrors.push('Conserved lands data');
    showPmtilesError();
});

cejstPmtiles.getHeader().catch((error) => {
    console.error('Error loading CEJST PMTiles:', error);
    pmtilesErrors.push('CEJST data');
    showPmtilesError();
});

// Ensure hatch pattern is loaded after map style loads
map.on('style.load', () => {
    if (!map.hasImage('hatch-red')) {
        const svgPattern = `<svg width="8" height="8" viewBox="0 0 8 8" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <pattern id="hatch" patternUnits="userSpaceOnUse" width="8" height="8">
                    <path d="M-1,1 L9,-7 M-1,9 L9,1" stroke="#d54400" stroke-width="1.5" stroke-opacity="0.6"/>
                </pattern>
            </defs>
            <rect width="8" height="8" fill="url(#hatch)"/>
        </svg>`;
        
        const img = new Image(8, 8);
        img.onload = () => {
            if (!map.hasImage('hatch-red')) {
                map.addImage('hatch-red', img);
            }
        };
        img.src = 'data:image/svg+xml;base64,' + btoa(svgPattern);
    }
});

function showPmtilesError() {
    if (pmtilesErrors.length > 0 && !document.getElementById('pmtiles-error')) {
        const errorDiv = document.createElement('div');
        errorDiv.id = 'pmtiles-error';
        errorDiv.className = 'alert alert-warning';
        errorDiv.style.cssText = 'position: absolute; top: 80px; left: 20px; z-index: 1001; max-width: 300px;';
        errorDiv.innerHTML = `
            <h5>Data Loading Warning</h5>
            <p>The following data layers failed to load: ${pmtilesErrors.join(', ')}.</p>
            <p>Some map features may not be available.</p>
        `;
        document.getElementById('map').appendChild(errorDiv);
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 10000);
    }
}

// Handle source errors
map.on('sourcedata', (e) => {
    if (e.isSourceLoaded && e.source && e.source.type === 'vector') {
        // Source loaded successfully
        console.log(`Source ${e.sourceId} loaded successfully`);
    }
});

// Handle layer errors
map.on('styleimagemissing', (e) => {
    console.warn('Missing image:', e.id);
    // For now, just log - we can add fallback images later if needed
});

// Search functionality (IMP-006)
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const locateButton = document.getElementById('locate-button');
    const searchResults = document.getElementById('search-results');
    
    if (!searchInput || !searchButton || !locateButton || !searchResults) {
        console.warn('Search elements not found');
        return;
    }
    
    // Geocoding using Nominatim (OpenStreetMap's geocoding service)
    async function geocode(query) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&bounded=1&viewbox=-71.0,43.0,-66.0,47.0`
            );
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Geocoding error:', error);
            return [];
        }
    }
    
    // Find nearest conserved land
    async function findNearestConservedLand(lng, lat) {
        // This would require querying the conserved lands layer
        // For now, we'll zoom to the location and show a message
        map.flyTo({
            center: [lng, lat],
            zoom: 14,
            duration: 1500
        });
        
        // Show a marker at the location
        if (map.getLayer('user-location')) {
            map.removeLayer('user-location');
            map.removeSource('user-location');
        }
        
        map.addSource('user-location', {
            type: 'geojson',
            data: {
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: [lng, lat]
                }
            }
        });
        
        map.addLayer({
            id: 'user-location',
            type: 'circle',
            source: 'user-location',
            paint: {
                'circle-radius': 8,
                'circle-color': '#4285F4',
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff'
            }
        });
        
        // Show popup with message
        new maplibregl.Popup()
            .setLngLat([lng, lat])
            .setHTML('<div class="popup-content"><h4>Your Location</h4><p>Use the map to explore conserved lands near you.</p></div>')
            .addTo(map);
    }
    
    // Search button handler
    searchButton.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        if (!query) return;
        
        searchResults.innerHTML = '<p>Searching...</p>';
        const results = await geocode(query);
        
        if (results.length === 0) {
            searchResults.innerHTML = '<p>No results found. Try a different search term.</p>';
            return;
        }
        
        let html = '<ul class="search-results-list">';
        results.forEach((result, index) => {
            html += `<li class="search-result-item" data-lng="${result.lon}" data-lat="${result.lat}" data-display="${result.display_name}">
                <strong>${result.display_name}</strong>
            </li>`;
        });
        html += '</ul>';
        searchResults.innerHTML = html;
        
        // Add click handlers to results
        document.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const lng = parseFloat(item.dataset.lng);
                const lat = parseFloat(item.dataset.lat);
                const displayName = item.dataset.display;
                
                map.flyTo({
                    center: [lng, lat],
                    zoom: 14,
                    duration: 1500
                });
                
                new maplibregl.Popup()
                    .setLngLat([lng, lat])
                    .setHTML(`<div class="popup-content"><h4>${displayName}</h4></div>`)
                    .addTo(map);
                
                searchResults.innerHTML = '';
                searchInput.value = '';
            });
        });
    });
    
    // Enter key handler
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchButton.click();
        }
    });
    
    // Location button handler (FR-003)
    locateButton.addEventListener('click', () => {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser.');
            return;
        }
        
        locateButton.disabled = true;
        locateButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lng = position.coords.longitude;
                const lat = position.coords.latitude;
                findNearestConservedLand(lng, lat);
                locateButton.disabled = false;
                locateButton.innerHTML = '<i class="fas fa-crosshairs"></i>';
            },
            (error) => {
                alert('Unable to retrieve your location. Please check your browser settings.');
                locateButton.disabled = false;
                locateButton.innerHTML = '<i class="fas fa-crosshairs"></i>';
            }
        );
    });
}

// Measurement state (global to persist across map events)
let isMeasuring = false;
let measurePoints = [];
let measureClickHandler = null;

// Calculate distance between two points (Haversine formula)
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // Earth radius in meters
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// Custom MapLibre Control for Tool Buttons (IMP-006)
class ToolControl {
    constructor() {
        this._container = document.createElement('div');
        this._container.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    }

    onAdd(map) {
        this._map = map;
        
        // Add measurement button
        const measureButton = document.createElement('button');
        measureButton.id = 'measure-button';
        measureButton.className = 'maplibregl-ctrl-icon';
        measureButton.type = 'button';
        measureButton.innerHTML = '<i class="fas fa-ruler"></i>';
        measureButton.title = 'Measure Distance';
        measureButton.setAttribute('aria-label', 'Measure distance');
        measureButton.setAttribute('tabindex', '0');
        
        // Measurement toggle handler
        measureButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            isMeasuring = !isMeasuring;
            
            if (isMeasuring) {
                measureButton.classList.add('active');
                this._map.getCanvas().style.cursor = 'crosshair';
                measurePoints = [];
                
                // Remove existing measurement if any
                if (this._map.getLayer('measure-line')) {
                    this._map.removeLayer('measure-line');
                }
                if (this._map.getSource('measure-line')) {
                    this._map.removeSource('measure-line');
                }
                
                // Add click handler for measurement
                if (!measureClickHandler) {
                    const mapInstance = this._map;
                    measureClickHandler = (e) => {
                        if (!isMeasuring) return;
                        
                        measurePoints.push([e.lngLat.lng, e.lngLat.lat]);
                        
                        if (measurePoints.length === 1) {
                            // First point - create source and layer
                            mapInstance.addSource('measure-line', {
                                type: 'geojson',
                                data: {
                                    type: 'Feature',
                                    geometry: {
                                        type: 'LineString',
                                        coordinates: measurePoints
                                    }
                                }
                            });
                            
                            mapInstance.addLayer({
                                id: 'measure-line',
                                type: 'line',
                                source: 'measure-line',
                                paint: {
                                    'line-color': '#4285F4',
                                    'line-width': 2,
                                    'line-dasharray': [2, 2]
                                }
                            });
                        } else {
                            // Update line
                            if (mapInstance.getSource('measure-line')) {
                                mapInstance.getSource('measure-line').setData({
                                    type: 'Feature',
                                    geometry: {
                                        type: 'LineString',
                                        coordinates: measurePoints
                                    }
                                });
                                
                                // Calculate distance
                                let totalDistance = 0;
                                for (let i = 1; i < measurePoints.length; i++) {
                                    const p1 = measurePoints[i - 1];
                                    const p2 = measurePoints[i];
                                    totalDistance += calculateDistance(p1[1], p1[0], p2[1], p2[0]);
                                }
                                
                                // Show distance in popup
                                const distanceKm = totalDistance / 1000;
                                const distanceMi = distanceKm * 0.621371;
                                const distanceText = distanceKm < 1 
                                    ? `${(totalDistance).toFixed(0)} m (${(totalDistance * 3.28084).toFixed(0)} ft)`
                                    : `${distanceKm.toFixed(2)} km (${distanceMi.toFixed(2)} mi)`;
                                
                                new maplibregl.Popup()
                                    .setLngLat(e.lngLat)
                                    .setHTML(`<div class="popup-content compact"><div class="popup-header"><strong>Distance</strong></div><div class="popup-row">${distanceText}</div><div class="popup-row"><small>Click to add more points, or click measure button to stop</small></div></div>`)
                                    .addTo(mapInstance);
                            }
                        }
                    };
                    this._map.on('click', measureClickHandler);
                }
            } else {
                measureButton.classList.remove('active');
                this._map.getCanvas().style.cursor = '';
                
                // Remove measurement layer
                if (this._map.getLayer('measure-line')) {
                    this._map.removeLayer('measure-line');
                }
                if (this._map.getSource('measure-line')) {
                    this._map.removeSource('measure-line');
                }
                
                // Remove click handler
                if (measureClickHandler) {
                    this._map.off('click', measureClickHandler);
                    measureClickHandler = null;
                }
                
                measurePoints = [];
            }
        });
        
        // Keyboard support
        measureButton.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                measureButton.click();
            }
        });
        
        // Add print button
        const printButton = document.createElement('button');
        printButton.id = 'print-button';
        printButton.className = 'maplibregl-ctrl-icon';
        printButton.type = 'button';
        printButton.innerHTML = '<i class="fas fa-print"></i>';
        printButton.title = 'Print Map';
        printButton.setAttribute('aria-label', 'Print map');
        printButton.setAttribute('tabindex', '0');
        printButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            window.print();
        });
        printButton.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                printButton.click();
            }
        });
        
        // Add export button
        const exportButton = document.createElement('button');
        exportButton.id = 'export-button';
        exportButton.className = 'maplibregl-ctrl-icon';
        exportButton.type = 'button';
        exportButton.innerHTML = '<i class="fas fa-download"></i>';
        exportButton.title = 'Export Map';
        exportButton.setAttribute('aria-label', 'Export map');
        exportButton.setAttribute('tabindex', '0');
        exportButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Export map as image - wait for map to render
            this._map.once('idle', () => {
                const canvas = this._map.getCanvas();
                canvas.toBlob((blob) => {
                    if (blob) {
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'map-export.png';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }
                }, 'image/png');
            });
        });
        exportButton.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                exportButton.click();
            }
        });
        
        // Add buttons to container
        this._container.appendChild(measureButton);
        this._container.appendChild(printButton);
        this._container.appendChild(exportButton);
        
        return this._container;
    }

    onRemove() {
        // Clean up measurement handler if active
        if (measureClickHandler) {
            this._map.off('click', measureClickHandler);
            measureClickHandler = null;
        }
        if (isMeasuring) {
            isMeasuring = false;
            this._map.getCanvas().style.cursor = '';
        }
        this._container.parentNode.removeChild(this._container);
        this._map = undefined;
    }
}

// Initialize tool controls on map load
map.on('load', () => {
    map.addControl(new ToolControl(), 'top-right');
});

// Keyboard navigation support (FR-003 - Accessibility)
document.addEventListener('keydown', (e) => {
    // Escape key closes popup
    if (e.key === 'Escape') {
        const popups = document.querySelectorAll('.maplibregl-popup');
        popups.forEach(popup => {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        });
    }
    
    // Tab navigation for map controls
    if (e.key === 'Tab') {
        // Ensure focus is visible
        const focused = document.activeElement;
        if (focused && (focused.classList.contains('map-control-button') || 
            focused.id === 'search-input' || 
            focused.id === 'basemap-select')) {
            focused.style.outline = '2px solid #508142';
            focused.style.outlineOffset = '2px';
        }
    }
});

// Remove focus outline on mouse click (but keep for keyboard)
document.addEventListener('mousedown', () => {
    document.body.classList.add('using-mouse');
});

document.addEventListener('keydown', () => {
    document.body.classList.remove('using-mouse');
});

// Screen reader announcements (FR-003 - Accessibility)
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

// Add ARIA labels to map controls
map.on('load', () => {
    const mapContainer = document.getElementById('map');
    if (mapContainer) {
        mapContainer.setAttribute('role', 'application');
        mapContainer.setAttribute('aria-label', 'Interactive map showing access to conserved lands in Maine');
    }
});

