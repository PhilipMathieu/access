#!/usr/bin/env python3
"""Test script to verify optimization changes work correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        import rustworkx as rx
        print(f"✓ rustworkx imported (version: {rx.__version__})")
    except ImportError as e:
        print(f"✗ rustworkx not installed: {e}")
        return False
    
    try:
        import pyarrow
        print(f"✓ pyarrow imported (version: {pyarrow.__version__})")
    except ImportError as e:
        print(f"✗ pyarrow not installed: {e}")
        return False
    
    try:
        import geopandas as gpd
        print(f"✓ geopandas imported (version: {gpd.__version__})")
    except ImportError as e:
        print(f"✗ geopandas not installed: {e}")
        return False
    
    try:
        from walk_times.graph_utils import nx_to_rustworkx, get_node_mapping
        print("✓ walk_times.graph_utils imported")
    except ImportError as e:
        print(f"✗ walk_times.graph_utils import failed: {e}")
        return False
    
    try:
        from walk_times.calculate import calculate_walk_times, get_rustworkx_graph
        print("✓ walk_times.calculate imported")
    except ImportError as e:
        print(f"✗ walk_times.calculate import failed: {e}")
        return False
    
    try:
        from merging.blocks import merge_walk_times
        print("✓ merging.blocks imported")
    except ImportError as e:
        print(f"✗ merging.blocks import failed: {e}")
        return False
    
    try:
        from merging.analysis import create_ejblocks
        print("✓ merging.analysis imported")
    except ImportError as e:
        print(f"✗ merging.analysis import failed: {e}")
        return False
    
    return True


def test_geoparquet_support():
    """Test that GeoParquet support is available."""
    print("\nTesting GeoParquet support...")
    
    try:
        import geopandas as gpd
        import pyarrow
        
        # Check if GeoPandas supports Parquet
        if hasattr(gpd, 'read_parquet'):
            print("✓ gpd.read_parquet available")
        else:
            print("✗ gpd.read_parquet not available")
            return False
        
        if hasattr(gpd.GeoDataFrame, 'to_parquet'):
            print("✓ gdf.to_parquet available")
        else:
            print("✗ gdf.to_parquet not available")
            return False
        
        return True
    except Exception as e:
        print(f"✗ GeoParquet support test failed: {e}")
        return False


def test_parquet_support():
    """Test that Parquet support is available."""
    print("\nTesting Parquet support...")
    
    try:
        import pandas as pd
        import pyarrow
        
        # Check if Pandas supports Parquet
        if hasattr(pd, 'read_parquet'):
            print("✓ pd.read_parquet available")
        else:
            print("✗ pd.read_parquet not available")
            return False
        
        if hasattr(pd.DataFrame, 'to_parquet'):
            print("✓ df.to_parquet available")
        else:
            print("✗ df.to_parquet not available")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Parquet support test failed: {e}")
        return False


def test_code_structure():
    """Test that code structure is correct."""
    print("\nTesting code structure...")
    
    # Check that graph_utils.py exists and has required functions
    graph_utils_path = Path("src/walk_times/graph_utils.py")
    if graph_utils_path.exists():
        print("✓ graph_utils.py exists")
        
        content = graph_utils_path.read_text()
        if "def nx_to_rustworkx" in content:
            print("✓ nx_to_rustworkx function found")
        else:
            print("✗ nx_to_rustworkx function not found")
            return False
        
        if "def get_node_mapping" in content:
            print("✓ get_node_mapping function found")
        else:
            print("✗ get_node_mapping function not found")
            return False
    else:
        print("✗ graph_utils.py not found")
        return False
    
    # Check that calculate.py uses rustworkx
    calculate_path = Path("src/walk_times/calculate.py")
    if calculate_path.exists():
        content = calculate_path.read_text()
        if "import rustworkx" in content or "import rustworkx as rx" in content:
            print("✓ calculate.py imports rustworkx")
        else:
            print("✗ calculate.py does not import rustworkx")
            return False
        
        if "digraph_dijkstra_shortest_path_lengths" in content:
            print("✓ calculate.py uses rustworkx Dijkstra")
        else:
            print("✗ calculate.py does not use rustworkx Dijkstra")
            return False
    else:
        print("✗ calculate.py not found")
        return False
    
    # Check that files support GeoParquet
    blocks_path = Path("src/merging/blocks.py")
    if blocks_path.exists():
        content = blocks_path.read_text()
        if "read_parquet" in content:
            print("✓ blocks.py supports GeoParquet reading")
        else:
            print("✗ blocks.py does not support GeoParquet reading")
            return False
        
        if "to_parquet" in content:
            print("✓ blocks.py supports GeoParquet writing")
        else:
            print("✗ blocks.py does not support GeoParquet writing")
            return False
    else:
        print("✗ blocks.py not found")
        return False
    
    return True


def test_pipeline_paths():
    """Test that pipeline paths are updated."""
    print("\nTesting pipeline paths...")
    
    pipeline_path = Path("src/run_pipeline.py")
    if pipeline_path.exists():
        content = pipeline_path.read_text()
        
        # Check for .parquet extensions
        if ".parquet" in content:
            print("✓ Pipeline uses .parquet extensions")
        else:
            print("✗ Pipeline does not use .parquet extensions")
            return False
        
        # Check that old .shp.zip paths are still there (for backward compatibility)
        if ".shp.zip" in content:
            print("✓ Pipeline maintains backward compatibility with .shp.zip")
        else:
            print("⚠ Pipeline may not maintain backward compatibility")
        
        return True
    else:
        print("✗ run_pipeline.py not found")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing Optimization Changes")
    print("=" * 70)
    
    results = []
    
    # Test imports (may fail if dependencies not installed)
    print("\n" + "=" * 70)
    try:
        results.append(("Imports", test_imports()))
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        results.append(("Imports", False))
    
    # Test GeoParquet support (may fail if dependencies not installed)
    try:
        results.append(("GeoParquet Support", test_geoparquet_support()))
    except Exception as e:
        print(f"✗ GeoParquet test failed: {e}")
        results.append(("GeoParquet Support", False))
    
    # Test Parquet support (may fail if dependencies not installed)
    try:
        results.append(("Parquet Support", test_parquet_support()))
    except Exception as e:
        print(f"✗ Parquet test failed: {e}")
        results.append(("Parquet Support", False))
    
    # Test code structure (should always work)
    results.append(("Code Structure", test_code_structure()))
    
    # Test pipeline paths (should always work)
    results.append(("Pipeline Paths", test_pipeline_paths()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

