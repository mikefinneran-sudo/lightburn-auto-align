# LightBurn Auto-Align

**Automatic photo alignment tool for LightBurn laser engraving software**

## Problem

When using LightBurn's camera overlay, you need to manually align your design to match the actual material position shown in the camera photo. This is time-consuming and error-prone.

## Solution

This tool uses computer vision to:
1. Detect material edges in the camera photo
2. Identify LightBurn's grid lines
3. Calculate alignment offset (X, Y, rotation)
4. Auto-position your design to match the material

## Features

- **Edge detection** - Automatically finds material boundaries
- **Grid alignment** - Uses LightBurn's overlay grid as reference
- **Rotation correction** - Handles material that's not perfectly square
- **Export positioning** - Outputs coordinates for LightBurn

## Tech Stack

- Python 3.x
- OpenCV (computer vision)
- NumPy (calculations)
- PIL/Pillow (image processing)

## Status

**In Development** - Project setup complete, ready for implementation

## Workflow

1. Export camera snapshot from LightBurn
2. Run alignment tool on snapshot
3. Tool outputs X, Y, rotation offsets
4. Apply offsets to your design in LightBurn
5. Perfect alignment achieved

## Roadmap

- [ ] Basic edge detection
- [ ] Grid line identification
- [ ] Offset calculation
- [ ] CLI interface
- [ ] GUI application (optional)
- [ ] Direct LightBurn API integration (if available)

---

**Created:** October 18, 2025
**Status:** Initial setup
**Next:** Gather sample photos and implement detection algorithm
