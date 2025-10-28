# LightBurn Auto-Align

**Camera-based precision alignment for laser engraving with sub-millimeter accuracy**

## Overview

LightBurn Auto-Align eliminates manual positioning by using ArUco markers and computer vision to automatically align designs with physical materials. Place your item in a jig, take a photo, and the system calculates exact positioning for LightBurn.

### Key Features

- **ArUco marker-based alignment** - Sub-mm precision using computer vision
- **Camera calibration** - Corrects for lens distortion
- **Homography mapping** - Accurate pixel-to-millimeter coordinate transformation
- **LightBurn integration** - Direct UDP communication to load and start jobs
- **Complete workflow** - From camera capture to engraving in seconds

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Generate and Print Markers

```bash
python3 generate_markers.py
```

This creates `markers/aruco_board.pdf`. Print at 100% scale and mount markers on a flat jig at the exact positions shown.

### 3. Calibrate Camera (Optional but Recommended)

```bash
# Generate calibration pattern
python3 calibrate.py generate

# Capture calibration images
python3 calibrate.py capture --num-images 20

# Run calibration
python3 calibrate.py calibrate calibration_images/*.jpg
```

### 4. Run Complete Workflow

```bash
# With text design
python3 align_tool.py --text "Hello" --rect 50 50 100 30 --send

# With image design
python3 align_tool.py --design logo.png --rect 60 60 80 80 --send
```

**Arguments:**
- `--rect X Y WIDTH HEIGHT` - Design position and size in millimeters
  - `X, Y` - Position from bottom-left corner (0,0)
  - `WIDTH, HEIGHT` - Design dimensions
- `--text "TEXT"` - Create text design
- `--design FILE` - Use image file (PNG)
- `--send` - Send to LightBurn automatically
- `--start` - Auto-start job (requires `--send`)

## System Components

### Core Modules

| Module | Purpose |
|--------|---------|
| `align_tool.py` | Main CLI - complete workflow |
| `aruco_align.py` | ArUco detection and homography |
| `design_warp.py` | Design warping and export |
| `lightburn_udp.py` | LightBurn UDP communication |
| `calibrate.py` | Camera calibration tool |
| `generate_markers.py` | Marker board generator |
| `test_alignment.py` | Test suite |

### Configuration Files

- `config/jigs/default.json` - Marker positions for your jig
- `config/camera.yml` - Camera calibration data (optional)

## Detailed Usage

### Individual Module Usage

#### 1. Generate Markers

```bash
# Default 200x200mm board with 40mm markers
python3 generate_markers.py

# Custom size
python3 generate_markers.py --size 150 --marker-size 30
```

#### 2. Camera Calibration

```bash
# Step 1: Generate chessboard pattern
python3 calibrate.py generate

# Step 2: Capture images (move chessboard to different positions/angles)
python3 calibrate.py capture --num-images 20

# Step 3: Calculate calibration
python3 calibrate.py calibrate calibration_images/*.jpg
```

Calibration corrects lens distortion for higher accuracy.

#### 3. ArUco Alignment

```bash
# Detect markers and calculate alignment
python3 aruco_align.py camera_snapshot.jpg --design 50 50 100 80

# Without camera calibration
python3 aruco_align.py camera_snapshot.jpg --camera-calib ""
```

This creates:
- `camera_snapshot_aligned.jpg` - Visualization showing detected markers
- Alignment data (printed to console)

#### 4. Design Export

```bash
# Export aligned design
python3 design_warp.py alignment_data.json --text "TEST" --output output/design.png

# With custom DPI
python3 design_warp.py alignment_data.json --design logo.png --dpi 600 --format svg
```

#### 5. LightBurn Communication

```bash
# Check if LightBurn is running
python3 lightburn_udp.py ping

# Load file
python3 lightburn_udp.py load output/design.png

# Load and start
python3 lightburn_udp.py load output/design.png --start
```

**Note:** Enable UDP in LightBurn: `Edit → Device Settings → Enable UDP`

### Complete Workflow Examples

#### Example 1: Quick Text Engraving

```bash
python3 align_tool.py \
  --text "Serial #12345" \
  --rect 70 70 60 20 \
  --send --start
```

1. Opens camera to capture jig photo (press SPACE)
2. Detects markers and calculates position
3. Creates text design at 70,70 (60x20mm)
4. Exports aligned PNG
5. Sends to LightBurn and starts job

#### Example 2: Logo with Existing Camera Image

```bash
python3 align_tool.py \
  --camera-image snapshot.jpg \
  --design company_logo.png \
  --rect 50 50 100 100 \
  --format svg
```

Uses existing camera image instead of capturing new one.

#### Example 3: Multiple Items

```bash
# Capture once
python3 align_tool.py --camera-image jig.jpg --text "Item 1" --rect 30 30 50 30
python3 align_tool.py --camera-image jig.jpg --text "Item 2" --rect 30 80 50 30
python3 align_tool.py --camera-image jig.jpg --text "Item 3" --rect 30 130 50 30
```

Reuse the same camera image for batch positioning.

## Coordinate System

```
Origin (0,0) is at BOTTOM-LEFT of engraving area

   (0,200)    Y ↑         (200,200)
      ┌────────────────────┐
      │                    │
      │   Engraving Area   │
      │                    │
      └────────────────────┘ → X
   (0,0)                  (200,0)
```

All measurements in millimeters.

## Testing

Run the test suite to verify everything works:

```bash
python3 test_alignment.py
```

This creates a synthetic test image with ArUco markers and validates:
- Marker detection
- Homography calculation
- Alignment workflow
- Design export

Expected output: `4/4 tests passed`

## Hardware Setup

### Required Hardware

1. **Overhead camera** - USB webcam mounted above laser bed
   - Rigidly mounted to avoid movement
   - Sufficient resolution (1080p+ recommended)
   - Even lighting (avoid glare)

2. **Flat jig** - Base platform with mounted ArUco markers
   - Print `markers/aruco_board.pdf` at 100% scale
   - Mount markers at exact positions shown
   - Ensure jig is flat and stable

### Recommended Setup

- Mount camera 300-500mm above bed
- Use diffuse LED lighting
- Place camera directly above center of engraving area
- Secure jig to laser bed (tape, magnets, or clamps)

## Accuracy

Expected accuracy with proper calibration:
- **Position:** ±0.5mm
- **Rotation:** ±0.5°
- **Size:** ±1% of design dimensions

Factors affecting accuracy:
- Camera calibration quality
- Marker print precision
- Jig stability
- Lighting conditions
- Camera resolution

## Troubleshooting

### No markers detected

- Ensure markers are clearly visible in camera view
- Check lighting (avoid glare on markers)
- Verify markers printed at correct size
- Try adjusting camera position/angle

### Poor alignment accuracy

- Run camera calibration (`calibrate.py`)
- Verify marker positions match configuration
- Check jig is flat and stable
- Ensure markers are printed at 100% scale

### LightBurn won't respond

- Enable UDP in LightBurn: `Edit → Device Settings → Enable UDP`
- Check LightBurn is running
- Try: `python3 lightburn_udp.py ping`

### Design size incorrect in LightBurn

- Verify DPI settings: `Edit → Settings → File Settings → SVG Import DPI`
- Set to match export DPI (default: 300)
- Try PNG export instead of SVG

## Project Structure

```
lightburn-auto-align/
├── align_tool.py              # Main workflow CLI
├── aruco_align.py             # ArUco detection & alignment
├── design_warp.py             # Design warping & export
├── lightburn_udp.py           # LightBurn UDP interface
├── calibrate.py               # Camera calibration
├── generate_markers.py        # Marker board generator
├── test_alignment.py          # Test suite
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── RESEARCH.md                # Technical research notes
├── config/
│   ├── camera.yml             # Camera calibration (created by calibrate.py)
│   └── jigs/
│       └── default.json       # Jig configuration
├── markers/
│   ├── aruco_board.pdf        # Printable marker board
│   └── aruco_board.png        # Preview image
├── calibration/
│   └── calibration_chessboard.pdf  # Camera calibration pattern
├── output/                    # Exported designs
└── test_output/               # Test results
```

## Technical Details

### ArUco Markers

- **Dictionary:** DICT_4X4_50
- **Marker IDs:** 0, 1, 2, 3 (corners)
- **Detection:** OpenCV ArUco module
- **Pose estimation:** Sub-pixel corner detection

### Homography Mapping

- **Algorithm:** RANSAC-based homography calculation
- **Transform:** Maps millimeter coordinates → pixel coordinates
- **Accuracy:** Sub-pixel precision with 4+ markers

### Export Formats

- **PNG:** Raster image with embedded DPI metadata
- **SVG:** Vector format with embedded raster image

### LightBurn UDP Protocol

- **Port:** 19840 (fixed, not configurable)
- **Reply Port:** 19841
- **Commands:** PING, STATUS, LOADFILE, START, CLOSE

## Advanced Usage

### Multiple Jig Configurations

Create multiple jig configs for different setups:

```bash
# Create custom jig
python3 generate_markers.py --size 300 --output-dir markers/large

# Use custom jig
python3 align_tool.py --jig-config config/jigs/custom.json ...
```

### Batch Processing

```python
from align_tool import AlignmentWorkflow

workflow = AlignmentWorkflow()

designs = [
    ("Item A", (30, 30, 50, 30)),
    ("Item B", (30, 80, 50, 30)),
    ("Item C", (30, 130, 50, 30)),
]

for text, rect in designs:
    workflow.run_complete_workflow(
        design_rect_mm=rect,
        text=text,
        camera_image_path="jig.jpg",
        send_to_lb=True
    )
```

## Requirements

- Python 3.7+
- OpenCV 4.8+ (with contrib modules)
- NumPy 1.24+
- Pillow 10.0+
- USB webcam
- LightBurn software

## Contributing

This is a personal project for laser engraving automation. Feel free to fork and adapt for your own setup.

## License

This project is provided as-is for personal and educational use.

---

**Created:** October 18, 2025
**Status:** ✓ Complete - Production Ready
**Version:** 1.0.0

