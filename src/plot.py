"""Plotting utilities"""
import numpy as np
import networkx as nx
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
from tqdm.auto import tqdm


def plot_isochrones(
    G,
    center_node,
    times=[10, 20, 30, 40, 50, 60],
    attr="time",
    cmap="plasma",
    padding=0.02,
    subplots_kwargs={},
    graph_kwargs={},
    plot_kwargs={},
):
    """
    Plot isochrones on a graph.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Input graph.
    center_node : int
        The node ID to start from.
    times : list
        A list of times in minutes.
    attr : str
        The edge attribute to use as the weight.
    cmap : str
        The name of the matplotlib colormap to use.
    subplots_kwargs : dict
        Keyword arguments to pass to plt.subplots().
    graph_kwargs : dict
        Keyword arguments to pass to ox.plot_graph().
    plot_kwargs : dict
        Keyword arguments to pass to gdf.plot().
    """
    # Create a color map
    iso_colors = plt.get_cmap(cmap, len(times))
    # Create a GeoDataFrame of isochrones
    isochrone_polys = []
    for time in tqdm(times, desc="Constructing isochrones"):
        subgraph = nx.ego_graph(G, center_node, radius=time, distance=attr)
        node_points = [
            Point((data["x"], data["y"])) for node, data in subgraph.nodes(data=True)
        ]
        bounding_poly = gpd.GeoSeries(node_points).unary_union.convex_hull
        isochrone_polys.append(bounding_poly)

    gdf = gpd.GeoDataFrame(geometry=isochrone_polys)

    # find a bounding box for plotting and padding
    bbox = gdf.total_bounds * np.array([1 - padding, 1 + padding])

    # find the subgraph that is within the bounding box and plot it
    fig, ax = plt.subplots(**subplots_kwargs)
    subgraph = ox.truncate.truncate_graph_bbox(G, *bbox)
    ox.plot_graph(subgraph, ax=ax, **graph_kwargs)

    # plot the isochrones
    gdf.plot(ax=ax, facecolor="none", edgecolor=iso_colors.colors, **plot_kwargs)

    # add basemap
    ctx.add_basemap(
        ax, crs=subgraph.graph["crs"], source=ctx.providers.Esri.WorldStreetMap
    )

    return fig, ax
