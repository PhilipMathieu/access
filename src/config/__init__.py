"""Configuration module for region and default settings."""

from .defaults import (
    DEFAULT_CENSUS_FIELDS,
    DEFAULT_CRS,
    DEFAULT_H3_RESOLUTION,
    DEFAULT_H3_RESOLUTION_AREA,
    DEFAULT_H3_RESOLUTIONS,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_TRIP_TIMES,
)
from .regions import NEW_ENGLAND_STATES, RegionConfig, get_multi_state_config, get_region_config

__all__ = [
    "RegionConfig",
    "get_region_config",
    "get_multi_state_config",
    "NEW_ENGLAND_STATES",
    "DEFAULT_TRIP_TIMES",
    "DEFAULT_TRAVEL_SPEED",
    "DEFAULT_H3_RESOLUTIONS",
    "DEFAULT_H3_RESOLUTION",
    "DEFAULT_H3_RESOLUTION_AREA",
    "DEFAULT_CRS",
    "DEFAULT_CENSUS_FIELDS",
]
