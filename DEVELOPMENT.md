# Development Guide

This document provides guidelines for contributors working on the ACCESS codebase.

## Logging Best Practices

This codebase uses Python's standard `logging` module. Follow these patterns for consistency:

### For Library Modules (files imported by other code)

Use `logging.getLogger(__name__)` WITHOUT calling `basicConfig()`:

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Processing data...")
    logger.warning("Data quality issue detected")
    logger.error("Failed to process file")
```

**Examples:** `src/walk_times/calculate.py`, `src/h3utils.py`, `src/merging/analysis.py`

### For Entry Point Scripts (standalone scripts with `if __name__ == "__main__"`)

Use `logging.basicConfig()` with handlers, then get a logger:

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/my_script_log.txt'),  # Optional: log to file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting processing...")
    # ... your code ...
```

**Examples:** `src/run_pipeline.py`, `src/update_data_sources.py`, `src/convert_to_pmtiles.py`

### Log Levels

Choose appropriate log levels:

- `logger.debug()` - Detailed diagnostic information (not shown by default)
- `logger.info()` - General informational messages about progress
- `logger.warning()` - Warning messages (something unexpected but not fatal)
- `logger.error()` - Error messages (operation failed but script continues)
- `logger.critical()` - Critical errors (script must exit)

### Integration with TQDM Progress Bars

When using TQDM for progress indication, logging works seamlessly:

```python
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

def process_items(items):
    logger.info(f"Processing {len(items)} items")
    for item in tqdm(items, desc="Processing"):
        # TQDM will show progress bar
        # logger messages will appear above the progress bar
        if item.needs_attention():
            logger.warning(f"Issue with item {item.id}")
```

**Examples:** `src/walk_times/calculate.py`, `src/walk_times/algorithms.py`

### Error Handling

Always log exceptions properly:

```python
# Good - logs error with details
try:
    process_data(file)
except ValueError as e:
    logger.error(f"Invalid data in {file}: {e}")

# Bad - silent failure
try:
    process_data(file)
except ValueError:
    pass
```

## Environment Variables

See `.env.example` for required environment variables. Copy it to `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env with your actual values
```

## Testing

- Write tests for new functionality in `tests/`
- Run tests with: `pytest tests/`
- See existing test files for examples

## Code Style

- Follow PEP 8 guidelines
- Use type hints where practical
- Add docstrings to public functions and classes
