"""Advanced algorithms for walk time computation."""

import heapq
import logging
from functools import partial
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Tuple

import geopandas as gpd
import networkx as nx
import pandas as pd
import rustworkx as rx
from tqdm import tqdm

from walk_times.graph_utils import convert_node_ids_to_rx_indices, nx_to_rustworkx

logger = logging.getLogger(__name__)


def bounded_dijkstra(
    graph: rx.PyDiGraph,
    source: int,
    max_distance: float,
) -> Dict[int, float]:
    """
    Custom Dijkstra algorithm with distance bounding.
    
    Stops exploring nodes once distance exceeds max_distance, preventing
    unnecessary computation for nodes beyond our radius of interest.
    
    Args:
        graph: rustworkx directed graph with edge weights
        source: Source node index (rustworkx index, not OSM ID)
        max_distance: Maximum distance to explore (in minutes)
        
    Returns:
        Dictionary mapping node indices to distances (only nodes within max_distance)
        
    Example:
        >>> distances = bounded_dijkstra(rx_graph, source_idx, max_distance=60.0)
        >>> # Returns only nodes reachable within 60 minutes
    """
    distances = {source: 0.0}
    visited = set()
    pq = [(0.0, source)]  # Priority queue: (distance, node)
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        # Skip if already visited
        if current_node in visited:
            continue
        
        # Early termination: don't explore beyond max_distance
        if current_dist > max_distance:
            break
            
        visited.add(current_node)
        
        # Explore neighbors
        for neighbor in graph.successor_indices(current_node):
            # Get edge weight (time in minutes)
            edge_data = graph.get_edge_data(current_node, neighbor)
            if edge_data is None:
                continue
                
            new_dist = current_dist + edge_data
            
            # Only add to queue if within radius
            if new_dist <= max_distance:
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    heapq.heappush(pq, (new_dist, neighbor))
    
    logger.debug(f"Bounded Dijkstra from node {source}: explored {len(distances)} nodes "
                f"(max_dist={max_distance:.1f})")
    
    return distances


def _process_single_center_node(
    center_node: int,
    rx_graph: rx.PyDiGraph,
    nx_to_rx: Dict[int, int],
    rx_to_nx: Dict[int, int],
    conserved_land_rx_to_nx: Dict[int, int],
    sorted_trip_times: List[int],
    max_trip_time: float,
) -> List[Tuple[int, int, int]]:
    """
    Process a single center node (called in parallel).
    
    This function is designed to be called by multiprocessing workers.
    All arguments must be pickleable.
    
    Args:
        center_node: Center node OSM ID
        rx_graph: rustworkx graph (read-only, safe for multiprocessing)
        nx_to_rx: Node ID to index mapping
        rx_to_nx: Index to node ID mapping  
        conserved_land_rx_to_nx: Conserved land mappings
        sorted_trip_times: Trip time thresholds (sorted)
        max_trip_time: Maximum trip time to explore
        
    Returns:
        List of (center_node, land_osmid, trip_time) tuples
    """
    if center_node not in nx_to_rx:
        return []
    
    center_rx_idx = nx_to_rx[center_node]
    
    try:
        # Use bounded Dijkstra to limit search
        distances = bounded_dijkstra(rx_graph, center_rx_idx, max_trip_time)
    except Exception as e:
        logger.warning(f"Error in worker processing node {center_node}: {e}")
        return []
    
    results = []
    for land_rx_idx, land_nx_id in conserved_land_rx_to_nx.items():
        if land_rx_idx in distances:
            distance = distances[land_rx_idx]
            for trip_time in sorted_trip_times:
                if distance <= trip_time:
                    results.append((center_node, land_nx_id, trip_time))
                    break
    
    return results


def calculate_walk_times_parallel(
    center_nodes: List[int],
    graph: nx.MultiDiGraph,
    conserved_lands: gpd.GeoDataFrame,
    trip_times: List[int],
    n_jobs: int = None,
    geography_type: str = None,
    progress_bar: bool = True,
) -> pd.DataFrame:
    """
    Calculate walk times using bounded Dijkstra with parallel processing.
    
    Args:
        center_nodes: List of center node OSM IDs
        graph: NetworkX graph with time attributes
        conserved_lands: GeoDataFrame with conserved lands
        trip_times: Trip time thresholds in minutes
        n_jobs: Number of parallel workers (default: CPU count - 1)
        geography_type: "tracts" or "blocks" for column naming
        progress_bar: Whether to show progress bar
        
    Returns:
        DataFrame with walk time results
    """
    # Determine number of workers
    if n_jobs is None:
        n_jobs = max(1, cpu_count() - 1)
    
    logger.info(f"Calculating walk times with {n_jobs} parallel workers")
    logger.info(f"Processing {len(center_nodes)} center nodes")
    
    # Determine column name
    if geography_type:
        center_node_col = "tract_osmid" if geography_type == "tracts" else "block_osmid"
    else:
        center_node_col = "tract_osmid" if len(center_nodes) < 50000 else "block_osmid"
    
    # Convert to rustworkx
    logger.info("Converting graph to rustworkx format")
    rx_graph, nx_to_rx, rx_to_nx = nx_to_rustworkx(graph, weight_attr="time")
    
    # Prepare conserved lands mapping
    conserved_land_nx_ids = conserved_lands["osmid"].astype(int).values
    conserved_land_rx_indices = convert_node_ids_to_rx_indices(
        conserved_land_nx_ids.tolist(),
        nx_to_rx
    )
    
    conserved_land_rx_to_nx = {
        rx_idx: nx_id
        for nx_id, rx_idx in zip(conserved_land_nx_ids, conserved_land_rx_indices)
        if rx_idx is not None
    }
    
    sorted_trip_times = sorted(trip_times)
    max_trip_time = max(trip_times)
    
    logger.info(f"Max trip time: {max_trip_time} minutes")
    logger.info(f"Conserved lands: {len(conserved_land_rx_to_nx)}")
    
    # Create worker function with fixed arguments
    worker_func = partial(
        _process_single_center_node,
        rx_graph=rx_graph,
        nx_to_rx=nx_to_rx,
        rx_to_nx=rx_to_nx,
        conserved_land_rx_to_nx=conserved_land_rx_to_nx,
        sorted_trip_times=sorted_trip_times,
        max_trip_time=max_trip_time,
    )
    
    # Process in parallel
    logger.info(f"Starting parallel processing with {n_jobs} workers...")
    with Pool(processes=n_jobs) as pool:
        if progress_bar:
            results_list = list(tqdm(
                pool.imap(worker_func, center_nodes, chunksize=10),
                total=len(center_nodes),
                desc=f"Walk times (×{n_jobs} parallel)"
            ))
        else:
            results_list = pool.map(worker_func, center_nodes, chunksize=10)
    
    # Flatten results
    all_results = [
        result
        for batch_results in results_list
        for result in batch_results
    ]
    
    # Create DataFrame
    df = pd.DataFrame(
        all_results,
        columns=[center_node_col, "land_osmid", "trip_time"]
    )
    
    logger.info(f"Calculated {len(df)} walk time records")
    return df

