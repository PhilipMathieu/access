# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when running the Access pipeline.

## Table of Contents

1. [Common Error Messages](#common-error-messages)
2. [Pipeline Failures](#pipeline-failures)
3. [Data Issues](#data-issues)
4. [Network/API Issues](#networkapi-issues)
5. [Performance Issues](#performance-issues)
6. [Recovery Procedures](#recovery-procedures)

---

## Common Error Messages

### ConfigurationError

**Error:** `ConfigurationError: Either state_fips or region_config must be provided`

**Cause:** Missing required configuration parameter.

**Solution:**
- Ensure you're passing either `state_fips` or `region_config` to the function
- Check that your region configuration is properly set up in `src/config/regions.py`

---

**Error:** `ConfigurationError: No API key provided and no cached data found`

**Cause:** Census API key is missing and no cached data is available.

**Solution:**
1. Set `CENSUS_API_KEY` in your `.env` file:
   ```bash
   CENSUS_API_KEY=your_api_key_here
   ```
2. Or pass it as an argument: `--census-api-key your_key`
3. Or ensure cached census data exists in `data/cache/census/`

---

### DataError

**Error:** `DataError: File not found: <path>`

**Cause:** Required input file is missing.

**Solution:**
1. Check that the file path is correct
2. Verify the file exists at the specified location
3. Run data preparation scripts if needed:
   - `src/download_graphs.py` for graph files
   - `src/find_centroids.py` for blocks with node IDs
   - `src/update_data_sources.py` for data updates

---

**Error:** `DataError: Output file was not created: <path>`

**Cause:** A processing step failed silently or was interrupted.

**Solution:**
1. Check the log file (`data/pipeline_log.txt`) for error messages
2. Verify you have write permissions in the output directory
3. Check available disk space
4. Re-run the failed step

---

### ValidationError

**Error:** `ValidationError: Blocks data is missing required columns: ['GEOID20']`

**Cause:** Input data doesn't have the expected schema.

**Solution:**
1. Verify your input data file is the correct version
2. Check that required columns exist
3. Re-run data preparation if needed
4. Check `DATA_DICTIONARY.md` for expected schema

---

**Error:** `ValidationError: Walk times column has X negative values`

**Cause:** Walk time calculation produced invalid results.

**Solution:**
1. Check the graph file for issues
2. Verify block centroids are correctly mapped to graph nodes
3. Re-run walk time calculation
4. Check for graph connectivity issues

---

### NetworkError / CensusAPIError

**Error:** `CensusAPIError: Census API rate limit exceeded`

**Cause:** Too many API requests in a short time period.

**Solution:**
1. The pipeline will automatically retry with exponential backoff
2. Wait a few minutes and try again
3. Check your API key usage limits at [Census API](https://api.census.gov/data/key_signup.html)
4. Use cached data if available (set `refresh_cache=False`)

---

**Error:** `NetworkError: Operation failed after 3 attempts`

**Cause:** Network operation failed multiple times (timeout, connection error, etc.).

**Solution:**
1. Check your internet connection
2. Verify the service is available (Census API, OSM servers)
3. Try again later if it's a temporary outage
4. For OSMnx downloads, check OSM server status

---

### GraphError

**Error:** `GraphError: Network error downloading graph`

**Cause:** Failed to download OSMnx graph from OpenStreetMap.

**Solution:**
1. Check your internet connection
2. Verify OSM servers are accessible
3. Try running `src/download_graphs.py` again (it will retry automatically)
4. Check available RAM (graph downloads require >10GB)

---

**Error:** `GraphError: Insufficient memory for graph download`

**Cause:** Not enough RAM available for graph processing.

**Solution:**
1. Close other applications to free up memory
2. Use a machine with more RAM
3. Consider processing smaller regions separately

---

## Pipeline Failures

### Step 1: Walk Time Calculation Fails

**Symptoms:**
- Error message about graph or blocks file
- Process hangs or crashes
- Output file not created

**Diagnosis:**
1. Check log file: `data/pipeline_log.txt`
2. Verify input files exist and are valid
3. Check available memory

**Recovery:**
```bash
# Re-run just the walk time step
python src/run_pipeline.py --skip-merging --skip-analysis --skip-visualization --skip-h3
```

**Prevention:**
- Validate input files before running
- Ensure sufficient RAM available
- Use `--n-jobs 1` for debugging (serial processing)

---

### Step 2: Merging Fails

**Symptoms:**
- Error about missing walk times or blocks
- Schema validation errors
- Join failures

**Diagnosis:**
1. Verify walk times output exists: `data/walk_times/walk_times_block_df.parquet`
2. Check that blocks file has required columns
3. Verify GEOID20 columns match between files

**Recovery:**
```bash
# Re-run from merging step
python src/run_pipeline.py --skip-walk-times --skip-analysis --skip-visualization --skip-h3
```

---

### Step 3: Analysis (EJ Blocks) Fails

**Symptoms:**
- Census API errors
- CEJST processing failures
- Missing demographic data

**Diagnosis:**
1. Check Census API key is set
2. Verify CEJST file exists: `data/cejst-me.zip`
3. Check relationship file exists
4. Review census data cache

**Recovery:**
```bash
# Re-run analysis step
python src/run_pipeline.py --skip-walk-times --skip-merging --skip-visualization --skip-h3
```

**If Census API fails:**
- Check cached data: `data/cache/census/`
- Use cached data if available (don't set `refresh_cache=True`)
- Wait and retry if rate limited

---

### Step 4: Visualization Fails

**Symptoms:**
- Error generating figures
- Missing ejblocks file
- File permission errors

**Diagnosis:**
1. Verify ejblocks file exists: `data/joins/ejblocks.parquet`
2. Check output directory permissions: `figs/`
3. Review figure generation code

**Recovery:**
```bash
# Re-run visualization only
python src/run_pipeline.py --skip-walk-times --skip-merging --skip-analysis --skip-h3
```

---

## Data Issues

### Missing Required Files

**Checklist:**
- [ ] Graph file: `data/graphs/maine_walk.graphml`
- [ ] Blocks with nodes: `data/blocks/tl_2020_23_tabblock20_with_nodes.shp.zip`
- [ ] Conserved lands: `data/conserved_lands/Maine_Conserved_Lands_with_nodes.shp.zip`
- [ ] CEJST data: `data/cejst-me.zip`
- [ ] Relationship file: `data/blocks/tab2010_tab2020_st23_*.txt`

**Solution:**
Run data preparation scripts:
```bash
# Download graphs
python src/download_graphs.py

# Find centroids and map to graph nodes
python src/find_centroids.py

# Update other data sources as needed
python src/update_data_sources.py
```

---

### Invalid Data Schema

**Symptoms:**
- ValidationError about missing columns
- Type mismatches
- Unexpected data format

**Solution:**
1. Check `DATA_DICTIONARY.md` for expected schema
2. Verify data file version matches expected format
3. Re-download or regenerate data files
4. Check for data corruption

---

### Corrupted Cache Files

**Symptoms:**
- Cache file exists but can't be read
- Validation errors when loading cache
- Inconsistent results

**Solution:**
```bash
# Delete corrupted cache
rm -rf data/cache/census/*

# Re-run with API key to regenerate cache
python src/run_pipeline.py --census-api-key YOUR_KEY
```

---

## Network/API Issues

### Census API Rate Limiting

**Symptoms:**
- `CensusAPIError: Census API rate limit exceeded`
- 429 HTTP errors

**Solution:**
1. Pipeline automatically retries with backoff (up to 5 attempts)
2. Wait 5-10 minutes between runs
3. Use cached data when possible
4. Request higher rate limits from Census Bureau if needed

---

### OSMnx Download Failures

**Symptoms:**
- `GraphError: Network error downloading graph`
- Timeout errors
- Connection refused

**Solution:**
1. Check internet connection
2. Verify OSM servers are accessible
3. Retry the download (automatic retry with backoff)
4. Check OSM status page for outages
5. Try downloading during off-peak hours

---

### Slow Network Operations

**Symptoms:**
- Downloads take very long
- Frequent timeouts

**Solution:**
1. Use cached data when available
2. Download graphs during off-peak hours
3. Consider using a faster internet connection
4. Pre-download all data before running pipeline

---

## Performance Issues

### Walk Time Calculation is Slow

**Symptoms:**
- Processing takes hours
- High CPU usage
- Memory pressure

**Solutions:**
1. Use parallel processing: `--n-jobs -1` (uses all CPUs)
2. Reduce number of trip times if not needed
3. Process smaller regions separately
4. Check for performance optimizations in `IMP-001` (see BACKLOG.md)

---

### Out of Memory Errors

**Symptoms:**
- Process killed by OS
- Memory errors in logs
- System becomes unresponsive

**Solutions:**
1. Reduce parallelism: `--n-jobs 1` (serial processing)
2. Process smaller batches
3. Use a machine with more RAM
4. Close other applications

---

## Recovery Procedures

### Resume from Checkpoint

If the pipeline fails partway through, you can resume from the last successful step:

```bash
# Example: Resume from merging (walk times already calculated)
python src/run_pipeline.py --skip-walk-times
```

### Clean Restart

If you need to start completely fresh:

```bash
# Remove intermediate outputs (keep source data)
rm -rf data/walk_times/*.parquet
rm -rf data/joins/*.parquet
rm -rf figs/*

# Re-run full pipeline
python src/run_pipeline.py
```

### Partial Recovery

If only one step failed:

1. Identify the failed step from logs
2. Fix the underlying issue
3. Re-run only that step using skip flags
4. Verify output before continuing

---

## Getting Help

If you encounter an issue not covered here:

1. **Check the logs:**
   - `data/pipeline_log.txt` - Main pipeline log
   - `data/processing_log.txt` - Processing operations
   - `data/validation_log.txt` - Validation results

2. **Review error messages:**
   - Look for specific exception types (DataError, ValidationError, etc.)
   - Check stack traces for file locations and line numbers

3. **Verify your environment:**
   - Python version (should be 3.10+)
   - Dependencies installed (`pip install -e .`)
   - Environment variables set (`.env` file)

4. **Check documentation:**
   - `README.md` - Setup and usage
   - `DEVELOPMENT.md` - Development guidelines
   - `DATA_DICTIONARY.md` - Data schemas

5. **Contact:**
   - Project Lead: Philip Mathieu (mathieu.p@northeastern.edu)

---

## Error Recovery Checklist

When encountering an error:

- [ ] Check log files for detailed error messages
- [ ] Verify all required input files exist
- [ ] Check file permissions and disk space
- [ ] Verify configuration (API keys, paths, etc.)
- [ ] Check network connectivity (for API/downloads)
- [ ] Review validation errors for data issues
- [ ] Try re-running the failed step in isolation
- [ ] Check for known issues in this guide
- [ ] Review recent changes to data or code

---

**Last Updated:** 2025-11-15
**Version:** 1.0
