#!/usr/bin/env python3
"""
Probe all data sources used in the Access project for availability.
If a source is unavailable, we will update it.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import osmnx as ox
import requests

# Set OSMnx cache folder
ox.settings.cache_folder = "./cache/"

# Metadata file for tracking data source versions
METADATA_FILE = Path("data/data_source_metadata.json")


def load_metadata() -> dict:
    """Load data source metadata from file."""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_metadata(metadata: dict):
    """Save data source metadata to file."""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2, default=str)


def get_version_from_url(url: str) -> str | None:
    """Extract version/year from URL if present."""
    # Look for year patterns like TIGER2020, TIGER2022, rel2020
    year_match = re.search(r"(?:TIGER|rel)(\d{4})", url, re.IGNORECASE)
    if year_match:
        return year_match.group(1)
    return None


def get_local_file_date(local_path: Path) -> datetime | None:
    """Get modification date of local file."""
    if local_path.exists():
        return datetime.fromtimestamp(local_path.stat().st_mtime)
    return None


def get_remote_file_date(url: str) -> datetime | None:
    """Get Last-Modified date from remote file."""
    try:
        response = requests.head(url, timeout=30, allow_redirects=True)
        if response.status_code == 200:
            last_modified = response.headers.get("Last-Modified")
            if last_modified:
                try:
                    from email.utils import parsedate_to_datetime

                    return parsedate_to_datetime(last_modified)
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass
    return None


# Data source URLs and endpoints
DATA_SOURCES = {
    "OpenStreetMap (OSMnx)": {
        "type": "osmnx",
        "test": "graph_from_place",
        "params": {"place": {"state": "Maine"}, "network_type": "walk"},
        "description": "Street network data via OSMnx from OpenStreetMap",
    },
    "Census TIGER/Line Blocks": {
        "type": "http",
        "url": "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_23_tabblock20.zip",
        "description": "Census block boundaries for Maine (FIPS code 23)",
    },
    "Census TIGER/Line Tracts": {
        "type": "http",
        "url": "https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_23_tract.zip",
        "description": "Census tract boundaries for Maine (FIPS code 23)",
    },
    "Census API": {
        "type": "census_api",
        "description": "Census Bureau API for demographic data (requires API key)",
    },
    "Census Relationship File": {
        "type": "http",
        "url": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/tabblock2010_tabblock2020_st23_me.txt",
        "alternative_urls": [
            "https://www2.census.gov/geo/docs/maps-data/data/rel2020/tabblock2010_tabblock2020_st23_me.zip",
            "https://www2.census.gov/programs-surveys/geography/technical-documentation/records-layout/2020-census-block-record-layout.html",
        ],
        "local_path": "data/tab2010_tab2020_st23_me.txt",
        "description": "Census block relationship file for Maine (2010 to 2020). May need to download manually from Census website.",
    },
    "Maine GeoLibrary Conserved Lands": {
        "type": "arcgis",
        "url": "https://gis.maine.gov/arcgis/rest/services/acf/Conserved_Lands/MapServer/0/query",
        "alternative_urls": [
            "https://www.maine.gov/geolib/catalog.html",
            "https://gis.maine.gov/arcgis/rest/services/",
        ],
        "local_path": "data/conserved_lands",
        "params": {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
            "returnGeometry": "true",
            "resultRecordCount": "1",
        },
        "description": "Maine Conserved Lands dataset from Maine GeoLibrary. Service endpoint may have changed - check Maine GeoLibrary catalog.",
    },
    "CEJST (Climate Equity and Justice Screening Tool)": {
        "type": "http",
        "url": "https://dblew8dgr6ajz.cloudfront.net/data-versions/2.0/data/score/downloadable/2.0-shapefile-codebook.zip",
        "alternative_urls": [
            "https://public-environmental-data-partners.github.io/j40-cejst-2/en/downloads",
            "https://screeningtool.geoplatform.gov/api/v1/cejst/download-file/state/me",
            "https://screeningtool.geoplatform.gov/api/v1/cejst/download-file/state/ME",
        ],
        "local_path": "data/cejst-us.zip",
        "description": "CEJST Version 2.0 shapefile covering all US census tracts from public-environmental-data-partners.github.io/j40-cejst-2",
    },
}


def test_osmnx_source(
    name: str, config: dict  # noqa: ARG001
) -> tuple[bool, str | None, dict | None]:
    """Test OSMnx data source availability."""
    metadata = load_metadata()
    try:
        print("  Testing OSMnx connection...")
        # Try a small test query to Portland, Maine (much smaller than full state)
        test_place = {"city": "Portland", "state": "Maine"}
        G = ox.graph_from_place(test_place, network_type="walk", simplify=True)
        if G is not None and len(G.nodes) > 0:
            message = f"Successfully connected. Test query returned {len(G.nodes)} nodes."
            # Update metadata
            new_metadata = {
                "last_checked": datetime.now().isoformat(),
                "update_available": False,  # OSMnx is continuously updated
            }
            metadata[name] = new_metadata
            save_metadata(metadata)
            return True, message, new_metadata
        else:
            return False, "Connection successful but returned empty graph.", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def test_http_source(name: str, config: dict) -> tuple[bool, str | None, dict | None]:
    """Test HTTP data source availability and check for updates."""
    url = config["url"]
    local_path = config.get("local_path")
    metadata = load_metadata()
    source_metadata = metadata.get(name, {})

    version = get_version_from_url(url)
    local_file = None
    local_date = None
    remote_date = None
    update_available = False

    # Check if local file exists first
    if local_path:
        local_file = Path(local_path)
        if local_file.exists():
            size = local_file.stat().st_size if local_file.is_file() else "directory"
            local_date = get_local_file_date(local_file)
            message = f"Available locally at {local_path} (Size: {size})"
            if local_date:
                message += f", Last modified: {local_date.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            message = "Not available locally"
    else:
        message = "No local path specified"

    # Check remote for updates
    try:
        print(f"  Testing HTTP connection to {url}...")
        response = requests.head(url, timeout=30, allow_redirects=True)
        if response.status_code == 200:
            content_length = response.headers.get("Content-Length", "unknown")
            remote_date = get_remote_file_date(url)

            if local_file and local_file.exists() and remote_date and local_date:
                if remote_date > local_date:
                    update_available = True
                    message += f" | UPDATE AVAILABLE: Remote is newer (Remote: {remote_date.strftime('%Y-%m-%d %H:%M:%S')})"
                else:
                    message += f" | Remote available (Last-Modified: {remote_date.strftime('%Y-%m-%d %H:%M:%S')})"
            else:
                message += f" | Available online (Status: {response.status_code}, Size: {content_length} bytes)"

            # Update metadata
            new_metadata = {
                "version": version or source_metadata.get("version"),
                "local_date": local_date.isoformat() if local_date else None,
                "remote_date": remote_date.isoformat() if remote_date else None,
                "last_checked": datetime.now().isoformat(),
                "update_available": update_available,
            }
            metadata[name] = new_metadata
            save_metadata(metadata)

            return True, message, new_metadata
        elif response.status_code == 301 or response.status_code == 302:
            # Follow redirect
            response = requests.get(url, timeout=30, allow_redirects=True, stream=True)
            if response.status_code == 200:
                return True, f"Available online (Status: {response.status_code}, redirected)", None
            else:
                return False, f"Redirected but returned status {response.status_code}", None
        else:
            if local_path and Path(local_path).exists():
                return (
                    True,
                    f"Online unavailable (Status: {response.status_code}), but available locally at {local_path}",
                    None,
                )
            return False, f"Status code: {response.status_code}", None
    except requests.exceptions.Timeout:
        if local_path and Path(local_path).exists():
            return True, f"Online timeout, but available locally at {local_path}", None
        return False, "Connection timeout", None
    except requests.exceptions.ConnectionError:
        if local_path and Path(local_path).exists():
            return True, f"Online connection error, but available locally at {local_path}", None
        return False, "Connection error - server may be down", None
    except Exception as e:
        if local_path and Path(local_path).exists():
            return True, f"Online error ({str(e)}), but available locally at {local_path}", None
        return False, f"Error: {str(e)}", None


def test_arcgis_source(name: str, config: dict) -> tuple[bool, str | None, dict | None]:
    """Test ArcGIS REST service availability and check for updates."""
    url = config["url"]
    params = config.get("params", {})
    local_path = config.get("local_path")
    metadata = load_metadata()

    local_date = None
    update_available = False

    # Check if local file exists first
    if local_path:
        local_file = Path(local_path)
        if local_file.exists():
            local_date = get_local_file_date(local_file)
            message = f"Available locally at {local_path}"
            if local_date:
                message += f" (Last modified: {local_date.strftime('%Y-%m-%d %H:%M:%S')})"
        else:
            message = "Not available locally"
    else:
        message = "No local path specified"

    try:
        print(f"  Testing ArcGIS REST service at {url}...")
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            try:
                data = response.json()
                if "features" in data or ("error" not in data and "error" not in str(data)):
                    feature_count = len(data.get("features", []))
                    # Check if service has been updated (basic check - could be enhanced)
                    # For now, just note that service is available
                    message += f" | Available online (Status: {response.status_code}, Features: {feature_count})"

                    # Update metadata
                    new_metadata = {
                        "local_date": local_date.isoformat() if local_date else None,
                        "last_checked": datetime.now().isoformat(),
                        "update_available": update_available,
                        "feature_count": feature_count,
                    }
                    metadata[name] = new_metadata
                    save_metadata(metadata)

                    return True, message, new_metadata
                else:
                    error_msg = (
                        data.get("error", {}).get("message", "Unknown error")
                        if isinstance(data.get("error"), dict)
                        else str(data.get("error", "Unknown error"))
                    )
                    if local_path and Path(local_path).exists():
                        return (
                            True,
                            f"Online service error ({error_msg}), but available locally at {local_path}",
                            None,
                        )
                    return False, f"Service returned error: {error_msg}", None
            except json.JSONDecodeError:
                if local_path and Path(local_path).exists():
                    return (
                        True,
                        f"Online response invalid JSON, but available locally at {local_path}",
                        None,
                    )
                return False, "Response is not valid JSON", None
        else:
            if local_path and Path(local_path).exists():
                return (
                    True,
                    f"Online unavailable (Status: {response.status_code}), but available locally at {local_path}",
                    None,
                )
            return False, f"Status code: {response.status_code}", None
    except requests.exceptions.Timeout:
        if local_path and Path(local_path).exists():
            return True, f"Online timeout, but available locally at {local_path}", None
        return False, "Connection timeout", None
    except requests.exceptions.ConnectionError:
        if local_path and Path(local_path).exists():
            return True, f"Online connection error, but available locally at {local_path}", None
        return False, "Connection error - server may be down", None
    except Exception as e:
        if local_path and Path(local_path).exists():
            return True, f"Online error ({str(e)}), but available locally at {local_path}", None
        return False, f"Error: {str(e)}", None


def test_census_api(
    name: str, config: dict  # noqa: ARG001
) -> tuple[bool, str | None, dict | None]:
    """Test Census API availability (requires API key)."""
    metadata = load_metadata()
    try:
        from census import Census
        from dotenv import dotenv_values

        env_path = Path(".env")
        if not env_path.exists():
            return False, "No .env file found. Census API requires CENSUS_API_KEY.", None

        config_env = dotenv_values(".env")
        api_key = config_env.get("CENSUS_API_KEY")

        if not api_key:
            return False, "CENSUS_API_KEY not found in .env file.", None

        print("  Testing Census API with provided key...")
        c = Census(api_key)
        # Test with a small query for Maine (state FIPS 23)
        # Use get method for block-level data (state_county_block method doesn't exist)
        result = c.pl.get(
            fields=["GEO_ID", "P1_001N"],
            geo={"for": "block:*", "in": "state:23 county:001"},  # Androscoggin County
            year=2020,
        )
        if result and len(result) > 0:
            message = f"Available. Test query returned {len(result)} blocks."
            # Update metadata
            new_metadata = {
                "last_checked": datetime.now().isoformat(),
                "update_available": False,  # API is real-time
            }
            metadata[name] = new_metadata
            save_metadata(metadata)
            return True, message, new_metadata
        else:
            return False, "API key valid but query returned no results.", None
    except ImportError:
        return False, "Required packages not installed: python-dotenv, census", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def probe_data_source(name: str, config: dict) -> tuple[bool, str | None, dict | None]:
    """Probe a single data source for availability."""
    print(f"\nProbing: {name}")
    print(f"  Description: {config['description']}")

    source_type = config["type"]

    if source_type == "osmnx":
        return test_osmnx_source(name, config)
    elif source_type == "http":
        return test_http_source(name, config)
    elif source_type == "arcgis":
        return test_arcgis_source(name, config)
    elif source_type == "census_api":
        return test_census_api(name, config)
    else:
        return False, f"Unknown source type: {source_type}", None


def main():
    """Main function to probe all data sources."""
    print("=" * 70)
    print("Access Project - Data Source Availability Probe")
    print("=" * 70)

    results = {}
    unavailable_sources = []
    updates_available = []

    for name, config in DATA_SOURCES.items():
        is_available, message, metadata = probe_data_source(name, config)
        results[name] = {"available": is_available, "message": message, "metadata": metadata}

        if not is_available:
            unavailable_sources.append((name, message))
        elif metadata and metadata.get("update_available"):
            updates_available.append((name, message))

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, result in results.items():
        status = "✓ AVAILABLE" if result["available"] else "✗ UNAVAILABLE"
        print(f"\n{status}: {name}")
        print(f"  {result['message']}")

    if updates_available:
        print("\n" + "=" * 70)
        print("UPDATES AVAILABLE")
        print("=" * 70)
        for name, message in updates_available:
            print(f"\n{name}:")
            print(f"  {message}")
        print("\nConsider running update_data_sources.py to download updates.")

    if unavailable_sources:
        print("\n" + "=" * 70)
        print("UNAVAILABLE SOURCES - ACTION REQUIRED")
        print("=" * 70)
        for name, message in unavailable_sources:
            print(f"\n{name}:")
            print(f"  {message}")
        print("\nThese sources need to be updated or fixed.")
        return 1
    else:
        print("\n" + "=" * 70)
        print("ALL DATA SOURCES ARE AVAILABLE")
        print("=" * 70)
        if updates_available:
            return 2  # Exit code 2 indicates updates available
        return 0


if __name__ == "__main__":
    sys.exit(main())
