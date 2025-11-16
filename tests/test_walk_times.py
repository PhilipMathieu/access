"""Tests for walk_times module."""

from unittest.mock import patch

import pandas as pd

from walk_times.calculate import (
    add_time_attributes,
    calculate_walk_times,
    get_rustworkx_graph,
    load_graph,
    process_walk_times,
)
from walk_times.graph_utils import (
    convert_node_ids_to_rx_indices,
    convert_rx_indices_to_node_ids,
    get_node_mapping,
    nx_to_rustworkx,
)


class TestGraphUtils:
    """Tests for graph_utils module."""

    def test_get_node_mapping(self, sample_graph):
        """Test node mapping creation."""
        nx_id_to_rx_idx, rx_idx_to_nx_id = get_node_mapping(sample_graph)

        assert len(nx_id_to_rx_idx) == 4
        assert len(rx_idx_to_nx_id) == 4
        assert nx_id_to_rx_idx[1] == 0
        assert rx_idx_to_nx_id[0] == 1

        # Test bidirectional mapping
        for nx_id, rx_idx in nx_id_to_rx_idx.items():
            assert rx_idx_to_nx_id[rx_idx] == nx_id

    def test_nx_to_rustworkx(self, sample_graph):
        """Test NetworkX to rustworkx conversion."""
        rx_graph, nx_id_to_rx_idx, rx_idx_to_nx_id = nx_to_rustworkx(
            sample_graph, weight_attr="time"
        )

        assert rx_graph.num_nodes() == 4
        assert rx_graph.num_edges() == 4
        assert len(nx_id_to_rx_idx) == 4
        assert len(rx_idx_to_nx_id) == 4

    def test_nx_to_rustworkx_missing_weight(self, sample_graph):
        """Test conversion with missing weight attributes."""
        # Remove time attribute from one edge
        sample_graph[1][2][0]["time"] = None

        rx_graph, _, _ = nx_to_rustworkx(sample_graph, weight_attr="time", default_weight=2.0)

        # Should still convert successfully with default weight
        assert rx_graph.num_edges() == 4

    def test_convert_node_ids_to_rx_indices(self, sample_rustworkx_graph):
        """Test converting node IDs to rustworkx indices."""
        _, nx_id_to_rx_idx, _ = sample_rustworkx_graph

        node_ids = [1, 2, 3]
        rx_indices = convert_node_ids_to_rx_indices(node_ids, nx_id_to_rx_idx)

        assert len(rx_indices) == 3
        assert rx_indices[0] == nx_id_to_rx_idx[1]
        assert rx_indices[1] == nx_id_to_rx_idx[2]
        assert rx_indices[2] == nx_id_to_rx_idx[3]

    def test_convert_node_ids_to_rx_indices_missing(self, sample_rustworkx_graph):
        """Test conversion with missing node IDs."""
        _, nx_id_to_rx_idx, _ = sample_rustworkx_graph

        node_ids = [1, 999, 3]  # 999 doesn't exist
        rx_indices = convert_node_ids_to_rx_indices(node_ids, nx_id_to_rx_idx)

        # Function skips missing nodes, so only returns indices for nodes that exist
        assert len(rx_indices) == 2  # Only nodes 1 and 3 exist
        assert rx_indices[0] == nx_id_to_rx_idx[1]
        assert rx_indices[1] == nx_id_to_rx_idx[3]

    def test_convert_rx_indices_to_node_ids(self, sample_rustworkx_graph):
        """Test converting rustworkx indices to node IDs."""
        _, _, rx_idx_to_nx_id = sample_rustworkx_graph

        rx_indices = [0, 1, 2]
        nx_ids = convert_rx_indices_to_node_ids(rx_indices, rx_idx_to_nx_id)

        assert len(nx_ids) == 3
        assert nx_ids[0] == rx_idx_to_nx_id[0]
        assert nx_ids[1] == rx_idx_to_nx_id[1]
        assert nx_ids[2] == rx_idx_to_nx_id[2]


class TestCalculate:
    """Tests for calculate module."""

    @patch("walk_times.calculate.ox.load_graphml")
    @patch("walk_times.calculate.ox.project_graph")
    def test_load_graph(self, mock_project, mock_load, sample_graph):
        """Test loading and projecting graph."""
        mock_load.return_value = sample_graph
        mock_project.return_value = sample_graph

        result = load_graph("dummy_path.graphml", crs="EPSG:3857")

        mock_load.assert_called_once()
        mock_project.assert_called_once()
        assert result == sample_graph

    def test_add_time_attributes(self, sample_graph):
        """Test adding time attributes to graph edges."""
        # Remove time attributes
        for _u, _v, _key, data in sample_graph.edges(data=True, keys=True):
            if "time" in data:
                del data["time"]

        add_time_attributes(sample_graph, travel_speed=4.5)

        # Check that time attributes were added
        for _u, _v, _key, data in sample_graph.edges(data=True, keys=True):
            assert "time" in data
            assert data["time"] > 0

    def test_add_time_attributes_calculation(self, sample_graph):
        """Test time attribute calculation."""
        # Clear time attributes
        for _u, _v, _key, data in sample_graph.edges(data=True, keys=True):
            if "time" in data:
                del data["time"]

        add_time_attributes(sample_graph, travel_speed=4.5)

        # Check calculation: length (m) / (speed km/h * 1000 / 60)
        # For 100m at 4.5 km/h: 100 / (4.5 * 1000 / 60) = 100 / 75 = 1.33 minutes
        edge_data = sample_graph[1][2][0]
        if "length" in edge_data:
            expected_time = edge_data["length"] / (4.5 * 1000 / 60)
            assert abs(edge_data["time"] - expected_time) < 0.01

    def test_get_rustworkx_graph(self, sample_graph):
        """Test getting rustworkx graph with caching."""
        # First call should convert
        rx_graph1, nx_id_to_rx_idx1, rx_idx_to_nx_id1 = get_rustworkx_graph(
            sample_graph, cache_key="test"
        )

        # Second call should use cache
        rx_graph2, nx_id_to_rx_idx2, rx_idx_to_nx_id2 = get_rustworkx_graph(
            sample_graph, cache_key="test"
        )

        assert rx_graph1.num_nodes() == rx_graph2.num_nodes()
        assert rx_graph1.num_edges() == rx_graph2.num_edges()
        assert nx_id_to_rx_idx1 == nx_id_to_rx_idx2

    def test_calculate_walk_times(self, sample_graph, sample_conserved_lands_gdf):
        """Test calculating walk times."""
        # Ensure graph has time attributes
        from walk_times.calculate import add_time_attributes

        add_time_attributes(sample_graph, travel_speed=4.5)

        center_nodes = [1, 2]
        trip_times = [5, 10, 15]

        df = calculate_walk_times(
            center_nodes,
            sample_graph,
            sample_conserved_lands_gdf,
            trip_times=trip_times,
            progress_bar=False,
            geography_type="blocks",
        )

        assert isinstance(df, pd.DataFrame)
        assert "block_osmid" in df.columns
        assert "land_osmid" in df.columns
        assert "trip_time" in df.columns
        assert len(df) > 0

    def test_calculate_walk_times_tracts(self, sample_graph, sample_conserved_lands_gdf):
        """Test calculating walk times for tracts."""
        from walk_times.calculate import add_time_attributes

        add_time_attributes(sample_graph, travel_speed=4.5)

        center_nodes = [1]
        trip_times = [5, 10]

        df = calculate_walk_times(
            center_nodes,
            sample_graph,
            sample_conserved_lands_gdf,
            trip_times=trip_times,
            progress_bar=False,
            geography_type="tracts",
        )

        assert "tract_osmid" in df.columns

    def test_calculate_walk_times_missing_node(self, sample_graph, sample_conserved_lands_gdf):
        """Test calculating walk times with missing center node."""
        from walk_times.calculate import add_time_attributes

        add_time_attributes(sample_graph, travel_speed=4.5)

        center_nodes = [999]  # Node doesn't exist
        trip_times = [5, 10]

        df = calculate_walk_times(
            center_nodes,
            sample_graph,
            sample_conserved_lands_gdf,
            trip_times=trip_times,
            progress_bar=False,
            geography_type="blocks",
        )

        # Should return empty DataFrame or handle gracefully
        assert isinstance(df, pd.DataFrame)

    @patch("walk_times.calculate.gpd.read_parquet")
    @patch("walk_times.calculate.gpd.read_file")
    @patch("walk_times.calculate.load_graph")
    @patch("walk_times.calculate.add_time_attributes")
    @patch("walk_times.calculate.calculate_walk_times")
    def test_process_walk_times(
        self,
        mock_calc,
        mock_add_time,
        mock_load,
        mock_gpd_read_file,
        mock_gpd_read_parquet,
        sample_graph,
        sample_blocks_gdf,
        sample_conserved_lands_gdf,
        sample_walk_times_df,
        temp_dir,
    ):
        """Test processing walk times workflow."""
        mock_load.return_value = sample_graph
        mock_calc.return_value = sample_walk_times_df

        # Mock file reading
        def mock_read(path, **kwargs):
            if str(path).endswith(".parquet"):
                if "geography" in str(path) or "blocks" in str(path):
                    return sample_blocks_gdf
                else:
                    return sample_conserved_lands_gdf
            else:
                if "geography" in str(path) or "blocks" in str(path):
                    return sample_blocks_gdf
                else:
                    return sample_conserved_lands_gdf

        mock_gpd_read_parquet.side_effect = mock_read
        mock_gpd_read_file.side_effect = mock_read

        output_path = temp_dir / "walk_times.parquet"

        result = process_walk_times(
            geography_type="blocks",
            graph_path="dummy.graphml",
            geography_path="dummy.parquet",
            conserved_lands_path="dummy.parquet",
            output_path=output_path,
            trip_times=[5, 10, 15],
        )

        mock_load.assert_called_once()
        mock_add_time.assert_called_once()
        mock_calc.assert_called_once()
        assert output_path.exists()
        assert isinstance(result, pd.DataFrame)
