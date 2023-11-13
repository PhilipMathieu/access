import argparse
import osmnx as ox
from tqdm.auto import tqdm

from utils import setup_osmnx, STATES


def download_graph(state, network_type):
    # download the street network
    G = ox.graph_from_place(
        state["name"], network_type=network_type, simplify=True, retain_all=True
    )
    # project the graph to UTM (zone calculated automatically) then plot it
    G = ox.project_graph(G)
    # save as graphml file
    ox.save_graphml(G, filepath=f"data/OSM/{state['FIPS']}_{network_type}.graphml")


def download_graphs(states, network_types):
    setup_osmnx()

    print(f"Downloading {len(states)} states and {len(network_types)} network types")

    # loop through the list of states
    for state in tqdm(states, desc="States"):
        for network_type in tqdm(network_types, leave=False, desc=f"{state['name']}"):
            tqdm.write(f"Downloading {state['name']} {network_type} network...")
            download_graph(state, network_type)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download street network graphs for specified states and network types"
    )
    parser.add_argument(
        "--states",
        nargs="+",
        default=[state["name"] for state in STATES],
        help="List of state names to download",
    )
    parser.add_argument(
        "--network-types",
        nargs="+",
        default=["walk", "drive"],
        help="List of network types to download",
    )
    args = parser.parse_args()

    if len(args.states) == 0:
        states = STATES
    else:
        states = []
        for state in args.states:
            for state_dict in STATES:
                if state_dict["FIPS"] == state:
                    states.append(state_dict)
                    break

    if len(args.network_types) == 0:
        network_types = ["walk", "drive"]
    else:
        network_types = args.network_types

    download_graphs(states, network_types)
