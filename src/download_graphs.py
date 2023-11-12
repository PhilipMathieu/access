import osmnx as ox
from tqdm.auto import tqdm

from utils import setup_osmnx, STATES

setup_osmnx()
print("Using OSMnx version", ox.__version__)
print("WARNING: This script requires ~16GB RAM and may take several hours to run.")
print(
    "See notebooks/download_graphs_colab.ipynb for a Google Colab version that"
    "can be run in a high-RAM notebook instance."
)

# loop through the list of states
for state in tqdm(STATES, desc="States"):
    for network_type in tqdm(["walk", "drive"], leave=False, desc=f"{state['name']}"):
        tqdm.write(f"Downloading {state['name']} {network_type} network...")
        # download the street network
        G = ox.graph_from_place(
            state["name"], network_type=network_type, simplify=True, retain_all=True
        )
        # project the graph to UTM (zone calculated automatically) then plot it
        G = ox.project_graph(G)
        # save as graphml file
        ox.save_graphml(G, filename=f"data/OSM/{state['FIPS']}_{network_type}.graphml")
