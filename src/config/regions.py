"""Region and state configuration for multi-state support."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, Union


@dataclass
class RegionConfig:
    """Configuration for a state or region.
    
    Attributes:
        state_fips: State FIPS code (e.g., "23" for Maine)
        state_abbrev: State abbreviation (e.g., "ME")
        state_name: Full state name (e.g., "Maine")
        data_root: Root directory for data files (default: "../data")
        blocks_pattern: Pattern for block shapefile names
        tracts_pattern: Pattern for tract shapefile names
        relationship_file_pattern: Pattern for Census relationship files
    """
    state_fips: str
    state_abbrev: str
    state_name: str
    data_root: Path = Path("../data")
    blocks_pattern: str = "tl_2020_{state_fips}_tabblock20.zip"
    tracts_pattern: str = "tl_2022_{state_fips}_tract.zip"
    relationship_file_pattern: str = "tab2010_tab2020_st{state_fips}_{state_abbrev_lower}.txt"
    
    def get_blocks_path(self, with_nodes: bool = False) -> Path:
        """Get path to blocks shapefile.
        
        Args:
            with_nodes: If True, append '_with_nodes' to filename
            
        Returns:
            Path to blocks shapefile
        """
        filename = self.blocks_pattern.format(state_fips=self.state_fips)
        if with_nodes:
            filename = filename.replace(".zip", "_with_nodes.shp.zip")
        return self.data_root / "blocks" / filename
    
    def get_tracts_path(self, with_nodes: bool = False) -> Path:
        """Get path to tracts shapefile.
        
        Args:
            with_nodes: If True, append '_with_nodes' to filename
            
        Returns:
            Path to tracts shapefile
        """
        filename = self.tracts_pattern.format(state_fips=self.state_fips)
        if with_nodes:
            filename = filename.replace(".zip", "_with_nodes.shp.zip")
        return self.data_root / "tracts" / filename
    
    def get_relationship_file_path(self) -> Path:
        """Get path to Census relationship file.
        
        Returns:
            Path to relationship file
        """
        filename = self.relationship_file_pattern.format(
            state_fips=self.state_fips,
            state_abbrev_lower=self.state_abbrev.lower()
        )
        return self.data_root / filename


# New England states configuration
NEW_ENGLAND_STATES: Dict[str, RegionConfig] = {
    "Maine": RegionConfig(
        state_fips="23",
        state_abbrev="ME",
        state_name="Maine",
    ),
    "New Hampshire": RegionConfig(
        state_fips="33",
        state_abbrev="NH",
        state_name="New Hampshire",
    ),
    "Vermont": RegionConfig(
        state_fips="50",
        state_abbrev="VT",
        state_name="Vermont",
    ),
    "Massachusetts": RegionConfig(
        state_fips="25",
        state_abbrev="MA",
        state_name="Massachusetts",
    ),
    "Rhode Island": RegionConfig(
        state_fips="44",
        state_abbrev="RI",
        state_name="Rhode Island",
    ),
    "Connecticut": RegionConfig(
        state_fips="09",
        state_abbrev="CT",
        state_name="Connecticut",
    ),
}


def get_region_config(state_name_or_fips: Union[str, int]) -> Optional[RegionConfig]:
    """Get region configuration for a state.
    
    Args:
        state_name_or_fips: State name (e.g., "Maine") or FIPS code (e.g., "23" or 23)
        
    Returns:
        RegionConfig if found, None otherwise
    """
    # Convert to string if int
    if isinstance(state_name_or_fips, int):
        state_name_or_fips = str(state_name_or_fips).zfill(2)
    
    # Try exact name match
    if state_name_or_fips in NEW_ENGLAND_STATES:
        return NEW_ENGLAND_STATES[state_name_or_fips]
    
    # Try case-insensitive name match
    state_name_or_fips_lower = state_name_or_fips.lower()
    for name, config in NEW_ENGLAND_STATES.items():
        if name.lower() == state_name_or_fips_lower:
            return config
    
    # Try FIPS code match
    for config in NEW_ENGLAND_STATES.values():
        if config.state_fips == state_name_or_fips:
            return config
        if config.state_abbrev.upper() == state_name_or_fips.upper():
            return config
    
    return None


def get_multi_state_config(state_list: List[Union[str, int]]) -> List[RegionConfig]:
    """Get region configurations for multiple states.
    
    Args:
        state_list: List of state names or FIPS codes
        
    Returns:
        List of RegionConfig objects
    """
    configs = []
    for state in state_list:
        config = get_region_config(state)
        if config:
            configs.append(config)
        else:
            raise ValueError(f"Could not find configuration for state: {state}")
    return configs

