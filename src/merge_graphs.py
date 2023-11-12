import os
import argparse
import osmnx as ox
import networkx as nx
from tqdm.auto import tqdm


def merge_graphs(graphs):
    """
    Merges a list of graphs using osmnx.

    Parameters:
    graphs (list): A list of networkx graphs.

    Returns:
    merged_graph (networkx.MultiDiGraph): A merged networkx graph.
    """
    merged_graph = nx.MultiDiGraph()
    for graph in tqdm(graphs, desc="Merging graphs"):
        G = ox.load_graphml(graph)
        merged_graph = nx.compose(merged_graph, G)
    return merged_graph


def main():
    """
    Parses command line arguments and merges the input graphs.
    """
    parser = argparse.ArgumentParser(
        description="Merge multiple graphml files using osmnx."
    )
    parser.add_argument(
        "output_filename", type=str, help="Output filename for the merged graph."
    )
    parser.add_argument(
        "input_filenames",
        type=str,
        nargs="+",
        help="Input filenames for the graphs to be merged.",
    )
    args = parser.parse_args()

    # Verify all paths are valid
    for filename in args.input_filenames:
        if not os.path.isfile(filename):
            print(f"{filename} is not a valid file path.")
            return

    graph = merge_graphs(args.input_filenames)
    ox.save_graphml(graph, args.output_filename)


if __name__ == "__main__":
    main()
