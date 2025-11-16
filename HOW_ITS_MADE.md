# How It's Made: The Access Project Pipeline

> **For Graduate Students and Researchers**
> This document provides a detailed technical deep-dive into the Access project pipeline, from data acquisition through analysis. It's designed to help other researchers understand the methodology, learn from design decisions, and potentially adapt this approach for their own work.

## Table of Contents

1. [Project Evolution](#project-evolution)
2. [Pipeline Overview](#pipeline-overview)
3. [Step-by-Step Pipeline Walkthrough](#step-by-step-pipeline-walkthrough)
4. [Key Algorithms and Methodologies](#key-algorithms-and-methodologies)
5. [Design Decisions and Trade-offs](#design-decisions-and-trade-offs)
6. [Performance Considerations](#performance-considerations)
7. [Extending the Pipeline](#extending-the-pipeline)

---

## Project Evolution

This project began as a graduate school research project analyzing spatial accessibility to conservation lands in Maine. Over time, it has evolved from a collection of Jupyter notebooks into a modular, reusable pipeline that can be extended to other regions.

### Initial Approach (Notebook-Based)
- **Phase 1**: Exploratory analysis in Jupyter notebooks
- **Phase 2**: Walk time calculations using NetworkX ego graphs
- **Phase 3**: Integration with Census and CEJST data
- **Phase 4**: Statistical analysis and visualization

### Current Architecture (Modular Pipeline)
- **Modular Design**: Core logic extracted into reusable Python modules
- **Pipeline Script**: Automated end-to-end processing (`src/run_pipeline.py`)
- **Multi-State Support**: Configuration system for regional expansion
- **Performance Optimizations**: Rustworkx integration, parallel processing

### Key Learnings
1. **Start with notebooks for exploration**, but migrate to modules for production
2. **Graph algorithms are computationally expensive** - optimization is critical
3. **Census geography changes** require careful handling (2010 → 2020 transition)
4. **Data format choices matter** - shapefiles have limitations for large datasets

---

## Pipeline Overview

The Access pipeline transforms raw spatial and demographic data into analysis-ready datasets with walk time metrics, demographic characteristics, and equity indicators.

### High-Level Data Flow

```
Raw Data Sources
    ↓
[Step 1] Graph Construction & Node Mapping
    ↓
[Step 2] Walk Time Calculation
    ↓
[Step 3] Data Merging & Aggregation
    ↓
[Step 4] Census & CEJST Integration
    ↓
[Step 5] Statistical Analysis
    ↓
[Step 6] Visualization & Webmap Generation
```

### Input Data Requirements

1. **Street Network**: OSMnx graph (`.graphml` format)
2. **Census Blocks**: TIGER/Line shapefiles with 2020 geography
3. **Conserved Lands**: State-specific shapefile of protected areas
4. **Census Data**: P.L. 94-171 Redistricting Data (block-level population)
5. **CEJST Data**: Climate Equity and Justice Screening Tool (tract-level)
6. **Relationship File**: Census 2010-2020 relationship file (for geography mapping)

### Output Products

1. **Walk Times**: Minimum walking time from each block to nearest conserved land
2. **EJ Blocks**: Blocks with walk times, demographics, and equity metrics
3. **Visualizations**: Publication-ready figures and maps
4. **Webmap**: Interactive PMTiles-based visualization
5. **H3 Relationships**: Hexagon indexing for alternative aggregation

---

## Step-by-Step Pipeline Walkthrough

### Step 1: Graph Construction & Node Mapping

**Purpose**: Create a walkable street network and map geographic features to network nodes.

#### 1.1 Download Street Network (`src/download_graphs.py`)

**What it does**:
- Uses OSMnx to download OpenStreetMap street network data
- Filters for walkable paths (excludes highways, motorways)
- Simplifies the graph topology
- Saves as GraphML format for efficient loading

**Key Parameters**:
- `network_type='walk'`: Filters for pedestrian-accessible roads
- `simplify=True`: Reduces graph complexity while preserving connectivity
- Custom filters for Maine-specific road types

**Output**: `data/graphs/maine_walk.graphml`

**Why this approach**:
- OSMnx provides a clean interface to OpenStreetMap data
- GraphML format preserves all edge/node attributes
- Simplification reduces computational load without losing accuracy

#### 1.2 Find Centroids (`src/find_centroids.py`)

**What it does**:
- Calculates centroid for each census block and conserved land polygon
- Finds nearest OSMnx node to each centroid
- Creates mapping: `GEOID20` → `osmid` (for blocks) and `feature_id` → `osmid` (for lands)

**Algorithm**:
1. Calculate geometric centroid of each polygon
2. Build spatial index (R-tree) of graph nodes
3. Query nearest node for each centroid
4. Handle edge cases (centroids outside network, islands)

**Output**:
- `data/blocks/tl_2020_23_tabblock20_with_nodes.shp.zip`
- `data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip`

**Why this approach**:
- Network analysis requires discrete nodes, not continuous polygons
- Nearest-node mapping is standard practice in network analysis
- Spatial indexing makes lookup efficient (O(log n) vs O(n))

**Challenges**:
- Blocks in rural areas may be far from network
- Islands require special handling (no network connection)
- Large polygons may have centroids outside the polygon

---

### Step 2: Walk Time Calculation

**Purpose**: Calculate minimum walking time from each census block to each conserved land.

**Module**: `src/walk_times/calculate.py`

#### 2.1 Algorithm: Bounded Dijkstra

**What it does**:
For each block centroid node, finds all conserved land nodes reachable within specified time thresholds (5, 10, 15, 20, 30, 45, 60 minutes).

**Implementation Details**:

```python
# Pseudocode
for each block_centroid_node:
    distances = bounded_dijkstra(
        graph,
        source=block_centroid_node,
        max_distance=max_trip_time
    )

    for each conserved_land_node:
        if conserved_land_node in distances:
            trip_time = smallest_threshold_that_fits(distances[conserved_land_node])
            record(block_centroid_node, conserved_land_node, trip_time)
```

**Key Optimizations**:

1. **Bounded Dijkstra**: Stops exploration once max trip time is reached
   - Reduces computation from O(V log V) to O(E_subgraph)
   - Critical for large graphs (Maine has ~500K nodes)

2. **Rustworkx Integration**:
   - Rust-based graph library (10-100x faster than NetworkX)
   - Used for shortest path calculations
   - NetworkX retained for graph construction (better OSMnx integration)

3. **Parallel Processing**:
   - Process multiple blocks simultaneously
   - Uses `joblib` for multiprocessing
   - Configurable via `n_jobs` parameter (-1 = all CPUs)

4. **Time Attribute Pre-computation**:
   - Edge travel time calculated once: `time = length / (speed * 1000 / 60)`
   - Default walking speed: 4.5 km/h (based on pedestrian research)

**Output**: `data/walk_times/walk_times_block_df.parquet`

**Columns**:
- `block_osmid`: OSMnx node ID of block centroid
- `land_osmid`: OSMnx node ID of conserved land
- `trip_time`: Minimum trip time threshold (5, 10, 15, 20, 30, 45, or 60 minutes)

**Performance**:
- Maine (~100K blocks): ~1-2 hours on 8-core machine
- Serial processing: ~4-8 hours
- Memory usage: ~2-4 GB (graph + results)

**Why this approach**:
- **Ego graphs** (original notebook approach) were too slow
- **Bounded Dijkstra** provides same results with better performance
- **Multiple time thresholds** allow flexible analysis (not just binary access)
- **Minimum time per land** captures closest access point

**Alternative Approaches Considered**:
1. **Isochrones**: Faster but less precise (polygon-based, not node-based)
2. **Pre-computed distance matrix**: Too large (100K × 1K = 100M entries)
3. **Sampling**: Faster but loses precision for equity analysis

---

### Step 3: Data Merging & Aggregation

**Purpose**: Combine walk times with block geometries and aggregate to block level.

**Module**: `src/merging/blocks.py`

#### 3.1 Merge Walk Times

**What it does**:
- Joins walk time results with block geometries
- Creates access columns (`AC_5`, `AC_10`, etc.) indicating if block has access within that time
- Handles one-to-many relationships (one block → multiple lands)

**Access Calculation**:
```python
# For each time threshold
blocks[f"AC_{time}"] = blocks.groupby("GEOID20")["trip_time"].apply(
    lambda x: 1 if any(x <= time) else 0
)
```

**Output**: `data/joins/block_merge.parquet`

#### 3.2 Dissolve Blocks

**What it does**:
- Aggregates multiple polygon parts per block (some blocks are multipolygons)
- Sums access indicators (1 = has access, 0 = no access)
- Preserves geometry and other attributes

**Why needed**:
- Census blocks can be split (e.g., by water bodies)
- Need single record per `GEOID20` for analysis
- Dissolve creates clean one-to-one mapping

**Output**: `data/joins/block_dissolve.parquet`

---

### Step 4: Census & CEJST Integration

**Purpose**: Add demographic and equity data to blocks.

**Module**: `src/merging/analysis.py`

#### 4.1 Census Data Integration

**What it does**:
- Fetches block-level population data from Census API
- Caches responses locally to reduce API calls
- Merges with blocks on `GEOID20`

**Census Variables**:
- `P1_001N`: Total population
- Additional demographic variables (race, ethnicity, age, etc.)

**Caching Strategy**:
- Saves API responses to `data/cache/census/`
- Cache key based on state FIPS and variable list
- Allows offline processing after first run
- `refresh_cache=True` forces new API calls

**Why caching**:
- Census API has rate limits
- Data doesn't change frequently
- Enables reproducible research without API dependency

#### 4.2 CEJST Data Processing

**Challenge**: CEJST uses 2010 Census geography (tracts), but blocks use 2020 geography.

**Solution**: Area-weighted aggregation using Census relationship file.

**Algorithm**:

1. **Load Relationship File**: Maps 2010 blocks → 2020 blocks with intersection areas
2. **Calculate Weights**:
   ```
   weight = intersection_area / 2020_block_area
   ```
3. **Aggregate**: Weighted average of CEJST variables per 2020 block
   ```python
   cejst_2020_block = weighted_average(
       cejst_2010_tract_values,
       weights=intersection_areas
   )
   ```

**Key Variables**:
- `TC`: Total Threshold Criteria Exceeded (disadvantaged indicator)
- `CC`: Total Categories Exceeded

**Output**: Block-level CEJST metrics aligned with 2020 geography

**Why this approach**:
- **Area weighting** is standard for cross-geography aggregation
- **Preserves statistical properties** better than simple assignment
- **Handles boundary changes** between 2010 and 2020

**Limitations**:
- Assumes uniform distribution within tracts (may not hold)
- Small intersection areas can create extreme weights
- Some blocks may have no CEJST data (water blocks, new blocks)

#### 4.3 Demographic Calculations

**What it does**:
- Calculates population density: `POPDENSE = population / land_area`
- Computes demographic percentages (race, ethnicity, etc.)
- Creates boolean indicators for analysis

**Output**: `data/joins/ejblocks.parquet`

**Final Dataset Contains**:
- Block geometries
- Walk time access indicators (`AC_5`, `AC_10`, etc.)
- Population and demographics
- CEJST equity metrics
- Calculated demographic percentages

---

### Step 5: Statistical Analysis

**Purpose**: Analyze disparities in access by demographic and equity characteristics.

**Module**: `src/analysis/statistical.py`

#### 5.1 Access Disparity Analysis

**Key Question**: Are disadvantaged communities (CEJST) more likely to lack access?

**Methodology**:
1. Create binary indicators: `AC_10_bool`, `TC_bool` (disadvantaged)
2. Cross-tabulation: Access × Disadvantage status
3. Calculate odds ratios and risk ratios
4. Statistical tests (chi-square, MANOVA)

**Example Output**:
```
Disadvantaged communities are 24% more likely to lack access
to conserved land within a 10-minute walk.
```

#### 5.2 Multivariate Analysis

**MANOVA**: Tests if multiple access thresholds differ by disadvantage status simultaneously.

**Why MANOVA**:
- Multiple dependent variables (AC_5, AC_10, AC_15, etc.)
- Controls for multiple comparisons
- More powerful than separate ANOVAs

---

### Step 6: Visualization & Webmap

**Purpose**: Create publication-ready figures and interactive webmap.

**Module**: `src/visualization/figures.py`

#### 6.1 Static Figures

**Types**:
- Access maps (choropleth by walk time)
- Demographic distribution maps
- Equity comparison maps
- Statistical summary charts

**Technology**: Matplotlib, GeoPandas

#### 6.2 Interactive Webmap

**Technology Stack**:
- **MapLibre GL JS**: Vector tile rendering
- **PMTiles**: Cloud-optimized tile format
- **Vanilla JavaScript**: No framework dependencies

**Data Pipeline**:
1. Convert GeoParquet/Shapefile → PMTiles
2. Separate layers: blocks, conserved lands, CEJST
3. Client-side rendering with MapLibre

**Why PMTiles**:
- Single file per layer (easier hosting)
- HTTP range requests (efficient loading)
- Vector tiles (scalable, interactive)
- Smaller file sizes than GeoJSON

**Features**:
- Click for block details
- Search by address
- Print/export functionality
- Mobile-responsive design

---

## Key Algorithms and Methodologies

### Network Analysis: Shortest Path Problem

**Problem**: Find shortest path from source to all targets within distance threshold.

**Solution**: Bounded Dijkstra's Algorithm

**Complexity**:
- Standard Dijkstra: O(V log V + E)
- Bounded Dijkstra: O(E_subgraph log V_subgraph)
- Where E_subgraph << E for sparse graphs

**Implementation**:
```python
def bounded_dijkstra(graph, source, max_distance):
    distances = {source: 0}
    queue = [(0, source)]

    while queue:
        current_dist, current = heapq.heappop(queue)

        if current_dist > max_distance:
            break  # Bounded: stop exploring beyond threshold

        for neighbor, edge_weight in graph.neighbors(current):
            new_dist = current_dist + edge_weight

            if new_dist <= max_distance and new_dist < distances.get(neighbor, inf):
                distances[neighbor] = new_dist
                heapq.heappush(queue, (new_dist, neighbor))

    return distances
```

### Geographic Aggregation: Area-Weighted Interpolation

**Problem**: Aggregate data from one geographic unit (2010 tracts) to another (2020 blocks).

**Solution**: Area-weighted averaging

**Formula**:
```
value_2020_block = Σ(value_2010_tract_i × intersection_area_i) / total_block_area
```

**Assumptions**:
- Uniform distribution within source units
- Intersection areas accurately represent overlap

**When it works well**:
- Source units are larger than target units
- Population/demographics are relatively uniform within tracts
- Boundary changes are minor

**When it breaks down**:
- Highly heterogeneous source units
- Very small intersection areas (extreme weights)
- Non-uniform distributions (e.g., population clustered in part of tract)

### Performance Optimization Strategies

1. **Algorithmic**:
   - Bounded search instead of full graph exploration
   - Spatial indexing for nearest-neighbor queries
   - Early termination when possible

2. **Implementation**:
   - Rustworkx for graph algorithms (Rust performance)
   - Parallel processing (multiprocessing)
   - Vectorized operations (NumPy/Pandas)

3. **Data Management**:
   - Caching API responses
   - Efficient file formats (Parquet > CSV > Shapefile)
   - Incremental processing where possible

---

## Design Decisions and Trade-offs

### 1. Blocks vs. Tracts vs. H3 Hexagons

**Decision**: Use Census blocks as primary geographic unit.

**Rationale**:
- **Blocks**: Finest granularity, official Census geography
- **Tracts**: Too coarse for walkability analysis (tracts can be large)
- **H3**: Standardized sizes, but requires additional processing

**Trade-offs**:
- ✅ Blocks provide fine-grained analysis
- ❌ Blocks have uneven sizes (urban vs. rural)
- ❌ Blocks can be very small (parks, parking lots)
- ⚠️ H3 infrastructure exists but not used as primary unit (see BACKLOG.md)

**Future Consideration**: H3 hexagons could provide more consistent analysis units.

### 2. Network-Based vs. Euclidean Distance

**Decision**: Use network-based (shortest path) distances.

**Rationale**:
- Walking requires following street network
- Euclidean distance underestimates true travel time
- Network analysis captures barriers (rivers, highways)

**Trade-offs**:
- ✅ More accurate for walkability
- ✅ Captures real-world constraints
- ❌ More computationally expensive
- ❌ Requires complete network data

**Alternative Considered**: Euclidean with buffer, but rejected for accuracy.

### 3. Multiple Time Thresholds vs. Single Threshold

**Decision**: Calculate access for multiple thresholds (5, 10, 15, 20, 30, 45, 60 min).

**Rationale**:
- Different policy questions require different thresholds
- Allows flexible analysis
- Single calculation provides all thresholds

**Trade-offs**:
- ✅ Flexibility for different research questions
- ✅ No need to re-run for different thresholds
- ❌ Slightly more computation (but minimal)
- ❌ More columns in output

**Alternative**: Single threshold (e.g., 10 minutes), but rejected for flexibility.

### 4. Minimum Time per Land vs. Average Time

**Decision**: Record minimum time to each conserved land.

**Rationale**:
- "Access" means ability to reach at least one land
- Minimum captures closest access point
- Average would be misleading (one close land + many far lands)

**Trade-offs**:
- ✅ Captures true access (can you get there?)
- ✅ Aligns with policy questions
- ❌ Doesn't capture quality (how many options?)
- ⚠️ Could add count of accessible lands (future enhancement)

### 5. Shapefile vs. GeoParquet

**Decision**: Migrating from Shapefile to GeoParquet.

**Rationale**:
- Shapefiles: Legacy format, 10-char field names, 2GB limit
- GeoParquet: Modern, efficient, cloud-optimized

**Status**: Migration in progress (see `src/migrate_to_geoparquet.py`)

**Trade-offs**:
- ✅ GeoParquet: Faster I/O, better compression, no field name limits
- ❌ Shapefile: Universal compatibility, works with all GIS software
- ⚠️ Hybrid approach: GeoParquet for processing, Shapefile for compatibility

---

## Performance Considerations

### Computational Bottlenecks

1. **Walk Time Calculation** (90% of runtime)
   - Solution: Bounded Dijkstra, Rustworkx, parallel processing
   - Current: ~1-2 hours for Maine (8 cores)
   - Target: <30 minutes

2. **Graph Loading** (5% of runtime)
   - Solution: GraphML format, caching
   - Current: ~2-5 minutes
   - Acceptable

3. **Data Merging** (3% of runtime)
   - Solution: Vectorized Pandas operations
   - Current: ~1-2 minutes
   - Acceptable

4. **CEJST Processing** (2% of runtime)
   - Solution: Efficient spatial joins
   - Current: ~30 seconds
   - Acceptable

### Memory Usage

- **Graph**: ~500MB (Maine network)
- **Blocks**: ~100MB (100K blocks)
- **Walk Times**: ~200MB (results)
- **Total**: ~1-2 GB peak

### Scalability

**Current Limits**:
- Maine: ~100K blocks, works well
- New England: ~500K blocks, feasible with optimization
- National: Would require distributed computing

**Optimization Opportunities**:
- Incremental processing (only changed blocks)
- Distributed computing (Dask, Spark)
- GPU acceleration (CuGraph)
- Pre-computed distance matrices for common queries

---

## Extending the Pipeline

### Adding a New State

1. **Data Acquisition**:
   - Download state's conserved lands shapefile
   - Download/update OSMnx graph
   - Ensure Census data available

2. **Configuration**:
   - Add state to `src/config/regions.py`
   - Define state FIPS, data paths
   - Test with `--state` parameter

3. **Processing**:
   ```bash
   python src/run_pipeline.py --state "NewHampshire"
   ```

### Adding New Analysis Variables

1. **Census Variables**: Add to `fetch_census_data()` field list
2. **CEJST Variables**: Already included in processing
3. **Custom Variables**: Add to `create_ejblocks()` merge step

### Modifying Walk Time Thresholds

Edit `src/config/defaults.py`:
```python
DEFAULT_TRIP_TIMES = [5, 10, 15, 20, 30, 45, 60]  # minutes
```

### Adding New Visualization Types

1. Add function to `src/visualization/figures.py`
2. Call from `generate_all_figures()`
3. Update webmap if needed

---

## Questions or Contributions

For questions about the pipeline or to contribute improvements:
- **Contact**: Philip Mathieu (mathieu.p@northeastern.edu)
- **Issues**: GitHub Issues
- **Documentation**: See README.md for usage, DATA_DICTIONARY.md for data details
