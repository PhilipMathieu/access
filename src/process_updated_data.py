#!/usr/bin/env python3
"""
Process updated data files after downloading new versions.
This script re-runs processing steps like finding centroids and adding OSMnx node IDs.
"""

import logging
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import osmnx as ox

from probe_data_sources import load_metadata

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data/processing_log.txt"), logging.StreamHandler()],
)

# Set OSMnx cache folder
ox.settings.cache_folder = "./cache/"


def find_shapefiles_in_directory(directory: Path) -> list[Path]:
    """Find all shapefiles in a directory."""
    shapefiles = []

    if not directory.exists():
        return shapefiles

    # Look for .shp files
    for shp_file in directory.rglob("*.shp"):
        # Skip files that already have _with_nodes suffix
        if "_with_nodes" not in shp_file.stem:
            shapefiles.append(shp_file)

    return shapefiles


def process_shapefile_with_centroids(
    shapefile: Path,
    graph_file: Path = Path("data/graphs/maine_walk.graphml"),
    output_suffix: str = "_with_nodes",
) -> bool:
    """Process a shapefile to add OSMnx node IDs using find_centroids.py."""
    try:
        logging.info(f"Processing {shapefile} with find_centroids.py...")

        # Check if output already exists
        output_file = shapefile.parent / f"{shapefile.stem}{output_suffix}.shp.zip"
        if output_file.exists():
            logging.info(f"Output file {output_file} already exists, skipping...")
            return True

        # Run find_centroids.py
        cmd = [
            sys.executable,
            "src/find_centroids.py",
            "-g",
            str(graph_file),
            str(shapefile),
            "-o",
            output_suffix,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        if result.returncode == 0:
            logging.info(f"Successfully processed {shapefile}")
            return True
        else:
            logging.error(f"Error processing {shapefile}: {result.stderr}")
            return False

    except Exception as e:
        logging.error(f"Exception processing {shapefile}: {e}")
        return False


def process_census_blocks() -> bool:
    """Process updated Census blocks."""
    blocks_dir = Path("data/blocks")
    graph_file = Path("data/graphs/maine_walk.graphml")

    if not graph_file.exists():
        logging.error(f"Graph file {graph_file} not found")
        return False

    shapefiles = find_shapefiles_in_directory(blocks_dir)

    if not shapefiles:
        logging.info("No shapefiles found in blocks directory")
        return True

    success = True
    for shp_file in shapefiles:
        if not process_shapefile_with_centroids(shp_file, graph_file):
            success = False

    return success


def process_census_tracts() -> bool:
    """Process updated Census tracts."""
    tracts_dir = Path("data/tracts")
    graph_file = Path("data/graphs/maine_walk.graphml")

    if not graph_file.exists():
        logging.error(f"Graph file {graph_file} not found")
        return False

    shapefiles = find_shapefiles_in_directory(tracts_dir)

    if not shapefiles:
        logging.info("No shapefiles found in tracts directory")
        return True

    success = True
    for shp_file in shapefiles:
        if not process_shapefile_with_centroids(shp_file, graph_file):
            success = False

    return success


def process_conserved_lands() -> bool:
    """Process updated conserved lands data."""
    conserved_lands_dir = Path("data/conserved_lands")
    graph_file = Path("data/graphs/maine_walk.graphml")

    if not graph_file.exists():
        logging.error(f"Graph file {graph_file} not found")
        return False

    # Look for GeoJSON or shapefiles
    geojson_files = list(conserved_lands_dir.glob("*.geojson"))
    shapefiles = find_shapefiles_in_directory(conserved_lands_dir)

    success = True

    # Process GeoJSON files (convert to shapefile first if needed)
    for geojson_file in geojson_files:
        try:
            # Read GeoJSON
            gdf = gpd.read_file(geojson_file)

            # Save as shapefile
            shp_file = geojson_file.with_suffix(".shp")
            gdf.to_file(shp_file, driver="ESRI Shapefile")

            # Process with centroids
            if not process_shapefile_with_centroids(shp_file, graph_file):
                success = False
        except Exception as e:
            logging.error(f"Error processing {geojson_file}: {e}")
            success = False

    # Process existing shapefiles
    for shp_file in shapefiles:
        if not process_shapefile_with_centroids(shp_file, graph_file):
            success = False

    return success


def validate_processed_file(file_path: Path) -> bool:
    """Validate that a processed file has the required columns."""
    try:
        gdf = gpd.read_file(file_path)

        # Check for required columns
        required_columns = ["osmid", "geometry"]

        missing_columns = [col for col in required_columns if col not in gdf.columns]

        if missing_columns:
            logging.error(f"{file_path}: Missing required columns: {missing_columns}")
            return False

        # Check for valid geometries
        invalid_geoms = gdf.geometry.isna().sum()
        if invalid_geoms > 0:
            logging.warning(f"{file_path}: {invalid_geoms} rows with invalid geometries")

        # Check for valid osmid values
        invalid_osmids = gdf["osmid"].isna().sum()
        if invalid_osmids > 0:
            logging.warning(f"{file_path}: {invalid_osmids} rows with missing osmid values")

        logging.info(f"{file_path}: Validation passed ({len(gdf)} rows)")
        return True

    except Exception as e:
        logging.error(f"Error validating {file_path}: {e}")
        return False


def process_updated_data_sources(sources: list[str] | None = None) -> dict[str, bool]:
    """Process data sources that have been updated."""
    metadata = load_metadata()
    results = {}

    # Map source names to processing functions
    processing_functions = {
        "Census TIGER/Line Blocks": process_census_blocks,
        "Census TIGER/Line Tracts": process_census_tracts,
        "Maine GeoLibrary Conserved Lands": process_conserved_lands,
    }

    # If specific sources provided, only process those
    if sources:
        sources_to_process = [s for s in sources if s in processing_functions]
    else:
        # Process all sources that have been updated
        sources_to_process = [
            name
            for name, source_metadata in metadata.items()
            if source_metadata.get("last_updated") and name in processing_functions
        ]

    if not sources_to_process:
        logging.info("No updated sources to process")
        return results

    logging.info(f"Processing {len(sources_to_process)} updated source(s)...")

    for source_name in sources_to_process:
        if source_name in processing_functions:
            logging.info(f"Processing {source_name}...")
            success = processing_functions[source_name]()
            results[source_name] = success
        else:
            logging.warning(f"No processing function for {source_name}")
            results[source_name] = False

    return results


def validate_all_processed_files() -> bool:
    """Validate all processed files in data directories."""
    logging.info("Validating all processed files...")

    directories = [Path("data/blocks"), Path("data/tracts"), Path("data/conserved_lands")]

    all_valid = True

    for directory in directories:
        if not directory.exists():
            continue

        # Find all _with_nodes files
        processed_files = list(directory.rglob("*_with_nodes.shp.zip"))

        for file_path in processed_files:
            if not validate_processed_file(file_path):
                all_valid = False

    return all_valid


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Process updated data files")
    parser.add_argument(
        "--sources", nargs="+", help="Specific sources to process (default: all updated sources)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing processed files, don't process new ones",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Access Project - Process Updated Data")
    print("=" * 70)

    if args.validate_only:
        success = validate_all_processed_files()
        sys.exit(0 if success else 1)

    # Process updated sources
    results = process_updated_data_sources(sources=args.sources)

    # Validate processed files
    validation_success = validate_all_processed_files()

    print("\n" + "=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)

    for source_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status}: {source_name}")

    print(f"\nValidation: {'✓ PASSED' if validation_success else '✗ FAILED'}")

    all_success = all(results.values()) and validation_success

    if all_success:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
