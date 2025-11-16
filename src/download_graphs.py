import osmnx as ox

ox.settings.cache_folder = "./cache/"
ox.settings.log_console = True
print("Using OSMnx version", ox.__version__)
print("WARNING: This script requires >10GB RAM available")

# download/model a network of driving routes for the state of Maine
G = ox.graph_from_place({"state": "Maine"}, network_type="drive")
filepath = "./data/graphs/maine_drive.graphml"
ox.save_graphml(G, filepath)

# download/model a network of walking routes for the state of Maine
G = ox.graph_from_place({"state": "Maine"}, network_type="walk")
filepath = "./data/graphs/maine_walk.graphml"
ox.save_graphml(G, filepath)
