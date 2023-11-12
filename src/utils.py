"""Utility functions for the project."""

# define a list of dictionaries containing the names and abbreviations of the states in New England
STATES = [
    {"name": "Connecticut", "abbrev": "CT", "FIPS": "09"},
    {"name": "Maine", "abbrev": "ME", "FIPS": "23"},
    {"name": "Massachusetts", "abbrev": "MA", "FIPS": "25"},
    {"name": "New Hampshire", "abbrev": "NH", "FIPS": "33"},
    {"name": "Rhode Island", "abbrev": "RI", "FIPS": "44"},
    {"name": "Vermont", "abbrev": "VT", "FIPS": "50"},
]


def setup_osmnx():
    """Set default settings for OSMNx specific to this project."""
    import osmnx as ox

    ox.settings.cache_folder = ".cache"
    ox.settings.log_filename = "osmnx"
    ox.settings.log_file = True
