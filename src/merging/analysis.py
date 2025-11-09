"""Block analysis with census and CEJST data."""

import logging
from pathlib import Path
from typing import List, Optional, Union

import geopandas as gpd
import numpy as np
import pandas as pd
from census import Census

from config.defaults import DEFAULT_CENSUS_FIELDS, DEFAULT_CENSUS_YEAR
from config.regions import RegionConfig, get_region_config

logger = logging.getLogger(__name__)


def fetch_census_data(
    api_key: str,
    state_fips: Union[str, int],
    fields: Optional[List[str]] = None,
    year: int = DEFAULT_CENSUS_YEAR,
    region_config: Optional[RegionConfig] = None,
) -> pd.DataFrame:
    """Retrieve census data for blocks.
    
    Args:
        api_key: Census API key
        state_fips: State FIPS code (e.g., "23" for Maine)
        fields: List of census field names (default: P1_001N, P1_003N, P2_001N, P2_002N)
        year: Census year (default: 2020)
        region_config: Optional region configuration (currently unused but reserved for future)
        
    Returns:
        DataFrame with census data and GEOID20 column
    """
    if fields is None:
        fields = DEFAULT_CENSUS_FIELDS
    
    # Ensure state_fips is string with leading zero
    state_fips = str(state_fips).zfill(2)
    
    logger.info(f"Fetching census data for state FIPS: {state_fips}")
    logger.info(f"Fields: {fields}")
    
    c = Census(api_key)
    
    # Build field list with GEO_ID
    census_fields = ['GEO_ID'] + fields
    
    me_census = pd.DataFrame.from_records(
        c.pl.state_county_block(
            fields=tuple(census_fields),
            state_fips=state_fips,
            county_fips="*",
            blockgroup="*",
            block="*",
            year=year
        )
    )
    
    # Extract GEOID20 from GEO_ID (format: 1000000US230110205001020)
    me_census["GEOID20"] = me_census["GEO_ID"].apply(lambda s: s[9:])
    
    logger.info(f"Retrieved {len(me_census)} census records")
    return me_census


def process_cejst_data(
    cejst_path: Union[str, Path],
    relationship_file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    region_config: Optional[RegionConfig] = None,
) -> pd.DataFrame:
    """Process CEJST data by mapping from 2010 to 2020 blocks.
    
    Uses Census relationship file to map CEJST tract-level data (2010 geography)
    to 2020 block-level data using area-weighted aggregation.
    
    Args:
        cejst_path: Path to CEJST shapefile (2010 geography)
        relationship_file_path: Path to Census relationship file (tab2010_tab2020_st*_*.txt)
        output_path: Optional path to save processed CEJST data
        region_config: Optional region configuration (currently unused but reserved for future)
        
    Returns:
        DataFrame with CEJST data at block level (2020 geography)
    """
    logger.info("Loading CEJST data")
    if str(cejst_path).endswith('.parquet'):
        cejst = gpd.read_parquet(str(cejst_path))
        # Ensure GEOID10 is string type
        if "GEOID10" in cejst.columns:
            cejst["GEOID10"] = cejst["GEOID10"].astype(str)
    else:
        cejst = gpd.read_file(str(cejst_path), converters={"GEOID10": str})  # Fallback for existing shapefiles
    
    logger.info("Loading relationship file")
    relationships = pd.read_csv(
        str(relationship_file_path),
        delimiter="|",
        converters={
            "STATE_2010": str,
            "COUNTY_2010": str,
            "TRACT_2010": str,
            "BLK_2010": str,
            "BLKSF_2010": str,
            "AREALAND_2010": float,
            "AREAWATER_2010": float,
            "BLOCK_PART_FLAG_O": str,
            "STATE_2020": str,
            "COUNTY_2020": str,
            "TRACT_2020": str,
            "BLK_2020": str,
            "BLKSF_2020": str,
            "AREALAND_2020": float,
            "AREAWATER_2020": float,
            "BLOCK_PART_FLAG_R": str,
            "AREALAND_INT": float,
            "AREAWATER_INT": float,
        }
    )
    
    # Create GEOID columns
    relationships["GEOID10"] = (
        relationships["STATE_2010"] +
        relationships["COUNTY_2010"] +
        relationships["TRACT_2010"]
    )
    relationships["GEOID10_blk"] = (
        relationships["STATE_2010"] +
        relationships["COUNTY_2010"] +
        relationships["TRACT_2010"] +
        relationships["BLK_2010"]
    )
    relationships["GEOID20"] = (
        relationships["STATE_2020"] +
        relationships["COUNTY_2020"] +
        relationships["TRACT_2020"] +
        relationships["BLK_2020"]
    )
    
    logger.info("Merging CEJST with relationship file")
    cejst20 = relationships.merge(cejst, how="left", on="GEOID10")
    
    # Calculate weight based on area intersection
    cejst20["WEIGHT"] = (
        (cejst20["AREALAND_INT"] + cejst20["AREAWATER_INT"]) /
        (cejst20["AREALAND_2020"] + cejst20["AREAWATER_2020"])
    )
    
    logger.info("Aggregating to block level using weighted average")
    
    def w_avg(x):
        """Weighted average function."""
        return int(np.ceil(np.average(x, weights=cejst20.loc[x.index, "WEIGHT"])))
    
    # Aggregate TC and CC columns using weighted average
    cejst_block = cejst20.groupby("GEOID20").agg({
        "TC": w_avg,
        "CC": w_avg
    })
    
    logger.info(f"Processed {len(cejst_block)} blocks")
    
    if output_path:
        logger.info(f"Saving processed CEJST data to {output_path}")
        if str(output_path).endswith('.parquet'):
            cejst_block.to_parquet(output_path)
        else:
            cejst_block.to_csv(output_path)  # Fallback for CSV output
    
    return cejst_block


def calculate_demographics(blocks_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate demographic percentages and percentiles.
    
    Adds columns for:
    - white_per: Percentage white
    - hisp_per: Percentage Hispanic/Latino
    - white_50: Boolean for >50th percentile white
    - hisp_75: Boolean for >75th percentile Hispanic/Latino
    
    Args:
        blocks_df: DataFrame with P1_001N, P1_003N, P2_001N, P2_002N columns
        
    Returns:
        DataFrame with demographic columns added
    """
    blocks_df = blocks_df.copy()
    
    logger.info("Calculating demographic percentages")
    blocks_df["white_per"] = blocks_df["P1_003N"] / blocks_df["P1_001N"]
    blocks_df["hisp_per"] = blocks_df["P2_002N"] / blocks_df["P2_001N"]
    
    logger.info("Calculating demographic percentiles")
    blocks_df["white_50"] = blocks_df["white_per"] > blocks_df["white_per"].describe()["50%"]
    blocks_df["hisp_75"] = blocks_df["hisp_per"] > blocks_df["hisp_per"].describe()["75%"]
    
    return blocks_df


def create_ejblocks(
    blocks_path: Union[str, Path],
    census_api_key: str,
    cejst_path: Union[str, Path],
    relationship_file_path: Union[str, Path],
    output_path: Union[str, Path],
    state_fips: Optional[Union[str, int]] = None,
    region_config: Optional[RegionConfig] = None,
) -> gpd.GeoDataFrame:
    """Create ejblocks dataset with all merged data.
    
    Full workflow: merges blocks with census data, CEJST data, and calculates
    demographics to create the final ejblocks dataset.
    
    Args:
        blocks_path: Path to blocks shapefile (with walk times merged)
        census_api_key: Census API key
        cejst_path: Path to CEJST shapefile (2010 geography)
        relationship_file_path: Path to Census relationship file
        output_path: Path to save final ejblocks shapefile
        state_fips: State FIPS code (required if region_config not provided)
        region_config: Optional region configuration (used to get state_fips if provided)
        
    Returns:
        GeoDataFrame with all merged data
    """
    # Get state FIPS from region_config if provided
    if region_config:
        state_fips = region_config.state_fips
    elif state_fips is None:
        raise ValueError("Either state_fips or region_config must be provided")
    
    state_fips = str(state_fips).zfill(2)
    
    logger.info("Loading blocks data")
    if str(blocks_path).endswith('.parquet'):
        blocks = gpd.read_parquet(str(blocks_path))
    else:
        blocks = gpd.read_file(str(blocks_path))  # Fallback for existing shapefiles
    
    # Add GEOID grouping columns
    blocks["GEOID_grp"] = blocks["GEOID20"].apply(lambda s: s[:-3])
    blocks["GEOID_tract"] = blocks["GEOID20"].apply(lambda s: s[:-4])
    
    # Fetch census data
    logger.info("Fetching census data")
    census_data = fetch_census_data(census_api_key, state_fips)
    
    # Merge census data
    logger.info("Merging census data")
    merge = blocks.merge(census_data, how="left", on="GEOID20")
    
    # Calculate population density
    logger.info("Calculating population density")
    merge["POPDENSE"] = merge["P1_001N"].astype(np.float64) / merge["ALAND20"].astype(np.float64)
    merge["POPDENSE"].replace(np.inf, np.nan, inplace=True)
    
    # Dissolve blocks (aggregate by GEOID20)
    logger.info("Dissolving blocks")
    dissolve = merge.dissolve(by="GEOID20", aggfunc='sum')
    
    # Process CEJST data
    logger.info("Processing CEJST data")
    cejst_block = process_cejst_data(cejst_path, relationship_file_path)
    
    # Merge CEJST data
    logger.info("Merging CEJST data")
    ejblocks = dissolve.merge(cejst_block, on="GEOID20", how="left")
    
    # Calculate demographics
    logger.info("Calculating demographics")
    ejblocks = calculate_demographics(ejblocks)
    
    # Save results
    logger.info(f"Saving ejblocks to {output_path}")
    if str(output_path).endswith('.parquet'):
        ejblocks.to_parquet(str(output_path))
    else:
        ejblocks.to_file(str(output_path))  # Fallback for shapefile output
    
    return ejblocks

