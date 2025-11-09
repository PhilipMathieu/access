"""Graph utilities for converting NetworkX graphs to rustworkx."""

import logging
from typing import Dict, Optional, Tuple

import networkx as nx
import rustworkx as rx

logger = logging.getLogger(__name__)


def get_node_mapping(nx_graph: nx.MultiDiGraph) -> Tuple[Dict[int, int], Dict[int, int]]:
    """Create bidirectional mapping between NetworkX node IDs and rustworkx indices.
    
    Args:
        nx_graph: NetworkX MultiDiGraph with OSMnx node IDs
        
    Returns:
        Tuple of (nx_id_to_rx_idx, rx_idx_to_nx_id) dictionaries
    """
    nx_id_to_rx_idx = {}
    rx_idx_to_nx_id = {}
    
    for rx_idx, nx_id in enumerate(nx_graph.nodes()):
        nx_id_to_rx_idx[nx_id] = rx_idx
        rx_idx_to_nx_id[rx_idx] = nx_id
    
    return nx_id_to_rx_idx, rx_idx_to_nx_id


def nx_to_rustworkx(
    nx_graph: nx.MultiDiGraph,
    weight_attr: str = "time",
    default_weight: float = 1.0,
) -> Tuple[rx.PyDiGraph, Dict[int, int], Dict[int, int]]:
    """Convert NetworkX MultiDiGraph to rustworkx PyDiGraph.
    
    Args:
        nx_graph: NetworkX MultiDiGraph (typically from OSMnx)
        weight_attr: Edge attribute to use as weight (default: "time")
        default_weight: Default weight if attribute is missing (default: 1.0)
        
    Returns:
        Tuple of (rustworkx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id)
    """
    logger.info(f"Converting NetworkX graph to rustworkx (nodes: {nx_graph.number_of_nodes()}, edges: {nx_graph.number_of_edges()})")
    
    # Create node mapping
    nx_id_to_rx_idx, rx_idx_to_nx_id = get_node_mapping(nx_graph)
    
    # Create rustworkx graph
    rx_graph = rx.PyDiGraph()
    
    # Add all nodes first (rustworkx uses indices, not node IDs)
    for _ in range(nx_graph.number_of_nodes()):
        rx_graph.add_node(None)
    
    # Add edges with weights
    edges_added = 0
    edges_skipped = 0
    
    for u, v, key, data in nx_graph.edges(data=True, keys=True):
        rx_u = nx_id_to_rx_idx[u]
        rx_v = nx_id_to_rx_idx[v]
        
        # Get weight from edge data
        if weight_attr in data and data[weight_attr] is not None:
            weight = float(data[weight_attr])
        else:
            weight = default_weight
            edges_skipped += 1
        
        # Add edge with weight
        rx_graph.add_edge(rx_u, rx_v, weight)
        edges_added += 1
    
    if edges_skipped > 0:
        logger.warning(f"Skipped {edges_skipped} edges missing '{weight_attr}' attribute (used default weight {default_weight})")
    
    logger.info(f"Converted graph: {rx_graph.num_nodes()} nodes, {rx_graph.num_edges()} edges")
    
    return rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id


def convert_node_ids_to_rx_indices(
    node_ids: list,
    nx_id_to_rx_idx: Dict[int, int],
) -> list:
    """Convert NetworkX node IDs to rustworkx indices.
    
    Args:
        node_ids: List of NetworkX node IDs
        nx_id_to_rx_idx: Mapping from NetworkX node ID to rustworkx index
        
    Returns:
        List of rustworkx indices
    """
    rx_indices = []
    missing = []
    
    for nx_id in node_ids:
        if nx_id in nx_id_to_rx_idx:
            rx_indices.append(nx_id_to_rx_idx[nx_id])
        else:
            missing.append(nx_id)
    
    if missing:
        logger.warning(f"Could not find rustworkx indices for {len(missing)} nodes: {missing[:10]}...")
    
    return rx_indices


def convert_rx_indices_to_node_ids(
    rx_indices: list,
    rx_idx_to_nx_id: Dict[int, int],
) -> list:
    """Convert rustworkx indices to NetworkX node IDs.
    
    Args:
        rx_indices: List of rustworkx indices
        rx_idx_to_nx_id: Mapping from rustworkx index to NetworkX node ID
        
    Returns:
        List of NetworkX node IDs
    """
    nx_ids = []
    missing = []
    
    for rx_idx in rx_indices:
        if rx_idx in rx_idx_to_nx_id:
            nx_ids.append(rx_idx_to_nx_id[rx_idx])
        else:
            missing.append(rx_idx)
    
    if missing:
        logger.warning(f"Could not find NetworkX node IDs for {len(missing)} indices: {missing[:10]}...")
    
    return nx_ids

