"""Default configuration values for the access analysis project."""

# Walk time analysis defaults
DEFAULT_TRIP_TIMES = [5, 10, 15, 20, 30, 45, 60]  # minutes
DEFAULT_TRAVEL_SPEED = 4.5  # km/hour

# H3 hexagon defaults
DEFAULT_H3_RESOLUTIONS = [5, 6, 7, 8, 9, 10]
DEFAULT_H3_RESOLUTION = 6  # Default for joins and general use
DEFAULT_H3_RESOLUTION_AREA = 8  # Default for area-based relationship files
DEFAULT_H3_RESOLUTION_POPULATION = 8  # Default for population-based relationship files

# Coordinate system
DEFAULT_CRS = "EPSG:3857"  # Web Mercator

# Census API defaults
DEFAULT_CENSUS_FIELDS = ["P1_001N", "P1_003N", "P2_001N", "P2_002N"]
DEFAULT_CENSUS_YEAR = 2020
