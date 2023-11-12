import os
import networkx as nx
import osmnx as ox
import geopandas as gpd
import argparse
import logging
from tqdm.auto import tqdm
from multiprocessing import Pool

tqdm.pandas()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


def polygon_to_nodes(G, polygon, fallback=False):
    """
    Find the graph nodes within a polygon.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        A graph object created by OSMNx.
    polygon : shapely.geometry.Polygon
        A polygon object created by shapely.

    Returns
    -------
    nodes : list
        A list of node IDs.
    """
    try:
        # calculate the bounding box of the polygon
        polygon_bbox = polygon.bounds
        # truncate graph to bounding box
        G = ox.truncate.truncate_graph_bbox(
            G, polygon_bbox[1], polygon_bbox[0], polygon_bbox[3], polygon_bbox[2]
        )
        # find the nodes within the polygon
        nodes = ox.graph_to_gdfs(G, edges=False)
        nodes = nodes[nodes.intersects(polygon)].index.values.tolist()
    except Exception as e:
        print(f"Error: {e}")
        if fallback:
            print("Falling back to brute force method...")
            nodes = polygon_to_nodes_brute_force(G, polygon)
        else:
            nodes = []
    return nodes


def polygon_to_nodes_brute_force(G, polygon):
    """Find the graph nodes within a polygon using brute force."""
    nodes = []
    for node in G.nodes(data=True):
        point = (node[1]["x"], node[1]["y"])
        if polygon.contains(point):
            nodes.append(node[0])
    return nodes


def polygon_to_centroid_node(G, polygon):
    """
    Find the graph node closest to the centroid of a polygon.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        A graph object created by OSMNx.
    polygon : shapely.geometry.Polygon
        A polygon object created by shapely.

    Returns
    -------
    node : int
        The node ID.
    """
    # calculate the centroid of the polygon
    centroid = polygon.centroid
    # find the node closest to the centroid
    node = ox.distance.nearest_nodes(G, centroid.x, centroid.y)
    return node


def gdf_to_nodes(
    G, gdf, mode="intersect", driver_in=None, index_col=None, nodes_only=False
):
    """
    Find graph nodes for each row in a GeoDataFrame.

    Parameters
    ----------
    G : str or MultiDiGraph
        A file path to a GraphML file or a MultiDiGraph object.
    gdf : str or GeoDataFrame
        A file path to a GeoDataFrame or a GeoDataFrame object.
    mode : str, optional
        The mode to use for finding nodes. Valid options are "intersect", "intersect_bf", or "centroid".
        Defaults to "intersect".
    driver_in : str, optional
        The OGR driver to use to read the input file. Defaults to None.
    index_col : str, optional
        The name of the column to use as the index. Defaults to None.
    nodes_only : bool, optional
        If True, only return the list of node IDs. Defaults to False.

    Returns
    -------
    GeoDataFrame or Series
        A GeoDataFrame with the original data and an additional column of node IDs, or a Series of node IDs if nodes_only is True.

    Raises
    ------
    ValueError
        If the mode is not one of "intersect", "intersect_bf", or "centroid".
        If the input GeoDataFrame is not a GeoDataFrame or does not exist.
        If the input graph is not a MultiDiGraph or does not exist.

    Notes
    -----
    This function finds the graph nodes that intersect with each row in the input GeoDataFrame.
    The mode parameter determines the method used to find the nodes:
    - "intersect": finds the nodes that intersect with the geometry of each row using a spatial index.
    - "intersect_bf": finds the nodes that intersect with the geometry of each row using a brute-force method.
    - "centroid": finds the node closest to the centroid of each row's geometry.

    If nodes_only is True, the function returns a Series of node IDs instead of a GeoDataFrame.
    """
    # check that mode is valid
    if mode not in ["intersect", "intersect_bf", "centroid"]:
        raise ValueError(
            "Invalid mode. Choose from 'intersect', 'intersect_bf', or 'centroid'."
        )

    # check that gdf is a GeoDataFrame
    if not isinstance(gdf, gpd.GeoDataFrame):
        if os.path.isfile(gdf):
            gdf = gpd.read_file(gdf, driver=driver_in, index_col=index_col)
        else:
            raise ValueError("Input file does not exist.")

    # check that G is a MultiDiGraph
    if not isinstance(G, nx.MultiDiGraph):
        if os.path.isfile(G):
            G = ox.load_graphml(G)
        else:
            raise ValueError("Graph file does not exist.")

    G = ox.project_graph(G, "EPSG:3857")

    # drop invalid geometries
    n_initial_rows = gdf.shape[0]
    gdf.dropna(subset="geometry", inplace=True)
    n_dropped = n_initial_rows - gdf.shape[0]
    if n_dropped > 0:
        print(f"Warning: {n_dropped} rows with invalid geometries will be return NaN.")

    def apply_func(row):
        if mode == "intersect":
            return polygon_to_nodes(G, row["geometry"])
        elif mode == "intersect_bf":
            return polygon_to_nodes_brute_force(G, row["geometry"])
        elif mode == "centroid":
            return polygon_to_centroid_node(G, row["geometry"])

    with Pool() as pool:
        gdf["osmid"] = list(
            tqdm(
                pool.imap(apply_func, [row for _, row in gdf.iterrows()]),
                total=len(gdf),
            )
        )

    if nodes_only:
        return gdf["osmid"]

    return gdf


def main():
    parser = argparse.ArgumentParser(
        description="Transform geospatial data onto the OSMnx graphs"
    )
    parser.add_argument("input_graph", type=str, help="path to input graph")
    parser.add_argument("input_file", type=str, help="path to input file")
    parser.add_argument("output_file", type=str, help="path to output file")
    parser.add_argument(
        "--mode",
        type=str,
        default="intersect",
        help="mode parameter for gdf_to_nodes function",
    )
    parser.add_argument(
        "--driver_in",
        type=str,
        default=None,
        help="driver_in parameter for gdf_to_nodes function",
    )
    parser.add_argument(
        "--driver_out",
        type=str,
        default=None,
        help="driver_out parameter for gdf_to_nodes function",
    )
    parser.add_argument(
        "--index_col",
        type=str,
        default=None,
        help="index_col parameter for gdf_to_nodes function",
    )
    parser.add_argument(
        "--nodes_only",
        action="store_true",
        help="nodes_only parameter for gdf_to_nodes function",
    )
    args = parser.parse_args()

    # load graph
    logging.info("Loading graph...")
    G = ox.load_graphml(args.input_graph)
    logging.info("Graph loaded from {args.input_graph}")

    # load input file
    logging.info("Loading input file...")
    gdf = gpd.read_file(
        args.input_file, driver=args.driver_in, index_col=args.index_col
    )
    logging.info("Input file loaded from {args.input_file}")

    # transform
    logging.info("Transforming data...")
    gdf = gdf_to_nodes(G, gdf, mode=args.mode, nodes_only=args.nodes_only)
    logging.info("Data transformed. Saving...")

    # save output
    if not os.path.isdir(os.path.dirname(args.output_file)):
        os.makedirs(os.path.dirname(args.output_file))
    if args.nodes_only:
        gdf.to_csv(args.output_file, index=True, header=True)
    else:
        gdf.to_file(args.output_file, driver=args.driver_out)
    logging.info("Output saved to {args.output_file}")


if __name__ == "__main__":
    main()
