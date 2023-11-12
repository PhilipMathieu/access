"""
Download shapefiles from the US Census Bureau for all states. Shapefiles are
at the Census Block resolution for the 2020 Census.
"""
import subprocess
from tqdm.auto import tqdm

from utils import STATES

# loop through the list of states
for state in tqdm(STATES, desc="States"):
    # download the shapefile to data/US Census/ from
    # https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{FIPS}_tabblock20.zip
    # where {FIPS} is the FIPS code for the state

    tqdm.write(f"Downloading {state['name']}...")
    return_code = subprocess.call(
        [
            "wget",
            "-q",
            "-nc",
            "-P",
            "data/US Census/",
            f"https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{state['FIPS']}_tabblock20.zip",
        ]
    )
    if return_code != 0:
        tqdm.write(f"Error downloading {state['name']}.")
        continue
