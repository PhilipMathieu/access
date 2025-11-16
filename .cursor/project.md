# Access Project Documentation

## Project Overview

**Access** is a spatial accessibility analysis project focused on analyzing access to conservation land in Maine. The project calculates walking times from Census block centroids to conserved properties and analyzes demographic disparities in access, particularly for communities identified as "disadvantaged" by the Climate Equity and Justice Screening Tool (CEJST).

### Key Findings
- 75% of Mainers lack access to conservation land within a 10-minute walk
- Communities identified as "disadvantaged" by CEJST are 24% more likely to lack access to conserved land within a 10-minute walk
- CEJST equity metrics reveal inequities not visible in purely demographic data

## Project Structure

```
access/
├── src/                    # Python utility scripts
│   ├── download_graphs.py  # Downloads OSMnx street network graphs for Maine
│   ├── find_centroids.py   # Finds nearest OSMnx nodes for Census block centroids
│   └── h3utils.py          # Utilities for H3 hexagon spatial indexing
├── notebooks/              # Jupyter notebook analysis workflow (numbered sequentially)
│   ├── 0a-0e/             # Data download and exploration
│   ├── 1a-1b/             # Walk time calculations (tracts and blocks)
│   ├── 2/                 # Block merging
│   ├── 3/                 # Block analysis
│   ├── 4/                 # Statistical analysis
│   ├── 5/                 # Figure generation
│   └── 6-6d/              # H3 hexagon analysis and joins
├── data/                   # Data files (managed with Git LFS)
├── docs/                   # Documentation website (HTML)
├── figs/                   # Generated figures
├── cache/                  # OSMnx cache directory
├── pyproject.toml          # uv project configuration
├── requirements.txt        # Python dependencies (alternative)
├── .python-version         # Python version specification
├── README.md               # Project readme
└── NOTES.md                # Reference notes and links
```

## Technology Stack

### Core Libraries
- **OSMnx**: Street network graphs from OpenStreetMap (walking/driving networks)
- **GeoPandas**: Geospatial data manipulation
- **H3**: Hexagon spatial indexing system (via h3pandas)
- **Cenpy**: US Census API wrapper
- **Pandas/NumPy**: Data manipulation
- **Matplotlib/Seaborn**: Visualization
- **Jupyter**: Interactive analysis notebooks

### Environment Management
- **uv**: Primary environment and package management (see `pyproject.toml`)
- Python version: 3.10 (specified in `.python-version`)
- Virtual environment: `.venv/` (created with `uv venv`)

### Data Version Control
- **Git LFS**: Data files in `data/` are managed with Git LFS (see `.gitattributes`)

## Methodology

The analysis follows this workflow:

1. **Network Graph Download**: Download street network graphs for Maine (walking and driving) using OSMnx
2. **Centroid Mapping**: Find nearest OSMnx nodes for each Census block centroid
3. **Walk Time Calculation**: Calculate walking times from block centroids to conserved lands at multiple time thresholds (5, 10, 15, 20, 30, 45, 60 minutes)
4. **Area Calculation**: Calculate total acres of conserved land reachable within each time threshold
5. **Demographic Integration**: Add Census demographic data via API
6. **Equity Analysis**: Identify blocks labeled as "disadvantaged" by CEJST
7. **Statistical Analysis**: Calculate differences in access for disadvantaged communities
8. **Visualization**: Generate maps and figures for publication

## Data Sources

### Primary Data
- **OpenStreetMap**: Street network data (via OSMnx)
- **US Census Bureau**:
  - TIGER/Line Shapefiles (Census block boundaries)
  - P.L. 94-171 Redistricting Data (demographics)
  - Census Block Relationship Files (for H3 mapping)
- **Maine GeoLibrary**: Maine Conserved Lands dataset
- **Climate Equity and Justice Screening Tool (CEJST)**: Disadvantaged community identification

### Data Storage
- Data files are managed with Git LFS (Git Large File Storage)
- OSMnx caches network graphs in `./cache/`
- Large datasets stored in `data/` directory

## Source Code

### `src/download_graphs.py`
Downloads and saves OSMnx street network graphs for Maine:
- Driving network: `data/graphs/maine_drive.graphml`
- Walking network: `data/graphs/maine_walk.graphml`
- Requires >10GB RAM
- Uses OSMnx cache in `./cache/`

### `src/find_centroids.py`
Command-line utility to find nearest OSMnx nodes for Census block centroids:
```bash
python src/find_centroids.py -g data/graphs/maine_walk.graphml input.shp
```
- Loads OSMnx graph and projects to EPSG:3857
- Finds nearest nodes using spatial index
- Adds `osmid` column to input shapefile
- Outputs shapefile with `_with_nodes` suffix

### `src/h3utils.py`
Utilities for H3 hexagon spatial indexing:
- `h3_merge()`: Merges dataframes with H3 relationship files
- `h3_weight()`: Weighted aggregation by H3 fraction
- `h3_weight_pop()`: Population-weighted aggregation
- `h3_plot()`: Visualization of H3 hexagon data
- `h3_to_h3t()`: Converts to H3J JSON format with schema validation

## Notebook Workflow

The notebooks follow a numbered sequence:

### Phase 0: Data Download & Exploration (0a-0e)
- `0a download_graphs.ipynb`: Download street network graphs
- `0a view_graph.ipynb`: Visualize network graphs
- `0b centroid_search_experiment.ipynb`: Experiment with centroid finding
- `0c portland_isochrones.ipynb`: Isochrone analysis for Portland
- `0d portland_greenspace_colab.ipynb`: Greenspace analysis (Colab)
- `0e portland_greenspace_h3.ipynb`: H3-based greenspace analysis

### Phase 1: Walk Time Calculations (1a-1b)
- `1a walk_times_tracts.ipynb`: Walk time calculations at tract level
- `1b walk_times_blocks.ipynb`: Walk time calculations at block level

### Phase 2: Data Merging (2)
- `2 merge_blocks.ipynb`: Merge block-level data

### Phase 3: Analysis (3-4)
- `3 analysis_blocks.ipynb`: Block-level analysis
- `4 statistical_analysis.ipynb`: Statistical analysis of disparities

### Phase 4: Visualization (5)
- `5 figures.ipynb`: Generate publication figures

### Phase 5: H3 Analysis (6-6d)
- `6 h3.ipynb`: H3 hexagon analysis
- `6b h3 relationship file.ipynb`: H3 relationship file processing
- `6c hex joins.ipynb`: Hexagon joins
- `6d h3j.ipynb`: H3J format generation

## Development Setup

### Environment Setup
1. Install `uv` (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
   uv pip install -e .  # Install from pyproject.toml
   # OR
   uv pip install -r requirements.txt  # Alternative: install from requirements.txt
   ```

3. Install Python 3.10 (if needed):
   ```bash
   uv python install 3.10
   ```

### Data Setup
- Data files are managed with Git LFS
- Pull data with: `git lfs pull` (or `git clone` will automatically pull LFS files)
- OSMnx will cache network graphs automatically in `./cache/`

### Running Scripts
- Download graphs: `python src/download_graphs.py`
- Find centroids: `python src/find_centroids.py -g <graph> <input.shp>`

## Key Concepts

### Spatial Indexing
- **OSMnx**: Street network graphs with nodes (intersections) and edges (roads)
- **H3**: Hexagon-based spatial indexing for efficient spatial joins and aggregation
- **Census Blocks**: Smallest geographic unit for Census data (~100-300 people)

### Coordinate Systems
- **EPSG:3857** (Web Mercator): Used for OSMnx graphs and spatial operations
- **WGS84** (EPSG:4326): Standard geographic coordinates

### Access Metrics
- Walking time thresholds: 5, 10, 15, 20, 30, 45, 60 minutes
- Access measured as total acres of conserved land reachable within each threshold
- Analysis focuses on 10-minute walk threshold for key findings

## Outputs

- **Documentation Website**: `docs/index.html` - Public-facing analysis results
- **Figures**: Generated in `figs/` directory
- **H3J Format**: JSON format for H3 hexagon data (see `h3utils.py`)

## Notes

- Project uses `uv` for environment and package management
- Virtual environment: `.venv/` (created with `uv venv`)
- OSMnx cache stored in `./cache/` (gitignored)
- Large data files managed with Git LFS
- Analysis focuses on Maine state
- Primary analysis unit: Census blocks
- Key equity metric: CEJST disadvantaged community designation

## References

See `NOTES.md` for:
- Census data product documentation links
- Package documentation links
- Statistical test guidance
