# LightBurn Auto-Align - Research & Design

## Core Concept

Use camera-calibrated alignment with ArUco/AprilTag markers to achieve sub-mm accuracy:

1. **Overhead camera** sees reference tags on jig
2. **Homography** maps pixel coordinates → engraving plane
3. **Warp design** into exact target area
4. **Export aligned file** at known DPI
5. **Send to LightBurn** via UDP command interface

---

## Hardware Setup

### Required
- **Overhead USB camera** rigidly mounted above laser bed
- **Flat jig** with printed ArUco board (4 tags at corners)
- **Even lighting** (diffuse, no glare)

### One-Time Calibration
1. **Camera intrinsics**: Print 9×6 chessboard, run OpenCV calibration → save `camera.yml`
2. **Reference board**: Define engraving region (e.g., 200×200mm), place ArUco tags at known coordinates
3. **Save config**: Tag IDs + mm positions for future sessions

---

## Workflow

### Everyday Use
1. Drop item in jig → camera sees tags
2. Load design (SVG/PNG) and set physical size (e.g., 120×80mm)
3. App detects tags → solves pose → computes homography → warps preview
4. Export aligned PNG/SVG at 300 DPI
5. Send to LightBurn via UDP → auto-load and start

### Precision
- **Sub-mm accuracy** from homography mapping
- **No manual placement** needed in LightBurn
- **Repeatable** for production runs

---

## LightBurn Integration

### UDP Command Interface
LightBurn listens on `localhost:19840` for commands:

**Available Commands:**
- `PING` - Check if LightBurn is running
- `STATUS` - Get current status
- `LOADFILE://path` - Load file into LightBurn
- `FORCELOAD://path` - Force load (close current)
- `START` - Start current job
- `CLOSE` - Close current file
- `FORCECLOSE` - Force close

**Port:** 19840 (fixed, not configurable)
**Reply Port:** 19841

### Python Implementation
```python
import socket

LB_HOST, LB_PORT = "127.0.0.1", 19840

def send_lightburn_command(cmd):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.5)
    s.sendto(cmd.encode("utf-8"), (LB_HOST, LB_PORT))
    try:
        reply = s.recvfrom(1024)[0].decode()
        return reply
    except socket.timeout:
        return None

# Usage
send_lightburn_command("PING")
send_lightburn_command("LOADFILE://path/to/aligned_export.svg")
send_lightburn_command("START")
```

### DPI Configuration
- Export SVG at known DPI (96 or 300)
- Set in LightBurn: `Edit → Settings → File Settings → SVG Import DPI`
- Ensures physical sizes match exactly

---

## ArUco Marker System

### Why ArUco/AprilTag?
- **Robust detection** even with partial occlusion
- **Pose estimation** gives exact position/rotation
- **Sub-pixel accuracy** for corner detection
- **Free to print** - just generate and print PDF

### Tag Layout
```
┌─────────────────────────────────┐
│ [ID:0]                  [ID:1]  │  ← 200mm →
│  (0,200)              (200,200) │
│                                 │
│                                 │
│         Engraving Area          │
│                                 │
│                                 │
│ [ID:3]                  [ID:2]  │
│  (0,0)                  (200,0) │
└─────────────────────────────────┘
```

### Tag Specifications
- **Dictionary**: DICT_4X4_50 (simple, reliable)
- **Size**: 25-50mm squares (visible from camera height)
- **Placement**: Fixed to jig with tape/pins (don't move)
- **IDs**: 0,1,2,3 (bottom-left, bottom-right, top-right, top-left)

---

## Technical Implementation

### Core Algorithm

1. **Detect Tags**
   ```python
   detector = cv2.aruco.ArucoDetector(ARUCO_DICT, PARAMS)
   corners, ids, _ = detector.detectMarkers(gray_image)
   ```

2. **Order Points**
   ```python
   # Map detected tag centers to known board coordinates
   board_mm = np.array([
       [0.0, 0.0],      # ID:0
       [200.0, 0.0],    # ID:1
       [200.0, 200.0],  # ID:2
       [0.0, 200.0]     # ID:3
   ])
   ```

3. **Compute Homography**
   ```python
   H, _ = cv2.findHomography(board_mm, image_pixels, cv2.RANSAC)
   ```

4. **Warp Design**
   ```python
   # Map design quad (in mm) to image pixels using H
   design_quad_px = cv2.perspectiveTransform(design_quad_mm, H)

   # Warp design image into camera view
   warped = cv2.warpPerspective(design, H_design_to_img, image_size)
   ```

5. **Export at Scale**
   ```python
   # Export at 300 DPI
   DPI = 300
   px_per_mm = DPI / 25.4
   canvas_size = (int(200 * px_per_mm), int(200 * px_per_mm))
   # Place design at exact mm coordinates
   ```

6. **Send to LightBurn**
   ```python
   send_lightburn_command(f"LOADFILE://{export_path}")
   send_lightburn_command("START")  # optional
   ```

---

## Dependencies

```txt
opencv-contrib-python>=4.8.0  # Includes ArUco
numpy>=1.24.0
Pillow>=10.0.0
```

**Note:** Use `opencv-contrib-python` (not `opencv-python`) for ArUco support

---

## Upgrades & Future Features

### Phase 1 (MVP)
- [x] ArUco tag detection
- [ ] Camera calibration tool
- [ ] Homography mapping
- [ ] Design warping
- [ ] SVG export at scale
- [ ] LightBurn UDP integration

### Phase 2
- [ ] Streamlit UI (drag-drop designs, live preview)
- [ ] Saved jig profiles (tag positions, sizes)
- [ ] Auto-detect object edges (no tags needed)
- [ ] Rotation/offset adjustments
- [ ] Batch processing

### Phase 3
- [ ] AprilTag support (more robust)
- [ ] Multiple jig configurations
- [ ] Integration with LightBurn Camera Overlay
- [ ] Auto-start safety checks
- [ ] Production logging

---

## File Structure

```
lightburn-auto-align/
├── align.py              # Main alignment tool (current)
├── aruco_align.py        # ArUco-based alignment (new)
├── calibrate.py          # Camera calibration tool
├── lightburn_udp.py      # LightBurn UDP interface
├── config/
│   ├── camera.yml        # Camera calibration
│   └── jigs/             # Saved jig configs
│       └── default.json
├── markers/
│   └── aruco_board.pdf   # Printable marker sheet
├── requirements.txt
└── README.md
```

---

## Resources

- **OpenCV ArUco**: https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html
- **AprilTag**: https://april.eecs.umich.edu/software/apriltag
- **LightBurn UDP**: https://forum.lightburnsoftware.com/t/udp-commands/
- **Camera Calibration**: https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html

---

**Next Steps:**
1. Generate ArUco board PDF for printing
2. Build camera calibration tool
3. Implement ArUco detection with homography
4. Add LightBurn UDP sender
5. Create simple UI (CLI first, then Streamlit)
