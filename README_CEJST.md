# CEJST Data Workflow

## Overview

The CEJST (Climate Equity and Justice Screening Tool) dataset is now downloaded as a full US coverage shapefile, then cropped to Maine for use in the webmap and analysis.

## Data Flow

1. **Download Full US Dataset**: The full US CEJST shapefile is downloaded to `data/cejst-us.zip` and extracted to `data/cejst-us/`
2. **Crop to Maine**: The dataset is cropped to Maine using `src/crop_cejst_to_state.py`, creating `data/cejst-maine.shp`
3. **Generate PMTiles**: The Maine-specific shapefile is converted to PMTiles for the webmap: `docs/data/cejst.pmtiles`

## Usage

### Download CEJST Data

```bash
# Download the full US CEJST dataset
python src/update_data_sources.py --source "CEJST (Climate Equity and Justice Screening Tool)"
```

### Crop to Maine

```bash
# Crop the full US dataset to Maine (default)
python src/crop_cejst_to_state.py

# Or specify explicitly
python src/crop_cejst_to_state.py --state "Maine" --output data/cejst-maine.shp
```

### Generate PMTiles for Webmap

```bash
# Convert the Maine-specific CEJST shapefile to PMTiles
python src/convert_to_pmtiles.py data/cejst-maine.shp docs/data/cejst.pmtiles -l cejst
```

## Important Notes

- **Webmap**: The webmap (`docs/js/map.js`) uses `./data/cejst.pmtiles`, which should be generated from the Maine-specific shapefile (`data/cejst-maine.shp`), NOT the full US dataset.
- **Analysis**: Notebooks and analysis scripts should use `data/cejst-maine.shp` (or the cropped version) for Maine-specific analysis.
- **Extensibility**: The cropping utility can be easily extended to other states by using the `--state` parameter.

## File Locations

- **Full US Dataset**: `data/cejst-us.zip` (compressed) and `data/cejst-us/` (extracted)
- **Maine-Specific**: `data/cejst-maine.shp` (cropped shapefile)
- **Webmap PMTiles**: `docs/data/cejst.pmtiles` (generated from Maine-specific data)

