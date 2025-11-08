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

// Create legend control
const legend = document.createElement('div');
legend.id = 'map-legend';
legend.className = 'map-legend';
legend.innerHTML = `
    <h5>Map Legend</h5>
    <div class="legend-item">
        <div class="legend-color" style="background-color: #508142; opacity: 0.5;"></div>
        <span>Census Blocks (darker = shorter walk time)</span>
    </div>
    <div class="legend-item">
        <div class="legend-color" style="background-color: #508142; opacity: 0.6;"></div>
        <span>Conserved Lands</span>
    </div>
    <div class="legend-item">
        <div class="legend-color" style="background-color: #d54400; opacity: 0.4;"></div>
        <span>CEJST Disadvantaged Communities</span>
    </div>
           <div class="legend-item">
               <div class="legend-color" style="background-color: #508142; opacity: 1.0;"></div>
               <span>&lt;5 min walk (dark green)</span>
           </div>
           <div class="legend-item">
               <div class="legend-color" style="background-color: #508142; opacity: 0.0;"></div>
               <span>60+ min walk (transparent)</span>
           </div>
`;

// Create layer toggle control
const layerToggle = document.createElement('div');
layerToggle.id = 'layer-toggle';
layerToggle.className = 'layer-toggle';
layerToggle.innerHTML = `
    <h5>Layers</h5>
    <label>
        <input type="checkbox" id="toggle-blocks" checked>
        Census Blocks
    </label>
    <label>
        <input type="checkbox" id="toggle-conserved" checked>
        Conserved Lands
    </label>
    <label>
        <input type="checkbox" id="toggle-cejst" checked>
        CEJST Disadvantaged
    </label>
`;

// Add legend and layer toggle to map when it loads
let controlsAdded = false;

// Wait for map to load before adding sources and layers
map.on('load', () => {
    // Add legend and layer toggle only once
    if (!controlsAdded) {
        document.getElementById('map').appendChild(legend);
        document.getElementById('map').appendChild(layerToggle);
        
        // Add toggle handlers
        document.getElementById('toggle-blocks').addEventListener('change', (e) => {
            const visibility = e.target.checked ? 'visible' : 'none';
            map.setLayoutProperty('blocks-fill', 'visibility', visibility);
            map.setLayoutProperty('blocks-outline', 'visibility', visibility);
        });
        
        document.getElementById('toggle-conserved').addEventListener('change', (e) => {
            const visibility = e.target.checked ? 'visible' : 'none';
            map.setLayoutProperty('conserved-lands-fill', 'visibility', visibility);
            map.setLayoutProperty('conserved-lands-outline', 'visibility', visibility);
        });
        
        document.getElementById('toggle-cejst').addEventListener('change', (e) => {
            const visibility = e.target.checked ? 'visible' : 'none';
            map.setLayoutProperty('cejst-hatching', 'visibility', visibility);
        });
        
        controlsAdded = true;
    }
    // Add PMTiles sources
    map.addSource('blocks', {
        type: 'vector',
        url: 'pmtiles://./data/blocks.pmtiles',
        attribution: '© US Census Bureau'
    });

    map.addSource('conserved-lands', {
        type: 'vector',
        url: 'pmtiles://./data/conserved_lands.pmtiles',
        attribution: '© Maine GeoLibrary'
    });

    map.addSource('cejst', {
        type: 'vector',
        url: 'pmtiles://./data/cejst.pmtiles',
        attribution: '© Climate Equity and Justice Screening Tool'
    });

    // Add Census blocks layer with clear walk times
    // Dark green for <5 min walk, progressing to transparent for 60+ min walk
    // Using primary green color #508142 with opacity inversely related to walk time
    // Calculate minimum walk time from AC_* fields (acres accessible within each time period)
    map.addLayer({
        id: 'blocks-fill',
        type: 'fill',
        source: 'blocks',
        'source-layer': 'blocks',
        paint: {
            'fill-color': '#508142', // Primary green from CSS
            'fill-opacity': [
                'case',
                // If AC_5 > 0, minimum walk time is 5 min = 100% opacity (dark green)
                ['>', ['get', 'AC_5'], 0], 1.0,
                // If AC_10 > 0, minimum walk time is 10 min = 80% opacity
                ['>', ['get', 'AC_10'], 0], 0.8,
                // If AC_15 > 0, minimum walk time is 15 min = 60% opacity
                ['>', ['get', 'AC_15'], 0], 0.6,
                // If AC_20 > 0, minimum walk time is 20 min = 50% opacity
                ['>', ['get', 'AC_20'], 0], 0.5,
                // If AC_30 > 0, minimum walk time is 30 min = 30% opacity
                ['>', ['get', 'AC_30'], 0], 0.3,
                // If AC_45 > 0, minimum walk time is 45 min = 15% opacity
                ['>', ['get', 'AC_45'], 0], 0.15,
                // If AC_60 > 0, minimum walk time is 60 min = 0% opacity (transparent)
                ['>', ['get', 'AC_60'], 0], 0.0,
                // Default: no conserved land accessible = transparent
                0.0
            ]
        }
    });

    // Add block outlines
    map.addLayer({
        id: 'blocks-outline',
        type: 'line',
        source: 'blocks',
        'source-layer': 'blocks',
        paint: {
            'line-color': '#508142',
            'line-width': 0.5,
            'line-opacity': 0.3
        }
    });

    // Add conserved lands layer with semi-transparent green fill
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

    // Add conserved lands outline
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

    // Create red hatching pattern using SVG
    // This creates a diagonal stripe pattern
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
        
        // Add CEJST layer with red hatching pattern for disadvantaged communities only
        // Filter: TC > 0 means the community is disadvantaged
        // Only add layer if it doesn't exist yet
        if (!map.getLayer('cejst-hatching')) {
            map.addLayer({
                id: 'cejst-hatching',
                type: 'fill',
                source: 'cejst',
                'source-layer': 'cejst',
                filter: ['>', ['get', 'TC'], 0], // Only show disadvantaged communities (TC > 0)
                paint: {
                    'fill-pattern': 'hatch-red',
                    'fill-opacity': 0.6
                }
            });
        }
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(svgPattern);

    // Add popup for blocks
    const popup = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: false
    });

    // Add click handler for blocks
    map.on('click', 'blocks-fill', (e) => {
        const feature = e.features[0];
        const props = feature.properties;
        
        let html = '<div class="popup-content">';
        html += `<h4>Census Block</h4>`;
        if (props.GEOID20) {
            html += `<p><strong>GEOID:</strong> ${props.GEOID20}</p>`;
        }
        if (props.NAME20) {
            html += `<p><strong>Name:</strong> ${props.NAME20}</p>`;
        }
        if (props.POP20 !== undefined) {
            html += `<p><strong>Population:</strong> ${props.POP20}</p>`;
        }
        // Calculate minimum walk time from AC_* fields
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
            html += `<p><strong>Minimum Walk Time:</strong> ${minWalkTime} minutes</p>`;
        } else {
            html += `<p><strong>Minimum Walk Time:</strong> >60 minutes (no conserved land accessible)</p>`;
        }
        html += '</div>';
        
        popup.setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map);
    });

    // Add hover effect for blocks
    map.on('mouseenter', 'blocks-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'blocks-fill', () => {
        map.getCanvas().style.cursor = '';
    });

    // Add click handler for conserved lands
    map.on('click', 'conserved-lands-fill', (e) => {
        const feature = e.features[0];
        const props = feature.properties;
        
        let html = '<div class="popup-content">';
        html += `<h4>Conserved Land</h4>`;
        if (props.PARCEL_NAM) {
            html += `<p><strong>Name:</strong> ${props.PARCEL_NAM}</p>`;
        }
        if (props.PROJECT) {
            html += `<p><strong>Project:</strong> ${props.PROJECT}</p>`;
        }
        if (props.RPT_AC) {
            html += `<p><strong>Acres:</strong> ${props.RPT_AC}</p>`;
        }
        html += '</div>';
        
        popup.setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map);
    });

    // Add hover effect for conserved lands
    map.on('mouseenter', 'conserved-lands-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'conserved-lands-fill', () => {
        map.getCanvas().style.cursor = '';
    });

    // Add click handler for CEJST
    map.on('click', 'cejst-hatching', (e) => {
        const feature = e.features[0];
        const props = feature.properties;
        
        let html = '<div class="popup-content">';
        html += `<h4>CEJST Disadvantaged Community</h4>`;
        if (props.GEOID20) {
            html += `<p><strong>GEOID:</strong> ${props.GEOID20}</p>`;
        } else if (props.GEOID10) {
            html += `<p><strong>GEOID:</strong> ${props.GEOID10}</p>`;
        }
        if (props.TC !== undefined && props.TC !== null) {
            html += `<p><strong>Threshold Count:</strong> ${props.TC}</p>`;
        }
        if (props.CC !== undefined && props.CC !== null) {
            html += `<p><strong>Census Count:</strong> ${props.CC}</p>`;
        }
        html += '</div>';
        
        popup.setLngLat(e.lngLat)
            .setHTML(html)
            .addTo(map);
    });

    // Add hover effect for CEJST
    map.on('mouseenter', 'cejst-hatching', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'cejst-hatching', () => {
        map.getCanvas().style.cursor = '';
    });

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

