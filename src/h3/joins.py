"""H3 joins and plotting utilities."""

import logging
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import pandas as pd

from config.defaults import DEFAULT_H3_RESOLUTION
from config.regions import RegionConfig

logger = logging.getLogger(__name__)


def h3_join(
    data_path: Union[str, Path],
    relationship_path: Optional[Union[str, Path]] = None,
    resolution: int = DEFAULT_H3_RESOLUTION,
    region_config: Optional[RegionConfig] = None,
) -> pd.DataFrame:
    """Join data with H3 relationship file.
    
    Args:
        data_path: Path to data shapefile or CSV
        relationship_path: Path to H3 relationship CSV file
        resolution: H3 resolution (used to construct default path if relationship_path not provided)
        region_config: Optional region configuration (used to construct default path)
        
    Returns:
        DataFrame with H3 joins
    """
    logger.info(f"Loading data from {data_path}")
    
    # Load data
    if str(data_path).endswith('.parquet'):
        df = gpd.read_parquet(str(data_path))
    elif str(data_path).endswith('.shp') or str(data_path).endswith('.zip'):
        df = gpd.read_file(str(data_path))  # Fallback for existing shapefiles
    else:
        df = pd.read_csv(str(data_path))
    
    # Load relationship file
    if relationship_path is None:
        if region_config:
            # Construct default path
            reln_file = region_config.data_root / "blocks" / f"tl_2020_{region_config.state_fips}_tabblock20_h3_{resolution}.csv"
        else:
            raise ValueError("Either relationship_path or region_config must be provided")
    else:
        reln_file = Path(relationship_path)
    
    logger.info(f"Loading relationship file from {reln_file}")
    if str(reln_file).endswith('.parquet'):
        reln = pd.read_parquet(str(reln_file))
        # Ensure correct types
        if 'GEOID20' in reln.columns:
            reln['GEOID20'] = reln['GEOID20'].astype(str)
        if 'h3id' in reln.columns:
            reln['h3id'] = reln['h3id'].astype(str)
        if 'h3_fraction' in reln.columns:
            reln['h3_fraction'] = reln['h3_fraction'].astype(float)
    else:
        reln = pd.read_csv(
            str(reln_file),
            converters={
                'GEOID20': str,
                'h3_fraction': float,
                'h3id': str
            }
        )  # Fallback for CSV input
    
    # Merge
    logger.info("Merging data with H3 relationship file")
    result = reln.merge(df, 'left', 'GEOID20').set_index(['GEOID20', 'h3id'])
    
    return result


def plot_h3_data(
    data: Union[pd.DataFrame, gpd.GeoDataFrame],
    column: str,
    output_path: Optional[Union[str, Path]] = None,
    lognorm: bool = True,
    **kwargs
):
    """Plot H3 hexagon data.
    
    Args:
        data: DataFrame with H3 data (must have h3id index or column)
        column: Column name to plot
        output_path: Optional path to save figure
        lognorm: Whether to use log normalization (default: True)
        **kwargs: Additional arguments passed to plot
        
    Returns:
        Matplotlib axes object
    """
    import matplotlib
    
    logger.info(f"Plotting H3 data for column: {column}")
    
    # Ensure h3id is in index
    if 'h3id' not in data.index.names and 'h3id' in data.columns:
        data = data.set_index('h3id', append=True)
    
    # Filter to H3 columns and group by h3id
    h3_cols = [col for col in data.columns if col.startswith('h3_')]
    if not h3_cols:
        raise ValueError("No H3-weighted columns found. Use h3_weight() or h3_weight_pop() first.")
    
    hexes = data.filter(regex='^h3_', axis=1).groupby('h3id').sum()
    
    # Convert to GeoDataFrame
    hexes_gdf = hexes.h3.h3_to_geo_boundary()
    
    # Plot
    norm = matplotlib.colors.LogNorm(vmin=1, vmax=hexes[[column]].max()) if lognorm else None
    ax = hexes_gdf.plot(column, norm=norm, label=column, **kwargs)
    
    if output_path:
        logger.info(f"Saving plot to {output_path}")
        import matplotlib.pyplot as plt
        plt.savefig(str(output_path))
    
    return ax

