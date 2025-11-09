"""Figure generation for publication."""

import logging
from pathlib import Path
from typing import List, Optional, Union

import contextily as cx
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import font_manager

logger = logging.getLogger(__name__)


def setup_fonts(font_path: Optional[Union[str, Path]] = None) -> None:
    """Configure matplotlib fonts to match website.
    
    Args:
        font_path: Optional path to font file (default: tries to find Lato)
    """
    if font_path:
        logger.info(f"Loading font from {font_path}")
        font_manager.fontManager.addfont(str(font_path))
        prop = font_manager.FontProperties(fname=str(font_path))
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = prop.get_name()
    else:
        # Try common Lato font paths
        common_paths = [
            '/usr/share/fonts/truetype/lato/Lato-Regular.ttf',
            '/System/Library/Fonts/Supplemental/Lato-Regular.ttf',
            'C:/Windows/Fonts/lato-regular.ttf',
        ]
        for path in common_paths:
            if Path(path).exists():
                logger.info(f"Found Lato font at {path}")
                font_manager.fontManager.addfont(path)
                prop = font_manager.FontProperties(fname=path)
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['font.sans-serif'] = prop.get_name()
                return
        logger.warning("Lato font not found, using default sans-serif")


def plot_access_by_group(
    data: pd.DataFrame,
    groupby_col: str,
    trip_time_cols: List[str],
    output_path: Optional[Union[str, Path]] = None,
    reverse_colors: bool = False,
    dpi: int = 100,
    title: Optional[str] = None,
    legend_title: Optional[str] = None,
    **kwargs
) -> tuple:
    """Generate bar plot showing access by group.
    
    Creates a bar plot showing percentage of population with access to
    conserved lands at different walk time thresholds, grouped by a variable.
    
    Args:
        data: DataFrame with population and trip time columns
        groupby_col: Column to group by (e.g., "TC_bool")
        trip_time_cols: List of trip time column names (e.g., ["AC_5", "AC_10", ...])
        output_path: Optional path to save figure
        reverse_colors: If True, reverse color palette
        dpi: Resolution for saved figure (default: 100)
        title: Optional custom title
        legend_title: Optional custom legend title
        **kwargs: Additional arguments passed to seaborn barplot
        
    Returns:
        Tuple of (figure, axes) objects
    """
    # Set up color palette
    if reverse_colors:
        palette = {False: "crimson", True: "green"}
    else:
        palette = {True: "crimson", False: "green"}
    
    # Calculate population-weighted percentages
    cols_pops = [col + "_pop" for col in trip_time_cols]
    g = data.groupby([groupby_col])[["P1_001N"] + cols_pops]
    p = g.sum()[cols_pops].divide(g.sum()["P1_001N"], axis='index')
    percents = (p * 100).melt(ignore_index=False, value_name="mean").reset_index()
    percents_std = np.sqrt(p * (1 - p) * 100).melt(ignore_index=False, value_name="std").reset_index()
    percents = pd.concat([percents, percents_std["std"]], axis=1)
    
    # Create plot
    fig, ax = plt.subplots(dpi=dpi)
    ax = sns.barplot(
        percents,
        x="variable",
        y="mean",
        hue=groupby_col,
        errorbar=None,
        palette=palette,
        ax=ax,
        **kwargs
    )
    ax.set_ylim(0, 100)
    
    if title:
        ax.set_title(title)
    else:
        ax.set_title("Percent of Population with Conserved Land within Walk Times")
    
    ax.set_ylabel("% of Population")
    ax.set_xlabel("Conservation Land within $x$-Minute Walk")
    
    if legend_title:
        ax.legend(title=legend_title)
    else:
        ax.legend(title='"Disadvantaged"')
    
    # Add manual error bars
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(x=x_coords, y=y_coords, yerr=percents["std"].values, fmt="none", c="k")
    
    # Use just the numeric component of the x variables
    ax.set_xticklabels([label.get_text().split("_")[1] for label in ax.get_xticklabels()])
    
    # Adjust widths to reflect proportion of overall population
    widths = 0.5 * np.tile(
        np.sqrt(g.sum()["P1_001N"] / g.sum()["P1_001N"].sum()).to_numpy().reshape(-1, 1),
        p.shape[1]
    )
    for bar, newwidth in zip(ax.patches, widths.ravel()):
        x = bar.get_x()
        width = bar.get_width()
        center = x + width / 2.
        bar.set_x(center - newwidth / 2.)
        bar.set_width(newwidth)
    
    if output_path:
        logger.info(f"Saving figure to {output_path}")
        fig.savefig(str(output_path))
    
    return fig, ax


def plot_nearest_lands(
    data: gpd.GeoDataFrame,
    trip_time_cols: List[str],
    output_path: Optional[Union[str, Path]] = None,
    disadvantage_col: str = "TC_bool",
    counties_url: Optional[str] = None,
    figsize: tuple = (10, 10),
    dpi: int = 100,
    **kwargs
) -> tuple:
    """Generate map showing walk time to nearest conserved land.
    
    Creates a map visualization showing the minimum walk time to reach
    conserved lands, with disadvantaged communities highlighted.
    
    Args:
        data: GeoDataFrame with trip time boolean columns and geometry
        trip_time_cols: List of trip time column names (e.g., ["AC_5", "AC_10", ...])
        output_path: Optional path to save figure
        disadvantage_col: Column name for disadvantage indicator (default: "TC_bool")
        counties_url: Optional URL to load county boundaries
        figsize: Figure size tuple (default: (10, 10))
        dpi: Resolution for saved figure (default: 100)
        **kwargs: Additional arguments passed to plot
        
    Returns:
        Tuple of (figure, axes) objects
    """
    cols_bools = [col + "_bool" for col in trip_time_cols]
    
    # Create melted dataframe with nearest walk time
    melt = data[data["ALAND20"] > 0].melt(
        id_vars=["GEOID20", "geometry", disadvantage_col],
        value_vars=cols_bools
    )
    melt["nearest"] = np.where(
        melt["value"],
        melt["variable"].apply(lambda s: int(s.split("_")[1])),
        60  # Max walk time if not accessible
    )
    melt = gpd.GeoDataFrame(
        melt.groupby("GEOID20").agg({
            "geometry": "first",
            "nearest": "min",
            disadvantage_col: "max"
        })
    ).set_crs("EPSG:3857")
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    melt.plot("nearest", ax=ax, cmap="Greens_r", legend=True, alpha=0.5, **kwargs)
    
    # Highlight disadvantaged communities
    melt[melt[disadvantage_col]].plot(
        ax=ax,
        facecolor='none',
        edgecolor="crimson",
        hatch="//",
        linewidth=0
    )
    
    # Add basemap
    try:
        cx.add_basemap(ax, source=cx.providers.Stamen.TonerLite)
        cx.add_basemap(ax, source=cx.providers.Stamen.TonerLabels)
    except Exception as e:
        logger.warning(f"Could not add basemap: {e}")
    
    # Add county boundaries if URL provided
    if counties_url:
        try:
            counties = gpd.read_file(counties_url)
            counties.plot(ax=ax, facecolor="none", edgecolor='k', lw=0.125)
        except Exception as e:
            logger.warning(f"Could not load county boundaries: {e}")
    
    ax.axis("off")
    ax.set_title("Walk Time to Nearest Conserved Land")
    
    if output_path:
        logger.info(f"Saving figure to {output_path}")
        fig.savefig(str(output_path))
        fig.clf()  # Clear figure so it's not saved in notebook
    
    return fig, ax


def generate_all_figures(
    ejblocks_path: Union[str, Path],
    output_dir: Union[str, Path] = "../figs/",
    trip_time_cols: Optional[List[str]] = None,
    font_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> None:
    """Generate all publication figures.
    
    Args:
        ejblocks_path: Path to ejblocks shapefile
        output_dir: Directory to save figures (default: "../figs/")
        trip_time_cols: Optional list of trip time columns (default: AC_5 through AC_60)
        font_path: Optional path to font file
        **kwargs: Additional arguments passed to figure functions
    """
    if trip_time_cols is None:
        trip_time_cols = ["AC_5", "AC_10", "AC_15", "AC_20", "AC_30", "AC_45", "AC_60"]
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Setting up fonts")
    setup_fonts(font_path)
    
    logger.info("Loading ejblocks data")
    if str(ejblocks_path).endswith('.parquet'):
        ejblocks = gpd.read_parquet(str(ejblocks_path))
    else:
        ejblocks = gpd.read_file(str(ejblocks_path))  # Fallback for existing shapefiles
    
    # Create boolean columns if they don't exist
    from ..analysis.statistical import create_boolean_columns
    if "AC_5_bool" not in ejblocks.columns:
        logger.info("Creating boolean columns")
        ejblocks = create_boolean_columns(ejblocks, trip_time_cols)
    
    # Generate bar plot
    logger.info("Generating access by group bar plot")
    fig, ax = plot_access_by_group(
        ejblocks,
        "TC_bool",
        trip_time_cols,
        output_path=output_dir / "disadvantaged_barplot.png",
        dpi=400,
        title="Maine's \"Disadvantaged\" Population is Less Likely\nto Have Access to Conservation Lands",
        legend_title='"Disadvantaged"',
    )
    plt.close(fig)
    
    # Generate nearest lands map
    logger.info("Generating nearest lands map")
    fig, ax = plot_nearest_lands(
        ejblocks,
        trip_time_cols,
        output_path=output_dir / "minimum_walk_time.png",
        figsize=(4, 4),
        dpi=300,
    )
    plt.close(fig)
    
    logger.info(f"All figures saved to {output_dir}")

