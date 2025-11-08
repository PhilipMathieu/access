# Task Assessment: Level of Effort Analysis

This document assesses the level of effort required for three major project tasks:
1. Replacing DVC with Git LFS
2. Updating layers when new data becomes available
3. Expanding analysis to use New England Protected Open Space dataset covering all of New England

---

## 1. Replacing DVC with Git LFS

### Current State
- **DVC Configuration**: 11 `.dvc` files tracking data directories
  - `data/graphs.dvc` (~162 MB)
  - `data/blocks.dvc` (~108 MB)
  - `data/conserved_lands.dvc` (~62 MB)
  - `data/tracts.dvc` (~3.1 MB)
  - Plus 7 other smaller files
- **DVC Remote**: Google Drive (`gdrive://1NP90N5H_E1MnXZ04YD0AyD2IiTPHzMOf`)
- **Existing Tools**: `src/remove_dvc.py` script already exists to remove DVC tracking
- **Git LFS Status**: Not currently installed

### Tasks Required

#### 1.1 Data Migration (Medium Effort)
- Remove all `.dvc` files (script exists)
- Install and configure Git LFS
- Migrate data files from DVC storage to Git LFS
- Update `.gitignore` to track large files with Git LFS
- Remove DVC configuration files (`.dvc/`, `.dvcignore`, `dvc.yaml`, `dvc.lock`)
- Remove DVC remote configuration

#### 1.2 Workflow Updates (Low-Medium Effort)
- Update documentation to replace DVC commands with Git LFS
- Update `run_notebooks.sh` and `setup_data.sh` if they reference DVC
- Update `src/probe_data_sources.py` to remove DVC checks
- Train team on Git LFS workflow (`git lfs pull`, `git lfs track`, etc.)

#### 1.3 Testing & Validation (Low Effort)
- Verify all data files are accessible after migration
- Test that notebooks can run with Git LFS-tracked files
- Ensure data integrity is maintained

### Challenges
- **Data Size**: ~340 MB total data (manageable for Git LFS)
- **Remote Storage**: Need to ensure Git LFS remote is configured (GitHub/GitLab LFS or external storage)
- **Team Training**: Team needs to learn Git LFS commands
- **No Pipeline Management**: DVC provides pipeline management that Git LFS doesn't (but this project doesn't appear to use DVC pipelines)

### Estimated Level of Effort
**Overall: LOW-MEDIUM (4-8 hours)**

- Data migration: 2-3 hours
- Workflow updates: 1-2 hours
- Documentation: 1 hour
- Testing: 1-2 hours

### Dependencies
- Git LFS installation
- Git LFS remote configuration (GitHub/GitLab or external storage)
- Team access to Git LFS remote

---

## 2. Updating Layers When New Data Becomes Available

### Current State
- **Data Sources**:
  - Census TIGER/Line (Blocks, Tracts) - updated annually
  - Maine GeoLibrary Conserved Lands - updated periodically
  - CEJST (Climate Equity and Justice Screening Tool) - updated periodically
  - Census API - real-time access
  - OSMnx/OpenStreetMap - continuously updated
- **Existing Tools**: `src/probe_data_sources.py` checks data source availability
- **Update Mechanism**: Currently manual (no automated updates)

### Tasks Required

#### 2.1 Automated Data Source Checking (Medium Effort)
- Enhance `src/probe_data_sources.py` to:
  - Check for updated versions of datasets
  - Compare file modification dates or version numbers
  - Detect schema changes in updated datasets
- Add version tracking for each data source

#### 2.2 Automated Download & Processing (Medium-High Effort)
- Create update scripts for each data source:
  - Census TIGER/Line: Check for newer year releases
  - Maine Conserved Lands: Check ArcGIS REST service for updates
  - CEJST: Check for new versions
  - OSMnx graphs: Re-download if needed
- Automate the processing pipeline:
  - Re-run `find_centroids.py` for updated shapefiles
  - Re-process with OSMnx node IDs
  - Validate data integrity after updates

#### 2.3 Data Validation & Schema Management (Medium Effort)
- Create validation scripts to:
  - Check for schema changes (new/removed columns)
  - Validate data quality (missing values, outliers)
  - Ensure coordinate system consistency
  - Check for data completeness
- Create schema versioning system

#### 2.4 Notification & Documentation (Low Effort)
- Add logging/notification when updates are detected
- Document update procedures
- Create changelog for data versions

### Challenges
- **Schema Changes**: Updated datasets may have different schemas
- **Breaking Changes**: Updates might break existing notebooks/analysis
- **Processing Time**: Re-processing large datasets (especially OSMnx graphs) takes time
- **Data Source Reliability**: Some sources may change URLs or formats

### Estimated Level of Effort
**Overall: MEDIUM-HIGH (16-24 hours)**

- Automated checking: 4-6 hours
- Download automation: 4-6 hours
- Processing automation: 4-6 hours
- Validation system: 2-4 hours
- Testing & documentation: 2-2 hours

### Dependencies
- Stable data source APIs/endpoints
- Understanding of update frequencies for each source
- Processing infrastructure (sufficient RAM for OSMnx)

---

## 3. Expanding Analysis to New England Protected Open Space Dataset

### Current State
- **Geographic Scope**: Maine only (FIPS code 23)
- **Protected Lands Dataset**: Maine Conserved Lands (Maine GeoLibrary)
- **Analysis Coverage**: 
  - Census blocks and tracts for Maine
  - Walk time calculations for Maine
  - Demographic analysis for Maine
- **Notebooks**: All notebooks currently hardcoded for Maine

### Tasks Required

#### 3.1 Dataset Acquisition & Research (Medium Effort)
- **Research NEPOS Dataset**:
  - Locate New England Protected Open Space (NEPOS) dataset
  - Verify data format, schema, and coverage
  - Check data quality and completeness
  - Understand update frequency
- **Alternative**: If NEPOS doesn't exist, compile from state sources:
  - Maine: Already have
  - New Hampshire: Find state protected lands dataset
  - Vermont: Find state protected lands dataset
  - Massachusetts: MassGIS Protected and Recreational OpenSpace
  - Rhode Island: Find state protected lands dataset
  - Connecticut: Find state protected lands dataset

#### 3.2 Data Harmonization (High Effort)
- **Schema Standardization**:
  - Align attribute schemas across all 6 states
  - Standardize field names, data types, units
  - Handle missing or inconsistent attributes
- **Coordinate System**:
  - Ensure all datasets use consistent projection
  - Reproject if necessary
- **Data Quality**:
  - Resolve overlaps/duplicates at state boundaries
  - Handle data gaps
  - Validate geometry integrity

#### 3.3 Geographic Expansion (High Effort)
- **Census Data**:
  - Download Census blocks for all 6 New England states (FIPS: 23, 33, 50, 25, 44, 09)
  - Download Census tracts for all 6 states
  - Update Census relationship files for all states
- **OSMnx Graphs**:
  - Download street networks for all 6 states (12 graphs: walk + drive for each)
  - Estimate: ~6x current size = ~1 GB for graphs
  - Requires significant RAM (>10GB per state, potentially 60GB+ total)
- **CEJST Data**:
  - Download CEJST data for all 6 states
- **Processing**:
  - Run `find_centroids.py` for all state datasets
  - Process all state data with OSMnx node IDs

#### 3.4 Code Refactoring (Medium-High Effort)
- **Parameterize State Codes**:
  - Remove hardcoded "Maine" / FIPS 23 references
  - Create configuration system for state selection
  - Update `src/download_graphs.py` to handle multiple states
- **Update Notebooks**:
  - Modify all 10+ notebooks to handle multiple states
  - Add state selection/filtering logic
  - Update data loading to handle multi-state datasets
- **Analysis Scaling**:
  - Optimize walk time calculations for larger dataset
  - Consider parallel processing for multi-state analysis
  - Update visualization to handle larger geographic area

#### 3.5 Infrastructure & Performance (Medium Effort)
- **Memory Requirements**:
  - Current: ~10GB RAM for Maine graphs
  - Expanded: Potentially 60GB+ RAM for all states
  - May need to process states separately or use distributed computing
- **Storage**:
  - Current data: ~340 MB
  - Expanded: Estimated 2-3 GB (6x increase)
- **Processing Time**:
  - Walk time calculations will take significantly longer
  - May need to optimize or parallelize

#### 3.6 Testing & Validation (Medium Effort)
- Validate results for each state individually
- Compare results across states
- Ensure consistency in analysis methodology
- Test edge cases (state boundaries, data gaps)

### Challenges
- **NEPOS Dataset Availability**: May not exist as a single harmonized dataset
- **Data Quality**: State datasets may have different quality/coverage
- **Computational Resources**: Significant increase in memory and processing requirements
- **Code Complexity**: Managing multi-state analysis adds complexity
- **State Boundary Issues**: Overlaps, gaps, or inconsistencies at borders

### Estimated Level of Effort
**Overall: HIGH (40-60 hours)**

- Dataset research & acquisition: 4-8 hours
- Data harmonization: 8-12 hours
- Geographic expansion (downloads & processing): 8-12 hours
- Code refactoring: 12-16 hours
- Infrastructure optimization: 4-6 hours
- Testing & validation: 4-6 hours

### Dependencies
- Access to NEPOS dataset or all 6 state protected lands datasets
- Sufficient computational resources (RAM, storage)
- Understanding of data schemas for all state datasets
- Time for processing large datasets

---

## Summary & Recommendations

### Effort Comparison

| Task | Estimated Effort | Complexity | Priority Recommendation |
|------|-----------------|------------|-------------------------|
| 1. DVC → Git LFS | **LOW-MEDIUM** (4-8 hours) | Low | **Do First** - Simplest, unblocks other work |
| 2. Data Updates | **MEDIUM-HIGH** (16-24 hours) | Medium | **Do Second** - Improves maintainability |
| 3. New England Expansion | **HIGH** (40-60 hours) | High | **Do Last** - Most complex, requires stable foundation |

### Recommended Approach

1. **Phase 1: DVC Migration** (Week 1)
   - Complete DVC to Git LFS migration
   - Establish stable data management workflow
   - Ensures clean foundation for future work

2. **Phase 2: Update Automation** (Weeks 2-3)
   - Implement automated data source checking
   - Create update procedures
   - Test with current Maine data

3. **Phase 3: New England Expansion** (Weeks 4-8)
   - Research and acquire NEPOS/state datasets
   - Harmonize data schemas
   - Expand geographic coverage incrementally (one state at a time)
   - Refactor code to handle multi-state analysis
   - Optimize for larger datasets

### Risk Mitigation

- **Task 1**: Low risk - well-understood migration path
- **Task 2**: Medium risk - depends on data source stability
- **Task 3**: High risk - depends on dataset availability and computational resources

### Questions to Resolve Before Starting

1. **NEPOS Dataset**: Does a harmonized New England Protected Open Space dataset exist? If not, what are the alternatives?
2. **Computational Resources**: Do we have sufficient RAM/storage for multi-state analysis?
3. **Timeline**: What is the target completion date?
4. **Team Capacity**: How many people can work on these tasks?

---

## Next Steps

1. **Immediate**: Review this assessment and prioritize tasks
2. **Research**: Investigate NEPOS dataset availability and alternatives
3. **Planning**: Create detailed implementation plans for each task
4. **Resource Assessment**: Verify computational resources for Task 3
5. **Stakeholder Alignment**: Confirm priorities and timeline

