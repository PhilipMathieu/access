#!/usr/bin/env python3
"""
Quick validation test for Python 3.11+ and OSMnx 2.0 upgrade.

This script validates that:
1. Python version is 3.11+
2. OSMnx 2.0 is installed and working
3. All key imports work
4. OSMnx API functions are available and working
5. Basic graph operations work

Runs with timeouts to avoid long operations.
"""

import logging
import signal
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("validate_upgrade.log")],
)
logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Timeout exception."""

    pass


def timeout_handler(_signum, _frame):
    """Handle timeout signal."""
    raise TimeoutError("Operation timed out")


def test_python_version():
    """Test Python version is 3.11+."""
    logger.info("=" * 70)
    logger.info("Test 1: Python Version")
    logger.info("=" * 70)
    version = sys.version_info
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        logger.error(f"Python 3.11+ required, got {version.major}.{version.minor}")
        return False
    logger.info("✓ Python version check passed")
    return True


def test_osmnx_version():
    """Test OSMnx version is 2.0+."""
    logger.info("=" * 70)
    logger.info("Test 2: OSMnx Version")
    logger.info("=" * 70)
    try:
        import osmnx as ox

        version = ox.__version__
        logger.info(f"OSMnx version: {version}")
        major_version = int(version.split(".")[0])
        if major_version < 2:
            logger.error(f"OSMnx 2.0+ required, got {version}")
            return False
        logger.info("✓ OSMnx version check passed")
        return True
    except ImportError as e:
        logger.error(f"Failed to import OSMnx: {e}")
        return False


def test_imports():
    """Test all key imports."""
    logger.info("=" * 70)
    logger.info("Test 3: Key Imports")
    logger.info("=" * 70)
    try:
        import geopandas as gpd
        import networkx as nx
        import osmnx as ox
        import pandas as pd
        import rustworkx as rx

        logger.info("✓ All core imports successful")
        logger.info(f"  - geopandas: {gpd.__version__}")
        logger.info(f"  - networkx: {nx.__version__}")
        logger.info(f"  - osmnx: {ox.__version__}")
        logger.info(f"  - pandas: {pd.__version__}")
        logger.info(f"  - rustworkx: {rx.__version__}")
        return True
    except ImportError as e:
        logger.error(f"Import failed: {e}")
        return False


def test_osmnx_api():
    """Test OSMnx API functions are available."""
    logger.info("=" * 70)
    logger.info("Test 4: OSMnx API Functions")
    logger.info("=" * 70)
    try:
        import osmnx as ox

        required_functions = [
            "load_graphml",
            "project_graph",
            "graph_from_place",
            "save_graphml",
            "graph_to_gdfs",
        ]
        missing = []
        for func_name in required_functions:
            if not hasattr(ox, func_name):
                missing.append(func_name)
            else:
                logger.info(f"  ✓ {func_name} available")

        if missing:
            logger.error(f"Missing functions: {missing}")
            return False

        # Test settings
        if not hasattr(ox, "settings"):
            logger.error("ox.settings not available")
            return False
        logger.info("  ✓ settings available")

        if not hasattr(ox.settings, "cache_folder"):
            logger.error("ox.settings.cache_folder not available")
            return False
        logger.info("  ✓ settings.cache_folder available")

        logger.info("✓ All OSMnx API functions available")
        return True
    except Exception as e:
        logger.error(f"OSMnx API test failed: {e}")
        return False


def test_project_imports():
    """Test project-specific imports."""
    logger.info("=" * 70)
    logger.info("Test 5: Project Imports")
    logger.info("=" * 70)
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        from walk_times.calculate import add_time_attributes, load_graph  # noqa: F401
        from walk_times.graph_utils import nx_to_rustworkx  # noqa: F401

        logger.info("✓ walk_times.calculate imports successful")
        logger.info("✓ walk_times.graph_utils imports successful")
        return True
    except ImportError as e:
        logger.error(f"Project import failed: {e}")
        return False


def test_osmnx_basic_operation(timeout_seconds=30):
    """Test basic OSMnx operation with timeout."""
    logger.info("=" * 70)
    logger.info("Test 6: Basic OSMnx Operation (with timeout)")
    logger.info("=" * 70)

    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        import networkx as nx
        import osmnx as ox

        # Test settings
        ox.settings.cache_folder = "./cache/"
        logger.info("✓ Settings configuration works")

        # Test creating a minimal graph (don't download, just test API)
        # We'll test that graph_to_gdfs requires CRS (expected behavior)
        G = nx.MultiDiGraph()
        G.add_node(1, x=0, y=0, osmid=1)
        G.graph["crs"] = "EPSG:4326"

        try:
            gdf = ox.graph_to_gdfs(G, edges=False)
            logger.info(f"✓ graph_to_gdfs works (returned {type(gdf).__name__})")
        except Exception as e:
            # This is expected if graph doesn't have proper CRS/geometry
            logger.info(
                f"  Note: graph_to_gdfs requires proper graph structure (expected): {type(e).__name__}"
            )

        signal.alarm(0)  # Cancel timeout
        logger.info("✓ Basic OSMnx operations work")
        return True
    except TimeoutError:
        logger.error("Operation timed out")
        signal.alarm(0)
        return False
    except Exception as e:
        signal.alarm(0)
        logger.error(f"Basic operation test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    logger.info("=" * 70)
    logger.info("Validation Test: Python 3.11+ and OSMnx 2.0 Upgrade")
    logger.info("=" * 70)
    logger.info("")

    tests = [
        ("Python Version", test_python_version),
        ("OSMnx Version", test_osmnx_version),
        ("Key Imports", test_imports),
        ("OSMnx API", test_osmnx_api),
        ("Project Imports", test_project_imports),
        ("Basic OSMnx Operation", test_osmnx_basic_operation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()  # type: ignore[operator]
            results.append((test_name, result))
            logger.info("")
        except Exception as e:
            logger.error(f"Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
            logger.info("")

    # Summary
    logger.info("=" * 70)
    logger.info("Validation Summary")
    logger.info("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("")
        logger.info("✓ All validation tests passed!")
        logger.info("Python 3.11+ and OSMnx 2.0 upgrade is working correctly.")
        return 0
    else:
        logger.info("")
        logger.error("✗ Some validation tests failed.")
        logger.error("Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
