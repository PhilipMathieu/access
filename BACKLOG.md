# Project Backlog and Roadmap

**Last Updated:** 2025-11-15
**Project:** Access - Spatial Accessibility Analysis for Conservation Lands

**Recent Completions:**
- ✅ TD-001: Python 3.10 Version Lock (2025-01-XX)
- ✅ TD-002: Outdated OSMnx Version (2025-01-XX)
- ✅ TD-009: Dependency Security Scanning (2025-11-15)
- ✅ IMP-005: Code Quality Tooling (2025-11-15)
- ✅ IMP-009: Enhanced Print Layouts (2025-11-15)
- ✅ IMP-006: Webmap Enhancements (2025-11-09)
- ✅ FR-003: Mobile-Friendly Webmap (2025-11-09)
- 🔄 TD-007: Error Handling Strategy - Partial (2025-11-15)
- 🔄 IMP-004: Improved Logging and Monitoring - Partial (2025-11-15)
- 🔄 IMP-003: Documentation Improvements - Partial (2025-11-15)

This document consolidates technical debt, feature requests, and improvements identified through comprehensive project analysis. Items are categorized by type, priority, and estimated effort.

---

## 📋 Table of Contents

1. [Technical Debt](#technical-debt)
2. [Feature Requests](#feature-requests)
3. [Improvements](#improvements)
4. [Priority Matrix](#priority-matrix)
5. [Effort Estimation Guide](#effort-estimation-guide)

---

## 🔧 Technical Debt

### TD-001: Python 3.10 Version Lock
**Priority:** High
**Effort:** Medium (16-24 hours)
**Status:** ✅ **COMPLETED** (2025-01-XX)
**Category:** Dependencies

**Description:**
The project is currently locked to Python 3.10 (`requires-python = ">=3.10,<3.11"`). This restriction prevents:
- Using Python 3.11+ performance improvements (20-25% faster)
- Access to newer language features (PEP 657 error locations, exception groups)
- Security updates and bug fixes in newer Python versions

**Impact:**
- Missing significant performance gains for CPU-intensive walk time calculations
- Inability to leverage newer Python ecosystem features
- Potential security vulnerabilities as Python 3.10 approaches end-of-life (October 2026)

**Completed Implementation:**
1. ✅ Updated `pyproject.toml` to require Python `>=3.11`
2. ✅ Updated tool configurations (Black, Ruff, mypy) to support Python 3.11+
3. ✅ Updated `.python-version` file to 3.11
4. ✅ Updated CI/CD workflows (code-quality.yml, security.yml) to use Python 3.11
5. ✅ Tested compatibility - all dependencies support Python 3.11+
6. ✅ Verified with `uv sync` - successfully installed Python 3.11.14 and all dependencies

**Dependencies:**
- All package dependencies support Python 3.11+ ✅
- OSMnx 2.0.6 supports Python 3.11+ ✅

**References:**
- [Python 3.11 Performance Improvements](https://docs.python.org/3.11/whatsnew/3.11.html#faster-cpython)
- [Python Release Schedule](https://peps.python.org/pep-0664/)

---

### TD-002: Outdated OSMnx Version
**Priority:** Medium
**Effort:** Medium (12-16 hours)
**Status:** ✅ **COMPLETED** (2025-01-XX)
**Category:** Dependencies

**Description:**
Project uses OSMnx 1.3.0 (pinned), but latest stable version is 2.0+ (as of 2025). Newer versions include:
- Performance optimizations for large graphs
- Better error handling and logging
- Improved graph simplification algorithms
- Enhanced coordinate system handling
- Better integration with modern GeoDataFrames

**Impact:**
- Missing performance improvements for graph operations
- Potential compatibility issues with newer geopandas/networkx versions
- Missing bug fixes and security updates

**Completed Implementation:**
1. ✅ Updated OSMnx version in `pyproject.toml` from `==1.3.0` to `>=2.0.0`
2. ✅ Verified latest version is 2.0.6 (installed successfully)
3. ✅ Tested API compatibility - all functions used in codebase are available:
   - `ox.load_graphml()` ✅
   - `ox.project_graph()` ✅
   - `ox.graph_from_place()` ✅
   - `ox.save_graphml()` ✅
   - `ox.graph_to_gdfs()` ✅
   - `ox.settings.cache_folder` ✅
   - `ox.settings.log_console` ✅
4. ✅ Verified imports work correctly with OSMnx 2.0.6
5. ✅ No code changes required - API is backward compatible

**Note:** Existing cached `.graphml` files should be compatible, but may benefit from regeneration with the newer version for optimal performance.

**References:**
- [OSMnx GitHub Releases](https://github.com/gboeing/osmnx/releases)
- [OSMnx Migration Guide](https://github.com/gboeing/osmnx/blob/main/CHANGELOG.md)

---

### TD-003: Mixed Import Patterns for H3 Module
**Priority:** Medium
**Effort:** Small (4-8 hours)
**Status:** ✅ **COMPLETED** (2025-11-15)
**Category:** Code Quality

**Description:**
The `src/h3/` module used an inconsistent import pattern due to naming conflict with the installed `h3` library. This has been resolved by renaming the module to `src/h3_utils/`.

**Completed Implementation:**
1. ✅ Renamed `src/h3/` to `src/h3_utils/`
2. ✅ Updated all imports throughout codebase (`src/run_pipeline.py`, `run_pipeline.sh`, `README.md`)
3. ✅ Updated `pyproject.toml` to include `h3_utils` in packages list
4. ✅ Updated documentation (`README.md`)
5. ✅ Removed mypy exclude for h3 module (no longer needed)
6. ✅ Updated pre-commit configuration

**Note:** Some legacy notebooks still use `from h3utils import *` (referring to `src/h3utils.py`, a separate utility file). The `src/h3_utils/` package directory is properly renamed and used throughout the main codebase.

**Files Modified:**
- `src/h3_utils/` (renamed from `src/h3/`)
- `src/run_pipeline.py` - Updated import
- `run_pipeline.sh` - Updated import
- `README.md` - Updated documentation
- `pyproject.toml` - Added to packages, removed exclude
- `.pre-commit-config.yaml` - Removed h3 exclude

---

### TD-004: Incomplete Test Coverage
**Priority:** High
**Effort:** Large (40-60 hours)
**Category:** Testing

**Description:**
Current test suite has significant gaps:
- Only 4 test files exist (`test_walk_times.py`, `test_merging.py`, `test_config.py`, `test_analysis.py`)
- No tests for visualization module
- No tests for H3 module
- No tests for data update/validation scripts
- No integration tests for full pipeline
- No tests for PMTiles conversion
- Missing edge case testing

**Current Coverage Gaps:**
- `src/visualization/` - 0% coverage
- `src/h3_utils/` - 0% coverage
- `src/update_data_sources.py` - 0% coverage
- `src/validate_data.py` - 0% coverage
- `src/convert_to_pmtiles.py` - 0% coverage
- `src/crop_cejst_to_state.py` - 0% coverage
- `src/probe_data_sources.py` - 0% coverage
- Integration/end-to-end tests - 0% coverage

**Impact:**
- High risk of regressions when making changes
- Difficult to refactor with confidence
- Hard to validate bug fixes
- No automated quality gates for CI/CD

**Solution:**
1. Add tests for visualization module (figures.py)
2. Add tests for H3 module (relationship.py, joins.py, h3j.py)
3. Add tests for data management scripts
4. Add integration tests for pipeline
5. Set up pytest-cov reporting
6. Establish minimum coverage threshold (e.g., 80%)
7. Add tests to CI/CD pipeline

**Priority Tasks:**
1. Test critical path: walk time calculations (expand existing)
2. Test data validation and schema checking
3. Test H3 relationship file generation
4. Integration test for `run_pipeline.py`

---

### TD-005: Hard-coded File Paths and Magic Strings
**Priority:** Medium
**Effort:** Medium (16-24 hours)
**Category:** Code Quality

**Description:**
Many scripts contain hard-coded paths and magic strings that make them brittle and hard to maintain:
- File paths like `data/graphs/maine_walk.graphml` repeated across multiple files
- Maine-specific logic (should use `RegionConfig`)
- Magic strings for column names (`"GEOID20"`, `"osmid"`, `"AC_10"`)
- No centralized configuration for defaults

**Examples:**
```python
# run_pipeline.sh line 42-44
graph_path='data/graphs/maine_walk.graphml'
conserved_lands_path='data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip'
```

**Impact:**
- Difficult to extend to other states
- Error-prone when paths change
- Hard to test with different configurations
- Code duplication

**Solution:**
1. Extend `RegionConfig` to include all data paths
2. Create configuration module for column name constants
3. Remove hard-coded "Maine" references
4. Use configuration throughout all scripts
5. Update documentation with configuration examples

**Files to Refactor:**
- `run_pipeline.sh`
- `src/run_pipeline.py`
- All processing scripts (`find_centroids.py`, `convert_to_pmtiles.py`, etc.)
- Notebooks that reference specific files

---

### TD-006: Shapefile Format Dependency
**Priority:** Medium
**Effort:** Large (30-40 hours)
**Category:** Data Format / Technical Architecture

**Description:**
Project heavily relies on shapefile format (`.shp`, `.shp.zip`) which is:
- Legacy format with known limitations (10-char field names, 2GB file size limit)
- Slower to read/write compared to modern formats
- Multiple files per dataset (.shp, .shx, .dbf, .prj, etc.)
- Less efficient for large datasets

Modern alternatives exist:
- **GeoParquet**: Columnar format, fast, supports complex types
- **GeoPackage**: SQLite-based, single-file, OGC standard
- **FlatGeobuf**: Streaming format, cloud-optimized

**Current State:**
- ✅ `src/migrate_to_geoparquet.py` exists with conversion functionality
- ❌ Migration utility not integrated into pipeline
- ❌ All processing still uses shapefiles
- ✅ PMTiles conversion works from shapefiles

**Impact:**
- Slower I/O performance for large datasets
- Field name truncation issues
- Multiple files to manage per dataset
- Not cloud-optimized

**Solution:**
1. Complete GeoParquet migration utility
2. Add support for reading GeoParquet in all processing functions
3. Update pipeline to use GeoParquet internally
4. Keep shapefile support for backward compatibility
5. Update documentation
6. Benchmark performance improvements

**Migration Path:**
1. Phase 1: Support both formats (read/write)
2. Phase 2: Default to GeoParquet for new data
3. Phase 3: Migrate existing datasets
4. Phase 4: Deprecate shapefile as primary format

**References:**
- [GeoParquet Specification](https://geoparquet.org/)
- `src/migrate_to_geoparquet.py` (exists with basic conversion functionality)

---

### TD-007: No Error Handling Strategy
**Priority:** High
**Effort:** Medium (20-30 hours) → **12-18 hours remaining**
**Status:** 🔄 **IN PROGRESS** (2025-11-15)
**Category:** Error Handling / Logging

**Description:**
Inconsistent error handling and logging across the codebase:
- Some functions log errors, others don't
- No centralized exception handling
- Unclear error messages for users
- No error recovery mechanisms
- Failed operations may leave partial data

**Progress (2025-11-15):**
- ✅ Fixed empty except blocks in `changelog.py` (2 locations)
- ✅ Fixed empty except blocks in `probe_data_sources.py` (2 locations)
- ✅ Added proper error logging with context messages
- ✅ Consistent logging patterns established (see DEVELOPMENT.md)
- ❌ Custom exception hierarchy not yet created
- ❌ Retry logic for network operations not yet implemented
- ❌ Pipeline validation checkpoints not yet added

**Examples of Issues:**
- What happens if OSMnx graph download fails mid-process?
- How are missing geometries handled in walk time calculations?
- What if Census API rate limit is hit?
- No validation of intermediate outputs

**Impact:**
- Hard to debug failures
- Users don't know why operations failed
- Data corruption risks
- Poor user experience

**Remaining Work:**
1. ❌ Create custom exception hierarchy
2. ❌ Add validation checkpoints in pipeline
3. ❌ Implement retry logic for network operations
4. ❌ Add data validation before/after processing steps
5. ❌ Create error recovery guide for common failures
6. ❌ Add structured logging (JSON) for monitoring

**Specific Improvements:**
- Add transaction-like behavior for data updates
- Validate schemas before/after transformations
- Add progress checkpoints and resume capability
- Create troubleshooting guide

---

### TD-008: Incomplete CI/CD Pipeline
**Priority:** Medium
**Effort:** Medium (16-24 hours)
**Category:** DevOps / Automation

**Description:**
Partial CI/CD pipeline exists but lacks critical automation:
- GitHub Actions workflow exists for webmap deployment (`.github/workflows/static.yml`)
- Tests must be run manually (no automated test execution)
- No automated quality checks (linting, type checking)
- No test coverage reporting
- No pre-commit hooks

**Current State:**
- ✅ GitHub Actions workflow for Pages deployment exists and is functional
- ❌ No automated test execution on PR/push
- ❌ No code quality checks in CI
- ❌ No pre-commit hooks configured

**Impact:**
- Higher risk of breaking changes
- Manual testing burden
- Inconsistent code quality
- Slower development cycle

**Solution:**
1. Extend existing GitHub Actions workflow to include:
   - Running tests on PR/push (pytest)
   - Code quality checks (linting, type checking)
   - Test coverage reporting (pytest-cov)
   - Keep existing webmap deployment automation
2. Add pre-commit hooks for:
   - Code formatting (black, isort)
   - Linting (ruff or pylint)
   - Type checking (mypy)
3. Set up branch protection rules
4. Add status badges to README

**Priority Tasks:**
1. Add test automation to existing GitHub Actions workflow (pytest on push/PR)
2. ✅ Webmap deployment automation (already implemented)
3. Add code quality checks to CI pipeline
4. Set up pre-commit hooks

---

### TD-009: No Dependency Security Scanning
**Priority:** Medium
**Effort:** Small (4-8 hours)
**Status:** ✅ **COMPLETED** (2025-11-15)
**Category:** Security

**Description:**
No automated security scanning for dependencies:
- Old dependency versions may have vulnerabilities
- No alerts for security updates
- Manual tracking of CVEs

**Completed Implementation:**
1. ✅ Added Dependabot configuration for automated dependency updates
2. ✅ Added `pip-audit` for vulnerability scanning in dev dependencies
3. ✅ Created security scanning GitHub Actions workflow
4. ✅ Configured weekly automated scans
5. ✅ Added security documentation to CONTRIBUTING.md

**Files Created/Modified:**
- `.github/dependabot.yml` - Automated dependency update configuration
- `.github/workflows/security.yml` - Security scanning CI/CD workflow
- `pyproject.toml` - Added pip-audit and bandit to dev dependencies
- `CONTRIBUTING.md` - Added security best practices section

---

### TD-010: Notebook Code Duplication
**Priority:** Low
**Effort:** Large (30-40 hours)
**Category:** Code Quality

**Description:**
Jupyter notebooks contain duplicated logic that should be in modules:
- Walk time calculation code duplicated between notebooks
- Visualization code not fully migrated to `visualization/` module
- Data loading patterns repeated
- Analysis patterns repeated

**Impact:**
- Harder to maintain and update
- Inconsistent results across notebooks
- Code drift between notebook and module implementations

**Solution:**
1. Audit notebooks for duplicated code
2. Extract common patterns to modules
3. Update notebooks to use module functions
4. Add notebook testing (nbconvert + papermill)
5. Document notebook → module workflow

**Note:**
README mentions: "Core data processing logic has been migrated to standalone Python modules in `src/` for better maintainability"
This suggests migration is ongoing but incomplete.

---

### TD-011: H3 Not Used as Primary Geographic Unit
**Priority:** Medium
**Effort:** Large (72-104 hours)
**Category:** Architecture / Analysis Methodology

**Description:**
H3 hexagon infrastructure was built to replace census blocks as standardized geographic units, but the original goal has not been achieved. H3 is currently only used for post-processing aggregation and visualization, while all core analysis still uses census blocks.

**Current State:**
- ✅ H3 relationship file generation exists (`src/h3_utils/relationship.py`)
- ✅ H3 join utilities exist (`src/h3_utils/joins.py`)
- ✅ H3 visualization functions exist
- ✅ H3J format conversion exists
- ❌ Walk times calculated at census block centroids (not H3 hexagon centroids)
- ❌ Access metrics calculated per census block (not per H3 hexagon)
- ❌ Statistical analysis uses census blocks (not H3 hexagons)
- ❌ No H3-centroid mapping to OSMnx nodes

**Impact:**
- Still subject to uneven census block granularity (urban vs. rural)
- Blocks don't represent meaningful geographic areas
- Blocks can be very small (parks, parking lots) or very large (rural areas)
- H3 benefits (standardized sizes, better comparisons) not realized
- Post-processing aggregation loses precision and accuracy

**Root Cause:**
The original intent was to use H3 hexagons as standardized geographic units instead of census blocks, which have uneven granularity. However, the implementation stopped at building infrastructure for aggregation rather than making H3 the primary analysis unit.

**Solution:**
See FR-004 for complete implementation plan. This technical debt item tracks the gap between original intent and current state.

**References:**
- `H3_PROGRESS_ASSESSMENT.md` - Detailed assessment of H3 progress
- Original goal: Use H3 hexagons instead of census blocks for standardized geographic detail
- `src/h3_utils/relationship.py` - Existing H3 relationship file generation
- `src/h3_utils/joins.py` - Existing H3 join utilities

---

## 🚀 Feature Requests

### FR-001: Multi-State Support Expansion
**Priority:** High
**Effort:** Large (60-80 hours)
**Category:** Geographic Expansion

**Description:**
Extend analysis from Maine to all New England states (NH, VT, MA, RI, CT).

**Current State:**
- `RegionConfig` class exists in `src/config/regions.py`
- All 6 New England states defined in `NEW_ENGLAND_STATES` dict
- Most scripts still hard-coded for Maine

**Benefits:**
- Comparative analysis across states
- Larger dataset for statistical analysis
- Greater research impact
- Reusable framework for other regions

**Requirements:**
1. **Data Acquisition:**
   - Conserved lands datasets for each state
   - OSMnx graphs for each state
   - Census data (already multi-state capable)
   - CEJST data (already national)

2. **Code Updates:**
   - Remove Maine-specific hard-coding
   - Use `RegionConfig` throughout
   - Update pipeline scripts for multi-state
   - Parallel processing for multiple states

3. **Webmap:**
   - Multi-state layer switching
   - State boundary overlay
   - Comparative statistics view

4. **Documentation:**
   - State-specific setup guides
   - Data source documentation per state
   - Comparison methodology

**Implementation Phases:**
1. Phase 1: Single additional state (NH) as proof-of-concept
2. Phase 2: All New England states
3. Phase 3: State comparison analysis
4. Phase 4: Regional webmap

**Dependencies:**
- TD-005 (Hard-coded paths)
- TD-006 (Data format optimization for larger datasets)

---

### FR-002: Interactive Dashboard for Analysis Results
**Priority:** Medium
**Effort:** Large (50-70 hours)
**Category:** Visualization / UI

**Description:**
Create an interactive dashboard (Dash/Streamlit/Panel) for exploring analysis results without running notebooks.

**Features:**
1. **Data Exploration:**
   - Filter by demographic variables
   - Select trip time thresholds
   - Geographic selection (state, county, tract)

2. **Visualizations:**
   - Interactive maps (Folium/Plotly)
   - Statistical charts and graphs
   - Comparison views

3. **Export:**
   - Download filtered data
   - Export publication-ready figures
   - Generate reports

4. **Analysis Tools:**
   - Custom access calculations
   - What-if scenarios
   - Demographic comparisons

**Technology Options:**
- **Streamlit**: Easiest, Python-native
- **Dash**: More powerful, Plotly integration
- **Panel**: Flexible, supports Jupyter widgets
- **Shiny for Python**: R-like reactive programming

**Implementation Phases:**
1. Phase 1: Basic data exploration (10-15 hours)
2. Phase 2: Interactive visualizations (15-20 hours)
3. Phase 3: Analysis tools (20-25 hours)
4. Phase 4: Deployment and hosting (5-10 hours)

**Benefits:**
- Accessible to non-technical stakeholders
- Real-time data exploration
- Supports policy decision-making
- Broader research impact

---

### FR-003: Mobile-Friendly Webmap
**Priority:** Medium
**Effort:** Medium (20-30 hours)
**Status:** ✅ **COMPLETED** (2025-11-09)
**Category:** Webmap / UI

**Description:**
Current webmap may not be fully optimized for mobile devices.

**Completed Requirements:**
1. **Responsive Design:**
   - ✅ Mobile-first layout (responsive CSS with media queries)
   - ✅ Touch-friendly controls (minimum 44px touch targets)
   - ✅ Optimized map interactions
   - ✅ Responsive positioning of controls for different screen sizes

2. **Performance:**
   - ✅ PMTiles format (efficient tile delivery)
   - ✅ Progressive loading (tiles load as needed)
   - ✅ Reduced data transfer (vector tiles, not raster)
   - ❌ Smaller initial load (could be further optimized)

3. **Features:**
   - ✅ Location services integration (geolocation button in search)
   - ✅ "Find nearest conserved land" feature (locate button)
   - ❌ Offline capability (PWA) (not implemented)

4. **Accessibility:**
   - ✅ Screen reader support (ARIA labels, semantic HTML)
   - ✅ High contrast mode support (CSS media queries)
   - ✅ Keyboard navigation (Tab navigation, Enter/Space activation)
   - ✅ Focus indicators for keyboard users

**Testing:**
- ✅ Cross-browser testing (basic)
- ⚠️ Device testing (iOS, Android) (recommended for production)
- ⚠️ Performance benchmarking (recommended)
- ⚠️ Accessibility audit (WCAG 2.1) (recommended for production)

**Notes:**
- All controls are accessible via keyboard
- Screen reader announcements implemented
- High contrast mode styles added
- Mobile-specific CSS adjustments for smaller screens

---

### FR-004: Complete H3 Implementation as Primary Geographic Unit
**Priority:** Medium
**Effort:** Large (72-104 hours)
**Category:** Analysis Methodology / Architecture

**Description:**
Complete the original goal of using H3 hexagons as standardized geographic units instead of census blocks. Currently, H3 infrastructure exists but is only used for post-processing aggregation. This feature request would make H3 the primary analysis unit throughout the pipeline.

**Current State:**
- H3 relationship files can be generated (maps blocks to hexagons)
- H3 joins can aggregate block-level results to hexagons
- But walk times, access metrics, and analysis all still use census blocks

**Benefits:**
- Standardized hexagon sizes provide consistent geographic detail
- Better for cross-regional comparisons
- More intuitive for visualization and analysis
- Avoids uneven census block granularity (urban vs. rural)
- Blocks don't represent meaningful geographic areas

**Implementation Phases:**

**Phase 1: H3-Centroid Mapping (Prerequisite) - 8-12 hours**
1. Generate H3 hexagons for the region
2. Calculate centroid for each hexagon
3. Find nearest OSMnx node for each centroid (similar to `find_centroids.py` for blocks)
4. Create `h3_hexagons.shp.zip` with `h3id` and `osmid` columns

**Phase 2: H3-Based Walk Time Calculations - 16-24 hours**
1. Add `geography_type="hexagons"` option to walk time functions
2. Use H3 hexagon centroids instead of block centroids
3. Calculate walk times per H3 hexagon
4. Output: `walk_times_hexagon_df.csv`

**Phase 3: H3-Based Merging and Analysis - 24-32 hours**
1. Create `create_ejhexagons()` function (H3 equivalent of `create_ejblocks()`)
2. Aggregate demographics to H3 hexagons
3. Calculate access metrics per hexagon
4. Join CEJST data at H3 level

**Phase 4: H3-Based Statistical Analysis - 16-24 hours**
1. Update analysis modules to work with H3 hexagons
2. Create H3-based visualization functions
3. Update notebooks to use H3 as primary unit

**Phase 5: Pipeline Integration - 8-12 hours**
1. Make H3 the default geographic unit in pipeline
2. Keep block-level as optional/legacy mode
3. Update documentation

**Dependencies:**
- TD-011 (H3 Not Used as Primary Geographic Unit) - This is the technical debt being addressed
- Existing H3 infrastructure provides foundation

**Alternative Approach:**
- Hybrid: Keep blocks for walk time calculations (more precise), use H3 for aggregation/visualization
- **Pros:** Less effort, maintains precision
- **Cons:** Doesn't fully achieve original goal
- **Effort:** ~40-50 hours

**References:**
- `H3_PROGRESS_ASSESSMENT.md` - Detailed assessment and implementation plan
- `src/h3_utils/relationship.py` - Existing H3 relationship file generation
- `src/h3_utils/joins.py` - Existing H3 join utilities

---

## 🔨 Improvements

### IMP-001: Performance Optimization for Walk Time Calculations
**Priority:** High
**Effort:** Large (40-60 hours)
**Category:** Performance

**Description:**
Walk time calculations are the most computationally intensive part of the pipeline. Several optimization opportunities exist.

**Current State:**
- Uses rustworkx for graph operations (already optimized)
- Bounded Dijkstra algorithm implemented
- Parallel processing support added (n_jobs parameter)
- Processing ~100K+ blocks for Maine takes significant time

**Optimization Opportunities:**

1. **Algorithm Improvements:**
   - Bidirectional search for specific source-target pairs
   - A* algorithm with heuristic for targeted searches
   - Precompute and cache common subgraphs
   - Early termination optimization

2. **Data Structure Optimization:**
   - Graph compression techniques
   - Spatial indexing for node lookups
   - Memory-mapped graph storage

3. **Parallel Processing Enhancement:**
   - Better chunk size optimization
   - Multi-level parallelism (state → county → tract)
   - GPU acceleration exploration (CuGraph)
   - Distributed computing (Dask)

4. **Caching Strategy:**
   - Cache intermediate results
   - Incremental updates only for changed data
   - Persistent result caching

**Benchmarking:**
```python
# Current performance (approximate):
# - Maine blocks (~100K): ~4-8 hours (single core)
# - Maine blocks: ~1-2 hours (8 cores)
# Target: <30 minutes for Maine, <4 hours for all New England
```

**Implementation:**
1. Benchmark current performance
2. Implement and test each optimization
3. Measure impact
4. Document performance characteristics
5. Add performance testing to CI

**Dependencies:**
- TD-002 (OSMnx version)
- TD-006 (Data format)

---

### IMP-002: Enhanced Data Validation
**Priority:** High
**Effort:** Medium (24-32 hours)
**Category:** Data Quality

**Description:**
Strengthen data validation throughout the pipeline.

**Current State:**
- ✅ `src/validate_data.py` exists with basic validation checks
- ✅ Schema validation implemented
- ✅ Quality metrics calculated
- ❌ No automated validation integrated into pipeline

**Enhancements:**

1. **Input Validation:**
   - Geometry validation (topology, area, completeness)
   - CRS consistency checks
   - Required fields validation
   - Value range checks
   - Missing data analysis

2. **Intermediate Validation:**
   - Walk time reasonableness checks
   - Join completeness verification
   - Calculation sanity checks
   - Progress checkpoints

3. **Output Validation:**
   - Statistical distribution checks
   - Comparison with previous runs
   - Known-good test cases
   - Publication-ready checks

4. **Reporting:**
   - Validation reports
   - Data quality dashboard
   - Trend analysis
   - Alert system

**Validation Rules:**
- Walk times should be positive and within reasonable bounds
- Access percentages should sum correctly
- Geographic coverage should be complete
- Demographic totals should match Census
- Conserved land areas should match source data

**Implementation:**
1. Define validation rule set
2. Implement validation functions
3. Integrate into pipeline
4. Create validation reports
5. Add to CI/CD

---

### IMP-003: Documentation Improvements
**Priority:** Medium
**Effort:** Medium (20-30 hours) → **16-25 hours remaining**
**Status:** 🔄 **IN PROGRESS** (2025-11-15)
**Category:** Documentation

**Description:**
Enhance documentation for users, developers, and researchers.

**Current State:**
- Good README with setup instructions
- DATA_DICTIONARY.md with comprehensive data documentation
- NOTES.md with references
- README_CEJST.md for CEJST workflow
- Test README
- Notebooks demonstrate workflows

**Progress (2025-11-15):**
- ✅ Created DEVELOPMENT.md with developer guidelines
- ✅ Documented logging best practices with code examples
- ✅ Documented library vs entry point patterns
- ✅ Documented TQDM integration
- ❌ .env.example not yet created (mentioned but file doesn't exist)
- ❌ No API documentation yet
- ❌ No auto-generated docs yet
- ❌ Contributing guidelines not yet created

**Improvements Needed:**

1. **API Documentation:**
   - ❌ Auto-generated API docs (Sphinx/MkDocs)
   - ❌ Module documentation
   - ❌ Function signatures and examples
   - ❌ Type hints throughout

2. **User Guides:**
   - ❌ Step-by-step tutorials
   - ❌ Common workflows
   - ❌ Troubleshooting guide (expand existing)
   - ❌ FAQ section

3. **Developer Guides:**
   - ✅ Development best practices (DEVELOPMENT.md)
   - ❌ Contributing guidelines (CONTRIBUTING.md)
   - ❌ Code style guide
   - ❌ Testing guide
   - ❌ Release process

4. **Research Documentation:**
   - ❌ Methodology documentation
   - ❌ Algorithm descriptions
   - ❌ Validation approach
   - ❌ Reproducibility guide

5. **Architecture Documentation:**
   - ❌ System design
   - ❌ Data flow diagrams (expand existing Mermaid)
   - ❌ Module dependencies
   - ❌ Extension points

**Tools:**
- **Sphinx**: Python standard, autodoc
- **MkDocs**: Modern, Markdown-based
- **Jupyter Book**: Integrate notebooks
- **Mermaid**: Diagrams (already used)

**Remaining Work:**
1. Choose documentation tool
2. Set up documentation structure
3. Add docstrings throughout code
4. Write CONTRIBUTING.md
5. Write guides and tutorials
6. Deploy documentation site

---

### IMP-004: Improved Logging and Monitoring
**Priority:** Medium
**Effort:** Medium (16-24 hours) → **8-12 hours remaining**
**Status:** 🔄 **IN PROGRESS** (2025-11-15)
**Category:** Observability

**Description:**
Enhance logging for better debugging and monitoring.

**Current State:**
- Basic logging in most modules
- Logs to `pipeline_log.txt`, `processing_log.txt`, etc.
- No structured logging
- No centralized log aggregation

**Progress (2025-11-15):**
- ✅ Replaced print() statements with proper logging in library modules
- ⚠️ CLI scripts (`probe_data_sources.py`, `changelog.py`) still use print() for user-facing output (acceptable for CLI)
- ✅ Established consistent logging patterns:
  - Entry scripts use `logging.basicConfig()` with handlers
  - Library modules use `logger = logging.getLogger(__name__)`
- ✅ Created DEVELOPMENT.md with logging guidelines and examples
- ✅ Documented integration with TQDM progress bars
- ✅ Proper log levels used (DEBUG, INFO, WARNING, ERROR)
- ❌ No structured logging (JSON) yet
- ❌ No centralized log aggregation yet
- ❌ No monitoring dashboards yet

**Improvements:**

1. **Structured Logging:**
   - ❌ JSON format for machine parsing
   - ✅ Consistent log levels
   - ❌ Context information (user, region, operation)
   - ❌ Request IDs for tracing

2. **Log Levels:**
   - ✅ Properly applied throughout codebase
   ```python
   DEBUG: Detailed diagnostic info
   INFO: General informational messages
   WARNING: Warning messages (degraded but functional)
   ERROR: Error messages (operation failed)
   CRITICAL: Critical failures (system/data integrity)
   ```

3. **Performance Logging:**
   - ❌ Operation timing
   - ❌ Resource usage
   - ❌ Progress tracking
   - ❌ Bottleneck identification

4. **Log Management:**
   - ❌ Log rotation
   - ❌ Compression
   - ❌ Retention policy
   - ❌ Search and analysis

5. **Monitoring:**
   - ❌ Metrics collection (Prometheus)
   - ❌ Dashboards (Grafana)
   - ❌ Alerting
   - ❌ Health checks

**Remaining Work:**
1. Add `structlog` library for structured logging
2. Add performance/timing logging
3. Set up log rotation and management
4. Create monitoring dashboards (optional)

---

### IMP-005: Code Quality Tooling
**Priority:** Medium
**Effort:** Small (8-16 hours)
**Status:** ✅ **COMPLETED** (2025-11-15)
**Category:** Development Tools

**Description:**
Set up code quality tools for consistent style and best practices.

**Completed Implementation:**

1. **Formatting:**
   - ✅ **Black**: Opinionated code formatter (line length: 100)
   - ✅ **isort**: Import sorting (Black profile)
   - ✅ **nbQA**: Notebook formatting integration

2. **Linting:**
   - ✅ **Ruff**: Fast modern linter with multiple rule sets
   - ✅ **mypy**: Static type checking
   - ✅ **bandit**: Security linting

3. **Pre-commit Hooks:**
   - ✅ Automatic formatting (Black, isort)
   - ✅ Linting checks (Ruff)
   - ✅ Type checking (mypy)
   - ✅ Security scanning (Bandit)
   - ✅ File checks (trailing whitespace, EOF, YAML/JSON validation)
   - ✅ Notebook formatting (nbQA integration)

4. **IDE Configuration:**
   - ✅ `.editorconfig` for cross-IDE consistency

**Configuration Files Created:**
- ✅ `.pre-commit-config.yaml` - Pre-commit hooks configuration
- ✅ `pyproject.toml` - All tool configurations (Black, isort, Ruff, mypy, Bandit, coverage)
- ✅ `.editorconfig` - Editor configuration for multiple file types
- ✅ `.github/workflows/code-quality.yml` - CI/CD workflow for code quality checks
- ✅ `CONTRIBUTING.md` - Developer guidelines and tool usage documentation

**Tools Added to Dev Dependencies:**
- ✅ black>=24.0.0
- ✅ isort>=5.13.0
- ✅ ruff>=0.6.0
- ✅ mypy>=1.11.0
- ✅ pre-commit>=3.8.0

**CI/CD Integration:**
- ✅ Automated formatting checks on push/PR
- ✅ Linting with Ruff
- ✅ Type checking with mypy
- ✅ Test execution with coverage
- ✅ Pre-commit hook validation

---

### IMP-006: Webmap Enhancements
**Priority:** Medium
**Effort:** Large (30-40 hours)
**Status:** ✅ **COMPLETED** (2025-11-09)
**Category:** Webmap / Visualization

**Description:**
Enhance the interactive webmap with additional features and improvements.

**Completed Features:**

1. **Map Features:**
   - ✅ Search by address/location (Nominatim geocoding)
   - ✅ Print/export functionality (print button, PNG export)
   - ✅ Bookmarkable views (URL hash state)
   - ❌ Measurement tools (removed - not necessary)

2. **Data Layers:**
   - ✅ Toggle layers on/off (integrated into legend with eye icons)
   - ✅ Remove census block outlines (reduces visual clutter)
   - ✅ Collapsible legend
   - ❌ Layer opacity control (removed - complicates legend interpretation)
   - ❌ Base map selection (removed - not needed)

3. **Interactive Analysis:**
   - ✅ Click for detailed info popup with comprehensive block data
   - ✅ Only census blocks are clickable (conserved lands and CEJST are visual layers only)
   - ❌ Enhanced hover tooltips (removed - only show details on click)
   - ❌ Buffer analysis (not implemented)
   - ❌ Demographic charts (not implemented)
   - ❌ Access comparisons (not implemented)

4. **Performance:**
   - ✅ PMTiles-based tile format (optimized rendering)
   - ✅ Mobile optimization (see FR-003)
   - ❌ Lazy loading (not implemented)
   - ❌ Tile caching (handled by browser)

5. **User Experience:**
   - ✅ Enhanced legend showing full spectrum of walk times (complete color scale)
   - ✅ Integrated controls with MapLibre native styling
   - ✅ Clean, compact popups
   - ✅ Proper spacing and positioning of controls
   - ❌ Tutorial/help overlay (not implemented)
   - ❌ Share functionality (not implemented)
   - ❌ Embed code for external sites (not implemented)

**Files:**
- `docs/index.html`
- `docs/js/map.js`
- `docs/js/scripts.js`
- `docs/css/` (styles)

**Notes:**
- Controls integrated with MapLibre's native control system
- Search positioned in top-left, legend in bottom-left
- Print and export buttons in top-right with navigation controls
- Removed site menu for single-page site

---

### IMP-007: Dependency Management Improvements
**Priority:** Low
**Effort:** Medium (12-16 hours)
**Category:** Dependencies

**Description:**
Improve dependency management and update strategy.

**Current Issues:**
- OSMnx pinned to old version (see TD-002)
- Mix of `>=` and `==` version specifications
- No automated dependency updates
- No security scanning (see TD-009)

**Improvements:**

1. **Version Strategy:**
   - Define when to pin (`==`) vs allow updates (`>=`)
   - Document version decision rationale
   - Regular dependency reviews

2. **Update Process:**
   - Automated dependency update PRs (Dependabot/Renovate)
   - Testing strategy for updates
   - Changelog for dependency changes
   - Rollback procedure

3. **Security:**
   - Vulnerability scanning
   - Security advisories monitoring
   - Timely security updates
   - Security policy

4. **Documentation:**
   - Dependency justification
   - Known issues/workarounds
   - Alternative packages considered

**Tools:**
- Dependabot (GitHub native)
- Renovate (more powerful)
- `pip-audit` or `safety`
- `pipdeptree` for dependency visualization

---

### IMP-008: Census Data Caching
**Priority:** Low
**Effort:** Medium (12-20 hours)
**Category:** Performance / Data Management

---

### IMP-009: Enhanced Print Layouts
**Priority:** Medium
**Effort:** Medium (12-16 hours)
**Status:** ✅ **COMPLETED** (2025-11-15)
**Category:** Webmap / Visualization

**Description:**
Improve print layouts for the webmap to create publication-ready printed maps.

**Current State:**
- ✅ Enhanced print functionality with optimized layout
- ✅ Print styles show properly formatted legend, title, metadata, scale bar, and north arrow
- ✅ Publication-ready print layout with proper styling
- ✅ Dynamic metadata population (date, coordinates, zoom, scale)

**Completed Enhancements:**

1. **Print Layout Options:**
   - ✅ Landscape and portrait orientation support with CSS @page rules
   - ✅ Letter page size optimized
   - ✅ Proper margin controls (10mm landscape, 15mm portrait)

2. **Map Styling for Print:**
   - ✅ Enhanced legend for print (larger, clearer, always visible)
   - ✅ Print-optimized styling with borders and shadows
   - ✅ Title and metadata inclusion (map title, date, center, zoom)
   - ✅ Scale bar with dynamic calculation
   - ✅ North arrow indicator
   - ✅ Attribution and data source information

3. **Layout Customization:**
   - ✅ Title block with map name and subtitle
   - ✅ Legend placement (bottom-right)
   - ✅ Metadata panel (bottom-left)
   - ✅ Scale bar and north arrow (top-right)

4. **Export Formats:**
   - ✅ PNG export functionality (already existed, maintained)
   - ✅ Browser print to PDF support

5. **Dynamic Updates:**
   - ✅ Print metadata updates on print button click
   - ✅ Scale calculation based on current zoom level
   - ✅ Map center coordinates display
   - ✅ Current date display

**Potential Future Enhancements:**
- Multiple page size options (A4, Legal) via print dialog
- Custom page size configuration
- Higher resolution rendering for print
- Advanced PDF export with multi-page support
- Print preview dialog before printing
- Print templates for common use cases
- Inset maps
- Custom header/footer options

**Implementation Summary:**
1. ✅ Created comprehensive print-specific CSS styles with @media print
2. ✅ Added print layout HTML elements (title, metadata, scale, north arrow, attribution)
3. ✅ Implemented dynamic metadata population in JavaScript
4. ✅ Added scale calculation based on map zoom and latitude
5. ✅ Integrated print functionality with existing print button

**Benefits:**
- ✅ Publication-ready maps with professional appearance
- ✅ Comprehensive map information for documentation
- ✅ Properly scaled and oriented print output
- ✅ Clear attribution and data sources

**Files Modified:**
- `docs/css/styles.css` (enhanced print media queries at lines 13437-13716)
- `docs/js/map.js` (print metadata functions at lines 1029-1128)
- `docs/index.html` (print-only HTML elements at lines 40-67)

**Dependencies:**
- IMP-006 (Webmap Enhancements) - Print functionality already existed

---

### IMP-008: Census Data Caching
**Priority:** Low
**Effort:** Medium (12-20 hours)
**Category:** Performance / Data Management

**Description:**
Implement caching for Census API calls to improve performance and reduce API usage.

**Current State:**
- Census API calls made each pipeline run
- No caching of Census data
- Rate limiting risks
- Dependency on API availability

**Improvements:**

1. **Response Caching:**
   - Cache API responses locally
   - TTL-based cache invalidation
   - Cache key based on query parameters
   - Cache versioning

2. **Smart Updates:**
   - Check data freshness before API calls
   - Incremental updates only
   - Batch API requests
   - Parallel requests with rate limiting

3. **Cache Management:**
   - Cache statistics
   - Cache cleaning
   - Manual cache refresh
   - Cache sharing across runs

4. **Fallback Strategy:**
   - Use cached data if API unavailable
   - Stale data warnings
   - Manual data provision

**Benefits:**
- Faster pipeline runs
- Reduced API dependency
- Lower risk of rate limiting
- Better offline capability

---

## 📊 Priority Matrix

### Priority Definitions

**High Priority:**
- Critical for core functionality
- Security concerns
- Blocking other work
- High user impact

**Medium Priority:**
- Important but not urgent
- Quality improvements
- Nice-to-have features
- Moderate user impact

**Low Priority:**
- Future enhancements
- Minor improvements
- Can be deferred
- Low immediate impact

### Effort Definitions

- **Small:** 4-8 hours (< 1 day)
- **Medium:** 12-32 hours (1-4 days)
- **Large:** 40-80 hours (1-2 weeks)

### Quick Wins (High Priority, Small/Medium Effort)

1. ✅ ~~**TD-009:** No Dependency Security Scanning~~ - COMPLETED (2025-11-15)
2. ✅ ~~**IMP-005:** Code Quality Tooling~~ - COMPLETED (2025-11-15)
3. **TD-007:** Error Handling Strategy - Medium effort (20-30 hours), critical for reliability
4. **TD-003:** Mixed Import Patterns for H3 Module - Small effort (4-8 hours), improves developer experience

### Strategic Items (High Priority, Large Effort)

1. **TD-001:** Python 3.10 Version Lock - Medium effort (16-24 hours), enables future improvements
2. **TD-004:** Incomplete Test Coverage - Large effort (40-60 hours), critical for long-term maintainability
3. **IMP-001:** Performance Optimization - Large effort (40-60 hours), core functionality improvement
4. **FR-001:** Multi-State Support - Large effort (60-80 hours), major feature expansion

### Medium Priority Items Worth Noting

1. **TD-002:** Outdated OSMnx Version - Medium effort (12-16 hours), performance and compatibility improvements
2. **TD-005:** Hard-coded File Paths - Medium effort (16-24 hours), prerequisite for FR-001
3. **TD-008:** Incomplete CI/CD Pipeline - Medium effort (16-24 hours), extends existing deployment automation
4. **TD-011:** H3 Not Used as Primary Geographic Unit - Large effort (72-104 hours), addresses original analysis methodology goal
5. **IMP-002:** Enhanced Data Validation - Medium effort (24-32 hours), improves data quality
6. **FR-002:** Interactive Dashboard - Large effort (50-70 hours), improves accessibility for non-technical users
7. **FR-003:** Mobile-Friendly Webmap - Medium effort (20-30 hours), improves user experience
8. **FR-004:** Complete H3 Implementation - Large effort (72-104 hours), completes original H3 standardization goal
9. **IMP-003:** Documentation Improvements - Medium effort (20-30 hours), improves maintainability
10. **IMP-004:** Improved Logging and Monitoring - Medium effort (16-24 hours), improves debugging
11. **IMP-006:** Webmap Enhancements - Large effort (30-40 hours), improves webmap functionality

---

## 📈 Recommended Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
**Focus: Code Quality, Testing, Security**

**Quick Wins:**
1. ✅ ~~TD-009: Dependency Security Scanning~~ - COMPLETED (2025-11-15)
2. ✅ ~~IMP-005: Code Quality Tooling~~ - COMPLETED (2025-11-15)
3. TD-003: H3 Module Import Pattern (Small, 4-8 hours)

**Core Infrastructure:**
4. TD-008: CI/CD Pipeline Extension (Medium, 16-24 hours) - Add test automation to existing deployment workflow
5. TD-007: Error Handling Strategy (Medium, 20-30 hours)
6. TD-004: Test Coverage - Priority Areas (Large, 40-60 hours) - Focus on critical path first

**Total Phase 1 Effort:** ~88-134 hours remaining (2-3.5 weeks full-time)
**Completed:** ~12-16 hours (TD-009 + IMP-005)

---

### Phase 2: Performance & Stability (Months 2-4)
**Focus: Optimization, Reliability**

**Dependency Updates:**
1. TD-001: Python Version Upgrade (Medium, 16-24 hours)
2. TD-002: OSMnx Update (Medium, 12-16 hours)

**Core Improvements:**
3. IMP-001: Performance Optimization (Large, 40-60 hours) - Critical for scalability
4. IMP-002: Enhanced Data Validation (Medium, 24-32 hours)
5. IMP-004: Improved Logging and Monitoring (Medium, 16-24 hours)

**Total Phase 2 Effort:** ~110-150 hours (2.75-4 weeks full-time)

---

### Phase 3: Code Cleanup & Preparation (Months 4-5)
**Focus: Maintainability, Multi-State Preparation**

**Code Quality:**
1. TD-005: Hard-coded Paths Refactoring (Medium, 16-24 hours) - **Prerequisite for FR-001**
2. TD-010: Notebook Code Duplication (Large, 30-40 hours)
3. IMP-003: Documentation Improvements (Medium, 20-30 hours)

**Optional:**
4. TD-006: Data Format Migration (Large, 30-40 hours) - Can be deferred if not blocking

**Total Phase 3 Effort:** ~65-95 hours (1.5-2.5 weeks full-time)

---

### Phase 4: Feature Development (Months 5-8)
**Focus: New Capabilities**

**Major Feature:**
1. FR-001: Multi-State Support (Large, 60-80 hours) - **Requires TD-005 completion**

**Webmap Improvements:**
2. FR-003: Mobile-Friendly Webmap (Medium, 20-30 hours)
3. IMP-006: Webmap Enhancements (Large, 30-40 hours)

**Total Phase 4 Effort:** ~110-150 hours (2.75-4 weeks full-time)

---

### Phase 5: Advanced Features (Months 8-12)
**Focus: Enhanced User Experience**

**Optional Enhancements:**
1. FR-002: Interactive Dashboard (Large, 50-70 hours) - Improves accessibility for non-technical users
2. IMP-007: Dependency Management Improvements (Medium, 12-16 hours)
3. IMP-008: Census Data Caching (Medium, 12-20 hours)

**Total Phase 5 Effort:** ~75-105 hours (2-2.5 weeks full-time)

---

### Summary by Priority

**Must Have (High Priority):**
- Phase 1: ✅ TD-009 (COMPLETED), ✅ IMP-005 (COMPLETED), TD-007, TD-004, TD-008
- Phase 2: TD-001, IMP-001, IMP-002
- Phase 3: TD-005 (prerequisite for FR-001)
- Phase 4: FR-001

**Should Have (Medium Priority):**
- Phase 2: TD-002, IMP-004
- Phase 3: TD-010, IMP-003
- Phase 4: FR-003, IMP-006
- Phase 5: FR-002

**Nice to Have (Low Priority):**
- Phase 3: TD-006 (can be deferred)
- Phase 5: IMP-007, IMP-008

---

## 🎯 Effort Estimation Guide

### Factors Affecting Effort

1. **Complexity:**
   - Algorithm changes
   - Architecture changes
   - Integration requirements

2. **Dependencies:**
   - Other tasks must complete first
   - External dependencies
   - Team coordination

3. **Testing:**
   - Test development time
   - Integration testing
   - User acceptance testing

4. **Documentation:**
   - Code documentation
   - User documentation
   - Tutorial creation

5. **Deployment:**
   - Migration planning
   - Deployment automation
   - Rollback procedures

### Estimation Confidence

- **High Confidence:** Well-understood, similar to past work
- **Medium Confidence:** Some unknowns, new technology
- **Low Confidence:** Significant unknowns, research needed

Most estimates in this document are medium confidence and should be refined during implementation planning.

---

## 📝 Notes on Implementation

### Dependencies Between Items

Some items have dependencies and should be implemented in order:

**Critical Dependencies:**
- `TD-005 → FR-001` (Hard-coded paths must be fixed before multi-state expansion)
- `TD-004 → All refactoring work` (Testing enables confident refactoring)
- `TD-001 → IMP-001` (Python upgrade enables performance improvements)

**Recommended Order:**
- `TD-008 → TD-004` (CI/CD should include test automation before expanding test coverage)
- `TD-002 → IMP-001` (OSMnx update may provide performance improvements)
- `TD-006 → IMP-001` (Data format affects performance, but can be deferred)

**Optional Dependencies:**
- `FR-003 → IMP-006` (Mobile optimization can inform webmap enhancements)
- `IMP-002 → FR-001` (Data validation helps ensure multi-state data quality)
- `TD-011 → FR-004` (Technical debt item tracks the gap, FR-004 addresses it)

### Risk Mitigation

For high-risk changes:
1. Create feature branch
2. Implement with comprehensive tests
3. Performance benchmarking
4. Document rollback procedure
5. Phased rollout

### Maintenance Budget

Recommended allocation:
- 40% New features
- 30% Technical debt
- 20% Improvements
- 10% Bug fixes / Security updates

---

## 🔄 Review and Update Process

This backlog should be reviewed and updated:
- **Monthly:** Priority adjustments, new items
- **Quarterly:** Roadmap revision, effort calibration
- **Annually:** Strategic direction, major initiatives

**Last Review:** 2025-11-09
**Next Review:** 2025-12-09

---

## 📞 Contact & Contributions

For questions or to contribute:
- **Project Lead:** Philip Mathieu (mathieu.p@northeastern.edu)
- **Documentation:** See README.md and DATA_DICTIONARY.md
- **Issues:** GitHub Issues (if repository is public)

---

**Document Version:** 1.4.1
**Last Updated:** 2025-11-15
**Previous Version:** 1.4 (2025-11-15)
**Analysis Method:** Comprehensive codebase review, dependency analysis, and best practices research

**Revision Notes:**

**v1.4.1 (2025-11-15):**
- Accuracy verification: Reviewed all status indicators against actual codebase
- Corrected IMP-003: .env.example not yet created (was incorrectly marked as completed)
- Clarified IMP-004: Print statements in CLI scripts are acceptable for user-facing output
- Updated TD-003: Fixed completion date placeholder and added note about legacy notebooks
- Verified TD-009, IMP-005, IMP-006, FR-003, IMP-009 completion status (all accurate)

**v1.4 (2025-11-15):**
- Updated TD-007 (Error Handling Strategy) - marked as IN PROGRESS
  - Fixed 4 empty except blocks with proper error logging
  - Documented progress and remaining work
- Updated IMP-004 (Improved Logging and Monitoring) - marked as IN PROGRESS
  - Replaced print() statements with proper logging in library modules
  - CLI scripts still use print() for user-facing output (acceptable)
  - Established consistent logging patterns
  - Created DEVELOPMENT.md with logging guidelines
- Updated IMP-003 (Documentation Improvements) - marked as IN PROGRESS
  - Created DEVELOPMENT.md with developer best practices
  - Corrected: .env.example not yet created (was incorrectly marked as completed)
- Updated TD-003 (H3 Module Import Pattern) - corrected completion date from placeholder
  - Added note about legacy notebooks using separate h3utils.py file
- Updated effort estimates for in-progress items
- Added recent completions section
- Verified accuracy of all status indicators against codebase

**v1.3 (2025-11-09):**
- Added TD-011: H3 Not Used as Primary Geographic Unit (technical debt)
- Added FR-004: Complete H3 Implementation as Primary Geographic Unit (feature request)
- Integrated findings from H3_PROGRESS_ASSESSMENT.md
- Updated Medium Priority Items section to include H3-related items
- Added dependency relationship between TD-011 and FR-004

**v1.2 (2025-11-09):**
- Rewrote prioritization sections to reflect streamlined backlog
- Removed references to deleted items (FR-004, FR-005, FR-006, FR-007, FR-008, IMP-009, IMP-010)
- Updated roadmap to focus on remaining items only
- Enhanced Quick Wins and Strategic Items sections with effort estimates
- Added Medium Priority Items section for better visibility
- Restructured roadmap with clearer phase descriptions and effort estimates
- Updated dependencies section to reflect current backlog structure

**v1.1 (2025-11-09):**
- Corrected TD-008 status: deployment pipeline exists, but test automation is missing
- Updated TD-002 to reflect current year (2025)
- Verified TD-006: GeoParquet migration file exists
- Updated status indicators (✅/❌/⚠️) throughout for clarity
- Clarified current state of various tools and scripts
