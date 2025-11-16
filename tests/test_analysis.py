"""Tests for analysis module."""

import pandas as pd

from analysis.statistical import (
    analyze_access_disparity,
    calculate_population_metrics,
    create_boolean_columns,
    run_manova,
)


class TestCreateBooleanColumns:
    """Tests for create_boolean_columns function."""

    def test_create_boolean_columns_basic(self):
        """Test creating boolean columns."""
        df = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 25.3],
                "AC_10": [0, 0, 15.0, 25.3],
                "AC_15": [20.0, 0, 15.0, 0],
                "P1_001N": [100, 200, 150, 180],
                "TC": [1, 0, 1, 0],
            }
        )

        trip_time_cols = ["AC_5", "AC_10", "AC_15"]
        result = create_boolean_columns(df, trip_time_cols, cumulative=True)

        # Check boolean columns were created
        assert "AC_5_bool" in result.columns
        assert "AC_10_bool" in result.columns
        assert "AC_15_bool" in result.columns

        # Check population columns were created
        assert "AC_5_pop" in result.columns
        assert "AC_10_pop" in result.columns
        assert "AC_15_pop" in result.columns

        # Check disadvantage boolean
        assert "TC_bool" in result.columns

    def test_create_boolean_columns_cumulative(self):
        """Test cumulative boolean columns."""
        df = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 0],
                "AC_10": [0, 0, 15.0, 0],
                "AC_15": [20.0, 0, 0, 0],
                "P1_001N": [100, 200, 150, 180],
                "TC": [1, 0, 1, 0],
            }
        )

        trip_time_cols = ["AC_5", "AC_10", "AC_15"]
        result = create_boolean_columns(df, trip_time_cols, cumulative=True)

        # AC_10_bool should be True if AC_5 > 0 OR AC_10 > 0
        assert result.loc[1, "AC_10_bool"]  # AC_5 > 0
        assert result.loc[2, "AC_10_bool"]  # AC_10 > 0

    def test_create_boolean_columns_non_cumulative(self):
        """Test non-cumulative boolean columns."""
        df = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 0],
                "AC_10": [0, 0, 15.0, 0],
                "P1_001N": [100, 200, 150, 180],
                "TC": [1, 0, 1, 0],
            }
        )

        trip_time_cols = ["AC_5", "AC_10"]
        result = create_boolean_columns(df, trip_time_cols, cumulative=False)

        # AC_10_bool should only be True if AC_10 > 0 (not AC_5)
        assert not result.loc[1, "AC_10_bool"]  # Only AC_5 > 0
        assert result.loc[2, "AC_10_bool"]  # AC_10 > 0

    def test_create_boolean_columns_population(self):
        """Test population-weighted columns."""
        df = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 0],
                "P1_001N": [100, 200, 150, 180],
                "TC": [1, 0, 1, 0],
            }
        )

        trip_time_cols = ["AC_5"]
        result = create_boolean_columns(df, trip_time_cols)

        # AC_5_pop should be population if AC_5 > 0, else 0
        assert result.loc[0, "AC_5_pop"] == 0
        assert result.loc[1, "AC_5_pop"] == 200


class TestRunManova:
    """Tests for run_manova function."""

    def test_run_manova_basic(self):
        """Test running MANOVA."""
        data = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 25.3, 15.0],
                "AC_10": [0, 0, 15.0, 25.3, 20.0],
                "TC_bool": [True, False, True, False, True],
            }
        )

        dependent_vars = ["AC_5", "AC_10"]
        independent_var = "TC_bool"

        fit = run_manova(data, dependent_vars, independent_var)

        assert fit is not None
        # Check that MANOVA was fit
        assert hasattr(fit, "mv_test")

    def test_run_manova_with_formula(self):
        """Test running MANOVA with custom formula."""
        data = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 25.3],
                "AC_10": [0, 0, 15.0, 25.3],
                "TC_bool": [True, False, True, False],
            }
        )

        formula = "AC_5 + AC_10 ~ TC_bool"
        fit = run_manova(data, [], "", formula=formula)

        assert fit is not None


class TestAnalyzeAccessDisparity:
    """Tests for analyze_access_disparity function."""

    def test_analyze_access_disparity_basic(self):
        """Test analyzing access disparity."""
        data = pd.DataFrame(
            {
                "AC_10_bool": [False, True, False, True, False, True],
                "TC_bool": [True, True, False, False, True, False],
                "P1_001N": [100, 200, 150, 180, 120, 160],
            }
        )

        tab, table = analyze_access_disparity(
            data,
            access_col="AC_10_bool",
            disadvantage_col="TC_bool",
            invert_access=True,
        )

        assert isinstance(tab, pd.DataFrame)
        assert table is not None
        # Check that table has expected structure
        assert hasattr(table, "table_orig")

    def test_analyze_access_disparity_not_inverted(self):
        """Test analyzing access disparity without inverting."""
        data = pd.DataFrame(
            {
                "AC_10_bool": [False, True, False, True],
                "TC_bool": [True, True, False, False],
                "P1_001N": [100, 200, 150, 180],
            }
        )

        tab, table = analyze_access_disparity(
            data,
            access_col="AC_10_bool",
            disadvantage_col="TC_bool",
            invert_access=False,
        )

        assert isinstance(tab, pd.DataFrame)
        assert table is not None


class TestCalculatePopulationMetrics:
    """Tests for calculate_population_metrics function."""

    def test_calculate_population_metrics_basic(self):
        """Test calculating population metrics."""
        data = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 25.3],
                "AC_10": [0, 0, 15.0, 25.3],
                "AC_5_pop": [0, 200, 0, 180],
                "AC_10_pop": [0, 0, 150, 180],
                "P1_001N": [100, 200, 150, 180],
            }
        )

        trip_time_cols = ["AC_5", "AC_10"]
        result = calculate_population_metrics(data, trip_time_cols)

        assert isinstance(result, pd.DataFrame)
        assert "mean" in result.columns
        assert "std" in result.columns

    def test_calculate_population_metrics_grouped(self):
        """Test calculating population metrics grouped by variable."""
        data = pd.DataFrame(
            {
                "AC_5": [0, 10.5, 0, 25.3],
                "AC_5_pop": [0, 200, 0, 180],
                "P1_001N": [100, 200, 150, 180],
                "TC_bool": [True, True, False, False],
            }
        )

        trip_time_cols = ["AC_5"]
        result = calculate_population_metrics(data, trip_time_cols, groupby_col="TC_bool")

        assert isinstance(result, pd.DataFrame)
        assert "TC_bool" in result.columns or "TC_bool" in result.index.names
