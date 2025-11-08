# Data Dictionary

This document provides a comprehensive guide to all data files in the Access project, their sources, processing steps, and usage. Use this to understand which files to update for different purposes (e.g., webmap updates, analysis).

## Table of Contents

- [Webmap Files](#webmap-files)
- [Raw Data Sources](#raw-data-sources)
- [Processed Data Files](#processed-data-files)
- [Data Processing Workflows](#data-processing-workflows)
- [Update Procedures](#update-procedures)

---

## Webmap Files

**Location**: `docs/data/`

These are the files used by the interactive webmap (`docs/index.html`). **Update these when you want to refresh the webmap.**

| File | Source | Description | Update Command |
|------|--------|-------------|----------------|
| `blocks.pmtiles` | `data/blocks/*_with_nodes.shp.zip` | Census blocks with walk times and OSMnx node IDs | See [Blocks Workflow](#blocks-workflow) |
| `conserved_lands.pmtiles` | `data/conserved_lands/*_with_nodes.shp.zip` | Maine conserved lands with OSMnx node IDs | See [Conserved Lands Workflow](#conserved-lands-workflow) |
| `cejst.pmtiles` | `data/cejst-maine.shp` | CEJST disadvantaged communities (Maine only) | See [CEJST Workflow](#cejst-workflow) |

### Webmap Update Checklist

To update the webmap with new data:

1. **Update source data** (see [Update Procedures](#update-procedures))
2. **Process data** (add centroids/node IDs if needed)
3. **Generate PMTiles**:
   ```bash
   # Blocks
   python src/convert_to_pmtiles.py data/blocks/*_with_nodes.shp.zip docs/data/blocks.pmtiles -l blocks
   
   # Conserved Lands
   python src/convert_to_pmtiles.py data/conserved_lands/*_with_nodes.shp.zip docs/data/conserved_lands.pmtiles -l conserved_lands
   
   # CEJST
   python src/convert_to_pmtiles.py data/cejst-maine.shp docs/data/cejst.pmtiles -l cejst
   ```
4. **Commit and push** the updated PMTiles files

---

## Raw Data Sources

**Location**: `data/`

These are the original data files downloaded from external sources.

### Census TIGER/Line Blocks

| File/Directory | Source | Description | Update Command |
|----------------|--------|-------------|----------------|
| `data/blocks/` | US Census Bureau | Census block boundaries for Maine (FIPS 23) | `python src/update_data_sources.py --source "Census TIGER/Line Blocks"` |
| `data/blocks/tl_2020_23_tabblock20.shp` | Census TIGER/Line 2020 | Main shapefile (may be in subdirectory) | Auto-downloaded via update script |

**Source URL**: `https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_23_tabblock20.zip`

**Metadata**: Stored in `data/data_source_metadata.json`

### Census TIGER/Line Tracts

| File/Directory | Source | Description | Update Command |
|----------------|--------|-------------|----------------|
| `data/tracts/` | US Census Bureau | Census tract boundaries for Maine (FIPS 23) | `python src/update_data_sources.py --source "Census TIGER/Line Tracts"` |
| `data/tracts/tl_2022_23_tract.shp` | Census TIGER/Line 2022 | Main shapefile (may be in subdirectory) | Auto-downloaded via update script |

**Source URL**: `https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_23_tract.zip`

### Maine GeoLibrary Conserved Lands

| File/Directory | Source | Description | Update Command |
|----------------|--------|-------------|----------------|
| `data/conserved_lands/` | Maine GeoLibrary | Maine conserved lands dataset | `python src/update_data_sources.py --source "Maine GeoLibrary Conserved Lands"` |
| `data/conserved_lands/*.geojson` | ArcGIS REST Service | GeoJSON format (may be converted to shapefile) | Auto-downloaded via update script |

**Source URL**: `https://gis.maine.gov/arcgis/rest/services/acf/Conserved_Lands/MapServer/0/query`

**Note**: Downloaded as GeoJSON, may be converted to shapefile during processing.

### CEJST (Climate Equity and Justice Screening Tool)

| File/Directory | Source | Description | Update Command |
|----------------|--------|-------------|----------------|
| `data/cejst-us.zip` | Public Environmental Data Partners | Full US CEJST shapefile (Version 2.0) | `python src/update_data_sources.py --source "CEJST (Climate Equity and Justice Screening Tool)"` |
| `data/cejst-us/` | Extracted from zip | Full US dataset (extracted) | Auto-extracted during download |
| `data/cejst-maine.shp` | Cropped from full US | Maine-only CEJST data | `python src/crop_cejst_to_state.py` |

**Source URL**: `https://dblew8dgr6ajz.cloudfront.net/data-versions/2.0/data/score/downloadable/2.0-shapefile-codebook.zip`

**Important**: The webmap uses `cejst-maine.shp` (Maine-only), NOT the full US dataset.

### Census Relationship File

| File | Source | Description | Update Command |
|------|--------|-------------|----------------|
| `data/tab2010_tab2020_st23_me.txt` | US Census Bureau | Block relationship file (2010 to 2020) for Maine | `python src/update_data_sources.py --source "Census Relationship File"` |

**Source URL**: `https://www2.census.gov/geo/docs/maps-data/data/rel2020/tabblock2010_tabblock2020_st23_me.txt`

**Usage**: Used for H3 hexagon mapping and block relationship analysis.

### OSMnx Street Network Graphs

| File | Source | Description | Update Command |
|------|--------|-------------|----------------|
| `data/graphs/maine_walk.graphml` | OpenStreetMap (via OSMnx) | Walking network graph for Maine | `python src/download_graphs.py` |
| `data/graphs/maine_drive.graphml` | OpenStreetMap (via OSMnx) | Driving network graph for Maine | `python src/download_graphs.py` |

**Source**: OpenStreetMap data downloaded via OSMnx

**Usage**: Used for walk time calculations and finding nearest nodes for centroids.

---

## Processed Data Files

**Location**: `data/`

These are intermediate files created during data processing. They include additional columns (like OSMnx node IDs) needed for analysis.

### Processed Census Blocks

| File Pattern | Description | Generated By |
|--------------|-------------|-------------|
| `data/blocks/*_with_nodes.shp.zip` | Blocks with OSMnx node IDs added | `src/find_centroids.py` or `src/process_updated_data.py` |
| `data/blocks/*_with_nodes.shp` | Uncompressed version | Same as above |

**Columns Added**:
- `osmid`: OSMnx node ID (for routing/walk time calculations)

**Usage**: 
- Input for walk time calculations
- Source for webmap PMTiles generation

### Processed Census Tracts

| File Pattern | Description | Generated By |
|--------------|-------------|-------------|
| `data/tracts/*_with_nodes.shp.zip` | Tracts with OSMnx node IDs added | `src/find_centroids.py` or `src/process_updated_data.py` |

**Columns Added**:
- `osmid`: OSMnx node ID

**Usage**: Tract-level analysis and walk time calculations.

### Processed Conserved Lands

| File Pattern | Description | Generated By |
|--------------|-------------|-------------|
| `data/conserved_lands/*_with_nodes.shp.zip` | Conserved lands with OSMnx node IDs | `src/find_centroids.py` or `src/process_updated_data.py` |

**Columns Added**:
- `osmid`: OSMnx node ID

**Usage**: 
- Source for webmap PMTiles generation
- Analysis of conserved land accessibility

---

## Data Processing Workflows

### Blocks Workflow

**Purpose**: Prepare census blocks for walk time analysis and webmap display.

1. **Download raw data**:
   ```bash
   python src/update_data_sources.py --source "Census TIGER/Line Blocks"
   ```

2. **Process (add OSMnx node IDs)**:
   ```bash
   python src/process_updated_data.py --sources "Census TIGER/Line Blocks"
   ```
   Or manually:
   ```bash
   python src/find_centroids.py -g data/graphs/maine_walk.graphml data/blocks/tl_2020_23_tabblock20.shp
   ```

3. **Generate PMTiles for webmap**:
   ```bash
   python src/convert_to_pmtiles.py data/blocks/*_with_nodes.shp.zip docs/data/blocks.pmtiles -l blocks
   ```

**Output Files**:
- `data/blocks/*_with_nodes.shp.zip` (processed blocks)
- `docs/data/blocks.pmtiles` (webmap file)

### Conserved Lands Workflow

**Purpose**: Prepare conserved lands data for webmap display.

1. **Download raw data**:
   ```bash
   python src/update_data_sources.py --source "Maine GeoLibrary Conserved Lands"
   ```

2. **Process (add OSMnx node IDs)**:
   ```bash
   python src/process_updated_data.py --sources "Maine GeoLibrary Conserved Lands"
   ```

3. **Generate PMTiles for webmap**:
   ```bash
   python src/convert_to_pmtiles.py data/conserved_lands/*_with_nodes.shp.zip docs/data/conserved_lands.pmtiles -l conserved_lands
   ```

**Output Files**:
- `data/conserved_lands/*_with_nodes.shp.zip` (processed conserved lands)
- `docs/data/conserved_lands.pmtiles` (webmap file)

### CEJST Workflow

**Purpose**: Prepare CEJST data (Maine-only) for webmap display.

1. **Download full US dataset**:
   ```bash
   python src/update_data_sources.py --source "CEJST (Climate Equity and Justice Screening Tool)"
   ```

2. **Crop to Maine**:
   ```bash
   python src/crop_cejst_to_state.py
   ```
   This creates `data/cejst-maine.shp`

3. **Generate PMTiles for webmap**:
   ```bash
   python src/convert_to_pmtiles.py data/cejst-maine.shp docs/data/cejst.pmtiles -l cejst
   ```

**Output Files**:
- `data/cejst-us.zip` (full US dataset - raw)
- `data/cejst-us/` (extracted full US dataset)
- `data/cejst-maine.shp` (Maine-only - for webmap and analysis)
- `docs/data/cejst.pmtiles` (webmap file)

**Important**: Always use `cejst-maine.shp` for the webmap, NOT the full US dataset.

---

## Update Procedures

### Quick Update: Webmap Only

If you only need to update the webmap with existing processed data:

```bash
# Blocks
python src/convert_to_pmtiles.py data/blocks/*_with_nodes.shp.zip docs/data/blocks.pmtiles -l blocks

# Conserved Lands
python src/convert_to_pmtiles.py data/conserved_lands/*_with_nodes.shp.zip docs/data/conserved_lands.pmtiles -l conserved_lands

# CEJST
python src/convert_to_pmtiles.py data/cejst-maine.shp docs/data/cejst.pmtiles -l cejst
```

### Full Update: Download + Process + Webmap

If you need to update everything from source:

1. **Check for updates**:
   ```bash
   python src/probe_data_sources.py
   ```

2. **Update data sources**:
   ```bash
   python src/update_data_sources.py --force
   ```

3. **Process updated data** (add centroids/node IDs):
   ```bash
   python src/process_updated_data.py
   ```

4. **Generate PMTiles for webmap**:
   ```bash
   # Blocks
   python src/convert_to_pmtiles.py data/blocks/*_with_nodes.shp.zip docs/data/blocks.pmtiles -l blocks
   
   # Conserved Lands
   python src/convert_to_pmtiles.py data/conserved_lands/*_with_nodes.shp.zip docs/data/conserved_lands.pmtiles -l conserved_lands
   
   # CEJST
   python src/convert_to_pmtiles.py data/cejst-maine.shp docs/data/cejst.pmtiles -l cejst
   ```

### Update Specific Data Source

To update a single data source:

```bash
# Update source
python src/update_data_sources.py --source "Source Name"

# Process if needed (for blocks, tracts, conserved lands)
python src/process_updated_data.py --sources "Source Name"

# Generate PMTiles if it's used in webmap
python src/convert_to_pmtiles.py <input> <output> -l <layer_name>
```

---

## File Naming Conventions

### Shapefiles

- `*_with_nodes.shp`: Processed shapefile with OSMnx node IDs added
- `*.shp.zip`: Compressed shapefile (includes .shp, .shx, .dbf, .prj files)

### PMTiles

- `*.pmtiles`: Vector tile format for webmap display
- Always located in `docs/data/` for webmap use

### Directories

- `data/blocks/`: Census block data
- `data/tracts/`: Census tract data
- `data/conserved_lands/`: Conserved lands data
- `data/cejst-us/`: Full US CEJST data (extracted)
- `data/graphs/`: OSMnx network graphs
- `docs/data/`: Webmap PMTiles files

---

## Dependencies

### Webmap Dependencies

The webmap (`docs/index.html`) depends on:
- `docs/data/blocks.pmtiles` ← `data/blocks/*_with_nodes.shp.zip`
- `docs/data/conserved_lands.pmtiles` ← `data/conserved_lands/*_with_nodes.shp.zip`
- `docs/data/cejst.pmtiles` ← `data/cejst-maine.shp`

### Processing Dependencies

Processing scripts require:
- `data/graphs/maine_walk.graphml` (for adding OSMnx node IDs)
- Raw data files (blocks, tracts, conserved lands)

### Analysis Dependencies

Analysis notebooks may use:
- Processed shapefiles (`*_with_nodes.shp`)
- Census relationship file (`tab2010_tab2020_st23_me.txt`)
- OSMnx graphs (`data/graphs/*.graphml`)

---

## Metadata Files

| File | Description |
|------|-------------|
| `data/data_source_metadata.json` | Tracks data source versions, update dates, availability |
| `data/schema_versions.json` | Tracks schema versions for data validation |
| `data/CHANGELOG.json` | Data change log |
| `data/update_log.txt` | Update operation log |
| `data/processing_log.txt` | Processing operation log |
| `data/validation_log.txt` | Validation operation log |

---

## Troubleshooting

### Webmap not showing data

1. Check that PMTiles files exist in `docs/data/`
2. Verify file paths in `docs/js/map.js` match actual files
3. Check browser console for errors
4. Verify PMTiles files were generated from correct source files

### Processing fails

1. Check that `data/graphs/maine_walk.graphml` exists
2. Verify raw data files are present
3. Check processing logs: `data/processing_log.txt`

### Update fails

1. Check internet connection
2. Verify source URLs are still valid
3. Check update logs: `data/update_log.txt`
4. Run `python src/probe_data_sources.py` to check availability

---

## Additional Resources

- **CEJST Workflow**: See `README_CEJST.md` for detailed CEJST workflow
- **Data Source Configuration**: See `src/probe_data_sources.py` for all data source URLs
- **Validation**: Run `python src/validate_data.py` to validate data files
- **Processing**: See `src/process_updated_data.py` for processing functions

