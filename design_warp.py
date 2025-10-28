#!/usr/bin/env python3
"""
Design Warping and Export Module
Warps designs to aligned positions and exports for LightBurn
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import json


class DesignWarper:
    """
    Warps design images to match alignment and exports at correct scale
    """

    def __init__(self, alignment_data, dpi=300):
        """
        Initialize design warper

        Args:
            alignment_data: Alignment data from ArucoAligner
            dpi: Target DPI for export (default 300)
        """
        self.alignment_data = alignment_data
        self.dpi = dpi
        self.px_per_mm = dpi / 25.4

        self.design_image = None
        self.warped_design = None

    def load_design(self, design_path):
        """
        Load design image (PNG, JPG, or simple SVG rasterization)

        Args:
            design_path: Path to design file
        """
        design_path = Path(design_path)

        if design_path.suffix.lower() == '.svg':
            # For SVG, we'll use cairosvg or simple rasterization
            # For now, raise an error and ask for PNG
            raise NotImplementedError(
                "SVG loading requires cairosvg. "
                "Please convert to PNG first or provide PNG design."
            )

        # Load as image
        self.design_image = cv2.imread(str(design_path), cv2.IMREAD_UNCHANGED)

        if self.design_image is None:
            raise ValueError(f"Could not load design: {design_path}")

        print(f"✓ Loaded design: {self.design_image.shape[1]}x{self.design_image.shape[0]}")
        print(f"  Channels: {self.design_image.shape[2] if len(self.design_image.shape) > 2 else 1}")

        return self.design_image

    def create_design_from_text(self, text, size_mm, font_scale=2, thickness=3):
        """
        Create a simple text design

        Args:
            text: Text to render
            size_mm: (width, height) in mm
            font_scale: Font scale factor
            thickness: Text thickness

        Returns:
            Design image
        """
        # Calculate size in pixels at target DPI
        width_px = int(size_mm[0] * self.px_per_mm)
        height_px = int(size_mm[1] * self.px_per_mm)

        # Create white canvas
        self.design_image = np.ones((height_px, width_px, 3), dtype=np.uint8) * 255

        # Get text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )

        # Center text
        x = (width_px - text_width) // 2
        y = (height_px + text_height) // 2

        # Draw text (black on white)
        cv2.putText(
            self.design_image, text, (x, y),
            font, font_scale, (0, 0, 0), thickness
        )

        print(f"✓ Created text design: '{text}'")
        print(f"  Size: {width_px}x{height_px}px ({size_mm[0]}x{size_mm[1]}mm @ {self.dpi} DPI)")

        return self.design_image

    def warp_to_alignment(self, camera_image):
        """
        Warp design to match the aligned position in camera view

        Args:
            camera_image: Camera snapshot image

        Returns:
            Warped design overlaid on camera image
        """
        if self.design_image is None:
            raise ValueError("No design loaded")

        # Get alignment corners
        corners_px = np.array(self.alignment_data['corners_px'], dtype=np.float32)

        # Source corners (design image corners)
        h, w = self.design_image.shape[:2]
        src_corners = np.array([
            [0, 0],
            [w, 0],
            [w, h],
            [0, h]
        ], dtype=np.float32)

        # Calculate perspective transform
        M = cv2.getPerspectiveTransform(src_corners, corners_px)

        # Warp design to camera view
        warped = cv2.warpPerspective(
            self.design_image,
            M,
            (camera_image.shape[1], camera_image.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255, 0)
        )

        # Create composite
        composite = camera_image.copy()

        # Handle alpha channel if present
        if len(warped.shape) == 3 and warped.shape[2] == 4:
            # Extract alpha channel
            alpha = warped[:, :, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=2)

            # Blend with alpha
            composite = (alpha * warped[:, :, :3] + (1 - alpha) * composite).astype(np.uint8)
        else:
            # Simple overlay (white = transparent)
            mask = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            mask = cv2.threshold(mask, 250, 255, cv2.THRESH_BINARY_INV)[1]
            composite = cv2.bitwise_and(composite, composite, mask=cv2.bitwise_not(mask))
            composite = cv2.add(composite, warped)

        self.warped_design = warped

        print(f"✓ Design warped to alignment")

        return composite

    def export_for_lightburn(self, output_path, format='png'):
        """
        Export design at correct physical size for LightBurn

        Args:
            output_path: Output file path
            format: 'png' or 'svg'

        Returns:
            Path to exported file
        """
        if self.design_image is None:
            raise ValueError("No design loaded")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get design size in mm
        design_rect_mm = self.alignment_data['design_rect_mm']
        width_mm, height_mm = design_rect_mm[2], design_rect_mm[3]

        # Calculate exact size in pixels at target DPI
        width_px = int(width_mm * self.px_per_mm)
        height_px = int(height_mm * self.px_per_mm)

        # Resize design to exact dimensions
        design_resized = cv2.resize(
            self.design_image,
            (width_px, height_px),
            interpolation=cv2.INTER_LINEAR
        )

        if format.lower() == 'png':
            # Export as PNG with DPI metadata
            pil_image = Image.fromarray(cv2.cvtColor(design_resized, cv2.COLOR_BGR2RGB))
            pil_image.save(
                str(output_path),
                dpi=(self.dpi, self.dpi),
                optimize=True
            )

            print(f"✓ Exported PNG: {output_path}")
            print(f"  Physical size: {width_mm:.1f}x{height_mm:.1f}mm")
            print(f"  Pixel size: {width_px}x{height_px}px")
            print(f"  DPI: {self.dpi}")

        elif format.lower() == 'svg':
            # Export as SVG with embedded image
            self._export_svg(design_resized, output_path, width_mm, height_mm)

        else:
            raise ValueError(f"Unsupported format: {format}")

        return output_path

    def _export_svg(self, design_image, output_path, width_mm, height_mm):
        """Export design as SVG with embedded raster image"""
        import base64

        # Convert to PNG bytes
        _, png_buffer = cv2.imencode('.png', design_image)
        png_base64 = base64.b64encode(png_buffer).decode('utf-8')

        # Create SVG with embedded image
        svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="{width_mm}mm"
   height="{height_mm}mm"
   viewBox="0 0 {width_mm} {height_mm}"
   version="1.1"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink">
  <image
     width="{width_mm}"
     height="{height_mm}"
     preserveAspectRatio="none"
     xlink:href="data:image/png;base64,{png_base64}"
     x="0"
     y="0" />
</svg>
'''

        with open(output_path, 'w') as f:
            f.write(svg_content)

        print(f"✓ Exported SVG: {output_path}")
        print(f"  Physical size: {width_mm:.1f}x{height_mm:.1f}mm")

    def save_alignment_json(self, output_path):
        """Save alignment data as JSON for reference"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.alignment_data, f, indent=2)

        print(f"✓ Alignment data saved: {output_path}")


class DesignPlacer:
    """
    Interactive tool for placing designs on camera view
    """

    def __init__(self, homography, board_size_mm):
        """
        Initialize design placer

        Args:
            homography: Homography matrix from ArucoAligner
            board_size_mm: Board size in mm
        """
        self.homography = homography
        self.board_size_mm = board_size_mm

    def place_design_interactive(self, camera_image, design_size_mm):
        """
        Interactive placement of design on camera view

        Args:
            camera_image: Camera snapshot
            design_size_mm: (width, height) in mm

        Returns:
            (x, y, width, height) in mm
        """
        print(f"\nInteractive Design Placement")
        print(f"Design size: {design_size_mm[0]}x{design_size_mm[1]}mm")
        print(f"Click to place design, ESC to cancel")

        self.selected_position = None

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.selected_position = (x, y)

        cv2.namedWindow('Place Design')
        cv2.setMouseCallback('Place Design', mouse_callback)

        while True:
            display = camera_image.copy()

            if self.selected_position:
                # Transform click position to mm coordinates
                click_px = np.array([[[self.selected_position[0], self.selected_position[1]]]], dtype=np.float32)
                click_mm = cv2.perspectiveTransform(click_px, np.linalg.inv(self.homography))
                x_mm, y_mm = click_mm[0][0]

                # Center design on click
                design_x = x_mm - design_size_mm[0] / 2
                design_y = y_mm - design_size_mm[1] / 2

                # Draw design rectangle
                design_rect_mm = (design_x, design_y, design_size_mm[0], design_size_mm[1])
                corners_mm = np.array([
                    [[design_x, design_y]],
                    [[design_x + design_size_mm[0], design_y]],
                    [[design_x + design_size_mm[0], design_y + design_size_mm[1]]],
                    [[design_x, design_y + design_size_mm[1]]]
                ], dtype=np.float32)

                corners_px = cv2.perspectiveTransform(corners_mm, self.homography)
                corners_int = corners_px.reshape(-1, 2).astype(int)

                cv2.polylines(display, [corners_int], True, (255, 0, 255), 2)
                cv2.circle(display, self.selected_position, 5, (255, 0, 255), -1)

                cv2.putText(display, f"Position: ({design_x:.1f}, {design_y:.1f})mm",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(display, "Press ENTER to confirm, ESC to cancel",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow('Place Design', display)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                print("Placement cancelled")
                cv2.destroyAllWindows()
                return None
            elif key == 13 and self.selected_position:  # ENTER
                cv2.destroyAllWindows()
                return design_rect_mm

        cv2.destroyAllWindows()
        return None


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Design warping and export tool')
    parser.add_argument('alignment_json', help='Alignment JSON file from aruco_align.py')
    parser.add_argument('--design', help='Design image file (PNG)')
    parser.add_argument('--text', help='Create text design instead')
    parser.add_argument('--camera-image', help='Camera image for preview')
    parser.add_argument('--output', default='output/aligned_design.png',
                       help='Output file path')
    parser.add_argument('--format', choices=['png', 'svg'], default='png',
                       help='Output format')
    parser.add_argument('--dpi', type=int, default=300,
                       help='Output DPI (default: 300)')

    args = parser.parse_args()

    try:
        # Load alignment data
        with open(args.alignment_json, 'r') as f:
            alignment_data = json.load(f)

        print(f"✓ Loaded alignment data: {args.alignment_json}")

        # Create warper
        warper = DesignWarper(alignment_data, dpi=args.dpi)

        # Load or create design
        if args.text:
            # Extract size from alignment data
            design_rect = alignment_data['design_rect_mm']
            size_mm = (design_rect[2], design_rect[3])
            warper.create_design_from_text(args.text, size_mm)
        elif args.design:
            warper.load_design(args.design)
        else:
            print("Error: Must specify either --design or --text")
            return 1

        # Create preview if camera image provided
        if args.camera_image:
            camera_img = cv2.imread(args.camera_image)
            if camera_img is not None:
                preview = warper.warp_to_alignment(camera_img)
                preview_path = Path(args.output).parent / 'preview.jpg'
                cv2.imwrite(str(preview_path), preview)
                print(f"✓ Preview saved: {preview_path}")

        # Export for LightBurn
        warper.export_for_lightburn(args.output, format=args.format)

        # Save alignment data copy
        json_path = Path(args.output).with_suffix('.json')
        warper.save_alignment_json(json_path)

        print(f"\n✓ Export complete!")
        print(f"\nNext steps:")
        print(f"1. Import {args.output} into LightBurn")
        print(f"2. Verify size is correct ({alignment_data['design_rect_mm'][2]:.1f}x{alignment_data['design_rect_mm'][3]:.1f}mm)")
        print(f"3. Position at ({alignment_data['design_rect_mm'][0]:.1f}, {alignment_data['design_rect_mm'][1]:.1f})mm")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
