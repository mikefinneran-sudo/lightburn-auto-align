#!/usr/bin/env python3
"""
LightBurn Auto-Align
Automatically align designs to material using camera photo edge detection
"""

import cv2
import numpy as np
from pathlib import Path


class LightBurnAligner:
    """
    Detects material edges and grid lines in LightBurn camera photos
    and calculates alignment offsets
    """

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.image = None
        self.gray = None
        self.edges = None

    def load_image(self):
        """Load and preprocess the camera image"""
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"Could not load image: {self.image_path}")

        # Convert to grayscale for edge detection
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        print(f"✓ Loaded image: {self.image.shape[1]}x{self.image.shape[0]}")

    def detect_edges(self):
        """Detect edges in the image using Canny edge detection"""
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)

        # Canny edge detection
        self.edges = cv2.Canny(blurred, 50, 150)
        print(f"✓ Edge detection complete")

    def find_material_bounds(self):
        """
        Find the bounding rectangle of the material
        Returns: (x, y, width, height, angle)
        """
        # Find contours
        contours, _ = cv2.findContours(
            self.edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            raise ValueError("No contours found in image")

        # Get the largest contour (likely the material)
        largest_contour = max(contours, key=cv2.contourArea)

        # Get minimum area rectangle (handles rotation)
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        center, (width, height), angle = rect

        print(f"✓ Material detected:")
        print(f"  Center: ({center[0]:.1f}, {center[1]:.1f})")
        print(f"  Size: {width:.1f} x {height:.1f}")
        print(f"  Rotation: {angle:.2f}°")

        return center, (width, height), angle, box

    def detect_grid_lines(self):
        """
        Detect LightBurn's overlay grid lines
        Returns: list of horizontal and vertical lines
        """
        # Use Hough Line Transform to detect straight lines
        lines = cv2.HoughLinesP(
            self.edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )

        if lines is None:
            print("⚠ No grid lines detected")
            return [], []

        horizontal_lines = []
        vertical_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Calculate angle
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

            # Classify as horizontal or vertical (with tolerance)
            if angle < 10 or angle > 170:
                horizontal_lines.append(line[0])
            elif 80 < angle < 100:
                vertical_lines.append(line[0])

        print(f"✓ Grid detected: {len(horizontal_lines)} horizontal, {len(vertical_lines)} vertical lines")
        return horizontal_lines, vertical_lines

    def calculate_alignment(self, center, angle):
        """
        Calculate the alignment offset needed
        Returns: dict with x_offset, y_offset, rotation
        """
        # Get image center as reference point
        img_center_x = self.image.shape[1] / 2
        img_center_y = self.image.shape[0] / 2

        # Calculate offsets from image center
        x_offset = center[0] - img_center_x
        y_offset = center[1] - img_center_y

        # Rotation needed to align (assuming 0° is desired)
        rotation_offset = -angle  # Negative to correct the rotation

        result = {
            'x_offset': x_offset,
            'y_offset': y_offset,
            'rotation': rotation_offset,
            'units': 'pixels'  # TODO: Convert to mm based on LightBurn calibration
        }

        print(f"\n✓ Alignment calculated:")
        print(f"  X offset: {x_offset:+.1f} pixels")
        print(f"  Y offset: {y_offset:+.1f} pixels")
        print(f"  Rotation: {rotation_offset:+.2f}°")

        return result

    def visualize_results(self, center, box, output_path=None):
        """Draw detected material and save visualization"""
        result_img = self.image.copy()

        # Draw bounding box
        cv2.drawContours(result_img, [box], 0, (0, 255, 0), 2)

        # Draw center point
        cv2.circle(result_img, (int(center[0]), int(center[1])), 10, (0, 0, 255), -1)

        # Draw image center for reference
        img_center = (self.image.shape[1] // 2, self.image.shape[0] // 2)
        cv2.circle(result_img, img_center, 10, (255, 0, 0), -1)

        # Draw line showing offset
        cv2.line(result_img, img_center, (int(center[0]), int(center[1])), (255, 255, 0), 2)

        if output_path:
            cv2.imwrite(output_path, result_img)
            print(f"✓ Visualization saved: {output_path}")

        return result_img

    def process(self, visualize=True):
        """
        Run the complete alignment process
        Returns: alignment dict
        """
        print(f"\n{'='*60}")
        print(f"LightBurn Auto-Align")
        print(f"{'='*60}\n")

        self.load_image()
        self.detect_edges()
        center, size, angle, box = self.find_material_bounds()
        h_lines, v_lines = self.detect_grid_lines()
        alignment = self.calculate_alignment(center, angle)

        if visualize:
            output_path = str(self.image_path.parent / f"{self.image_path.stem}_aligned.png")
            self.visualize_results(center, box, output_path)

        print(f"\n{'='*60}")
        print(f"Alignment Complete")
        print(f"{'='*60}\n")

        return alignment


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='LightBurn Auto-Align Tool')
    parser.add_argument('image', help='Path to LightBurn camera snapshot')
    parser.add_argument('--no-viz', action='store_true', help='Skip visualization output')

    args = parser.parse_args()

    try:
        aligner = LightBurnAligner(args.image)
        alignment = aligner.process(visualize=not args.no_viz)

        print("\nApply these offsets in LightBurn:")
        print(f"  X: {alignment['x_offset']:+.1f} {alignment['units']}")
        print(f"  Y: {alignment['y_offset']:+.1f} {alignment['units']}")
        print(f"  Rotation: {alignment['rotation']:+.2f}°\n")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
