"""Block merging operations."""

import logging
from pathlib import Path
from typing import List, Optional, Union

import geopandas as gpd
import numpy as np
import pandas as pd

from config.defaults import DEFAULT_TRIP_TIMES
from config.regions import RegionConfig

logger = logging.getLogger(__name__)


def merge_walk_times(
    blocks_path: Union[str, Path],
    walk_times_path: Union[str, Path],
    conserved_lands_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    trip_times: Optional[List[int]] = None,
    region_config: Optional[RegionConfig] = None,
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
    blocks = gpd.read_file(str(blocks_path))
    
    logger.info("Loading conserved lands data")
    conserved_lands = gpd.read_file(str(conserved_lands_path))
    
    logger.info("Loading walk times data")
    df = pd.read_csv(str(walk_times_path), index_col=0)
    
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
        conserved_lands.drop(columns='geometry'),
        how="left",
        left_on="land_osmid",
        right_on="osmid"
    )
    
    # Merge with blocks
    logger.info("Merging with blocks")
    # Rename the center node column to match blocks' osmid column for merging
    # We'll keep the original column name for reference
    merge = gpd.GeoDataFrame(
        blocks.merge(
            df_with_lands,
            how="outer",
            left_on="osmid",
            right_on=center_node_col
        )
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
        osmid_columns = [col for col in merge.columns if 'osmid' in col.lower()]
        for col in osmid_columns:
            if col in merge.columns:
                merge[col] = merge[col].astype(str)
        merge.to_file(str(output_path))
    
    return merge


def create_trip_time_columns(
    merge_df: gpd.GeoDataFrame,
    trip_times: List[int],
    acres_col: str = "CALC_AC",
) -> gpd.GeoDataFrame:
    """Create AC_* columns for each trip time.
    
    Creates columns like AC_5, AC_10, etc. containing acres of conserved land
    accessible within that trip time threshold.
    
    Args:
        merge_df: GeoDataFrame with trip_time and acres columns
        trip_times: List of trip time thresholds in minutes
        acres_col: Name of column containing acres (default: "CALC_AC")
        
    Returns:
        GeoDataFrame with AC_* columns added
    """
    merge_df = merge_df.copy()  # Avoid SettingWithCopyWarning
    
    for time in trip_times:
        col_name = f"AC_{time}"
        # Copy acres column
        merge_df[col_name] = merge_df[acres_col]
        # Set to NA for non-matching times
        merge_df.loc[merge_df["trip_time"] != time, col_name] = pd.NA
    
    return merge_df


def dissolve_blocks(
    merge_df: gpd.GeoDataFrame,
    groupby_col: str = "GEOID20",
    aggfunc: str = "sum",
) -> gpd.GeoDataFrame:
    """Aggregate blocks by dissolving on a groupby column.
    
    Args:
        merge_df: GeoDataFrame with block-level data
        groupby_col: Column to group by (default: "GEOID20")
        aggfunc: Aggregation function (default: "sum")
        
    Returns:
        Dissolved GeoDataFrame
    """
    logger.info(f"Dissolving blocks by {groupby_col}")
    dissolve = merge_df.dissolve(by=groupby_col, aggfunc=aggfunc)
    return dissolve

