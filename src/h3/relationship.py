"""H3 relationship file generation."""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
from tqdm import tqdm

# Import h3 library directly (local h3 package is not installed as top-level)
import h3 as h3_lib
from config.defaults import (
    DEFAULT_CRS,
    DEFAULT_H3_RESOLUTION_AREA,
    DEFAULT_H3_RESOLUTION_POPULATION,
)
from config.regions import RegionConfig

tqdm.pandas()

logger = logging.getLogger(__name__)


def get_boundary_tiles(row, resolution: int) -> list:
    """Get H3 tiles from polygon boundary coordinates.

    Args:
        row: GeoDataFrame row with geometry
        resolution: H3 resolution level

    Returns:
        List of H3 tile IDs
    """
    try:
        coords = list(row["geometry"].exterior.coords)
    except AttributeError:
        coords = [coord for poly in row["geometry"].geoms for coord in list(poly.exterior.coords)]
    h3ids = [h3_lib.geo_to_h3(lat, lng, resolution) for lng, lat in coords]
    return list(set(h3ids))


def calculate_h3_fractions(
    blocks_gdf: gpd.GeoDataFrame,
    resolution: int,
    method: str = "area",
) -> pd.DataFrame:
    """Calculate H3 fractions for blocks.

    Args:
        blocks_gdf: GeoDataFrame with blocks and geometry
        resolution: H3 resolution level
        method: "area" or "population" (default: "area")

    Returns:
        DataFrame with GEOID20, h3id, and fraction columns
    """
    logger.info(f"Calculating H3 fractions using {method} method at resolution {resolution}")

    # Polyfill blocks
    logger.info("Polyfilling blocks")
    blocks = blocks_gdf[["GEOID20", "geometry"]].h3.polyfill(resolution)

    # Add boundary tiles
    logger.info("Adding boundary tiles")
    blocks["h3_boundary"] = blocks.progress_apply(
        lambda row: get_boundary_tiles(row, resolution), axis=1
    )
    blocks["h3ids"] = (blocks["h3_polyfill"] + blocks["h3_boundary"]).apply(set).apply(list)

    # Calculate fractions
    if method == "area":
        logger.info("Calculating area fractions")
        blocks = blocks.to_crs(DEFAULT_CRS)

        def calculate_area_fraction(row):
            h3ids = pd.DataFrame.from_records(
                [{"fraction": 0, "h3id": tile} for tile in row["h3ids"]], index="h3id"
            )
            h3ids = h3ids.h3.h3_to_geo_boundary().to_crs(DEFAULT_CRS)
            h3ids["fraction"] = (
                h3ids["geometry"].intersection(row["geometry"]).area / row["geometry"].area
            )
            return list(zip(h3ids.index.values, h3ids["fraction"], strict=False))

        blocks["h3_fraction"] = blocks.progress_apply(calculate_area_fraction, axis=1)

    elif method == "population":
        logger.info("Calculating population fractions")
        blocks = blocks.to_crs(DEFAULT_CRS)

        def calculate_population_fraction(row):
            population = row["P1_001N"]
            h3ids = pd.DataFrame(
                {"POPULATION": [population for tile in row["h3ids"]]}, index=row["h3ids"]
            )
            h3ids = h3ids.h3.h3_to_geo_boundary().to_crs(DEFAULT_CRS)
            fraction = h3ids["geometry"].intersection(row["geometry"]).area / row["geometry"].area
            h3ids["POPULATION"] = population * fraction
            return [
                {tile["index"]: tile["POPULATION"]}
                for tile in h3ids[["POPULATION"]].reset_index().to_dict("records")
            ]

        blocks["h3_population"] = blocks.progress_apply(calculate_population_fraction, axis=1)
        blocks = blocks.explode("h3_population")
        blocks["h3id"] = blocks["h3_population"].apply(lambda x: list(x.keys())[0])
        blocks["population_fraction"] = blocks["h3_population"].apply(lambda x: list(x.values())[0])

        # Group by h3id and sum population fractions
        result = blocks.groupby("h3id", as_index=False).sum(numeric_only=True)
        result = result[["h3id", "population_fraction"]].rename(
            columns={"population_fraction": "h3_fraction"}
        )
        return result

    # Explode for area method
    blocks_explode = blocks[["GEOID20", "h3_fraction"]].explode("h3_fraction")
    blocks_explode["h3id"] = blocks_explode["h3_fraction"].apply(lambda x: x[0])
    blocks_explode["h3_fraction"] = blocks_explode["h3_fraction"].apply(lambda x: x[1])

    return blocks_explode[["GEOID20", "h3id", "h3_fraction"]]


def generate_h3_relationship_area(
    blocks_path: str | Path,
    output_path: str | Path,
    resolution: int = DEFAULT_H3_RESOLUTION_AREA,
    region_config: RegionConfig | None = None,  # noqa: ARG001
) -> pd.DataFrame:
    """Generate H3 relationship file using area fractions.

    Args:
        blocks_path: Path to blocks shapefile
        output_path: Path to save relationship CSV file
        resolution: H3 resolution level (default: 8)
        region_config: Optional region configuration (currently unused but reserved for future)

    Returns:
        DataFrame with relationship data
    """
    logger.info(f"Generating H3 relationship file (area method) at resolution {resolution}")

    if str(blocks_path).endswith(".parquet"):
        blocks_raw = gpd.read_parquet(str(blocks_path))
    else:
        blocks_raw = gpd.read_file(str(blocks_path))  # Fallback for existing shapefiles
    result = calculate_h3_fractions(blocks_raw, resolution, method="area")

    logger.info(f"Saving relationship file to {output_path}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if str(output_path).endswith(".parquet"):
        result.to_parquet(output_path, index=False)
    else:
        result.to_csv(output_path, index=False)  # Fallback for CSV output

    return result


def generate_h3_relationship_population(
    blocks_path: str | Path,
    output_path: str | Path,
    resolution: int = DEFAULT_H3_RESOLUTION_POPULATION,
    census_api_key: str | None = None,
    region_config: RegionConfig | None = None,
) -> pd.DataFrame:
    """Generate H3 relationship file using population-weighted fractions.

    Args:
        blocks_path: Path to blocks shapefile
        output_path: Path to save relationship CSV file
        resolution: H3 resolution level (default: 8)
        census_api_key: Census API key (required if blocks don't have P1_001N)
        region_config: Optional region configuration (used to get state_fips if needed)

    Returns:
        DataFrame with relationship data
    """
    logger.info(f"Generating H3 relationship file (population method) at resolution {resolution}")

    if str(blocks_path).endswith(".parquet"):
        blocks_raw = gpd.read_parquet(str(blocks_path))
    else:
        blocks_raw = gpd.read_file(str(blocks_path))  # Fallback for existing shapefiles

    # Check if population data exists
    if "P1_001N" not in blocks_raw.columns:
        if not census_api_key:
            raise ValueError("census_api_key required if blocks don't have P1_001N column")

        # Get state FIPS from region_config or extract from GEOID20
        if region_config:
            state_fips = region_config.state_fips
        else:
            # Extract state FIPS from first GEOID20
            state_fips = blocks_raw["GEOID20"].iloc[0][:2]

        logger.info(f"Fetching census population data for state FIPS: {state_fips}")
        from merging.analysis import fetch_census_data

        census_data = fetch_census_data(census_api_key, state_fips)
        blocks_raw = blocks_raw.merge(
            census_data, left_on="GEOID20", right_on="GEOID20", how="left"
        )

    result = calculate_h3_fractions(blocks_raw, resolution, method="population")

    logger.info(f"Saving relationship file to {output_path}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if str(output_path).endswith(".parquet"):
        result.to_parquet(output_path, index=False)
    else:
        result.to_csv(output_path, index=False)  # Fallback for CSV output

    return result
