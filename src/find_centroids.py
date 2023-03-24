import argparse
import pathlib
import geopandas as gpd
import osmnx as ox

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--graph", help="graph to use for search", default="data/maine.graphml", type=pathlib.Path)
parser.add_argument("input", help="GeoPandas-compatible file to add centroids to", type=pathlib.Path)
parser.add_argument("-o", "--suffix", help="output shapefile suffix", default="_with_nodes", type=str)
args = parser.parse_args()

if __name__ == "__main__":
    # load graph and create geodataframe with nodes
    G = ox.load_graphml(args.graph)
    G = ox.project_graph(G, "EPSG:3857")
    gdf_nodes = ox.graph_to_gdfs(G, edges=False).reset_index()
    print("Loaded", args.graph)

    # load input file
    polys = gpd.read_file(args.input).to_crs("EPSG:3857")
    print("Loaded", args.input)

    # drop invalid geometries
    raw_rows = polys.shape[0]
    polys.dropna(subset="geometry", inplace=True)
    n_dropped = raw_rows - polys.shape[0]
    if n_dropped > 0:
        print("Dropped {} rows with invalid geometries.".format(n_dropped))

    # find nearest nodes using spatial index
    polys["osmid"] = gdf_nodes.loc[gdf_nodes.sindex.nearest(polys.centroid)[1]]["osmid"].values

    # save output
    outfile = str(args.input)+args.suffix+".shp.zip"
    print("Saving", outfile)
    polys.to_file(outfile, driver="ESRI Shapefile")

    exit(0)

