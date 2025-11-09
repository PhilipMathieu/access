#!/usr/bin/env python3
"""
Run the complete analysis pipeline with updated data.

This script runs all processing steps:
1. Process updated data (add centroids/node IDs if needed)
2. Calculate walk times for blocks
3. Merge walk times with blocks
4. Create ejblocks with census/CEJST data
5. Generate visualizations
6. Generate H3 relationship files
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path to import h3 module
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from config.regions import get_region_config
from config.defaults import (
    DEFAULT_TRIP_TIMES,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_H3_RESOLUTION_AREA,
)
from walk_times.calculate import process_walk_times
from merging.blocks import merge_walk_times, dissolve_blocks
from merging.analysis import create_ejblocks
from visualization.figures import generate_all_figures
from src.h3.relationship import generate_h3_relationship_area

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/pipeline_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def check_required_files(region_config) -> bool:
    """Check that all required input files exist."""
    logger.info("Checking required files...")
    
    required_files = [
        ("Graph", Path("data/graphs/maine_walk.graphml")),
        ("Blocks", region_config.get_blocks_path(with_nodes=True)),
        ("Conserved Lands", Path("data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip")),
        ("CEJST", Path("data/cejst-me.zip")),
        ("Relationship File", region_config.get_relationship_file_path()),
    ]
    
    missing_files = []
    for name, path in required_files:
        if not path.exists():
            missing_files.append(f"{name}: {path}")
            logger.error(f"Missing required file: {name} at {path}")
        else:
            logger.info(f"✓ Found {name}: {path}")
    
    if missing_files:
        logger.error(f"Missing {len(missing_files)} required file(s)")
        return False
    
    return True


def run_pipeline(
    state: str = "Maine",
    census_api_key: Optional[str] = None,
    skip_walk_times: bool = False,
    skip_merging: bool = False,
    skip_analysis: bool = False,
    skip_visualization: bool = False,
    skip_h3: bool = False,
) -> bool:
    """Run the complete analysis pipeline.
    
    Args:
        state: State name (default: "Maine")
        census_api_key: Census API key (if None, reads from CENSUS_API_KEY env var)
        skip_walk_times: Skip walk time calculation step
        skip_merging: Skip merging step
        skip_analysis: Skip analysis step
        skip_visualization: Skip visualization step
        skip_h3: Skip H3 processing step
        
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    logger.info("=" * 70)
    logger.info("Access Project - Full Pipeline")
    logger.info("=" * 70)
    
    # Get region configuration
    region_config = get_region_config(state)
    if not region_config:
        logger.error(f"Could not find configuration for state: {state}")
        return False
    
    # Fix data_root to use absolute path from project root
    project_root = Path(__file__).parent.parent
    region_config.data_root = project_root / "data"
    
    logger.info(f"Processing state: {region_config.state_name} (FIPS: {region_config.state_fips})")
    
    # Check required files
    if not check_required_files(region_config):
        return False
    
    # Get Census API key
    if census_api_key is None:
        census_api_key = os.getenv("CENSUS_API_KEY")
    
    if not census_api_key and not skip_analysis:
        logger.error("CENSUS_API_KEY not found. Set it in .env file or pass as argument.")
        logger.error("Skipping analysis step. Set skip_analysis=True to skip this check.")
        return False
    
    # Create output directories
    Path("data/walk_times").mkdir(parents=True, exist_ok=True)
    Path("data/joins").mkdir(parents=True, exist_ok=True)
    Path("figs").mkdir(parents=True, exist_ok=True)
    
    success = True
    
    # Step 1: Calculate walk times
    if not skip_walk_times:
        logger.info("\n" + "=" * 70)
        logger.info("STEP 1: Calculate Walk Times")
        logger.info("=" * 70)
        
        try:
            walk_times_output = Path("data/walk_times/walk_times_block_df.csv")
            
            process_walk_times(
                geography_type="blocks",
                graph_path="data/graphs/maine_walk.graphml",
                geography_path=region_config.get_blocks_path(with_nodes=True),
                conserved_lands_path="data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip",
                output_path=walk_times_output,
                trip_times=DEFAULT_TRIP_TIMES,
                travel_speed=DEFAULT_TRAVEL_SPEED,
                region_config=region_config,
            )
            logger.info(f"✓ Walk times calculated: {walk_times_output}")
        except Exception as e:
            logger.error(f"✗ Error calculating walk times: {e}")
            success = False
    else:
        logger.info("Skipping walk time calculation")
    
    # Step 2: Merge walk times with blocks
    if not skip_merging and success:
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: Merge Walk Times with Blocks")
        logger.info("=" * 70)
        
        try:
            walk_times_path = Path("data/walk_times/walk_times_block_df.csv")
            merge_output = Path("data/joins/block_merge.shp.zip")
            
            merge = merge_walk_times(
                blocks_path=region_config.get_blocks_path(with_nodes=True),
                walk_times_path=walk_times_path,
                conserved_lands_path="data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip",
                output_path=merge_output,
                trip_times=DEFAULT_TRIP_TIMES,
                region_config=region_config,
            )
            logger.info(f"✓ Merged walk times: {merge_output}")
            
            # Dissolve blocks
            dissolve_output = Path("data/joins/block_dissolve.shp.zip")
            dissolved = dissolve_blocks(merge, groupby_col='GEOID20')
            dissolved.to_file(str(dissolve_output))
            logger.info(f"✓ Dissolved blocks: {dissolve_output}")
        except Exception as e:
            logger.error(f"✗ Error merging blocks: {e}")
            success = False
    else:
        logger.info("Skipping merging step")
    
    # Step 3: Create ejblocks with census/CEJST data
    if not skip_analysis and success:
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: Create EJ Blocks with Census/CEJST Data")
        logger.info("=" * 70)
        
        try:
            blocks_path = Path("data/joins/block_dissolve.shp.zip")
            ejblocks_output = Path("data/joins/ejblocks.shp.zip")
            
            create_ejblocks(
                blocks_path=blocks_path,
                census_api_key=census_api_key,
                cejst_path="data/cejst-me.zip",
                relationship_file_path=region_config.get_relationship_file_path(),
                output_path=ejblocks_output,
                state_fips=region_config.state_fips,
                region_config=region_config,
            )
            logger.info(f"✓ Created ejblocks: {ejblocks_output}")
        except Exception as e:
            logger.error(f"✗ Error creating ejblocks: {e}")
            success = False
    else:
        logger.info("Skipping analysis step")
    
    # Step 4: Generate visualizations
    if not skip_visualization and success:
        logger.info("\n" + "=" * 70)
        logger.info("STEP 4: Generate Visualizations")
        logger.info("=" * 70)
        
        try:
            ejblocks_path = Path("data/joins/ejblocks.shp.zip")
            
            generate_all_figures(
                ejblocks_path=ejblocks_path,
                output_dir="figs/",
            )
            logger.info("✓ Visualizations generated")
        except Exception as e:
            logger.error(f"✗ Error generating visualizations: {e}")
            success = False
    else:
        logger.info("Skipping visualization step")
    
    # Step 5: Generate H3 relationship files
    if not skip_h3 and success:
        logger.info("\n" + "=" * 70)
        logger.info("STEP 5: Generate H3 Relationship Files")
        logger.info("=" * 70)
        
        try:
            blocks_path = region_config.get_blocks_path(with_nodes=False)
            h3_output = Path(f"data/blocks/tl_2020_{region_config.state_fips}_tabblock20_h3_{DEFAULT_H3_RESOLUTION_AREA}.csv")
            
            generate_h3_relationship_area(
                blocks_path=blocks_path,
                output_path=h3_output,
                resolution=DEFAULT_H3_RESOLUTION_AREA,
                region_config=region_config,
            )
            logger.info(f"✓ H3 relationship file generated: {h3_output}")
        except Exception as e:
            logger.error(f"✗ Error generating H3 relationship file: {e}")
            success = False
    else:
        logger.info("Skipping H3 processing step")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 70)
    
    if success:
        logger.info("✓ Pipeline completed successfully!")
    else:
        logger.error("✗ Pipeline completed with errors")
    
    return success


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the complete analysis pipeline")
    parser.add_argument(
        "--state",
        default="Maine",
        help="State name (default: Maine)"
    )
    parser.add_argument(
        "--census-api-key",
        help="Census API key (default: read from CENSUS_API_KEY env var)"
    )
    parser.add_argument(
        "--skip-walk-times",
        action="store_true",
        help="Skip walk time calculation step"
    )
    parser.add_argument(
        "--skip-merging",
        action="store_true",
        help="Skip merging step"
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip analysis step (census/CEJST)"
    )
    parser.add_argument(
        "--skip-visualization",
        action="store_true",
        help="Skip visualization step"
    )
    parser.add_argument(
        "--skip-h3",
        action="store_true",
        help="Skip H3 processing step"
    )
    
    args = parser.parse_args()
    
    success = run_pipeline(
        state=args.state,
        census_api_key=args.census_api_key,
        skip_walk_times=args.skip_walk_times,
        skip_merging=args.skip_merging,
        skip_analysis=args.skip_analysis,
        skip_visualization=args.skip_visualization,
        skip_h3=args.skip_h3,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

