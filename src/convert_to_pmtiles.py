#!/usr/bin/env python3
"""
Convert shapefiles and GeoJSON files to PMTiles format for use with MapLibre GL JS.

This script uses ogr2ogr to convert shapefiles to GeoJSON (EPSG:4326) and
tippecanoe (v2.17+) to generate PMTiles directly.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_command(command: str) -> bool:
    """Check if a command is available."""
    return shutil.which(command) is not None


def convert_to_geojson(input_path: Path, output_path: Path, layer_name: str = None) -> bool:
    """
    Convert shapefile, GeoJSON, or Parquet to GeoJSON in EPSG:4326 using GeoPandas.
    
    Args:
        input_path: Path to input shapefile, GeoJSON, or Parquet file
        output_path: Path to output GeoJSON file
        layer_name: Optional layer name for shapefiles (not used with GeoPandas)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import geopandas as gpd
        
        # Read the file - handle parquet files specially
        if input_path.suffix.lower() == '.parquet':
            gdf = gpd.read_parquet(input_path)
        else:
            gdf = gpd.read_file(input_path)
        
        # Reproject to EPSG:4326 if needed
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        
        # Save as GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")
        logging.info(f"Converted {input_path} to {output_path}")
        return True
    except ImportError:
        logging.error("geopandas not found. Please install geopandas.")
        return False
    except Exception as e:
        logging.error(f"Error converting {input_path}: {e}")
        return False


def convert_to_pmtiles(
    geojson_path: Path,
    output_path: Path,
    layer_name: str,
    min_zoom: int = 0,
    max_zoom: int = 14,
    projection: str = "EPSG:4326"
) -> bool:
    """
    Convert GeoJSON to PMTiles using tippecanoe.
    
    Args:
        geojson_path: Path to input GeoJSON file
        output_path: Path to output PMTiles file
        layer_name: Name for the layer in the PMTiles
        min_zoom: Minimum zoom level
        max_zoom: Maximum zoom level
        projection: Projection (default EPSG:4326)
    
    Returns:
        True if successful, False otherwise
    """
    if not check_command("tippecanoe"):
        logging.error("tippecanoe not found. Please install tippecanoe (v2.17+).")
        return False

    # Check tippecanoe version supports PMTiles
    try:
        version_result = subprocess.run(
            ["tippecanoe", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_str = version_result.stdout.strip()
        logging.info(f"Using tippecanoe: {version_str}")
    except subprocess.CalledProcessError:
        logging.warning("Could not check tippecanoe version")
    
    cmd = [
        "tippecanoe",
        "-zg",  # Automatic zoom level calculation
        f"--projection={projection}",
        "--detect-shared-borders",  # Preserve shared boundaries between adjacent polygons
        "--buffer=10",  # Increase buffer size to maintain polygon continuity (default is 5)
        "--force",  # Overwrite existing output file
        "-o", str(output_path),
        "-l", layer_name,
        str(geojson_path)
    ]
    
    # Add zoom level options if not using -zg
    if min_zoom is not None:
        cmd.insert(-1, f"-Z{min_zoom}")
    if max_zoom is not None:
        cmd.insert(-1, f"-z{max_zoom}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Converted {geojson_path} to {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error converting to PMTiles: {e.stderr}")
        return False


def convert_file(
    input_path: Path,
    output_path: Path,
    layer_name: str,
    min_zoom: int = 0,
    max_zoom: int = 14
) -> bool:
    """
    Convert a shapefile or GeoJSON to PMTiles.
    
    Args:
        input_path: Path to input file (shapefile or GeoJSON)
        output_path: Path to output PMTiles file
        layer_name: Name for the layer in the PMTiles
        min_zoom: Minimum zoom level
        max_zoom: Maximum zoom level
    
    Returns:
        True if successful, False otherwise
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if input is already GeoJSON
    is_geojson = input_path.suffix.lower() in ['.geojson', '.json']
    is_parquet = input_path.suffix.lower() == '.parquet'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        if is_geojson:
            # If already GeoJSON, just ensure it's in EPSG:4326
            geojson_path = tmp_path / "input.geojson"
            if not convert_to_geojson(input_path, geojson_path):
                return False
        elif is_parquet:
            # Convert parquet to GeoJSON
            geojson_path = tmp_path / "input.geojson"
            if not convert_to_geojson(input_path, geojson_path):
                return False
        else:
            # Convert shapefile to GeoJSON
            geojson_path = tmp_path / "input.geojson"
            if not convert_to_geojson(input_path, geojson_path):
                return False
        
        # Convert GeoJSON to PMTiles
        return convert_to_pmtiles(geojson_path, output_path, layer_name, min_zoom, max_zoom)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Convert shapefiles and GeoJSON to PMTiles format"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input shapefile or GeoJSON file"
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output PMTiles file path"
    )
    parser.add_argument(
        "-l", "--layer",
        required=True,
        help="Layer name for the PMTiles"
    )
    parser.add_argument(
        "--min-zoom",
        type=int,
        default=0,
        help="Minimum zoom level (default: 0)"
    )
    parser.add_argument(
        "--max-zoom",
        type=int,
        default=14,
        help="Maximum zoom level (default: 14)"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logging.error(f"Input file {args.input} does not exist")
        sys.exit(1)

    success = convert_file(
        args.input,
        args.output,
        args.layer,
        args.min_zoom,
        args.max_zoom
    )

    if success:
        logging.info(f"Successfully created {args.output}")
        sys.exit(0)
    else:
        logging.error(f"Failed to create {args.output}")
        sys.exit(1)


if __name__ == "__main__":
    main()

