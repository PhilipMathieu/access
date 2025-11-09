"""Tests for merging module."""

import pytest
import pandas as pd
import geopandas as gpd
from pathlib import Path
from unittest.mock import patch, MagicMock

from merging.blocks import (
    merge_walk_times,
    create_trip_time_columns,
    dissolve_blocks,
)
from merging.analysis import (
    fetch_census_data,
    process_cejst_data,
    calculate_demographics,
    create_ejblocks,
)


class TestBlocks:
    """Tests for blocks merging functions."""
    
    def test_create_trip_time_columns(self, sample_merged_blocks_gdf):
        """Test creating trip time columns."""
        # Get the actual number of rows
        n_rows = len(sample_merged_blocks_gdf)
        
        # Add trip_time column if not present
        if "trip_time" not in sample_merged_blocks_gdf.columns:
            sample_merged_blocks_gdf["trip_time"] = [5, 10, 15, 20, 5][:n_rows]
        
        # Add CALC_AC column if not present
        if "CALC_AC" not in sample_merged_blocks_gdf.columns:
            sample_merged_blocks_gdf["CALC_AC"] = [10.5, 25.3, 15.0, 20.0, 12.0][:n_rows]
        
        trip_times = [5, 10, 15, 20]
        result = create_trip_time_columns(sample_merged_blocks_gdf, trip_times)
        
        # Check that AC_* columns were created
        for time in trip_times:
            col_name = f"AC_{time}"
            assert col_name in result.columns
    
    def test_create_trip_time_columns_values(self, sample_merged_blocks_gdf):
        """Test trip time column values."""
        # Get the actual number of rows
        n_rows = len(sample_merged_blocks_gdf)
        
        # Setup data
        sample_merged_blocks_gdf["trip_time"] = [5, 10, 15, 20, 5][:n_rows]
        sample_merged_blocks_gdf["CALC_AC"] = [10.5, 25.3, 15.0, 20.0, 12.0][:n_rows]
        
        trip_times = [5, 10, 15, 20]
        result = create_trip_time_columns(sample_merged_blocks_gdf, trip_times)
        
        # Check that AC_5 has value only where trip_time == 5
        ac_5_values = result["AC_5"].dropna()
        assert len(ac_5_values) > 0
        assert all(result.loc[result["AC_5"].notna(), "trip_time"] == 5)
    
    def test_dissolve_blocks(self, sample_merged_blocks_gdf):
        """Test dissolving blocks."""
        # Get the actual number of rows
        n_rows = len(sample_merged_blocks_gdf)
        
        # Add a groupby column
        if "GEOID20" not in sample_merged_blocks_gdf.columns:
            geoids = ["230010001001", "230010001001", "230010001002", "230010001002", "230010001003"]
            sample_merged_blocks_gdf["GEOID20"] = geoids[:n_rows]
        
        # Add numeric column for aggregation
        if "CALC_AC" not in sample_merged_blocks_gdf.columns:
            calc_ac = [10.5, 25.3, 15.0, 20.0, 12.0]
            sample_merged_blocks_gdf["CALC_AC"] = calc_ac[:n_rows]
        
        result = dissolve_blocks(sample_merged_blocks_gdf, groupby_col="GEOID20")
        
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) <= len(sample_merged_blocks_gdf)
    
    @patch("merging.blocks.gpd.read_parquet")
    @patch("merging.blocks.pd.read_parquet")
    def test_merge_walk_times_parquet(
        self,
        mock_pd_read,
        mock_gpd_read,
        sample_blocks_gdf,
        sample_conserved_lands_gdf,
        sample_walk_times_df,
        temp_dir,
    ):
        """Test merging walk times with parquet files."""
        mock_gpd_read.side_effect = [sample_blocks_gdf, sample_conserved_lands_gdf]
        mock_pd_read.return_value = sample_walk_times_df
        
        output_path = temp_dir / "merged.parquet"
        
        result = merge_walk_times(
            blocks_path="blocks.parquet",
            walk_times_path="walk_times.parquet",
            conserved_lands_path="lands.parquet",
            output_path=output_path,
        )
        
        assert isinstance(result, gpd.GeoDataFrame)
        assert output_path.exists()
    
    @patch("merging.blocks.gpd.read_file")
    @patch("merging.blocks.pd.read_csv")
    def test_merge_walk_times_csv(
        self,
        mock_pd_read,
        mock_gpd_read,
        sample_blocks_gdf,
        sample_conserved_lands_gdf,
        sample_walk_times_df,
        temp_dir,
    ):
        """Test merging walk times with CSV/shapefile files."""
        mock_gpd_read.side_effect = [sample_blocks_gdf, sample_conserved_lands_gdf]
        mock_pd_read.return_value = sample_walk_times_df
        
        output_path = temp_dir / "merged.shp"
        
        result = merge_walk_times(
            blocks_path="blocks.shp",
            walk_times_path="walk_times.csv",
            conserved_lands_path="lands.shp",
            output_path=output_path,
        )
        
        assert isinstance(result, gpd.GeoDataFrame)


class TestAnalysis:
    """Tests for analysis merging functions."""
    
    @patch("merging.analysis.Census")
    def test_fetch_census_data(self, mock_census_class, mock_census_api):
        """Test fetching census data."""
        mock_census_instance = MagicMock()
        # Use get method instead of state_county_block (which doesn't exist)
        mock_census_instance.pl.get.return_value = [
            {
                "GEO_ID": "1000000US230010001001",
                "P1_001N": 100,
                "P1_003N": 80,
                "P2_001N": 100,
                "P2_002N": 5,
            }
        ]
        mock_census_class.return_value = mock_census_instance
        
        result = fetch_census_data(
            api_key="test_key",
            state_fips="23",
            fields=["P1_001N", "P1_003N"],
        )
        
        assert isinstance(result, pd.DataFrame)
        assert "GEOID20" in result.columns
        assert len(result) > 0
    
    def test_calculate_demographics(self, sample_census_data):
        """Test calculating demographic percentages."""
        result = calculate_demographics(sample_census_data)
        
        assert "white_per" in result.columns
        assert "hisp_per" in result.columns
        assert "white_50" in result.columns
        assert "hisp_75" in result.columns
        
        # Check calculations
        assert all(result["white_per"] == result["P1_003N"] / result["P1_001N"])
        assert all(result["hisp_per"] == result["P2_002N"] / result["P2_001N"])
    
    def test_calculate_demographics_percentiles(self, sample_census_data):
        """Test demographic percentile calculations."""
        result = calculate_demographics(sample_census_data)
        
        # white_50 should be boolean
        assert result["white_50"].dtype == bool
        # hisp_75 should be boolean
        assert result["hisp_75"].dtype == bool
    
    @patch("merging.analysis.gpd.read_parquet")
    @patch("merging.analysis.gpd.read_file")
    @patch("merging.analysis.pd.read_csv")
    def test_process_cejst_data(
        self,
        mock_csv_read,
        mock_gpd_read_file,
        mock_gpd_read_parquet,
        sample_cejst_data,
        sample_relationship_file,
        temp_dir,
    ):
        """Test processing CEJST data."""
        # Mock parquet reading
        mock_gpd_read_parquet.return_value = sample_cejst_data
        # Mock file reading (fallback)
        mock_gpd_read_file.return_value = sample_cejst_data
        mock_csv_read.return_value = sample_relationship_file
        
        output_path = temp_dir / "cejst_block.parquet"
        
        result = process_cejst_data(
            cejst_path="cejst.parquet",
            relationship_file_path="relationship.txt",
            output_path=output_path,
        )
        
        assert isinstance(result, pd.DataFrame)
        assert "TC" in result.columns
        assert "CC" in result.columns
        # GEOID20 should be in the index (from groupby)
        assert result.index.name == "GEOID20" or "GEOID20" in result.columns
    
    @patch("merging.analysis.fetch_census_data")
    @patch("merging.analysis.process_cejst_data")
    @patch("merging.analysis.gpd.read_parquet")
    @patch("merging.analysis.gpd.read_file")
    def test_create_ejblocks(
        self,
        mock_gpd_read_file,
        mock_gpd_read_parquet,
        mock_process_cejst,
        mock_fetch_census,
        sample_merged_blocks_gdf,
        sample_census_data,
        sample_cejst_data,
        temp_dir,
    ):
        """Test creating ejblocks dataset."""
        # Create a copy of the merged blocks for testing
        test_blocks = sample_merged_blocks_gdf.copy()
        n_rows = len(test_blocks)
        
        # Always ensure GEOID20 exists (it should from sample_blocks_gdf)
        # Map osmid to GEOID20 based on sample_blocks_gdf structure
        # sample_blocks_gdf has osmid [1, 2, 3] and GEOID20 ["230010001001", "230010001002", "230010001003"]
        geoid_map = {1: "230010001001", 2: "230010001002", 3: "230010001003"}
        test_blocks["GEOID20"] = test_blocks["osmid"].map(geoid_map)
        # Fill any missing values
        test_blocks["GEOID20"] = test_blocks["GEOID20"].fillna("230010001001")
        
        # Always ensure ALAND20 exists
        # Map osmid to ALAND20 based on sample_blocks_gdf structure
        aland_map = {1: 1000000, 2: 2000000, 3: 1500000}
        test_blocks["ALAND20"] = test_blocks["osmid"].map(aland_map)
        # Fill any missing values
        test_blocks["ALAND20"] = test_blocks["ALAND20"].fillna(1000000)
        
        # Setup mocks
        mock_gpd_read_parquet.return_value = test_blocks
        mock_gpd_read_file.return_value = test_blocks
        
        # Ensure census data has matching GEOID20 values
        # First, get the unique GEOID20 values from blocks
        unique_geoids = list(test_blocks["GEOID20"].unique())
        
        # Create census data with matching GEOID20 values
        census_data = sample_census_data.copy()
        # Extend census data to match all unique GEOIDs
        while len(census_data) < len(unique_geoids):
            # Duplicate rows as needed
            new_row = census_data.iloc[len(census_data) % len(census_data)].copy()
            census_data = pd.concat([census_data, pd.DataFrame([new_row])], ignore_index=True)
        # Update GEOID20 to match blocks
        census_data["GEOID20"] = unique_geoids[:len(census_data)]
        mock_fetch_census.return_value = census_data
        
        # Create processed CEJST data with GEOID20 index
        cejst_block = pd.DataFrame({
            "TC": [1, 0],
            "CC": [1, 0],
        }, index=["230010001001", "230010001002"])
        mock_process_cejst.return_value = cejst_block
        
        output_path = temp_dir / "ejblocks.parquet"
        
        result = create_ejblocks(
            blocks_path="blocks.parquet",
            census_api_key="test_key",
            cejst_path="cejst.shp",
            relationship_file_path="relationship.txt",
            output_path=output_path,
            state_fips="23",
        )
        
        assert isinstance(result, gpd.GeoDataFrame)
        assert output_path.exists()

