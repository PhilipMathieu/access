import os
import argparse
import osmnx as ox
import networkx as nx


def merge_graphs(graphs):
    """
    Merges a list of graphs using osmnx.

    Parameters:
    graphs (list): A list of networkx graphs.

    Returns:
    merged_graph (networkx.MultiDiGraph): A merged networkx graph.
    """
    merged_graph = nx.MultiDiGraph()
    for graph in graphs:
        merged_graph = nx.compose(merged_graph, graph)
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

    # Load the graphs
    graphs = []
    for filename in args.input_filenames:
        graph = ox.load_graphml(filename)
        graphs.append(graph)

    # Merge the graphs
    merged_graph = merge_graphs(graphs)

    # Save the merged graph
    ox.save_graphml(merged_graph, args.output_filename)


if __name__ == "__main__":
    main()
