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
    # Need to match std values to patches in the same order as bars are drawn
    # Seaborn barplot with hue orders patches as: [var1_group1, var1_group2, var2_group1, var2_group2, ...]
    # So we need to sort percents to match this order
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    
    # Sort percents to match the order seaborn creates patches
    # First by variable, then by groupby_col (to match seaborn's hue ordering)
    percents_sorted = percents.sort_values(by=["variable", groupby_col])
    std_values = percents_sorted["std"].values
    
    # Ensure we have the right number of std values
    if len(std_values) != len(ax.patches):
        # Fallback: create a mapping and extract in patch order
        std_dict = dict(zip(zip(percents[groupby_col], percents["variable"]), percents["std"]))
        std_values = []
        for patch in ax.patches:
            # Get the x position to determine which variable
            x_pos = patch.get_x() + patch.get_width() / 2
            # Find which variable this corresponds to
            var_name = None
            for i, tick in enumerate(ax.get_xticks()):
                if abs(x_pos - tick) < 0.1:  # Close enough to the tick
                    var_name = percents["variable"].unique()[i]
                    break
            
            # Get the hue value from the patch color or position
            # For seaborn barplot with hue, patches alternate by hue within each x position
            patch_idx = ax.patches.index(patch)
            n_groups = len(percents[groupby_col].unique())
            group_idx = patch_idx % n_groups
            group_val = percents[groupby_col].unique()[group_idx]
            
            if var_name:
                std_values.append(std_dict.get((group_val, var_name), 0))
            else:
                std_values.append(0)
    
    ax.errorbar(x=x_coords, y=y_coords, yerr=std_values, fmt="none", c="k")
    
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
    
    # Check which columns are available
    required_cols = ["geometry", disadvantage_col] + cols_bools
    available_cols = [col for col in required_cols if col in data.columns]
    missing_cols = [col for col in required_cols if col not in data.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Use GEOID20 if available, otherwise use index
    id_vars = ["geometry", disadvantage_col]
    if "GEOID20" in data.columns:
        id_vars.insert(0, "GEOID20")
    else:
        # Create a temporary index column if GEOID20 is missing
        data = data.copy()
        data["_index"] = data.index
        id_vars.insert(0, "_index")
    
    # Filter to rows with valid area
    if "ALAND20" in data.columns:
        data_filtered = data[data["ALAND20"] > 0]
    else:
        data_filtered = data
    
    # Create melted dataframe with nearest walk time
    melt = data_filtered.melt(
        id_vars=id_vars,
        value_vars=cols_bools
    )
    melt["nearest"] = np.where(
        melt["value"],
        melt["variable"].apply(lambda s: int(s.split("_")[1])),
        60  # Max walk time if not accessible
    )
    # Group by the ID column (GEOID20 or _index)
    groupby_col = id_vars[0]  # First id_var is the grouping column
    
    melt = gpd.GeoDataFrame(
        melt.groupby(groupby_col).agg({
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
    from analysis.statistical import create_boolean_columns
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

