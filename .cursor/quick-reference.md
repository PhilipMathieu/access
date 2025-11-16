# Quick Reference Guide

## Common Commands

### Environment
```bash
# Create and activate uv virtual environment
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
uv pip install -e .  # Install from pyproject.toml
# OR
uv pip install -r requirements.txt
```

### Data Management
```bash
# Pull data with DVC
dvc pull

# Download OSMnx graphs
python src/download_graphs.py
```

### Scripts
```bash
# Find nearest OSMnx nodes for Census blocks
python src/find_centroids.py -g data/graphs/maine_walk.graphml input.shp

# With custom output suffix
python src/find_centroids.py -g data/graphs/maine_walk.graphml input.shp -o _custom_suffix
```

## Key File Locations

- **Graphs**: `data/graphs/maine_walk.graphml`, `data/graphs/maine_drive.graphml`
- **OSMnx Cache**: `./cache/`
- **Source Code**: `src/`
- **Notebooks**: `notebooks/` (numbered sequentially)
- **Documentation**: `docs/index.html`
- **Project Config**: `pyproject.toml`
- **Dependencies**: `requirements.txt`
- **Python Version**: `.python-version`

## Notebook Sequence

1. **0a-0e**: Data download and exploration
2. **1a-1b**: Walk time calculations
3. **2**: Block merging
4. **3**: Block analysis
5. **4**: Statistical analysis
6. **5**: Figures
7. **6-6d**: H3 analysis

## Key Libraries

- `osmnx`: Street networks
- `geopandas`: Geospatial data
- `h3pandas`: H3 hexagon indexing
- `cenpy`: Census API
- `pandas`, `numpy`: Data manipulation
- `matplotlib`, `seaborn`: Visualization

## Data Sources

- **OSM**: OpenStreetMap (via OSMnx)
- **Census**: TIGER/Line, Redistricting Data, Relationship Files
- **Maine GeoLibrary**: Conserved Lands
- **CEJST**: Climate Equity and Justice Screening Tool

## Important Notes

- Python 3.10 (specified in `.python-version`)
- Package manager: `uv`
- Virtual environment: `.venv/`
- Coordinate system: EPSG:3857 (Web Mercator)
- Analysis region: Maine state
- Primary unit: Census blocks
- Key threshold: 10-minute walk
