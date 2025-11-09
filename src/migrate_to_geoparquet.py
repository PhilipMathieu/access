#!/usr/bin/env python3
"""Migration script to convert existing shapefiles and GeoJSON to GeoParquet format.

This script helps migrate existing data files from shapefile/GeoJSON format
to GeoParquet format for better performance and smaller file sizes.
"""

import argparse
import logging
from pathlib import Path
from typing import List, Optional

import geopandas as gpd
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def convert_shapefile_to_geoparquet(
    input_path: Path,
    output_path: Optional[Path] = None,
    overwrite: bool = False,
) -> bool:
    """Convert a shapefile or GeoJSON to GeoParquet format.
    
    Args:
        input_path: Path to input shapefile or GeoJSON
        output_path: Optional output path (default: same as input with .parquet extension)
        overwrite: Whether to overwrite existing output file
        
    Returns:
        True if successful, False otherwise
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        return False
    
    # Determine output path
    if output_path is None:
        if input_path.suffix in ['.shp', '.zip']:
            # Remove .shp or .zip extension and add .parquet
            output_path = input_path.with_suffix('.parquet')
        elif input_path.suffix in ['.geojson', '.json']:
            output_path = input_path.with_suffix('.parquet')
        else:
            output_path = input_path.with_suffix('.parquet')
    else:
        output_path = Path(output_path)
    
    # Check if output exists
    if output_path.exists() and not overwrite:
        logger.warning(f"Output file already exists: {output_path}. Use --overwrite to overwrite.")
        return False
    
    try:
        logger.info(f"Loading {input_path}")
        gdf = gpd.read_file(str(input_path))
        
        logger.info(f"Converting to GeoParquet: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_parquet(str(output_path))
        
        # Compare file sizes
        input_size = input_path.stat().st_size / (1024 * 1024)  # MB
        output_size = output_path.stat().st_size / (1024 * 1024)  # MB
        reduction = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        
        logger.info(f"✓ Converted: {input_path.name} -> {output_path.name}")
        logger.info(f"  Input size: {input_size:.2f} MB")
        logger.info(f"  Output size: {output_size:.2f} MB")
        logger.info(f"  Size reduction: {reduction:.1f}%")
        
        return True
    except Exception as e:
        logger.error(f"Error converting {input_path}: {e}")
        return False


def convert_csv_to_parquet(
    input_path: Path,
    output_path: Optional[Path] = None,
    overwrite: bool = False,
) -> bool:
    """Convert a CSV file to Parquet format.
    
    Args:
        input_path: Path to input CSV file
        output_path: Optional output path (default: same as input with .parquet extension)
        overwrite: Whether to overwrite existing output file
        
    Returns:
        True if successful, False otherwise
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        return False
    
    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix('.parquet')
    else:
        output_path = Path(output_path)
    
    # Check if output exists
    if output_path.exists() and not overwrite:
        logger.warning(f"Output file already exists: {output_path}. Use --overwrite to overwrite.")
        return False
    
    try:
        logger.info(f"Loading {input_path}")
        df = pd.read_csv(str(input_path))
        
        logger.info(f"Converting to Parquet: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(str(output_path), index=False)
        
        # Compare file sizes
        input_size = input_path.stat().st_size / (1024 * 1024)  # MB
        output_size = output_path.stat().st_size / (1024 * 1024)  # MB
        reduction = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        
        logger.info(f"✓ Converted: {input_path.name} -> {output_path.name}")
        logger.info(f"  Input size: {input_size:.2f} MB")
        logger.info(f"  Output size: {output_size:.2f} MB")
        logger.info(f"  Size reduction: {reduction:.1f}%")
        
        return True
    except Exception as e:
        logger.error(f"Error converting {input_path}: {e}")
        return False


def find_shapefiles(directory: Path) -> List[Path]:
    """Find all shapefiles in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of shapefile paths
    """
    shapefiles = []
    
    # Find .shp files
    for shp_file in directory.rglob("*.shp"):
        shapefiles.append(shp_file)
    
    # Find .shp.zip files
    for zip_file in directory.rglob("*.shp.zip"):
        shapefiles.append(zip_file)
    
    # Find .geojson files
    for geojson_file in directory.rglob("*.geojson"):
        shapefiles.append(geojson_file)
    
    return shapefiles


def find_csv_files(directory: Path) -> List[Path]:
    """Find all CSV files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of CSV file paths
    """
    csv_files = []
    
    for csv_file in directory.rglob("*.csv"):
        csv_files.append(csv_file)
    
    return csv_files


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Convert shapefiles/GeoJSON/CSV to GeoParquet/Parquet format"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input file or directory to convert"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file or directory (default: same as input with .parquet extension)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively convert all files in directory"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Convert CSV files instead of shapefiles"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1
    
    success_count = 0
    error_count = 0
    
    if input_path.is_file():
        # Convert single file
        if args.csv or input_path.suffix == '.csv':
            success = convert_csv_to_parquet(
                input_path,
                args.output,
                args.overwrite
            )
        else:
            success = convert_shapefile_to_geoparquet(
                input_path,
                args.output,
                args.overwrite
            )
        
        if success:
            success_count += 1
        else:
            error_count += 1
    else:
        # Convert directory
        if args.csv:
            files = find_csv_files(input_path)
        else:
            files = find_shapefiles(input_path)
        
        if not files:
            logger.warning(f"No files found to convert in {input_path}")
            return 0
        
        logger.info(f"Found {len(files)} files to convert")
        
        for file_path in files:
            if args.csv or file_path.suffix == '.csv':
                success = convert_csv_to_parquet(
                    file_path,
                    None,
                    args.overwrite
                )
            else:
                success = convert_shapefile_to_geoparquet(
                    file_path,
                    None,
                    args.overwrite
                )
            
            if success:
                success_count += 1
            else:
                error_count += 1
    
    logger.info("=" * 70)
    logger.info(f"Migration complete: {success_count} successful, {error_count} errors")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

