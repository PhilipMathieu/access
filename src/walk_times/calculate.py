"""Calculate walk times from geographic units to conserved lands."""

import logging
from pathlib import Path
from typing import List, Optional, Union

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
from tqdm import tqdm

from config.defaults import DEFAULT_CRS, DEFAULT_TRAVEL_SPEED, DEFAULT_TRIP_TIMES
from config.regions import RegionConfig

logger = logging.getLogger(__name__)


def load_graph(
    graph_path: Union[str, Path],
    cache_folder: Optional[Union[str, Path]] = None,
    crs: str = DEFAULT_CRS,
) -> nx.MultiDiGraph:
    """Load and project OSMnx graph.
    
    Args:
        graph_path: Path to GraphML file
        cache_folder: Optional path to OSMnx cache folder
        crs: Coordinate reference system (default: EPSG:3857)
        
    Returns:
        Projected NetworkX graph
    """
    if cache_folder:
        ox.settings.cache_folder = str(cache_folder)
    
    logger.info(f"Loading graph from {graph_path}")
    G = ox.load_graphml(str(graph_path))
    
    logger.info(f"Projecting graph to {crs}")
    G = ox.project_graph(G, crs)
    
    return G


def add_time_attributes(
    graph: nx.MultiDiGraph,
    travel_speed: float = DEFAULT_TRAVEL_SPEED,
) -> None:
    """Add time attributes to graph edges.
    
    Modifies the graph in place by adding a "time" attribute to each edge
    representing the time in minutes required to traverse that edge.
    
    Args:
        graph: NetworkX graph with "length" attributes on edges
        travel_speed: Travel speed in km/hour (default: 4.5)
    """
    meters_per_minute = travel_speed * 1000 / 60  # km per hour to m per minute
    
    logger.info(f"Adding time attributes with travel speed {travel_speed} km/h")
    for _, _, _, data in graph.edges(data=True, keys=True):
        if "length" in data:
            data["time"] = data["length"] / meters_per_minute
        else:
            logger.warning("Edge missing 'length' attribute, skipping")


def calculate_walk_times(
    center_nodes: Union[List[int], pd.Series],
    graph: nx.MultiDiGraph,
    conserved_lands: gpd.GeoDataFrame,
    trip_times: List[int] = DEFAULT_TRIP_TIMES,
    travel_speed: float = DEFAULT_TRAVEL_SPEED,
    progress_bar: bool = True,
    geography_type: Optional[str] = None,
) -> pd.DataFrame:
    """Calculate walk times from center nodes to conserved lands.
    
    For each center node, finds all conserved lands reachable within the
    specified trip times and returns the minimum trip time for each land.
    
    Args:
        center_nodes: List or Series of OSMnx node IDs (center points)
        graph: NetworkX graph with time attributes on edges
        conserved_lands: GeoDataFrame with "osmid" column containing node IDs
        trip_times: List of trip time thresholds in minutes (default: [5,10,15,20,30,45,60])
        travel_speed: Travel speed in km/hour (default: 4.5)
        progress_bar: Whether to show progress bar (default: True)
        geography_type: "tracts" or "blocks" to determine column name (default: auto-detect)
        
    Returns:
        DataFrame with columns: [center_node_col, "land_osmid", "trip_time"]
        where center_node_col is "tract_osmid" or "block_osmid" depending on geography_type
    """
    # Ensure graph has time attributes
    sample_edge = next(iter(graph.edges(data=True, keys=True)))[3]
    if "time" not in sample_edge:
        logger.info("Graph missing time attributes, adding them")
        add_time_attributes(graph, travel_speed)
    
    # Determine column name based on geography type
    if geography_type:
        center_node_col = "tract_osmid" if geography_type == "tracts" else "block_osmid"
    else:
        # Fallback heuristic based on number of nodes
        center_node_col = "tract_osmid" if len(center_nodes) < 50000 else "block_osmid"
        logger.warning(f"geography_type not provided, using heuristic: {center_node_col}")
    
    logger.info(f"Calculating walk times for {len(center_nodes)} center nodes")
    logger.info(f"Trip times: {trip_times} minutes")
    
    def get_lands(center_node: int) -> List[List[int]]:
        """Find accessible lands from a center node.
        
        Args:
            center_node: OSMnx node ID
            
        Returns:
            List of [center_node, land_osmid, trip_time] lists
        """
        node_times = {}
        # Loop over allowed trip times, reversed to ensure lowest trip time is selected
        for trip_time in reversed(trip_times):
            # Find subgraph from center node
            try:
                subgraph = nx.ego_graph(graph, center_node, radius=trip_time, distance="time")
                # Set node distance to current trip_time
                for node in subgraph.nodes():
                    node_times[node] = trip_time
            except nx.NetworkXError:
                logger.warning(f"Node {center_node} not found in graph")
                continue
        
        # Map conserved lands to trip times
        full_dict = {
            int(node): node_times[int(node)] if int(node) in node_times else None
            for node in conserved_lands["osmid"].values
        }
        
        return [
            [center_node, k, v]
            for k, v in full_dict.items()
            if v is not None
        ]
    
    # Calculate walk times for all center nodes
    if progress_bar:
        records = [
            land
            for node in tqdm(center_nodes, desc="Calculating walk times")
            for land in get_lands(node)
        ]
    else:
        records = [
            land
            for node in center_nodes
            for land in get_lands(node)
        ]
    
    df = pd.DataFrame.from_records(
        records,
        columns=[center_node_col, "land_osmid", "trip_time"]
    )
    
    logger.info(f"Calculated {len(df)} walk time records")
    return df


def process_walk_times(
    geography_type: str,
    graph_path: Union[str, Path],
    geography_path: Union[str, Path],
    conserved_lands_path: Union[str, Path],
    output_path: Union[str, Path],
    trip_times: Optional[List[int]] = None,
    travel_speed: float = DEFAULT_TRAVEL_SPEED,
    cache_folder: Optional[Union[str, Path]] = None,
    region_config: Optional[RegionConfig] = None,
) -> pd.DataFrame:
    """Process walk times for tracts or blocks.
    
    Full workflow: loads data, calculates walk times, and saves results.
    
    Args:
        geography_type: "tracts" or "blocks"
        graph_path: Path to OSMnx GraphML file
        geography_path: Path to tracts or blocks shapefile with OSMnx node IDs
        conserved_lands_path: Path to conserved lands shapefile with OSMnx node IDs
        output_path: Path to save output CSV file
        trip_times: List of trip time thresholds in minutes (default: [5,10,15,20,30,45,60])
        travel_speed: Travel speed in km/hour (default: 4.5)
        cache_folder: Optional path to OSMnx cache folder
        region_config: Optional region configuration (currently unused but reserved for future)
        
    Returns:
        DataFrame with walk time calculations
    """
    if trip_times is None:
        trip_times = DEFAULT_TRIP_TIMES
    
    logger.info(f"Processing walk times for {geography_type}")
    logger.info(f"Graph: {graph_path}")
    logger.info(f"Geography: {geography_path}")
    logger.info(f"Conserved lands: {conserved_lands_path}")
    logger.info(f"Output: {output_path}")
    
    # Load data
    logger.info("Loading geography data")
    geography = gpd.read_file(str(geography_path))
    
    logger.info("Loading conserved lands data")
    conserved_lands = gpd.read_file(str(conserved_lands_path))
    
    # Load and prepare graph
    G = load_graph(graph_path, cache_folder=cache_folder)
    add_time_attributes(G, travel_speed)
    
    # Calculate walk times
    center_nodes = geography["osmid"].values
    df = calculate_walk_times(
        center_nodes,
        G,
        conserved_lands,
        trip_times=trip_times,
        travel_speed=travel_speed,
        geography_type=geography_type,
    )
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    return df

