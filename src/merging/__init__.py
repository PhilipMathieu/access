"""Data merging module for blocks and analysis."""

from .blocks import merge_walk_times, create_trip_time_columns, dissolve_blocks
from .analysis import (
    fetch_census_data,
    process_cejst_data,
    calculate_demographics,
    create_ejblocks,
)

__all__ = [
    "merge_walk_times",
    "create_trip_time_columns",
    "dissolve_blocks",
    "fetch_census_data",
    "process_cejst_data",
    "calculate_demographics",
    "create_ejblocks",
]

