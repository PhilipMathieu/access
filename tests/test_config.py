"""Tests for config module."""

import pytest
from pathlib import Path

from config.defaults import (
    DEFAULT_TRIP_TIMES,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_H3_RESOLUTIONS,
    DEFAULT_H3_RESOLUTION,
    DEFAULT_CRS,
    DEFAULT_CENSUS_FIELDS,
    DEFAULT_CENSUS_YEAR,
)
from config.regions import (
    RegionConfig,
    get_region_config,
    get_multi_state_config,
    NEW_ENGLAND_STATES,
)


class TestDefaults:
    """Tests for default configuration values."""
    
    def test_default_trip_times(self):
        """Test default trip times."""
        assert isinstance(DEFAULT_TRIP_TIMES, list)
        assert len(DEFAULT_TRIP_TIMES) > 0
        assert all(isinstance(t, int) for t in DEFAULT_TRIP_TIMES)
        assert all(t > 0 for t in DEFAULT_TRIP_TIMES)
    
    def test_default_travel_speed(self):
        """Test default travel speed."""
        assert isinstance(DEFAULT_TRAVEL_SPEED, float)
        assert DEFAULT_TRAVEL_SPEED > 0
    
    def test_default_h3_resolutions(self):
        """Test default H3 resolutions."""
        assert isinstance(DEFAULT_H3_RESOLUTIONS, list)
        assert len(DEFAULT_H3_RESOLUTIONS) > 0
        assert all(isinstance(r, int) for r in DEFAULT_H3_RESOLUTIONS)
    
    def test_default_crs(self):
        """Test default CRS."""
        assert isinstance(DEFAULT_CRS, str)
        assert DEFAULT_CRS == "EPSG:3857"
    
    def test_default_census_fields(self):
        """Test default census fields."""
        assert isinstance(DEFAULT_CENSUS_FIELDS, list)
        assert len(DEFAULT_CENSUS_FIELDS) > 0
        assert all(isinstance(f, str) for f in DEFAULT_CENSUS_FIELDS)
    
    def test_default_census_year(self):
        """Test default census year."""
        assert isinstance(DEFAULT_CENSUS_YEAR, int)
        assert DEFAULT_CENSUS_YEAR > 2000


class TestRegionConfig:
    """Tests for RegionConfig class."""
    
    def test_region_config_creation(self):
        """Test creating a RegionConfig."""
        config = RegionConfig(
            state_fips="23",
            state_abbrev="ME",
            state_name="Maine",
        )
        
        assert config.state_fips == "23"
        assert config.state_abbrev == "ME"
        assert config.state_name == "Maine"
    
    def test_get_blocks_path(self, region_config_maine):
        """Test getting blocks path."""
        path = region_config_maine.get_blocks_path()
        
        assert isinstance(path, Path)
        assert "tabblock20" in str(path)
        assert region_config_maine.state_fips in str(path)
    
    def test_get_blocks_path_with_nodes(self, region_config_maine):
        """Test getting blocks path with nodes."""
        path = region_config_maine.get_blocks_path(with_nodes=True)
        
        assert isinstance(path, Path)
        assert "_with_nodes" in str(path)
    
    def test_get_tracts_path(self, region_config_maine):
        """Test getting tracts path."""
        path = region_config_maine.get_tracts_path()
        
        assert isinstance(path, Path)
        assert "tract" in str(path)
        assert region_config_maine.state_fips in str(path)
    
    def test_get_tracts_path_with_nodes(self, region_config_maine):
        """Test getting tracts path with nodes."""
        path = region_config_maine.get_tracts_path(with_nodes=True)
        
        assert isinstance(path, Path)
        assert "_with_nodes" in str(path)
    
    def test_get_relationship_file_path(self, region_config_maine):
        """Test getting relationship file path."""
        path = region_config_maine.get_relationship_file_path()
        
        assert isinstance(path, Path)
        assert region_config_maine.state_fips in str(path)
        assert region_config_maine.state_abbrev.lower() in str(path)


class TestGetRegionConfig:
    """Tests for get_region_config function."""
    
    def test_get_region_config_by_name(self):
        """Test getting region config by state name."""
        config = get_region_config("Maine")
        
        assert config is not None
        assert config.state_name == "Maine"
        assert config.state_fips == "23"
    
    def test_get_region_config_by_name_case_insensitive(self):
        """Test getting region config by state name (case insensitive)."""
        config = get_region_config("maine")
        
        assert config is not None
        assert config.state_name == "Maine"
    
    def test_get_region_config_by_fips_string(self):
        """Test getting region config by FIPS code (string)."""
        config = get_region_config("23")
        
        assert config is not None
        assert config.state_fips == "23"
    
    def test_get_region_config_by_fips_int(self):
        """Test getting region config by FIPS code (int)."""
        config = get_region_config(23)
        
        assert config is not None
        assert config.state_fips == "23"
    
    def test_get_region_config_by_abbrev(self):
        """Test getting region config by state abbreviation."""
        config = get_region_config("ME")
        
        assert config is not None
        assert config.state_abbrev == "ME"
    
    def test_get_region_config_not_found(self):
        """Test getting region config for non-existent state."""
        config = get_region_config("XX")
        
        assert config is None
    
    def test_get_multi_state_config(self):
        """Test getting multiple region configs."""
        configs = get_multi_state_config(["Maine", "New Hampshire"])
        
        assert len(configs) == 2
        assert configs[0].state_name == "Maine"
        assert configs[1].state_name == "New Hampshire"
    
    def test_get_multi_state_config_invalid(self):
        """Test getting multiple region configs with invalid state."""
        with pytest.raises(ValueError):
            get_multi_state_config(["Maine", "InvalidState"])


class TestNewEnglandStates:
    """Tests for NEW_ENGLAND_STATES configuration."""
    
    def test_new_england_states_count(self):
        """Test that all New England states are included."""
        assert len(NEW_ENGLAND_STATES) == 6
    
    def test_new_england_states_names(self):
        """Test that all expected states are present."""
        expected_states = [
            "Maine",
            "New Hampshire",
            "Vermont",
            "Massachusetts",
            "Rhode Island",
            "Connecticut",
        ]
        
        for state in expected_states:
            assert state in NEW_ENGLAND_STATES
    
    def test_new_england_states_fips(self):
        """Test that FIPS codes are correct."""
        expected_fips = {
            "Maine": "23",
            "New Hampshire": "33",
            "Vermont": "50",
            "Massachusetts": "25",
            "Rhode Island": "44",
            "Connecticut": "09",
        }
        
        for state, fips in expected_fips.items():
            assert NEW_ENGLAND_STATES[state].state_fips == fips

