import os
import argparse
import osmnx as ox
import networkx as nx
from tqdm.auto import tqdm


def add_trip_times(G, speed=4.5):
    """
    Given an input graph, add trip times in minutes to each edge.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Input graph.
    speed : float
        Average speed of travel in kilometers per hour.

    Returns
    -------
    G : networkx.MultiDiGraph
        Input graph with trip times added to each edge.
    """
    # Calculate time to traverse each edge
    for u, v, k, data in tqdm(G.edges(keys=True, data=True)):
        # Calculate distance in km
        dist = data["length"] / 1000
        # Calculate time in hours
        data["time"] = dist / speed
        # Convert to minutes
        data["time"] *= 60
    return G


def get_isochrone_nodes(G, start_node, radius, key="time"):
    """
    Given an input graph and a starting node, return a list of nodes that are
    within the specified distance.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Input graph.
    start_node : int
        The node ID to start from.
    radius : float
        The radius of the isochrone in minutes.
    key : str
        The edge attribute to use as the weight.

    Returns
    -------
    nodes : list
        A list of nodes within the specified distance.
    """
    subgraph = nx.ego_graph(G, start_node, radius, distance=key)
    nodes = list(subgraph.nodes())
    return nodes


def main():
    """
    Parses command line arguments and adds trip times to the input graph.
    """
    parser = argparse.ArgumentParser(description="Add trip times to a graph.")
    parser.add_argument(
        "input_filename", type=str, help="Input filename for the graph."
    )
    parser.add_argument(
        "output_filename", type=str, help="Output filename for the graph."
    )
    args = parser.parse_args()

    # Verify the input path is valid
    if not os.path.isfile(args.input_filename):
        print(f"{args.input_filename} is not a valid file path.")
        return

    # Load the graph
    print("Loading graph...")
    G = ox.load_graphml(args.input_filename)

    # Add trip times
    print("Adding trip times...")
    G = add_trip_times(G)

    # Save the graph
    print("Saving graph...")
    ox.save_graphml(G, args.output_filename)


if __name__ == "__main__":
    main()
