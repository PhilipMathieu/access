[![pages-build-deployment](https://github.com/PhilipMathieu/access/actions/workflows/pages/pages-build-deployment/badge.svg?branch=main)](https://github.com/PhilipMathieu/access/actions/workflows/pages/pages-build-deployment)
# access

This project does not yet have complete documentation. At this stage, the best source for information is in the form of the set of Jupyter notebooks available in the [notebooks/](notebooks/) subdirectory.

In the interim, please feel free to contact Philip Mathieu (mathieu.p@northeastern.edu) with questions.

## Data Files

For information about data files, their sources, processing workflows, and how to update them (especially for webmap updates), see **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)**.

The data dictionary includes:
- Webmap file locations and update procedures
- Raw data source information
- Processing workflows
- File naming conventions
- Troubleshooting guides

## Local Development

To test the site locally before deploying to GitHub Pages, use `http-server` which supports HTTP range requests required for PMTiles:

```bash
# Install http-server globally (if not already installed)
npm install -g http-server

# Navigate to the docs directory and start the server
cd docs
http-server -p 8000 --cors
```

The site will be available at `http://localhost:8000`. The `--cors` flag enables Cross-Origin Resource Sharing, which is important for PMTiles to work correctly.

**Note:** Python's `http.server` does not support HTTP range requests, which are required for PMTiles. Use `http-server` instead for local testing.

