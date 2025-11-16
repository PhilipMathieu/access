# Map Export Comparison: Current Approach vs. water-gis mapbox-gl-export Plugin

## Overview

This document compares our current custom print/export implementation with the `watergis/mapbox-gl-export` plugin for MapLibre GL JS (compatible with Mapbox GL JS).

## Current Implementation Status: Hybrid Approach ✅

**As of latest update**: We now use a **hybrid approach**:
- **Print Preview & Browser Print**: Custom implementation (kept)
- **PNG/PDF Export**: water-gis mapbox-gl-export plugin (integrated)

This gives us the best of both worlds: publication-quality print layouts with print preview, plus high-resolution direct exports.

## Current Implementation

### Features

1. **Print Preview Mode** ✅
   - Toggle-able preview mode (eye icon button)
   - Shows exact print layout in browser
   - Real-time updates as you zoom/pan
   - No deployment needed for testing

2. **Browser Print to PDF** ✅
   - Uses browser's native print dialog
   - CSS `@media print` styles for layout
   - Supports landscape and portrait orientations
   - Letter page size with configurable margins

3. **PNG Export** ✅
   - Direct canvas export to PNG
   - Exports current map view
   - Simple download functionality

4. **Print Layout Elements** ✅
   - Title block (top center)
   - Legend (bottom right, print-optimized)
   - Scale bar (bottom right, dynamic calculation)
   - North arrow (top right)
   - Attribution footer (date, data sources, copyright)
   - Dynamic metadata (coordinates, zoom level, date)

5. **Map Resize Handling** ✅
   - Automatic resize on print dialog open/close
   - Proper centering in print viewport
   - Handles container dimension changes

### Implementation Details

- **Files**: `docs/js/map.js`, `docs/css/styles.css`, `docs/index.html`
- **Approach**: Custom CSS print styles + JavaScript metadata updates
- **Dependencies**: None (uses native browser APIs)
- **Maintenance**: Fully custom, requires manual updates

### Advantages

✅ **Full Control**: Complete customization of print layout
✅ **WYSIWYG Preview**: See exactly what will print before printing
✅ **No External Dependencies**: No additional libraries to maintain
✅ **Iterative Development**: Print preview mode enables fast iteration
✅ **Professional Layout**: Publication-ready cartographic elements
✅ **Dynamic Metadata**: Auto-updates date, coordinates, scale

### Limitations

❌ **Browser-Dependent**: Print quality depends on browser's print engine
❌ **Resolution**: Limited to browser's print resolution (typically 96-150 DPI)
❌ **No High-Res Export**: PNG export uses canvas resolution (screen resolution)
❌ **Manual Implementation**: All features must be built and maintained
❌ **Print Dialog Required**: PDF export requires browser print dialog

---

## water-gis mapbox-gl-export Plugin

### Features (Based on Documentation)

1. **Direct Export** ✅
   - Export button control added to map
   - No print dialog required
   - Direct PNG/PDF generation

2. **Export Formats** ✅
   - PNG export
   - PDF export
   - Configurable resolution

3. **Integration** ✅
   - Simple MapLibre/Mapbox GL JS integration
   - Adds export control to map interface
   - Minimal code required

### Advantages

✅ **Quick Export**: One-click export without print dialog
✅ **Higher Resolution**: Can export at higher resolutions than screen
✅ **Format Flexibility**: Both PNG and PDF in one solution
✅ **Maintained Library**: Third-party maintenance and updates
✅ **Simple Integration**: Easy to add to existing maps

### Limitations

❌ **Less Customization**: Limited control over export layout
❌ **No Print Preview**: Can't preview before exporting
❌ **External Dependency**: Requires additional library
❌ **Layout Control**: May not support custom print layouts (title, legend positioning, etc.)
❌ **Compatibility**: Must ensure compatibility with MapLibre GL JS version

---

## Feature Comparison Matrix

| Feature | Current Implementation | water-gis Plugin |
|---------|----------------------|------------------|
| **Print Preview Mode** | ✅ Yes (toggle-able) | ❌ No |
| **Browser Print to PDF** | ✅ Yes | ❌ No |
| **PNG Export** | ✅ Yes (screen resolution) | ✅ Yes (configurable resolution) |
| **PDF Export** | ✅ Yes (via print dialog) | ✅ Yes (direct) |
| **Custom Print Layout** | ✅ Full control | ❓ Limited/Unknown |
| **Title Block** | ✅ Yes | ❓ Unknown |
| **Legend in Export** | ✅ Yes (print-optimized) | ❓ Unknown |
| **Scale Bar** | ✅ Yes (dynamic) | ❓ Unknown |
| **North Arrow** | ✅ Yes | ❓ Unknown |
| **Attribution Footer** | ✅ Yes | ❓ Unknown |
| **Dynamic Metadata** | ✅ Yes (date, coords, zoom) | ❓ Unknown |
| **High-Resolution Export** | ❌ No | ✅ Yes |
| **No Print Dialog** | ❌ No | ✅ Yes |
| **External Dependencies** | ✅ None | ❌ Requires plugin |
| **Customization Level** | ✅ Full | ❓ Limited |
| **Iterative Development** | ✅ Print preview mode | ❌ No preview |

---

## Use Case Analysis

### When Current Implementation is Better

1. **Publication-Quality Maps**: Need precise control over layout, typography, and cartographic elements
2. **Print Workflow**: Users need to print physical copies or PDFs via browser
3. **Development Iteration**: Need to quickly test and adjust print layouts
4. **Custom Requirements**: Need specific layout elements (title blocks, metadata panels, etc.)
5. **No Dependencies**: Want to avoid external libraries

### When water-gis Plugin is Better

1. **Quick Exports**: Need fast PNG/PDF exports without print dialog
2. **High Resolution**: Need exports at resolutions higher than screen resolution
3. **Simple Integration**: Want minimal code to add export functionality
4. **Standard Layouts**: Standard map export is sufficient (no custom layout needed)
5. **Automated Workflows**: Need programmatic export without user interaction

---

## Recommendations

### Option 1: Keep Current Implementation (Recommended for Your Use Case)

**Best if:**
- You need publication-quality print layouts
- You want full control over cartographic elements
- Print preview is important for your workflow
- You prefer no external dependencies

**Action**: Continue refining current implementation, consider adding high-res export option.

### Option 2: Add water-gis Plugin Alongside Current Implementation

**Best if:**
- You want both quick exports AND print preview
- Users need high-resolution exports
- You want to offer multiple export options

**Action**: Integrate plugin for quick exports, keep print preview for publication-quality output.

### Option 3: Replace with water-gis Plugin

**Best if:**
- Quick exports are more important than print layout control
- You don't need custom print layouts
- You want to reduce maintenance burden

**Action**: Evaluate plugin's customization options first to ensure it meets your needs.

---

## Potential Enhancements to Current Implementation

If keeping current approach, consider adding:

1. **High-Resolution PNG Export**
   - Use `map.getCanvas()` with scale factor
   - Export at 2x or 3x screen resolution
   - Add resolution selector in export button

2. **Direct PDF Export** (without print dialog)
   - Use jsPDF or similar library
   - Generate PDF from canvas
   - Include print layout elements

3. **Export Templates**
   - Multiple layout templates
   - User-selectable templates
   - Save/load custom templates

4. **Batch Export**
   - Export multiple views
   - Export at different zoom levels
   - Automated export workflows

---

## Conclusion

Your current implementation is well-suited for **publication-quality map printing** with full control over cartographic elements. The water-gis plugin is better for **quick, high-resolution exports** but may lack the customization you need.

**Current Status**: ✅ **Hybrid Approach Implemented**
- **Print Preview & Browser Print**: Custom implementation (kept for publication-quality layouts)
- **PNG/PDF Export**: water-gis mapbox-gl-export plugin (integrated for high-resolution exports)

This hybrid approach provides:
- Publication-quality print layouts with full customization
- High-resolution PNG/PDF exports via plugin
- Print preview for iterative development
- Best of both worlds for different use cases

---

## References

- [water-gis mapbox-gl-export](https://water-gis.com/en/packages/)
- Current implementation: `docs/js/map.js`, `docs/css/styles.css`
- Print preview guide: `docs/PRINT_PREVIEW_GUIDE.md`

