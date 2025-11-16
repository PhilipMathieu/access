"""Calculate walk times from geographic units to conserved lands."""

import logging
from pathlib import Path

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
import rustworkx as rx
from tqdm import tqdm

from config.defaults import DEFAULT_CRS, DEFAULT_TRAVEL_SPEED, DEFAULT_TRIP_TIMES
from config.regions import RegionConfig
from walk_times.algorithms import bounded_dijkstra, calculate_walk_times_parallel
from walk_times.graph_utils import convert_node_ids_to_rx_indices, nx_to_rustworkx

logger = logging.getLogger(__name__)


def load_graph(
    graph_path: str | Path,
    cache_folder: str | Path | None = None,
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


# Cache for rustworkx graph conversions
_rx_graph_cache: dict[str, tuple[rx.PyDiGraph, dict[int, int], dict[int, int]]] = {}


def get_rustworkx_graph(
    nx_graph: nx.MultiDiGraph,
    cache_key: str | None = None,
) -> tuple[rx.PyDiGraph, dict[int, int], dict[int, int]]:
    """Get rustworkx graph from NetworkX graph, with caching.

    Args:
        nx_graph: NetworkX MultiDiGraph
        cache_key: Optional cache key for caching the conversion

    Returns:
        Tuple of (rustworkx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id)
    """
    if cache_key and cache_key in _rx_graph_cache:
        logger.info(f"Using cached rustworkx graph (key: {cache_key})")
        return _rx_graph_cache[cache_key]

    rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id = nx_to_rustworkx(nx_graph, weight_attr="time")

    if cache_key:
        _rx_graph_cache[cache_key] = (rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id)
        logger.info(f"Cached rustworkx graph (key: {cache_key})")

    return rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id


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
    center_nodes: list[int] | pd.Series,
    graph: nx.MultiDiGraph,
    conserved_lands: gpd.GeoDataFrame,
    trip_times: list[int] = DEFAULT_TRIP_TIMES,
    travel_speed: float = DEFAULT_TRAVEL_SPEED,
    progress_bar: bool = True,
    geography_type: str | None = None,
    n_jobs: int = 1,
) -> pd.DataFrame:
    """Calculate walk times from center nodes to conserved lands.

    For each center node, finds all conserved lands reachable within the
    specified trip times and returns the minimum trip time for each land.

    Uses rustworkx for faster graph operations and bounded Dijkstra algorithm
    to limit exploration radius. Supports parallel processing for speedup.

    Args:
        center_nodes: List or Series of OSMnx node IDs (center points)
        graph: NetworkX graph with time attributes on edges
        conserved_lands: GeoDataFrame with "osmid" column containing node IDs
        trip_times: List of trip time thresholds in minutes (default: [5,10,15,20,30,45,60])
        travel_speed: Travel speed in km/hour (default: 4.5)
        progress_bar: Whether to show progress bar (default: True)
        geography_type: "tracts" or "blocks" to determine column name (default: auto-detect)
        n_jobs: Number of parallel workers. Set to 1 for serial processing,
                -1 for all CPUs, or specific number (default: 1)

    Returns:
        DataFrame with columns: [center_node_col, "land_osmid", "trip_time"]
        where center_node_col is "tract_osmid" or "block_osmid" depending on geography_type
    """
    # Ensure graph has time attributes
    sample_edge = next(iter(graph.edges(data=True, keys=True)))[3]
    if "time" not in sample_edge:
        logger.info("Graph missing time attributes, adding them")
        add_time_attributes(graph, travel_speed)

    # Use parallel implementation if n_jobs != 1
    if n_jobs != 1:
        from multiprocessing import cpu_count

        if n_jobs == -1:
            n_jobs = cpu_count()

        logger.info(f"Using parallel implementation with {n_jobs} workers")
        return calculate_walk_times_parallel(
            center_nodes=list(center_nodes),
            graph=graph,
            conserved_lands=conserved_lands,
            trip_times=trip_times,
            n_jobs=n_jobs,
            geography_type=geography_type,
            progress_bar=progress_bar,
        )

    # Determine column name based on geography type
    if geography_type:
        center_node_col = "tract_osmid" if geography_type == "tracts" else "block_osmid"
    else:
        # Fallback heuristic based on number of nodes
        center_node_col = "tract_osmid" if len(center_nodes) < 50000 else "block_osmid"
        logger.warning(f"geography_type not provided, using heuristic: {center_node_col}")

    logger.info(f"Calculating walk times for {len(center_nodes)} center nodes")
    logger.info(f"Trip times: {trip_times} minutes")

    # Convert NetworkX graph to rustworkx once
    logger.info("Converting graph to rustworkx format")
    rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id = get_rustworkx_graph(graph)

    # Get conserved land node IDs and convert to rustworkx indices
    conserved_land_nx_ids = conserved_lands["osmid"].astype(int).values
    conserved_land_rx_indices = convert_node_ids_to_rx_indices(
        conserved_land_nx_ids.tolist(), nx_id_to_rx_idx
    )

    # Create mapping from rx_idx to nx_id for conserved lands
    conserved_land_rx_to_nx = {
        rx_idx: nx_id
        for nx_id, rx_idx in zip(conserved_land_nx_ids, conserved_land_rx_indices, strict=False)
        if rx_idx is not None
    }

    # Sort trip times for efficient filtering
    sorted_trip_times = sorted(trip_times, reverse=True)
    max_trip_time = max(trip_times)

    def get_lands(center_node: int) -> list[list[int]]:
        """Find accessible lands from a center node using single Dijkstra.

        Args:
            center_node: OSMnx node ID

        Returns:
            List of [center_node, land_osmid, trip_time] lists
        """
        # Convert center node to rustworkx index
        if center_node not in nx_id_to_rx_idx:
            logger.warning(f"Node {center_node} not found in graph")
            return []

        center_rx_idx = nx_id_to_rx_idx[center_node]

        # Run bounded Dijkstra to find distances within max_trip_time
        try:
            # Use bounded Dijkstra to limit exploration radius
            distances = bounded_dijkstra(
                rx_graph,
                center_rx_idx,
                max_distance=max_trip_time,
            )
        except Exception as e:
            logger.warning(f"Error calculating shortest paths from node {center_node}: {e}")
            return []

        # Filter to conserved lands and find minimum trip time for each
        results = []
        for land_rx_idx, land_nx_id in conserved_land_rx_to_nx.items():
            if land_rx_idx in distances:
                distance = distances[land_rx_idx]

                # Find the smallest trip time threshold that this distance fits into
                for trip_time in sorted_trip_times:
                    if distance <= trip_time:
                        results.append([center_node, land_nx_id, trip_time])
                        break  # Use the smallest trip time threshold

        return results

    # Calculate walk times for all center nodes
    if progress_bar:
        records = [
            land
            for node in tqdm(center_nodes, desc="Calculating walk times")
            for land in get_lands(node)
        ]
    else:
        records = [land for node in center_nodes for land in get_lands(node)]

    df = pd.DataFrame.from_records(records, columns=[center_node_col, "land_osmid", "trip_time"])

    logger.info(f"Calculated {len(df)} walk time records")
    return df


def process_walk_times(
    geography_type: str,
    graph_path: str | Path,
    geography_path: str | Path,
    conserved_lands_path: str | Path,
    output_path: str | Path,
    trip_times: list[int] | None = None,
    travel_speed: float = DEFAULT_TRAVEL_SPEED,
    cache_folder: str | Path | None = None,
    region_config: RegionConfig | None = None,  # noqa: ARG001
    n_jobs: int = 1,
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
        n_jobs: Number of parallel workers (default: 1 for serial, -1 for all CPUs)

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
    if str(geography_path).endswith(".parquet"):
        geography = gpd.read_parquet(str(geography_path))
    else:
        geography = gpd.read_file(str(geography_path))  # Fallback for existing shapefiles

    logger.info("Loading conserved lands data")
    if str(conserved_lands_path).endswith(".parquet"):
        conserved_lands = gpd.read_parquet(str(conserved_lands_path))
    else:
        conserved_lands = gpd.read_file(
            str(conserved_lands_path)
        )  # Fallback for existing shapefiles

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
        n_jobs=n_jobs,
    )

    # Save results
    logger.info(f"Saving results to {output_path}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if str(output_path).endswith(".parquet"):
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)  # Fallback for CSV output

    return df
