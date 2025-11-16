#!/usr/bin/env python3
"""
Validate data files for schema changes, data quality, and consistency.
This script checks for schema changes, validates data quality, and ensures coordinate system consistency.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data/validation_log.txt"), logging.StreamHandler()],
)

# Schema version file
SCHEMA_FILE = Path("data/schema_versions.json")


def load_schema_versions() -> dict:
    """Load schema version history."""
    if SCHEMA_FILE.exists():
        try:
            with open(SCHEMA_FILE) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_schema_versions(schemas: dict):
    """Save schema version history."""
    SCHEMA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEMA_FILE, "w") as f:
        json.dump(schemas, f, indent=2, default=str)


def get_schema(file_path: Path) -> dict:
    """Extract schema information from a data file."""
    try:
        if file_path.suffix == ".parquet":
            gdf = gpd.read_parquet(file_path)
        elif (
            file_path.suffix == ".geojson"
            or file_path.suffix == ".json"
            or file_path.suffix == ".shp"
            or file_path.suffix == ".zip"
        ):
            gdf = gpd.read_file(file_path)
        else:
            # Try to read as Parquet, CSV, or other format
            try:
                if file_path.suffix == ".parquet":
                    df = pd.read_parquet(file_path)
                else:
                    df = pd.read_csv(file_path)
                return {
                    "columns": list(df.columns),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "row_count": len(df),
                    "has_geometry": False,
                }
            except Exception:
                logging.warning(f"Could not read {file_path} as GeoDataFrame or DataFrame")
                return {}

        schema = {
            "columns": list(gdf.columns),
            "dtypes": {col: str(dtype) for col, dtype in gdf.dtypes.items()},
            "row_count": len(gdf),
            "has_geometry": True,
            "crs": str(gdf.crs) if gdf.crs else None,
            "geometry_type": (
                gdf.geometry.geom_type.unique().tolist()
                if hasattr(gdf.geometry, "geom_type")
                else None
            ),
        }

        return schema

    except Exception as e:
        logging.error(f"Error reading schema from {file_path}: {e}")
        return {}


def compare_schemas(old_schema: dict, new_schema: dict) -> dict:
    """Compare two schemas and detect changes."""
    changes = {
        "added_columns": [],
        "removed_columns": [],
        "type_changes": [],
        "row_count_change": None,
        "crs_change": None,
        "geometry_type_change": None,
    }

    if not old_schema or not new_schema:
        return changes

    old_columns = set(old_schema.get("columns", []))
    new_columns = set(new_schema.get("columns", []))

    changes["added_columns"] = list(new_columns - old_columns)
    changes["removed_columns"] = list(old_columns - new_columns)

    # Check for type changes in common columns
    old_dtypes = old_schema.get("dtypes", {})
    new_dtypes = new_schema.get("dtypes", {})

    common_columns = old_columns & new_columns
    for col in common_columns:
        old_type = old_dtypes.get(col)
        new_type = new_dtypes.get(col)
        if old_type and new_type and old_type != new_type:
            changes["type_changes"].append(
                {"column": col, "old_type": old_type, "new_type": new_type}
            )

    # Check row count change
    old_count = old_schema.get("row_count", 0)
    new_count = new_schema.get("row_count", 0)
    if old_count != new_count:
        changes["row_count_change"] = {
            "old": old_count,
            "new": new_count,
            "difference": new_count - old_count,
            "percent_change": (
                ((new_count - old_count) / old_count * 100) if old_count > 0 else None
            ),
        }

    # Check CRS change
    old_crs = old_schema.get("crs")
    new_crs = new_schema.get("crs")
    if old_crs != new_crs:
        changes["crs_change"] = {"old": old_crs, "new": new_crs}

    # Check geometry type change
    old_geom_type = old_schema.get("geometry_type")
    new_geom_type = new_schema.get("geometry_type")
    if old_geom_type != new_geom_type:
        changes["geometry_type_change"] = {"old": old_geom_type, "new": new_geom_type}

    return changes


def validate_data_quality(file_path: Path, schema: dict | None = None) -> dict:  # noqa: ARG001
    """Validate data quality metrics."""
    quality_metrics = {
        "missing_values": {},
        "outliers": {},
        "invalid_geometries": 0,
        "empty_geometries": 0,
        "duplicate_rows": 0,
    }

    try:
        if file_path.suffix == ".parquet":
            gdf = gpd.read_parquet(file_path)
        elif file_path.suffix in [".geojson", ".json", ".shp", ".zip"]:
            gdf = gpd.read_file(file_path)
        else:
            # Try Parquet or CSV
            if file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)
            gdf = None

        if gdf is not None:
            # Check for invalid geometries
            invalid_geoms = gdf.geometry.isna().sum()
            quality_metrics["invalid_geometries"] = int(invalid_geoms)

            # Check for empty geometries
            if hasattr(gdf.geometry, "is_empty"):
                empty_geoms = gdf.geometry.is_empty.sum()
                quality_metrics["empty_geometries"] = int(empty_geoms)

            # Check for missing values in all columns
            for col in gdf.columns:
                if col != "geometry":
                    missing = gdf[col].isna().sum()
                    if missing > 0:
                        quality_metrics["missing_values"][col] = {
                            "count": int(missing),
                            "percent": (missing / len(gdf)) * 100,
                        }

            # Check for duplicate rows
            duplicates = gdf.duplicated().sum()
            quality_metrics["duplicate_rows"] = int(duplicates)

            # Check for outliers in numeric columns
            numeric_cols = gdf.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col != "geometry":
                    values = gdf[col].dropna()
                    if len(values) > 0:
                        q1 = values.quantile(0.25)
                        q3 = values.quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        outliers = ((values < lower_bound) | (values > upper_bound)).sum()
                        if outliers > 0:
                            quality_metrics["outliers"][col] = {
                                "count": int(outliers),
                                "percent": (outliers / len(values)) * 100,
                            }
        else:
            # DataFrame validation
            for col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    quality_metrics["missing_values"][col] = {
                        "count": int(missing),
                        "percent": (missing / len(df)) * 100,
                    }

            duplicates = df.duplicated().sum()
            quality_metrics["duplicate_rows"] = int(duplicates)

            # Check for outliers in numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                values = df[col].dropna()
                if len(values) > 0:
                    q1 = values.quantile(0.25)
                    q3 = values.quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = ((values < lower_bound) | (values > upper_bound)).sum()
                    if outliers > 0:
                        quality_metrics["outliers"][col] = {
                            "count": int(outliers),
                            "percent": (outliers / len(values)) * 100,
                        }

        return quality_metrics

    except Exception as e:
        logging.error(f"Error validating data quality for {file_path}: {e}")
        return quality_metrics


def check_coordinate_system_consistency(
    file_path: Path, expected_crs: str | None = None
) -> tuple[bool, str | None]:
    """Check if coordinate system is consistent."""
    try:
        if file_path.suffix == ".parquet":
            gdf = gpd.read_parquet(file_path)
        elif file_path.suffix in [".geojson", ".json", ".shp", ".zip"]:
            gdf = gpd.read_file(file_path)

            if gdf.crs is None:
                return False, "No CRS defined"

            current_crs = str(gdf.crs)

            if expected_crs and current_crs != expected_crs:
                # Check if CRS matches expected
                return False, f"CRS mismatch: expected {expected_crs}, got {current_crs}"

            return True, current_crs
        else:
            return True, "Not a geospatial file"

    except Exception as e:
        logging.error(f"Error checking coordinate system for {file_path}: {e}")
        return False, str(e)


def validate_data_file(file_path: Path, source_name: str | None = None) -> dict:
    """Validate a single data file."""
    validation_result = {
        "file_path": str(file_path),
        "source_name": source_name,
        "timestamp": datetime.now().isoformat(),
        "schema": {},
        "schema_changes": {},
        "quality_metrics": {},
        "crs_check": {},
        "valid": True,
        "warnings": [],
        "errors": [],
    }

    logging.info(f"Validating {file_path}...")

    # Get current schema
    current_schema = get_schema(file_path)
    validation_result["schema"] = current_schema

    if not current_schema:
        validation_result["valid"] = False
        validation_result["errors"].append("Could not read schema from file")
        return validation_result

    # Check for schema changes
    if source_name:
        schema_versions = load_schema_versions()
        source_schemas = schema_versions.get(source_name, {})

        if source_schemas:
            # Get most recent schema
            latest_version = max(
                source_schemas.keys(), key=lambda x: source_schemas[x].get("timestamp", "")
            )
            old_schema = source_schemas[latest_version].get("schema", {})

            schema_changes = compare_schemas(old_schema, current_schema)
            validation_result["schema_changes"] = schema_changes

            # Check for breaking changes
            if schema_changes["removed_columns"]:
                validation_result["warnings"].append(
                    f"Removed columns: {', '.join(schema_changes['removed_columns'])}"
                )

            if schema_changes["type_changes"]:
                validation_result["warnings"].append(
                    f"Type changes: {len(schema_changes['type_changes'])} columns"
                )

            if schema_changes["crs_change"]:
                validation_result["warnings"].append(
                    f"CRS changed: {schema_changes['crs_change']['old']} -> {schema_changes['crs_change']['new']}"
                )

        # Save current schema version
        if source_name not in schema_versions:
            schema_versions[source_name] = {}

        version_key = datetime.now().strftime("%Y%m%d_%H%M%S")
        schema_versions[source_name][version_key] = {
            "timestamp": datetime.now().isoformat(),
            "schema": current_schema,
        }
        save_schema_versions(schema_versions)

    # Validate data quality
    quality_metrics = validate_data_quality(file_path, current_schema)
    validation_result["quality_metrics"] = quality_metrics

    # Check for quality issues
    if quality_metrics["invalid_geometries"] > 0:
        validation_result["warnings"].append(
            f"{quality_metrics['invalid_geometries']} invalid geometries"
        )

    if quality_metrics["empty_geometries"] > 0:
        validation_result["warnings"].append(
            f"{quality_metrics['empty_geometries']} empty geometries"
        )

    high_missing = {
        col: metrics
        for col, metrics in quality_metrics["missing_values"].items()
        if metrics["percent"] > 10
    }
    if high_missing:
        validation_result["warnings"].append(
            f"High missing values (>10%): {', '.join(high_missing.keys())}"
        )

    # Check coordinate system
    crs_valid, crs_message = check_coordinate_system_consistency(file_path)
    validation_result["crs_check"] = {"valid": crs_valid, "message": crs_message}

    if not crs_valid:
        validation_result["warnings"].append(f"CRS issue: {crs_message}")

    return validation_result


def validate_all_data_sources() -> dict[str, dict]:
    """Validate all data sources."""
    results = {}

    # Map source names to file paths
    source_files = {
        "Census TIGER/Line Blocks": Path("data/blocks"),
        "Census TIGER/Line Tracts": Path("data/tracts"),
        "Maine GeoLibrary Conserved Lands": Path("data/conserved_lands"),
        "CEJST (Climate Equity and Justice Screening Tool)": Path("data/cejst-us"),
        "Census Relationship File": Path("data/tab2010_tab2020_st23_me.txt"),
    }

    for source_name, file_path in source_files.items():
        if file_path.is_file():
            # Single file
            result = validate_data_file(file_path, source_name)
            results[source_name] = result
        elif file_path.is_dir():
            # Directory - find main files
            # Look for shapefiles or GeoJSON files
            shapefiles = list(file_path.rglob("*.shp"))
            geojson_files = list(file_path.rglob("*.geojson"))
            parquet_files = list(file_path.rglob("*.parquet"))

            # Prefer parquet files, then shapefiles with nodes, then regular shapefiles
            if parquet_files:
                with_nodes = [f for f in parquet_files if "_with_nodes" in f.stem]
                target_file = with_nodes[0] if with_nodes else parquet_files[0]
                result = validate_data_file(target_file, source_name)
                results[source_name] = result
            elif shapefiles:
                # Use first shapefile (or _with_nodes version if available)
                with_nodes = [f for f in shapefiles if "_with_nodes" in f.stem]
                target_file = with_nodes[0] if with_nodes else shapefiles[0]
                result = validate_data_file(target_file, source_name)
                results[source_name] = result
            elif geojson_files:
                result = validate_data_file(geojson_files[0], source_name)
                results[source_name] = result
            else:
                logging.warning(f"No data files found for {source_name} in {file_path}")

    return results


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate data files")
    parser.add_argument("--file", type=Path, help="Validate a specific file")
    parser.add_argument("--source", type=str, help="Validate a specific source by name")
    parser.add_argument("--all", action="store_true", help="Validate all data sources")

    args = parser.parse_args()

    print("=" * 70)
    print("Access Project - Data Validation")
    print("=" * 70)

    if args.file:
        # Validate single file
        result = validate_data_file(args.file)
        print(f"\nValidation result for {args.file}:")
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result["valid"] else 1)
    elif args.source:
        # Validate specific source
        source_files = {
            "Census TIGER/Line Blocks": Path("data/blocks"),
            "Census TIGER/Line Tracts": Path("data/tracts"),
            "Maine GeoLibrary Conserved Lands": Path("data/conserved_lands"),
            "CEJST (Climate Equity and Justice Screening Tool)": Path("data/cejst-maine.shp"),
            "Census Relationship File": Path("data/tab2010_tab2020_st23_me.txt"),
        }

        if args.source not in source_files:
            print(f"Error: Source '{args.source}' not found")
            print(f"Available sources: {', '.join(source_files.keys())}")
            sys.exit(1)

        file_path = source_files[args.source]
        result = validate_data_file(file_path, args.source)
        print(f"\nValidation result for {args.source}:")
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result["valid"] else 1)
    elif args.all:
        # Validate all sources
        results = validate_all_data_sources()

        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)

        all_valid = True
        for source_name, result in results.items():
            status = "✓ VALID" if result["valid"] else "✗ INVALID"
            print(f"\n{status}: {source_name}")

            if result["warnings"]:
                print("  Warnings:")
                for warning in result["warnings"]:
                    print(f"    - {warning}")

            if result["errors"]:
                print("  Errors:")
                for error in result["errors"]:
                    print(f"    - {error}")
                all_valid = False

        sys.exit(0 if all_valid else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
