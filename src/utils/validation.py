"""Validation utilities for data quality checks and schema validation.

This module provides functions for validating data at various stages
of the pipeline to catch errors early and provide clear error messages.
"""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

from exceptions import DataError, ValidationError

logger = logging.getLogger(__name__)


def validate_file_exists(file_path: Path, description: str = "File") -> None:
    """Validate that a file exists.

    Args:
        file_path: Path to the file
        description: Description of the file for error messages

    Raises:
        DataError: If file does not exist
    """
    if not file_path.exists():
        raise DataError(f"{description} not found: {file_path}")


def validate_geodataframe_schema(
    gdf: gpd.GeoDataFrame,
    required_columns: list[str],
    description: str = "GeoDataFrame",
) -> None:
    """Validate that a GeoDataFrame has required columns.

    Args:
        gdf: GeoDataFrame to validate
        required_columns: List of required column names
        description: Description of the data for error messages

    Raises:
        ValidationError: If required columns are missing
    """
    missing_columns = [col for col in required_columns if col not in gdf.columns]
    if missing_columns:
        raise ValidationError(
            f"{description} is missing required columns: {missing_columns}. "
            f"Available columns: {list(gdf.columns)}"
        )


def validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: list[str],
    description: str = "DataFrame",
) -> None:
    """Validate that a DataFrame has required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        description: Description of the data for error messages

    Raises:
        ValidationError: If required columns are missing
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValidationError(
            f"{description} is missing required columns: {missing_columns}. "
            f"Available columns: {list(df.columns)}"
        )


def validate_geometry(gdf: gpd.GeoDataFrame, description: str = "GeoDataFrame") -> None:
    """Validate that geometries are valid.

    Args:
        gdf: GeoDataFrame to validate
        description: Description of the data for error messages

    Raises:
        ValidationError: If geometries are invalid
    """
    if gdf.geometry.isna().any():
        invalid_count = gdf.geometry.isna().sum()
        raise ValidationError(
            f"{description} has {invalid_count} rows with missing/null geometries"
        )

    # Check for invalid geometries
    invalid_geoms = ~gdf.geometry.is_valid
    if invalid_geoms.any():
        invalid_count = invalid_geoms.sum()
        logger.warning(f"{description} has {invalid_count} invalid geometries")
        # Try to fix invalid geometries
        gdf.loc[invalid_geoms, "geometry"] = gdf.loc[invalid_geoms, "geometry"].buffer(0)


def validate_walk_times_data(
    df: pd.DataFrame,
    required_columns: list[str] | None = None,
) -> None:
    """Validate walk times data structure and values.

    Args:
        df: DataFrame with walk time data
        required_columns: Optional list of required columns (default: common walk time columns)

    Raises:
        ValidationError: If data validation fails
    """
    if required_columns is None:
        required_columns = ["GEOID20", "osmid"]

    validate_dataframe_schema(df, required_columns, "Walk times data")

    # Check for reasonable walk time values (should be positive and not too large)
    walk_time_columns = [
        col for col in df.columns if "walk_time" in col.lower() or "minutes" in col.lower()
    ]
    if walk_time_columns:
        for col in walk_time_columns:
            if df[col].notna().any():
                negative_values = (df[col] < 0).sum()
                if negative_values > 0:
                    raise ValidationError(
                        f"Walk times column {col} has {negative_values} negative values"
                    )
                # Warn about very large values (likely errors)
                large_values = (df[col] > 1000).sum()  # > 16 hours seems unreasonable
                if large_values > 0:
                    logger.warning(
                        f"Walk times column {col} has {large_values} values > 1000 minutes "
                        "(>16 hours), which may indicate errors"
                    )


def validate_blocks_data(gdf: gpd.GeoDataFrame) -> None:
    """Validate blocks GeoDataFrame structure.

    Args:
        gdf: GeoDataFrame with block data

    Raises:
        ValidationError: If data validation fails
    """
    required_columns = ["GEOID20"]
    validate_geodataframe_schema(gdf, required_columns, "Blocks data")
    validate_geometry(gdf, "Blocks data")

    # Check that GEOID20 is unique
    if gdf["GEOID20"].duplicated().any():
        duplicate_count = gdf["GEOID20"].duplicated().sum()
        raise ValidationError(f"Blocks data has {duplicate_count} duplicate GEOID20 values")


def validate_census_data(df: pd.DataFrame) -> None:
    """Validate census data structure.

    Args:
        df: DataFrame with census data

    Raises:
        ValidationError: If data validation fails
    """
    required_columns = ["GEOID20"]
    validate_dataframe_schema(df, required_columns, "Census data")

    # Check that GEOID20 is unique
    if df["GEOID20"].duplicated().any():
        duplicate_count = df["GEOID20"].duplicated().sum()
        raise ValidationError(f"Census data has {duplicate_count} duplicate GEOID20 values")


def validate_output_file(output_path: Path, min_size_bytes: int = 100) -> None:
    """Validate that an output file was created and has reasonable size.

    Args:
        output_path: Path to the output file
        min_size_bytes: Minimum expected file size in bytes

    Raises:
        DataError: If file validation fails
    """
    if not output_path.exists():
        raise DataError(f"Output file was not created: {output_path}")

    file_size = output_path.stat().st_size
    if file_size < min_size_bytes:
        raise DataError(
            f"Output file is suspiciously small ({file_size} bytes < {min_size_bytes} bytes): {output_path}"
        )

    logger.info(f"✓ Validated output file: {output_path} ({file_size:,} bytes)")
