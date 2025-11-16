#!/bin/bash
# Run the complete analysis pipeline with updated data

set -e  # Exit on error

cd "$(dirname "$0")"
source .venv/bin/activate

# Add project root to Python path for imports
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "============================================================"
echo "Access Project - Full Pipeline"
echo "============================================================"

# Check for Census API key
if [ -z "$CENSUS_API_KEY" ] && [ ! -f .env ]; then
    echo "Warning: CENSUS_API_KEY not set. Analysis step will be skipped."
    SKIP_ANALYSIS="true"
else
    SKIP_ANALYSIS="false"
fi

# Step 1: Calculate walk times
echo ""
echo "============================================================"
echo "STEP 1: Calculate Walk Times"
echo "============================================================"
(cd src && python -c "
from config.regions import get_region_config
from config.defaults import DEFAULT_TRIP_TIMES, DEFAULT_TRAVEL_SPEED
from walk_times.calculate import process_walk_times
from pathlib import Path
import os

os.chdir('..')  # Change back to project root
region_config = get_region_config('Maine')
Path('data/walk_times').mkdir(parents=True, exist_ok=True)

process_walk_times(
    geography_type='blocks',
    graph_path='data/graphs/maine_walk.graphml',
    geography_path=region_config.get_blocks_path(with_nodes=True),
    conserved_lands_path='data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip',
    output_path='data/walk_times/walk_times_block_df.csv',
    trip_times=DEFAULT_TRIP_TIMES,
    travel_speed=DEFAULT_TRAVEL_SPEED,
    region_config=region_config,
)
print('✓ Walk times calculated')
")

# Step 2: Merge walk times with blocks
echo ""
echo "============================================================"
echo "STEP 2: Merge Walk Times with Blocks"
echo "============================================================"
(cd src && python -c "
from config.regions import get_region_config
from config.defaults import DEFAULT_TRIP_TIMES
from merging.blocks import merge_walk_times, dissolve_blocks
from pathlib import Path
import os

os.chdir('..')  # Change back to project root
region_config = get_region_config('Maine')
Path('data/joins').mkdir(parents=True, exist_ok=True)

merge = merge_walk_times(
    blocks_path=region_config.get_blocks_path(with_nodes=True),
    walk_times_path='data/walk_times/walk_times_block_df.csv',
    conserved_lands_path='data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip',
    output_path='data/joins/block_merge.shp.zip',
    trip_times=DEFAULT_TRIP_TIMES,
    region_config=region_config,
)
print('✓ Merged walk times')

dissolved = dissolve_blocks(merge, groupby_col='GEOID20')
dissolved.to_file('data/joins/block_dissolve.shp.zip')
print('✓ Dissolved blocks')
")

# Step 3: Create ejblocks (if API key available)
if [ "$SKIP_ANALYSIS" = "false" ]; then
    echo ""
    echo "============================================================"
    echo "STEP 3: Create EJ Blocks with Census/CEJST Data"
    echo "============================================================"
    (cd src && python -c "
import os
os.chdir('..')  # Change back to project root
from dotenv import load_dotenv
load_dotenv()
from config.regions import get_region_config
from merging.analysis import create_ejblocks
from pathlib import Path

region_config = get_region_config('Maine')
census_api_key = os.getenv('CENSUS_API_KEY')

if not census_api_key:
    print('Error: CENSUS_API_KEY not found')
    exit(1)

create_ejblocks(
    blocks_path='data/joins/block_dissolve.shp.zip',
    census_api_key=census_api_key,
    cejst_path='data/cejst-me.zip',
    relationship_file_path=region_config.get_relationship_file_path(),
    output_path='data/joins/ejblocks.shp.zip',
    state_fips=region_config.state_fips,
    region_config=region_config,
)
print('✓ Created ejblocks')
")
else
    echo ""
    echo "Skipping analysis step (Census API key not available)"
fi

# Step 4: Generate visualizations
echo ""
echo "============================================================"
echo "STEP 4: Generate Visualizations"
echo "============================================================"
(cd src && python -c "
import os
os.chdir('..')  # Change back to project root
from visualization.figures import generate_all_figures
from pathlib import Path

Path('figs').mkdir(parents=True, exist_ok=True)

try:
    generate_all_figures(
        ejblocks_path='data/joins/ejblocks.shp.zip',
        output_dir='figs/',
    )
    print('✓ Visualizations generated')
except FileNotFoundError as e:
    print(f'⚠ Skipping visualizations: {e}')
")

# Step 5: Generate H3 relationship files
echo ""
echo "============================================================"
echo "STEP 5: Generate H3 Relationship Files"
echo "============================================================"
(cd src && python -c "
import os
os.chdir('..')  # Change back to project root
from config.regions import get_region_config
from config.defaults import DEFAULT_H3_RESOLUTION_AREA
from h3_utils.relationship import generate_h3_relationship_area
from pathlib import Path

region_config = get_region_config('Maine')
h3_output = Path(f'data/blocks/tl_2020_{region_config.state_fips}_tabblock20_h3_{DEFAULT_H3_RESOLUTION_AREA}.csv')

generate_h3_relationship_area(
    blocks_path=region_config.get_blocks_path(with_nodes=False),
    output_path=h3_output,
    resolution=DEFAULT_H3_RESOLUTION_AREA,
    region_config=region_config,
)
print(f'✓ H3 relationship file generated: {h3_output}')
")

echo ""
echo "============================================================"
echo "Pipeline completed successfully!"
echo "============================================================"
