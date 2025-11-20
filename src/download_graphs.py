import logging
from pathlib import Path

import osmnx as ox

from exceptions import GraphError, NetworkError
from utils.retry import retry_with_backoff

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

ox.settings.cache_folder = "./cache/"
ox.settings.log_console = True
logger.info(f"Using OSMnx version {ox.__version__}")
logger.warning("This script requires >10GB RAM available")


@retry_with_backoff
def download_graph(place: dict[str, str], network_type: str, output_path: Path) -> None:
    """Download and save an OSMnx graph with retry logic.

    Args:
        place: Place dictionary for OSMnx (e.g., {"state": "Maine"})
        network_type: Network type ("drive" or "walk")
        output_path: Path to save the graph file

    Raises:
        GraphError: If graph download or save fails
    """
    try:
        logger.info(f"Downloading {network_type} network for {place}")
        G = ox.graph_from_place(place, network_type=network_type)
        logger.info(f"Downloaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges")

        logger.info(f"Saving graph to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ox.save_graphml(G, str(output_path))
        logger.info(f"Successfully saved graph to {output_path}")
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg or "connection" in error_msg:
            raise GraphError(f"Network error downloading graph: {e}") from e
        elif "memory" in error_msg or "ram" in error_msg:
            raise GraphError(f"Insufficient memory for graph download: {e}") from e
        else:
            raise GraphError(f"Failed to download/save graph: {e}") from e


def main() -> None:
    """Download driving and walking networks for Maine."""
    try:
        # Download/model a network of driving routes for the state of Maine
        download_graph(
            place={"state": "Maine"},
            network_type="drive",
            output_path=Path("./data/graphs/maine_drive.graphml"),
        )

        # Download/model a network of walking routes for the state of Maine
        download_graph(
            place={"state": "Maine"},
            network_type="walk",
            output_path=Path("./data/graphs/maine_walk.graphml"),
        )

        logger.info("All graphs downloaded successfully!")
    except (GraphError, NetworkError) as e:
        logger.error(f"Failed to download graphs: {e}")
        raise


if __name__ == "__main__":
    main()
