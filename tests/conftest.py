"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import Mock

import geopandas as gpd
import networkx as nx
import pandas as pd
import pytest
from shapely.geometry import Point

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_graph():
    """Create a simple NetworkX graph for testing."""
    G = nx.MultiDiGraph()

    # Add nodes with coordinates
    nodes = [
        (1, {"x": 0, "y": 0}),
        (2, {"x": 100, "y": 0}),
        (3, {"x": 200, "y": 0}),
        (4, {"x": 100, "y": 100}),
    ]
    G.add_nodes_from(nodes)

    # Add edges with length and time attributes
    edges = [
        (1, 2, {"length": 100.0, "time": 1.0}),  # 100m, 1 minute
        (2, 3, {"length": 100.0, "time": 1.0}),
        (2, 4, {"length": 141.4, "time": 1.4}),  # ~100m diagonal
        (4, 3, {"length": 141.4, "time": 1.4}),
    ]
    G.add_edges_from(edges)

    return G


@pytest.fixture
def sample_rustworkx_graph(sample_graph):
    """Create a rustworkx graph from sample NetworkX graph."""
    from walk_times.graph_utils import nx_to_rustworkx

    rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id = nx_to_rustworkx(sample_graph, weight_attr="time")
    return rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id


@pytest.fixture
def sample_blocks_gdf():
    """Create a sample GeoDataFrame for blocks."""
    data = {
        "GEOID20": ["230010001001", "230010001002", "230010001003"],
        "osmid": [1, 2, 3],
        "ALAND20": [1000000, 2000000, 1500000],
    }
    geometries = [
        Point(0, 0),
        Point(100, 0),
        Point(200, 0),
    ]
    gdf = gpd.GeoDataFrame(data, geometry=geometries, crs="EPSG:3857")
    return gdf


@pytest.fixture
def sample_conserved_lands_gdf():
    """Create a sample GeoDataFrame for conserved lands."""
    data = {
        "osmid": [3, 4],
        "CALC_AC": [10.5, 25.3],
        "name": ["Park A", "Park B"],
    }
    geometries = [
        Point(200, 0),
        Point(100, 100),
    ]
    gdf = gpd.GeoDataFrame(data, geometry=geometries, crs="EPSG:3857")
    return gdf


@pytest.fixture
def sample_walk_times_df():
    """Create a sample walk times DataFrame."""
    data = {
        "block_osmid": [1, 1, 2, 2],
        "land_osmid": [3, 4, 3, 4],
        "trip_time": [5, 10, 15, 20],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_merged_blocks_gdf(sample_blocks_gdf, sample_walk_times_df):
    """Create a sample merged blocks GeoDataFrame."""
    # Merge walk times with blocks
    merged = sample_blocks_gdf.merge(
        sample_walk_times_df, left_on="osmid", right_on="block_osmid", how="left"
    )
    return merged


@pytest.fixture
def sample_census_data():
    """Create sample census data."""
    data = {
        "GEO_ID": [
            "1000000US230010001001",
            "1000000US230010001002",
            "1000000US230010001003",
        ],
        "GEOID20": ["230010001001", "230010001002", "230010001003"],
        "P1_001N": [100, 200, 150],  # Total population
        "P1_003N": [80, 150, 120],  # White population
        "P2_001N": [100, 200, 150],  # Hispanic or Latino (total)
        "P2_002N": [5, 10, 8],  # Hispanic or Latino (yes)
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_cejst_data():
    """Create sample CEJST data."""
    data = {
        "GEOID10": ["23001000100", "23001000200"],
        "TC": [1, 0],  # Tract is disadvantaged
        "CC": [1, 0],  # Community is disadvantaged
    }
    geometries = [
        Point(0, 0).buffer(1000),
        Point(1000, 0).buffer(1000),
    ]
    gdf = gpd.GeoDataFrame(data, geometry=geometries, crs="EPSG:3857")
    return gdf


@pytest.fixture
def sample_relationship_file():
    """Create sample Census relationship file data."""
    data = {
        "STATE_2010": ["23", "23"],
        "COUNTY_2010": ["001", "001"],
        "TRACT_2010": ["000100", "000100"],
        "BLK_2010": ["0001", "0002"],
        "BLKSF_2010": ["0", "0"],
        "AREALAND_2010": [1000000.0, 2000000.0],
        "AREAWATER_2010": [0.0, 0.0],
        "BLOCK_PART_FLAG_O": ["00", "00"],
        "STATE_2020": ["23", "23"],
        "COUNTY_2020": ["001", "001"],
        "TRACT_2020": ["000100", "000100"],
        "BLK_2020": ["0001", "0002"],
        "BLKSF_2020": ["0", "0"],
        "AREALAND_2020": [1000000.0, 2000000.0],
        "AREAWATER_2020": [0.0, 0.0],
        "BLOCK_PART_FLAG_R": ["00", "00"],
        "AREALAND_INT": [1000000.0, 2000000.0],
        "AREAWATER_INT": [0.0, 0.0],
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_census_api():
    """Mock Census API."""
    mock_census = Mock()
    # Use get method instead of state_county_block (which doesn't exist)
    mock_census.pl.get.return_value = [
        {
            "GEO_ID": "1000000US230010001001",
            "P1_001N": 100,
            "P1_003N": 80,
            "P2_001N": 100,
            "P2_002N": 5,
        },
        {
            "GEO_ID": "1000000US230010001002",
            "P1_001N": 200,
            "P1_003N": 150,
            "P2_001N": 200,
            "P2_002N": 10,
        },
    ]
    return mock_census


@pytest.fixture
def region_config_maine():
    """Create a RegionConfig for Maine."""
    from pathlib import Path

    from config.regions import RegionConfig

    return RegionConfig(
        state_fips="23",
        state_abbrev="ME",
        state_name="Maine",
        data_root=Path("data"),
    )
