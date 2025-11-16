"""H3J format conversion utilities."""

import json
import logging
from pathlib import Path

import pandas as pd
from jsonschema import validate

from config.defaults import DEFAULT_H3_RESOLUTION
from config.regions import RegionConfig

from .joins import h3_join

logger = logging.getLogger(__name__)

# H3J schema
_H3J_SCHEMA = {
    "$id": "https://inspide.com/h3j.schema.json",
    "$schema": "http://json-schema.org/draft/2020-12/schema#",
    "title": "H3J",
    "description": "A compact way to deliver H3 data",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "metadata": {"type": "object"},
        "cells": {"type": "array", "items": {"$ref": "#/$defs/cell"}},
    },
    "required": ["cells"],
    "$defs": {
        "cell": {
            "type": "object",
            "properties": {"h3id": {"type": "string"}},
            "required": ["h3id"],
            "additionalProperties": {},
        }
    },
}


def convert_to_h3j(
    data_path: str | Path,
    output_path: str | Path,
    relationship_path: str | Path | None = None,
    resolution: int = DEFAULT_H3_RESOLUTION,
    region_config: RegionConfig | None = None,
) -> dict:
    """Convert data to H3J format.

    Args:
        data_path: Path to data shapefile or CSV
        output_path: Path to save H3J JSON file
        relationship_path: Optional path to H3 relationship CSV file
        resolution: H3 resolution (used if relationship_path not provided)
        region_config: Optional region configuration (used to construct default path)

    Returns:
        Dictionary with H3J data structure
    """
    logger.info("Converting data to H3J format")

    # Join data with H3 relationship file
    df = h3_join(data_path, relationship_path, resolution, region_config)

    # Reset index to get h3id as column
    df = df.reset_index()

    # Replace NaN with 0
    df = df.where(pd.notnull(df), 0)

    # Create JSON structure
    json_dict = {
        "metadata": {"note": "created with h3_utils.h3j module"},
        "cells": df.drop(columns="geometry", errors="ignore").to_dict("records"),
    }

    # Validate schema
    logger.info("Validating H3J schema")
    validate(json_dict, _H3J_SCHEMA)

    # Save to file
    logger.info(f"Saving H3J file to {output_path}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as outfile:
        json.dumps(json_dict, indent=4, allow_nan=False, skipkeys=True)
        json.dump(json_dict, outfile, indent=4, allow_nan=False, skipkeys=True)

    return json_dict
