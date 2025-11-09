"""Statistical analysis functions for access disparities."""

import logging
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.multivariate.manova import MANOVA

logger = logging.getLogger(__name__)


def create_boolean_columns(
    df: pd.DataFrame,
    trip_time_cols: List[str],
    cumulative: bool = True,
    disadvantage_col: str = "TC",
) -> pd.DataFrame:
    """Create boolean columns for trip times and population metrics.
    
    Creates boolean columns indicating access (e.g., AC_10_bool) and
    population-weighted columns (e.g., AC_10_pop).
    
    Args:
        df: DataFrame with trip time columns (AC_5, AC_10, etc.) and population
        trip_time_cols: List of trip time column names (e.g., ["AC_5", "AC_10", ...])
        cumulative: If True, cumulative access (True if accessible at any lower threshold)
        disadvantage_col: Column name for disadvantage indicator (default: "TC")
        
    Returns:
        DataFrame with boolean and population columns added
    """
    df = df.copy()
    
    cols_bools = [col + "_bool" for col in trip_time_cols]
    cols_pops = [col + "_pop" for col in trip_time_cols]
    
    # Create disadvantage boolean
    df[f"{disadvantage_col}_bool"] = df[disadvantage_col] > 0
    
    logger.info(f"Creating boolean columns for {len(trip_time_cols)} trip times")
    
    for i, col in enumerate(trip_time_cols):
        if i == 0:
            # First trip time: just check if > 0
            df[cols_bools[i]] = df[col] > 0
        else:
            if cumulative:
                # Cumulative: accessible at this threshold OR any lower threshold
                df[cols_bools[i]] = (df[col] > 0) | df[cols_bools[i-1]]
            else:
                # Non-cumulative: only accessible at this threshold
                df[cols_bools[i]] = df[col] > 0
        
        # Population-weighted column: population if accessible, 0 otherwise
        df[cols_pops[i]] = np.where(df[cols_bools[i]], df["P1_001N"], 0)
    
    return df


def run_manova(
    data: pd.DataFrame,
    dependent_vars: List[str],
    independent_var: str,
    formula: Optional[str] = None,
) -> MANOVA:
    """Run Multivariate Analysis of Variance (MANOVA).
    
    Args:
        data: DataFrame with dependent and independent variables
        dependent_vars: List of dependent variable column names
        independent_var: Independent variable column name
        formula: Optional formula string (if None, constructs from dependent_vars and independent_var)
        
    Returns:
        MANOVA model fit object
    """
    if formula is None:
        dep_str = " + ".join(dependent_vars)
        formula = f"{dep_str} ~ {independent_var}"
    
    logger.info(f"Running MANOVA with formula: {formula}")
    fit = MANOVA.from_formula(formula, data=data)
    
    return fit


def analyze_access_disparity(
    data: pd.DataFrame,
    access_col: str,
    disadvantage_col: str = "TC_bool",
    population_col: str = "P1_001N",
    invert_access: bool = True,
) -> Tuple[pd.DataFrame, sm.stats.Table2x2]:
    """Analyze access disparity using 2x2 contingency table.
    
    Creates a contingency table comparing disadvantaged vs non-disadvantaged
    communities and their access to conserved lands.
    
    Args:
        data: DataFrame with access and disadvantage columns
        access_col: Column name for access boolean (e.g., "AC_10_bool")
        disadvantage_col: Column name for disadvantage boolean (default: "TC_bool")
        population_col: Column name for population (default: "P1_001N")
        invert_access: If True, analyze lack of access (default: True)
        
    Returns:
        Tuple of (contingency table DataFrame, Table2x2 stats object)
    """
    logger.info(f"Analyzing access disparity: {access_col} vs {disadvantage_col}")
    
    # Create access variable (invert if needed)
    if invert_access:
        access_var = ~data[access_col]
    else:
        access_var = data[access_col]
    
    # Create contingency table weighted by population
    tab = pd.crosstab(
        data[disadvantage_col],
        access_var,
        data[population_col],
        aggfunc='sum'
    )
    
    # Create Table2x2 object for statistical tests
    table = sm.stats.Table2x2(tab)
    
    logger.info(f"Total population: {int(np.sum(tab.values))}")
    
    return tab, table


def calculate_population_metrics(
    data: pd.DataFrame,
    trip_time_cols: List[str],
    population_col: str = "P1_001N",
    groupby_col: Optional[str] = None,
) -> pd.DataFrame:
    """Calculate population-weighted metrics for trip times.
    
    Calculates percentage of population with access at each trip time threshold,
    optionally grouped by another variable.
    
    Args:
        data: DataFrame with trip time boolean columns and population
        trip_time_cols: List of trip time column names (e.g., ["AC_5", "AC_10", ...])
        population_col: Column name for population (default: "P1_001N")
        groupby_col: Optional column to group by (e.g., "TC_bool")
        
    Returns:
        DataFrame with percentage metrics
    """
    cols_pops = [col + "_pop" for col in trip_time_cols]
    
    if groupby_col:
        logger.info(f"Calculating population metrics grouped by {groupby_col}")
        g = data.groupby([groupby_col])[[population_col] + cols_pops]
    else:
        logger.info("Calculating overall population metrics")
        g = data.groupby(lambda x: True)[[population_col] + cols_pops]
    
    # Calculate percentages
    p = g.sum()[cols_pops].divide(g.sum()[population_col], axis='index')
    percents = (p * 100).melt(ignore_index=False, value_name="mean").reset_index()
    
    # Calculate standard deviations
    percents_std = np.sqrt(p * (1 - p) * 100).melt(ignore_index=False, value_name="std").reset_index()
    percents = pd.concat([percents, percents_std["std"]], axis=1)
    
    return percents

