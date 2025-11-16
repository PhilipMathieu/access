#!/usr/bin/env python3
"""
Update data sources when new versions become available.
This script downloads and updates data files based on probe_data_sources.py metadata.
"""

import json
import logging
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import osmnx as ox
import requests

# Import from probe_data_sources
from probe_data_sources import DATA_SOURCES, load_metadata, save_metadata

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data/update_log.txt"), logging.StreamHandler()],
)

# Set OSMnx cache folder
ox.settings.cache_folder = "./cache/"


def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file from URL to output path."""
    try:
        logging.info(f"Downloading {url} to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if downloaded % (chunk_size * 100) == 0:  # Log every 100 chunks
                            logging.info(
                                f"Downloaded {percent:.1f}% ({downloaded}/{total_size} bytes)"
                            )

        logging.info(f"Successfully downloaded {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error downloading {url}: {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract a zip file to a directory."""
    try:
        logging.info(f"Extracting {zip_path} to {extract_to}")
        extract_to.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)

        logging.info(f"Successfully extracted to {extract_to}")
        return True
    except Exception as e:
        logging.error(f"Error extracting {zip_path}: {e}")
        return False


def update_census_tiger_line(name: str, config: dict) -> bool:
    """Update Census TIGER/Line data."""
    url = config["url"]
    local_path = config.get("local_path")

    if not local_path:
        # Determine local path from URL
        filename = url.split("/")[-1]
        local_path = f"data/{filename}"

    local_file = Path(local_path)

    # Check if update is needed
    metadata = load_metadata()
    source_metadata = metadata.get(name, {})

    if not source_metadata.get("update_available", False):
        logging.info(f"{name}: No update available")
        return True

    # Download the file
    temp_file = local_file.with_suffix(".tmp")
    if download_file(url, temp_file):
        # Backup old file if it exists
        if local_file.exists():
            backup_file = local_file.with_suffix(".bak")
            shutil.move(local_file, backup_file)
            logging.info(f"Backed up old file to {backup_file}")

        # Move temp file to final location
        shutil.move(temp_file, local_file)

        # Extract if it's a zip file
        if local_file.suffix == ".zip":
            extract_dir = local_file.parent / local_file.stem
            if extract_zip(local_file, extract_dir):
                logging.info(f"{name}: Successfully updated")
                # Update metadata
                source_metadata["local_date"] = datetime.now().isoformat()
                source_metadata["update_available"] = False
                source_metadata["last_updated"] = datetime.now().isoformat()
                metadata[name] = source_metadata
                save_metadata(metadata)
                return True

        return True
    else:
        return False


def update_arcgis_service(name: str, config: dict) -> bool:
    """Update ArcGIS REST service data."""
    url = config["url"]
    params = config.get("params", {})
    local_path = config.get("local_path")

    if not local_path:
        logging.error(f"{name}: No local_path specified")
        return False

    local_dir = Path(local_path)

    try:
        # Modify params to get all features
        download_params = params.copy()
        download_params["where"] = "1=1"
        download_params["resultRecordCount"] = None  # Get all records
        download_params["outFields"] = "*"
        download_params["f"] = "geojson"  # Request GeoJSON format

        logging.info(f"Downloading {name} from ArcGIS service...")
        response = requests.get(url, params=download_params, timeout=300)
        response.raise_for_status()

        data = response.json()

        if "features" in data:
            # Save as GeoJSON
            output_file = local_dir / f"{name.replace(' ', '_')}.geojson"
            local_dir.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(data, f)

            logging.info(f"{name}: Successfully downloaded {len(data['features'])} features")

            # Update metadata
            metadata = load_metadata()
            source_metadata = metadata.get(name, {})
            source_metadata["local_date"] = datetime.now().isoformat()
            source_metadata["update_available"] = False
            source_metadata["last_updated"] = datetime.now().isoformat()
            source_metadata["feature_count"] = len(data["features"])
            metadata[name] = source_metadata
            save_metadata(metadata)

            return True
        else:
            logging.error(f"{name}: No features in response")
            return False

    except Exception as e:
        logging.error(f"Error updating {name}: {e}")
        return False


def update_osmnx_graphs(name: str, config: dict) -> bool:
    """Update OSMnx street network graphs."""
    params = config.get("params", {})
    place = params.get("place", {})
    network_type = params.get("network_type", "walk")

    try:
        logging.info(f"Downloading OSMnx graph for {place} ({network_type} network)...")

        # Download graph
        G = ox.graph_from_place(place, network_type=network_type, simplify=True)

        if G is None or len(G.nodes) == 0:
            logging.error(f"{name}: Failed to download graph")
            return False

        # Save graph
        state_name = place.get("state", "unknown").lower().replace(" ", "_")
        output_file = Path(f"data/graphs/{state_name}_{network_type}.graphml")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        ox.save_graphml(G, str(output_file))

        logging.info(f"{name}: Successfully downloaded graph with {len(G.nodes)} nodes")

        # Update metadata
        metadata = load_metadata()
        source_metadata = metadata.get(name, {})
        source_metadata["local_date"] = datetime.now().isoformat()
        source_metadata["update_available"] = False
        source_metadata["last_updated"] = datetime.now().isoformat()
        source_metadata["node_count"] = len(G.nodes)
        metadata[name] = source_metadata
        save_metadata(metadata)

        return True

    except Exception as e:
        logging.error(f"Error updating {name}: {e}")
        return False


def update_cejst(name: str, config: dict) -> bool:
    """Update CEJST data - downloads full US shapefile."""
    url = config.get("url")
    local_path = config.get("local_path", "data/cejst-us.zip")
    local_file = Path(local_path)

    if not url:
        logging.error(f"{name}: No URL specified")
        return False

    # Download the full US shapefile
    logging.info(f"Downloading CEJST full US shapefile from {url}")
    if download_file(url, local_file):
        # Extract the zip file
        extract_dir = local_file.parent / local_file.stem
        if extract_zip(local_file, extract_dir):
            logging.info(f"{name}: Successfully downloaded and extracted full US shapefile")
            # Update metadata
            metadata = load_metadata()
            source_metadata = metadata.get(name, {})
            source_metadata["local_date"] = datetime.now().isoformat()
            source_metadata["update_available"] = False
            source_metadata["last_updated"] = datetime.now().isoformat()
            metadata[name] = source_metadata
            save_metadata(metadata)
            return True

    logging.error(f"{name}: Failed to download CEJST shapefile")
    return False


def update_data_source(name: str, config: dict) -> bool:
    """Update a single data source based on its type."""
    source_type = config["type"]

    logging.info(f"Updating {name} ({source_type})...")

    if source_type == "http":
        # Check if this is CEJST data source
        if "CEJST" in name:
            return update_cejst(name, config)
        else:
            return update_census_tiger_line(name, config)
    elif source_type == "arcgis":
        return update_arcgis_service(name, config)
    elif source_type == "osmnx":
        return update_osmnx_graphs(name, config)
    else:
        logging.warning(f"{name}: Update not implemented for type {source_type}")
        return False


def update_all_sources(force: bool = False) -> dict[str, bool]:
    """Update all data sources that have updates available."""
    metadata = load_metadata()
    results = {}

    for name, config in DATA_SOURCES.items():
        source_metadata = metadata.get(name, {})

        if force or source_metadata.get("update_available", False):
            assert isinstance(config, dict)
            success = update_data_source(name, config)
            results[name] = success
        else:
            logging.info(f"{name}: No update needed")
            results[name] = True  # Not an error, just no update needed

    return results


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Update data sources")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update all sources, even if no update is available",
    )
    parser.add_argument("--source", type=str, help="Update a specific source by name")

    args = parser.parse_args()

    print("=" * 70)
    print("Access Project - Data Source Update")
    print("=" * 70)

    if args.source:
        # Update single source
        if args.source in DATA_SOURCES:
            config = DATA_SOURCES[args.source]
            assert isinstance(config, dict)
            success = update_data_source(args.source, config)
            sys.exit(0 if success else 1)
        else:
            print(f"Error: Source '{args.source}' not found")
            print(f"Available sources: {', '.join(DATA_SOURCES.keys())}")
            sys.exit(1)
    else:
        # Update all sources
        results = update_all_sources(force=args.force)

        print("\n" + "=" * 70)
        print("UPDATE SUMMARY")
        print("=" * 70)

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        for name, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{status}: {name}")

        print(f"\nUpdated {success_count}/{total_count} sources successfully")

        if success_count == total_count:
            return 0
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())
