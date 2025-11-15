import pandas as pd
import geopandas as gpd
import matplotlib
import h3pandas
from jsonschema import validate
import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    from .config.defaults import DEFAULT_H3_RESOLUTION
    from .config.regions import RegionConfig
except ImportError:
    # Fallback for when imported as standalone module
    DEFAULT_H3_RESOLUTION = 6
    RegionConfig = None

# Merge a dataframe with a relationship file. If no relationship file is provided,
# default to the resolution 6 file.
def h3_merge(df, reln=None, inplace=False, resolution=None, region_config=None):
    """Merge a dataframe with an H3 relationship file.
    
    Args:
        df: DataFrame to merge
        reln: Optional relationship DataFrame (if None, loads from default path)
        inplace: If True, modify df in place
        resolution: H3 resolution (default: 6)
        region_config: Optional RegionConfig for constructing default path
    """
    if reln is None:
        if region_config:
            reln_path = region_config.data_root / "blocks" / f"tl_2020_{region_config.state_fips}_tabblock20_h3_{resolution or DEFAULT_H3_RESOLUTION}.csv"
        else:
            # Default to Maine for backward compatibility
            reln_path = Path('../data/blocks/tl_2020_23_tabblock20_h3_6.csv')
        
        reln = pd.read_csv(str(reln_path), converters={
                'GEOID20':str,
                'h3_fraction':float,
                'h3id':str
            })
    if inplace:
        df = reln.merge(df, 'left', 'GEOID20').set_index(['GEOID20','h3id'])
    else:
        return reln.merge(df, 'left', 'GEOID20').set_index(['GEOID20','h3id'])
    
# Summarize a given column by h3 fraction
def h3_weight(df, col, prefix='h3_'):
    logger.info(f"Creating {prefix+col}")
    df[prefix+col] = df[col] * df['h3_fraction']

# Summarize a given column by h3 fraction, further weighting by population fraction
def h3_weight_pop(df, col, prefix='h3_'):
    logger.info(f"Creating {prefix+col}")
    df[prefix+col] = df[col] * df['P1_001N'] * df['h3_fraction']

# Summarize a given column by h3 fraction
def h3_plot(df, col:str, lognorm=True, inplace=False, **plot_kwargs):
    df = df if inplace else df.copy()
    if not 'h3id' in df.index.names:
        df = h3_merge(df)
    if not col.startswith('h3_'):
        logger.info(f"Interpreting '{col}' as 'h3_{col}'")
        col = 'h3_'+col
    if not col in df.columns:
        h3_weight(df, col[3:])
    hexes = df.filter(regex='^h3_', axis=1).groupby('h3id').sum()
    norm = matplotlib.colors.LogNorm(vmin=1, vmax=hexes[[col]].max()) if lognorm else None 
    return hexes.h3.h3_to_geo_boundary().plot(
            col,
            norm=norm,
            label=col,
            **plot_kwargs
        )

def h3_to_h3t(df, filename=None, inplace=False):
    df = df if inplace else df.copy()
    if not 'h3id' in df.index.names:
        df = h3_merge(df)
    df = df.reset_index()
    df = df.where(pd.notnull(df), 0)
    json_dict = {
        "metadata": {
            "note": "created with h3utils.py"
        },
        "cells": df.drop(columns='geometry').to_dict('records')
    }
    validate(json_dict, _schema)
    if filename:
        # Serializing json
        json_object = json.dumps(json_dict, indent=4, allow_nan=False, skipkeys=True)
        
        # Writing to sample.json
        with open(filename, "w") as outfile:
            outfile.write(json_object)
        
        return True
    return json_dict

_schema = {
    "$id": "https://inspide.com/h3j.schema.json",
    "$schema": "http://json-schema.org/draft/2020-12/schema#",
    # "$ref": "#/definitions/H3J",
    "title": "H3J",
    "description": "A compact way to deliver H3 data",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "metadata": {
            "type": "object"
        },
        "cells": {
            "type": "array",
            "items": {
                "$ref": "#/$defs/cell"
            }
        }
    },
    "required": [
        "cells"
    ],
    "$defs": {
        "cell":{
            "type": "object",
            "properties": {
                "h3id": {
                    "type": "string"
                }
            },
            "required": [
                "h3id"
            ],
            "additionalProperties": {}
        }
    }
}