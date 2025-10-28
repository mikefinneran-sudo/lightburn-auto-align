#!/usr/bin/env python3
"""
ArUco Marker Board Generator
Creates printable PDF with 4 ArUco markers for laser engraving jig
"""

import cv2
import numpy as np
from pathlib import Path


class ArucoMarkerGenerator:
    """
    Generates ArUco marker boards for camera-based alignment
    """

    def __init__(self, board_size_mm=200, marker_size_mm=40, margin_mm=10):
        """
        Initialize marker generator

        Args:
            board_size_mm: Size of the engraving area (square)
            marker_size_mm: Size of each ArUco marker
            margin_mm: Margin around the board
        """
        self.board_size_mm = board_size_mm
        self.marker_size_mm = marker_size_mm
        self.margin_mm = margin_mm

        # Use DICT_4X4_50 - simple and reliable
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        # Calculate output size (A4 is 210x297mm, use 300 DPI)
        self.dpi = 300
        self.px_per_mm = self.dpi / 25.4

    def generate_marker(self, marker_id, size_px):
        """Generate a single ArUco marker image"""
        marker_img = cv2.aruco.generateImageMarker(
            self.aruco_dict,
            marker_id,
            size_px
        )
        return marker_img

    def create_board(self):
        """
        Create the complete marker board with 4 corner markers

        Layout:
        [ID:3]                  [ID:2]
         (0,200)              (200,200)

              Engraving Area

        [ID:0]                  [ID:1]
         (0,0)                  (200,0)
        """
        # Calculate canvas size in pixels
        total_size_mm = self.board_size_mm + (2 * self.margin_mm)
        canvas_size_px = int(total_size_mm * self.px_per_mm)

        # Create white canvas
        canvas = np.ones((canvas_size_px, canvas_size_px), dtype=np.uint8) * 255

        # Marker size in pixels
        marker_size_px = int(self.marker_size_mm * self.px_per_mm)

        # Generate all 4 markers
        markers = {
            0: self.generate_marker(0, marker_size_px),  # Bottom-left
            1: self.generate_marker(1, marker_size_px),  # Bottom-right
            2: self.generate_marker(2, marker_size_px),  # Top-right
            3: self.generate_marker(3, marker_size_px),  # Top-left
        }

        # Calculate positions (in pixels from top-left)
        margin_px = int(self.margin_mm * self.px_per_mm)
        board_size_px = int(self.board_size_mm * self.px_per_mm)

        # Position markers at corners
        positions = {
            0: (margin_px, canvas_size_px - margin_px - marker_size_px),  # Bottom-left
            1: (margin_px + board_size_px - marker_size_px,
                canvas_size_px - margin_px - marker_size_px),  # Bottom-right
            2: (margin_px + board_size_px - marker_size_px, margin_px),  # Top-right
            3: (margin_px, margin_px),  # Top-left
        }

        # Place markers on canvas
        for marker_id, (x, y) in positions.items():
            marker = markers[marker_id]
            canvas[y:y+marker_size_px, x:x+marker_size_px] = marker

        # Draw engraving area outline
        top_left = (margin_px, margin_px)
        bottom_right = (margin_px + board_size_px, margin_px + board_size_px)
        cv2.rectangle(canvas, top_left, bottom_right, 128, 2)

        # Add labels and dimensions
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2

        # Label each marker
        for marker_id, (x, y) in positions.items():
            label = f"ID:{marker_id}"
            label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
            label_x = x + (marker_size_px - label_size[0]) // 2
            label_y = y + marker_size_px + 30
            cv2.putText(canvas, label, (label_x, label_y),
                       font, font_scale, 0, font_thickness)

        # Add coordinate labels
        coords = {
            0: f"(0, 0)",
            1: f"({self.board_size_mm}, 0)",
            2: f"({self.board_size_mm}, {self.board_size_mm})",
            3: f"(0, {self.board_size_mm})",
        }

        for marker_id, (x, y) in positions.items():
            coord_label = coords[marker_id]
            label_size = cv2.getTextSize(coord_label, font, 0.4, 1)[0]
            label_x = x + (marker_size_px - label_size[0]) // 2
            label_y = y + marker_size_px + 55
            cv2.putText(canvas, coord_label, (label_x, label_y),
                       font, 0.4, 0, 1)

        # Add title and info
        title = "LightBurn Auto-Align - ArUco Marker Board"
        cv2.putText(canvas, title, (margin_px, margin_px - 40),
                   font, 0.8, 0, 2)

        info_lines = [
            f"Engraving Area: {self.board_size_mm}mm x {self.board_size_mm}mm",
            f"Marker Size: {self.marker_size_mm}mm",
            f"Dictionary: DICT_4X4_50",
            "Mount markers at EXACT positions shown",
            "Origin (0,0) is BOTTOM-LEFT (ID:0)",
        ]

        y_offset = canvas_size_px - margin_px + 40
        for i, line in enumerate(info_lines):
            cv2.putText(canvas, line, (margin_px, y_offset + i*25),
                       font, 0.4, 0, 1)

        return canvas

    def save_image(self, canvas, output_path):
        """Save the marker board as PNG"""
        cv2.imwrite(output_path, canvas)
        print(f"✓ Marker board saved: {output_path}")

    def save_pdf(self, canvas, output_path):
        """Save the marker board as PDF"""
        from PIL import Image

        # Convert from OpenCV BGR to RGB
        pil_image = Image.fromarray(canvas)

        # Calculate PDF size in points (1 inch = 72 points)
        width_inches = canvas.shape[1] / self.dpi
        height_inches = canvas.shape[0] / self.dpi
        width_points = width_inches * 72
        height_points = height_inches * 72

        # Save as PDF
        pil_image.save(
            output_path,
            "PDF",
            resolution=self.dpi,
            page_size=(width_points, height_points)
        )
        print(f"✓ PDF saved: {output_path}")

    def create_config(self, output_path):
        """
        Create JSON config file with marker positions
        This will be used by the alignment tool
        """
        import json

        config = {
            "jig_name": "default",
            "board_size_mm": self.board_size_mm,
            "marker_size_mm": self.marker_size_mm,
            "dictionary": "DICT_4X4_50",
            "markers": {
                "0": {"position_mm": [0.0, 0.0], "corner": "bottom-left"},
                "1": {"position_mm": [float(self.board_size_mm), 0.0], "corner": "bottom-right"},
                "2": {"position_mm": [float(self.board_size_mm), float(self.board_size_mm)], "corner": "top-right"},
                "3": {"position_mm": [0.0, float(self.board_size_mm)], "corner": "top-left"},
            },
            "notes": [
                "Origin (0,0) is at bottom-left corner (ID:0)",
                "Y-axis increases upward",
                "X-axis increases to the right",
                "All measurements in millimeters"
            ]
        }

        # Ensure config directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Config saved: {output_path}")


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate ArUco marker board for laser engraving alignment'
    )
    parser.add_argument(
        '--size',
        type=int,
        default=200,
        help='Engraving area size in mm (default: 200)'
    )
    parser.add_argument(
        '--marker-size',
        type=int,
        default=40,
        help='Marker size in mm (default: 40)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='markers',
        help='Output directory (default: markers/)'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(__file__).parent / args.output_dir
    output_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"ArUco Marker Board Generator")
    print(f"{'='*60}\n")

    # Generate marker board
    generator = ArucoMarkerGenerator(
        board_size_mm=args.size,
        marker_size_mm=args.marker_size
    )

    print(f"Generating board:")
    print(f"  Engraving area: {args.size}mm x {args.size}mm")
    print(f"  Marker size: {args.marker_size}mm")
    print(f"  Dictionary: DICT_4X4_50\n")

    canvas = generator.create_board()

    # Save outputs
    png_path = str(output_dir / "aruco_board.png")
    pdf_path = str(output_dir / "aruco_board.pdf")
    config_path = output_dir.parent / "config" / "jigs" / "default.json"

    generator.save_image(canvas, png_path)
    generator.save_pdf(canvas, pdf_path)
    generator.create_config(config_path)

    print(f"\n{'='*60}")
    print(f"Next Steps:")
    print(f"{'='*60}")
    print(f"1. Print {pdf_path} at 100% scale (no scaling!)")
    print(f"2. Verify printed size with ruler")
    print(f"3. Mount markers on flat jig at exact positions")
    print(f"4. Run camera calibration tool")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
