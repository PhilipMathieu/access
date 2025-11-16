"""Block merging operations."""

import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from config.regions import RegionConfig

logger = logging.getLogger(__name__)


def merge_walk_times(
    blocks_path: str | Path,
    walk_times_path: str | Path,
    conserved_lands_path: str | Path,
    output_path: str | Path | None = None,
    trip_times: list[int] | None = None,
    region_config: RegionConfig | None = None,  # noqa: ARG001
) -> gpd.GeoDataFrame:
    """Merge walk times with blocks and conserved lands data.

    Args:
        blocks_path: Path to blocks shapefile with OSMnx node IDs
        walk_times_path: Path to walk times CSV file
        conserved_lands_path: Path to conserved lands shapefile with OSMnx node IDs
        output_path: Optional path to save merged GeoDataFrame
        trip_times: Optional list of trip times (default: from walk_times data)
        region_config: Optional region configuration (currently unused but reserved for future)

    Returns:
        GeoDataFrame with merged data
    """
    logger.info("Loading blocks data")
    if str(blocks_path).endswith(".parquet"):
        blocks = gpd.read_parquet(str(blocks_path))
    else:
        blocks = gpd.read_file(str(blocks_path))  # Fallback for existing shapefiles

    logger.info("Loading conserved lands data")
    if str(conserved_lands_path).endswith(".parquet"):
        conserved_lands = gpd.read_parquet(str(conserved_lands_path))
    else:
        conserved_lands = gpd.read_file(
            str(conserved_lands_path)
        )  # Fallback for existing shapefiles

    logger.info("Loading walk times data")
    if str(walk_times_path).endswith(".parquet"):
        df = pd.read_parquet(str(walk_times_path))
        # Handle index if it was saved as index
        if df.index.name in ["tract_osmid", "block_osmid"]:
            pass  # Index is already set correctly
        elif df.index.name is None and len(df.index) > 0 and isinstance(df.index, pd.RangeIndex):
            # Try to reset index if it's a default integer index
            df = df.reset_index(drop=True)
    else:
        df = pd.read_csv(str(walk_times_path), index_col=0)  # Fallback for CSV input

    # Determine the column name for center node (could be tract_osmid or block_osmid)
    # Check if it's in the index name or columns
    if df.index.name in ["tract_osmid", "block_osmid"]:
        center_node_col = df.index.name
        # Reset index to make it a column for merging
        df = df.reset_index()
    elif "tract_osmid" in df.columns:
        center_node_col = "tract_osmid"
    elif "block_osmid" in df.columns:
        center_node_col = "block_osmid"
    else:
        raise ValueError(
            f"Walk times CSV must contain either 'tract_osmid' or 'block_osmid' as index or column. "
            f"Index name: {df.index.name}, Columns: {list(df.columns)}"
        )

    logger.info(f"Using center node column: {center_node_col}")

    # Merge walk times with conserved lands
    logger.info("Merging walk times with conserved lands")
    df_with_lands = df.merge(
        conserved_lands.drop(columns="geometry"), how="left", left_on="land_osmid", right_on="osmid"
    )

    # Merge with blocks
    logger.info("Merging with blocks")
    # Rename the center node column to match blocks' osmid column for merging
    # We'll keep the original column name for reference
    merge = gpd.GeoDataFrame(
        blocks.merge(df_with_lands, how="outer", left_on="osmid", right_on=center_node_col)
    )

    # Create trip time columns
    if trip_times is None:
        trip_times = sorted(merge["trip_time"].dropna().unique().astype(int).tolist())

    logger.info(f"Creating trip time columns for: {trip_times}")
    merge = create_trip_time_columns(merge, trip_times)

    if output_path:
        logger.info(f"Saving merged data to {output_path}")
        # Convert OSMnx ID columns to strings to avoid shapefile field width limitations
        # Shapefiles have a 10-digit limit for integers, but OSMnx IDs can be much larger
        osmid_columns = [col for col in merge.columns if "osmid" in col.lower()]
        for col in osmid_columns:
            if col in merge.columns:
                merge[col] = merge[col].astype(str)

        if str(output_path).endswith(".parquet"):
            merge.to_parquet(str(output_path))
        else:
            merge.to_file(str(output_path))  # Fallback for shapefile output

    return merge


def create_trip_time_columns(
    merge_df: gpd.GeoDataFrame,
    trip_times: list[int],
    acres_col: str = "CALC_AC",
) -> gpd.GeoDataFrame:
    """Create AC_* columns for each trip time.

    Creates columns like AC_5, AC_10, etc. containing acres of conserved land
    accessible within that trip time threshold. Columns are cumulative - AC_5
    includes all lands accessible within 5 minutes, AC_10 includes all within
    10 minutes, etc.

    Args:
        merge_df: GeoDataFrame with trip_time and acres columns
        trip_times: List of trip time thresholds in minutes (should be sorted)
        acres_col: Name of column containing acres (default: "CALC_AC")

    Returns:
        GeoDataFrame with AC_* columns added
    """
    merge_df = merge_df.copy()  # Avoid SettingWithCopyWarning

    # Ensure trip_times are sorted
    trip_times = sorted(trip_times)

    for time in trip_times:
        col_name = f"AC_{time}"
        # Include all conserved lands accessible within this time threshold
        # (trip_time <= time means accessible within this threshold)
        # Initialize column with 0.0
        merge_df[col_name] = 0.0
        # Set to acres value where trip_time <= time
        mask = merge_df["trip_time"] <= time
        merge_df.loc[mask, col_name] = merge_df.loc[mask, acres_col]

    return merge_df


def dissolve_blocks(
    merge_df: gpd.GeoDataFrame,
    groupby_col: str = "GEOID20",
    aggfunc: str = "sum",
) -> gpd.GeoDataFrame:
    """Aggregate blocks by dissolving on a groupby column.

    Optimized to handle large datasets by:
    1. Separating geometry operations from data aggregation
    2. Using unique geometries per group (blocks with same GEOID20 have same geometry)
    3. Aggregating numeric data separately

    Args:
        merge_df: GeoDataFrame with block-level data
        groupby_col: Column to group by (default: "GEOID20")
        aggfunc: Aggregation function (default: "sum")

    Returns:
        Dissolved GeoDataFrame
    """
    logger.info(f"Dissolving blocks by {groupby_col}")
    logger.info(f"Input rows: {len(merge_df):,}")

    # Identify numeric columns to aggregate (exclude geometry and groupby_col)
    numeric_cols = merge_df.select_dtypes(include=[np.number]).columns.tolist()
    if groupby_col in numeric_cols:
        numeric_cols.remove(groupby_col)

    # Identify geometry column
    geom_col = merge_df.geometry.name

    # Get unique geometries per groupby_col (blocks with same GEOID20 have same geometry)
    logger.info("Extracting unique geometries per group...")
    unique_geoms = merge_df[[groupby_col, geom_col]].drop_duplicates(subset=[groupby_col])
    logger.info(f"Unique groups: {len(unique_geoms):,}")

    # Aggregate numeric data separately (much faster than dissolve with geometry)
    logger.info("Aggregating numeric data...")
    agg_dict = {col: aggfunc for col in numeric_cols if col in merge_df.columns}

    # Handle non-numeric columns that might need aggregation
    # For now, we'll drop them or take first value
    other_cols = [
        col
        for col in merge_df.columns
        if col not in numeric_cols and col != geom_col and col != groupby_col
    ]

    if other_cols:
        logger.info(
            f"Dropping non-numeric columns: {other_cols[:5]}..."
            if len(other_cols) > 5
            else f"Dropping non-numeric columns: {other_cols}"
        )

    # Aggregate numeric columns
    aggregated = merge_df.groupby(groupby_col, as_index=False).agg(agg_dict)
    logger.info(f"Aggregated rows: {len(aggregated):,}")

    # Merge with unique geometries
    logger.info("Merging aggregated data with geometries...")
    dissolved = unique_geoms.merge(aggregated, on=groupby_col, how="right")

    # Ensure it's a GeoDataFrame
    dissolved = gpd.GeoDataFrame(dissolved, geometry=geom_col, crs=merge_df.crs)

    logger.info(f"Dissolved rows: {len(dissolved):,}")
    return dissolved
