// Print page map initialization
// PMTiles file URLs
const BLOCKS_PMTILES = './data/blocks.pmtiles';
const CONSERVED_LANDS_PMTILES = './data/conserved_lands.pmtiles';
const CEJST_PMTILES = './data/cejst.pmtiles';

// Initialize PMTiles protocol
if (typeof pmtiles === 'undefined') {
    console.error('PMTiles library not loaded. Ensure pmtiles.js is loaded before print-map.js');
}

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

// Create PMTiles instances
const blocksPmtiles = new pmtiles.PMTiles(BLOCKS_PMTILES);
const conservedLandsPmtiles = new pmtiles.PMTiles(CONSERVED_LANDS_PMTILES);
const cejstPmtiles = new pmtiles.PMTiles(CEJST_PMTILES);

protocol.add(blocksPmtiles);
protocol.add(conservedLandsPmtiles);
protocol.add(cejstPmtiles);

// Get map center and zoom from URL parameters (passed from main page)
const urlParams = new URLSearchParams(window.location.search);
const center = urlParams.get('center') ? 
    urlParams.get('center').split(',').map(Number) : 
    [-69.0, 44.5]; // Default to Maine center
const zoom = urlParams.get('zoom') ? 
    parseFloat(urlParams.get('zoom')) : 
    6.5; // Default zoom

// Initialize map
const map = new maplibregl.Map({
    container: 'map',
    style: 'https://tiles.openfreemap.org/styles/positron',
    center: center,
    zoom: zoom,
    hash: false // Don't use URL hash on print page
});

// Add default MapLibre scale control after map is ready
map.on('style.load', () => {
    map.addControl(new maplibregl.ScaleControl({
        maxWidth: 100,
        unit: 'metric'
    }), 'bottom-left');
});

// Update print metadata
function updatePrintMetadata() {
    const now = new Date();
    const mapCenter = map.getCenter();
    const mapZoom = map.getZoom();

    // Update date in footer
    const printDateFooter = document.getElementById('print-date-footer');
    if (printDateFooter) {
        printDateFooter.textContent = now.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // Update center coordinates
    const printCenter = document.getElementById('print-center');
    if (printCenter) {
        printCenter.textContent = `${mapCenter.lat.toFixed(3)}°N, ${Math.abs(mapCenter.lng).toFixed(3)}°W`;
    }

    // Update zoom level
    const printZoom = document.getElementById('print-zoom');
    if (printZoom) {
        printZoom.textContent = mapZoom.toFixed(1);
    }

    // Update scale
    updatePrintScale();
}

// Calculate scale bar
function updatePrintScale() {
    const y = map.getCenter().lat;
    const metersPerPixel = 40075017 * Math.abs(Math.cos(y * Math.PI / 180)) / Math.pow(2, map.getZoom() + 8);

    // Scale bar is 25mm on print (approximately 94 pixels at 96 DPI)
    const scaleBarWidthPixels = 94;
    const scaleBarMeters = metersPerPixel * scaleBarWidthPixels;

    // Convert to appropriate unit (km or miles)
    let scaleText;
    let scaleRatio;

    if (scaleBarMeters >= 1000) {
        const km = scaleBarMeters / 1000;
        let roundedKm;
        if (km >= 10) {
            roundedKm = Math.round(km / 10) * 10;
        } else if (km >= 5) {
            roundedKm = 5;
        } else if (km >= 2) {
            roundedKm = 2;
        } else {
            roundedKm = 1;
        }
        scaleText = `0 — ${roundedKm} km`;
        scaleRatio = `1:${Math.round(roundedKm * 1000 / 0.025).toLocaleString()}`; // 25mm in meters
    } else {
        let roundedM;
        if (scaleBarMeters >= 500) {
            roundedM = 500;
        } else if (scaleBarMeters >= 200) {
            roundedM = 200;
        } else if (scaleBarMeters >= 100) {
            roundedM = 100;
        } else {
            roundedM = 50;
        }
        scaleText = `0 — ${roundedM} m`;
        scaleRatio = `1:${Math.round(roundedM / 0.025).toLocaleString()}`;
    }

    // Update scale distance label
    const printScaleDistance = document.getElementById('print-scale-distance');
    if (printScaleDistance) {
        printScaleDistance.textContent = scaleText;
    }
}

// Add map sources and layers
function addMapLayers() {
    // Add blocks source
    if (!map.getSource('blocks')) {
        map.addSource('blocks', {
            type: 'vector',
            url: 'pmtiles://./data/blocks.pmtiles',
            attribution: '© US Census Bureau',
            buffer: 256
        });
    }

    // Add conserved lands source
    if (!map.getSource('conserved-lands')) {
        map.addSource('conserved-lands', {
            type: 'vector',
            url: 'pmtiles://./data/conserved_lands.pmtiles',
            attribution: '© Maine GeoLibrary',
            buffer: 256
        });
    }

    // Add CEJST source
    if (!map.getSource('cejst')) {
        map.addSource('cejst', {
            type: 'vector',
            url: 'pmtiles://./data/cejst.pmtiles',
            attribution: '© Climate Equity and Justice Screening Tool',
            buffer: 256
        });
    }

    // Add blocks layer
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

    // Add conserved lands layer
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

// Initialize map when loaded
map.on('load', () => {
    addMapLayers();
    updatePrintMetadata();

    // Update metadata when map moves
    map.on('moveend', () => {
        updatePrintMetadata();
    });

    // Resize map to fit container
    setTimeout(() => {
        map.resize();
    }, 100);
});

// Handle window resize
window.addEventListener('resize', () => {
    map.resize();
});

// Handle print
window.addEventListener('beforeprint', () => {
    map.resize();
    updatePrintMetadata();
});

