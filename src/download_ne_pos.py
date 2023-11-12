"""
Download the New England Protected Open Space Shapefile
"""
import subprocess

return_code = subprocess.call(
    [
        "wget",
        "-q",
        "-nc",
        "-P",
        "data/Harvard/",
        "https://zenodo.org/records/7764284/files/NE_POS_v1-2_SHP.zip?download=1",
    ]
)
if return_code != 0:
    print("Error downloading New England Protected Open Space Shapefile.")
    exit(1)
