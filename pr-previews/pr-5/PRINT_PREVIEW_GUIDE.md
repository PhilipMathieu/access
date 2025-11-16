# Print Preview Development Guide

## Overview

The print layout rendering system allows you to preview how the map will look when printed without actually printing or deploying. This makes iterative development much faster.

## How Print Rendering Works

### Components

1. **CSS Print Styles** (`docs/css/styles.css` lines 13716+)
   - `@media print` rules control what appears when printing
   - Hides interactive controls, shows print-only elements
   - Sets page size (letter landscape/portrait) and margins

2. **Print-Only HTML Elements** (`docs/index.html` lines 40-68)
   - `.print-title` - Map title and subtitle
   - `.print-scale` - Scale bar with dynamic calculation
   - `.print-north` - North arrow indicator
   - `.print-attribution` - Footer with date, data sources, copyright
   - Hidden by default (`display: none`), shown only in print mode

3. **JavaScript Metadata Updates** (`docs/js/map.js` lines 1029-1117)
   - `updatePrintMetadata()` - Updates date, coordinates, zoom level
   - `updatePrintScale()` - Calculates scale based on current zoom and latitude
   - Triggered when print button is clicked or preview mode is activated

### Print Layout Elements

- **Title Block**: Top center, shows map name and subtitle
- **Legend**: Bottom right, shows walk time color scale and layer toggles
- **Scale Bar**: Bottom left, shows map scale with ratio and distance
- **North Arrow**: Upper right, indicates map orientation
- **Attribution Footer**: Bottom, shows date, data sources, and copyright

## Using Print Preview Mode

### Local Development Setup

1. **Start the local development server**:
   ```bash
   cd docs
   ./serve.sh
   ```
   Or manually:
   ```bash
   cd docs
   http-server -p 8000 --cors
   ```

2. **Open in browser**:
   ```
   http://localhost:8000
   ```

3. **Toggle Print Preview**:
   - Click the eye icon (👁️) button in the top-right controls
   - This toggles preview mode on/off
   - The button changes to an eye-slash icon (👁️‍🗨️) when active

### Preview Mode Features

- **Real-time updates**: Scale and metadata update as you zoom/pan
- **Full print layout**: Shows exactly how the map will look when printed
- **No deployment needed**: Test changes instantly without deploying
- **Easy toggling**: Click the preview button to enter/exit preview mode

### Development Workflow

1. Make changes to print CSS in `docs/css/styles.css`
2. Refresh the browser (or use auto-reload if configured)
3. Click the print preview button to see changes
4. Adjust CSS as needed
5. Repeat until satisfied
6. Test actual print output using the print button (printer icon)

## Print Styles Location

Print-specific styles are in `docs/css/styles.css`:

- **Print Preview Mode**: Lines 13437-13714 (applies when `body.print-preview` class is active)
- **Actual Print Styles**: Lines 13716+ (applies when `@media print` is active)

Both sections contain similar styles - preview mode mimics print mode for development.

## Tips for Iterative Development

1. **Use Browser DevTools**: Inspect print elements in preview mode to see exact positioning
2. **Test Different Zoom Levels**: Scale bar updates dynamically - test at various zoom levels
3. **Check Both Orientations**: Print styles support both landscape and portrait
4. **Verify Metadata**: Ensure date, coordinates, and scale are updating correctly
5. **Test Actual Print**: After preview looks good, use the print button to verify final output

## Troubleshooting

- **Preview not showing**: Make sure you clicked the eye icon button (not the print button)
- **Elements overlapping**: Check z-index values in print CSS
- **Scale not updating**: Ensure `updatePrintScale()` is called on map move events
- **Styles not applying**: Check that CSS selectors match the HTML structure

## Files Modified

- `docs/js/map.js` - Added print preview button and toggle functionality
- `docs/css/styles.css` - Added print preview mode styles
- `docs/index.html` - Print-only HTML elements (already existed)

