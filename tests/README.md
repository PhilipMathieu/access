# Test Suite

This directory contains the pytest test suite for the access analysis project.

## Running Tests

### Install Test Dependencies

First, install the project with dev dependencies:

```bash
uv pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
pytest tests/test_walk_times.py
pytest tests/test_merging.py
pytest tests/test_config.py
pytest tests/test_analysis.py
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test Classes or Functions

```bash
pytest tests/test_walk_times.py::TestGraphUtils
pytest tests/test_walk_times.py::TestGraphUtils::test_get_node_mapping
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Run Tests with Output

```bash
pytest -s
```

## Test Structure

- `conftest.py`: Shared fixtures and pytest configuration
- `test_walk_times.py`: Tests for walk time calculation functions
- `test_merging.py`: Tests for block merging and analysis functions
- `test_config.py`: Tests for configuration modules
- `test_analysis.py`: Tests for statistical analysis functions

## Fixtures

The `conftest.py` file provides several fixtures for testing:

- `sample_graph`: A simple NetworkX graph for testing
- `sample_rustworkx_graph`: A rustworkx graph converted from sample_graph
- `sample_blocks_gdf`: Sample GeoDataFrame for blocks
- `sample_conserved_lands_gdf`: Sample GeoDataFrame for conserved lands
- `sample_walk_times_df`: Sample walk times DataFrame
- `sample_merged_blocks_gdf`: Sample merged blocks GeoDataFrame
- `sample_census_data`: Sample census data
- `sample_cejst_data`: Sample CEJST data
- `sample_relationship_file`: Sample Census relationship file
- `temp_dir`: Temporary directory for test files
- `mock_census_api`: Mock Census API
- `region_config_maine`: RegionConfig for Maine

## Writing New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py` for test files, `test_*` for test functions
2. Use fixtures from `conftest.py` when possible
3. Mock external dependencies (APIs, file I/O) using `unittest.mock`
4. Use descriptive test names that explain what is being tested
5. Group related tests in test classes

## Example Test

```python
def test_my_function(sample_graph):
    """Test my function with sample data."""
    result = my_function(sample_graph)
    assert result is not None
    assert len(result) > 0
```

