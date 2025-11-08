#!/usr/bin/env python3
"""
Utility to crop the CEJST (Climate Equity and Justice Screening Tool) dataset
from the full US coverage to a specific state.

This script is designed to be easily extensible to include other states in the future.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
import geopandas as gpd
from shapely.geometry import box

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# State FIPS codes mapping (easily extensible for other states)
STATE_FIPS_CODES = {
    "Maine": "23",
    "Alabama": "01",
    "Alaska": "02",
    "Arizona": "04",
    "Arkansas": "05",
    "California": "06",
    "Colorado": "08",
    "Connecticut": "09",
    "Delaware": "10",
    "Florida": "12",
    "Georgia": "13",
    "Hawaii": "15",
    "Idaho": "16",
    "Illinois": "17",
    "Indiana": "18",
    "Iowa": "19",
    "Kansas": "20",
    "Kentucky": "21",
    "Louisiana": "22",
    "Maine": "23",
    "Maryland": "24",
    "Massachusetts": "25",
    "Michigan": "26",
    "Minnesota": "27",
    "Mississippi": "28",
    "Missouri": "29",
    "Montana": "30",
    "Nebraska": "31",
    "Nevada": "32",
    "New Hampshire": "33",
    "New Jersey": "34",
    "New Mexico": "35",
    "New York": "36",
    "North Carolina": "37",
    "North Dakota": "38",
    "Ohio": "39",
    "Oklahoma": "40",
    "Oregon": "41",
    "Pennsylvania": "42",
    "Rhode Island": "44",
    "South Carolina": "45",
    "South Dakota": "46",
    "Tennessee": "47",
    "Texas": "48",
    "Utah": "49",
    "Vermont": "50",
    "Virginia": "51",
    "Washington": "53",
    "West Virginia": "54",
    "Wisconsin": "55",
    "Wyoming": "56",
    "District of Columbia": "11",
    "Puerto Rico": "72",
}


def find_cejst_shapefile(cejst_dir: Path) -> Optional[Path]:
    """Find the CEJST shapefile in the extracted directory."""
    if not cejst_dir.exists():
        return None
    
    # Look for .shp files in the directory
    shapefiles = list(cejst_dir.rglob("*.shp"))
    
    if not shapefiles:
        logging.error(f"No shapefile found in {cejst_dir}")
        return None
    
    # Prefer files that don't have "codebook" in the name
    main_shapefiles = [f for f in shapefiles if "codebook" not in f.stem.lower()]
    if main_shapefiles:
        return main_shapefiles[0]
    
    # Fall back to first shapefile found
    return shapefiles[0]


def get_state_fips_code(state_name: str) -> Optional[str]:
    """Get the FIPS code for a state name."""
    # Try exact match first
    if state_name in STATE_FIPS_CODES:
        return STATE_FIPS_CODES[state_name]
    
    # Try case-insensitive match
    state_name_lower = state_name.lower()
    for state, fips in STATE_FIPS_CODES.items():
        if state.lower() == state_name_lower:
            return fips
    
    # Try matching by FIPS code directly
    if state_name in STATE_FIPS_CODES.values():
        return state_name
    
    return None


def crop_cejst_to_state(
    cejst_shapefile: Path,
    state_name: str,
    output_path: Path,
    state_fips_column: str = "STUSPS",
    fips_code_column: str = "STATEFP"
) -> bool:
    """
    Crop CEJST dataset to a specific state.
    
    Parameters:
    -----------
    cejst_shapefile : Path
        Path to the full US CEJST shapefile
    state_name : str
        Name of the state to crop to (e.g., "Maine")
    output_path : Path
        Path where the cropped shapefile will be saved
    state_fips_column : str
        Column name containing state FIPS codes (default: "STATEFP")
    fips_code_column : str
        Alternative column name for state codes (default: "STUSPS")
    
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    try:
        logging.info(f"Loading CEJST shapefile from {cejst_shapefile}")
        gdf = gpd.read_file(cejst_shapefile)
        
        logging.info(f"Loaded {len(gdf)} census tracts from full US dataset")
        logging.info(f"Columns: {list(gdf.columns)}")
        
        # Get state FIPS code
        state_fips = get_state_fips_code(state_name)
        if not state_fips:
            logging.error(f"Could not find FIPS code for state: {state_name}")
            logging.info(f"Available states: {', '.join(STATE_FIPS_CODES.keys())}")
            return False
        
        logging.info(f"Filtering for state: {state_name} (FIPS code: {state_fips})")
        
        # Try to filter by FIPS code column
        filtered_gdf = None
        if fips_code_column in gdf.columns:
            filtered_gdf = gdf[gdf[fips_code_column] == state_fips].copy()
            logging.info(f"Filtered using column '{fips_code_column}': {len(filtered_gdf)} tracts")
        elif state_fips_column in gdf.columns:
            # Try with state FIPS column (might be numeric)
            try:
                state_fips_int = int(state_fips)
                filtered_gdf = gdf[gdf[state_fips_column] == state_fips_int].copy()
            except (ValueError, TypeError):
                filtered_gdf = gdf[gdf[state_fips_column] == state_fips].copy()
            logging.info(f"Filtered using column '{state_fips_column}': {len(filtered_gdf)} tracts")
        else:
            # Try to find any column that might contain state information
            logging.warning(f"Neither '{fips_code_column}' nor '{state_fips_column}' found in columns")
            logging.info("Searching for state-related columns...")
            
            # Look for columns that might contain state info
            state_cols = [col for col in gdf.columns if 'state' in col.lower() or 'fips' in col.lower()]
            if state_cols:
                logging.info(f"Found potential state columns: {state_cols}")
                for col in state_cols:
                    # Try filtering with this column
                    try:
                        test_filter = gdf[gdf[col].astype(str).str.startswith(state_fips)]
                        if len(test_filter) > 0:
                            filtered_gdf = test_filter.copy()
                            logging.info(f"Filtered using column '{col}': {len(filtered_gdf)} tracts")
                            break
                    except Exception as e:
                        logging.debug(f"Could not filter with column '{col}': {e}")
                        continue
        
        if filtered_gdf is None or len(filtered_gdf) == 0:
            logging.error(f"No tracts found for state {state_name} (FIPS: {state_fips})")
            logging.info("Available column names:")
            for col in gdf.columns:
                if 'state' in col.lower() or 'fips' in col.lower() or 'st' in col.lower():
                    unique_vals = gdf[col].unique()[:10]  # Show first 10 unique values
                    logging.info(f"  {col}: {unique_vals}")
            return False
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the cropped shapefile
        logging.info(f"Saving cropped shapefile to {output_path}")
        filtered_gdf.to_file(output_path, driver="ESRI Shapefile")
        
        logging.info(f"Successfully cropped CEJST dataset to {state_name}")
        logging.info(f"  Input: {len(gdf)} tracts (full US)")
        logging.info(f"  Output: {len(filtered_gdf)} tracts ({state_name})")
        
        return True
        
    except Exception as e:
        logging.error(f"Error cropping CEJST dataset: {e}", exc_info=True)
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Crop CEJST dataset from full US coverage to a specific state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crop to Maine (default)
  python crop_cejst_to_state.py
  
  # Crop to a specific state
  python crop_cejst_to_state.py --state "California"
  
  # Specify custom input/output paths
  python crop_cejst_to_state.py --input data/cejst-us/cejst.shp --output data/cejst-maine.shp
        """
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to CEJST shapefile or directory containing extracted CEJST data (default: auto-detect from data/cejst-us)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for cropped shapefile (default: data/cejst-{state}.shp)"
    )
    
    parser.add_argument(
        "--state",
        type=str,
        default="Maine",
        help="State name to crop to (default: Maine). Can be full name or FIPS code."
    )
    
    parser.add_argument(
        "--fips-column",
        type=str,
        default="STATEFP",
        help="Column name containing state FIPS codes (default: STATEFP)"
    )
    
    args = parser.parse_args()
    
    # Determine input path
    if args.input:
        input_path = Path(args.input)
        if input_path.is_dir():
            # Find shapefile in directory
            shapefile = find_cejst_shapefile(input_path)
            if not shapefile:
                logging.error(f"Could not find shapefile in directory: {input_path}")
                return 1
            cejst_shapefile = shapefile
        else:
            cejst_shapefile = input_path
    else:
        # Auto-detect from default location
        cejst_dir = Path("data/cejst-us")
        shapefile = find_cejst_shapefile(cejst_dir)
        if not shapefile:
            logging.error(f"Could not find CEJST shapefile. Expected location: {cejst_dir}")
            logging.info("Please run: python src/update_data_sources.py --source 'CEJST (Climate Equity and Justice Screening Tool)'")
            return 1
        cejst_shapefile = shapefile
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        state_slug = args.state.lower().replace(" ", "_")
        output_path = Path(f"data/cejst-{state_slug}.shp")
    
    # Validate input file exists
    if not cejst_shapefile.exists():
        logging.error(f"CEJST shapefile not found: {cejst_shapefile}")
        return 1
    
    logging.info("=" * 70)
    logging.info("CEJST State Cropping Utility")
    logging.info("=" * 70)
    logging.info(f"Input: {cejst_shapefile}")
    logging.info(f"State: {args.state}")
    logging.info(f"Output: {output_path}")
    logging.info("=" * 70)
    
    # Crop the dataset
    success = crop_cejst_to_state(
        cejst_shapefile=cejst_shapefile,
        state_name=args.state,
        output_path=output_path,
        fips_code_column=args.fips_column
    )
    
    if success:
        logging.info("=" * 70)
        logging.info("SUCCESS: Dataset cropped successfully")
        logging.info("=" * 70)
        return 0
    else:
        logging.error("=" * 70)
        logging.error("FAILED: Could not crop dataset")
        logging.error("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

