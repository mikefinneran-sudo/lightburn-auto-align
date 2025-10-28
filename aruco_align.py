#!/usr/bin/env python3
"""
ArUco-Based Alignment System
Precise laser engraving alignment using ArUco markers and homography mapping
"""

import cv2
import numpy as np
from pathlib import Path
import json


class ArucoAligner:
    """
    Detects ArUco markers and calculates precise alignment using homography
    """

    def __init__(self, jig_config_path, camera_config_path=None):
        """
        Initialize aligner

        Args:
            jig_config_path: Path to jig configuration JSON
            camera_config_path: Optional path to camera calibration YAML
        """
        self.jig_config = self.load_jig_config(jig_config_path)
        self.camera_matrix = None
        self.dist_coeffs = None

        if camera_config_path:
            self.load_camera_calibration(camera_config_path)

        # Initialize ArUco detector
        aruco_dict_name = self.jig_config.get('dictionary', 'DICT_4X4_50')
        aruco_dict_id = getattr(cv2.aruco, aruco_dict_name)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_id)

        # Create detector with parameters
        self.detector_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.detector_params)

        # Storage for detection results
        self.image = None
        self.detected_markers = {}
        self.homography = None

    def load_jig_config(self, config_path):
        """Load jig configuration (marker positions)"""
        with open(config_path, 'r') as f:
            config = json.load(f)

        print(f"✓ Loaded jig config: {config['jig_name']}")
        print(f"  Board size: {config['board_size_mm']}mm")
        print(f"  Markers: {len(config['markers'])}")

        return config

    def load_camera_calibration(self, calib_path):
        """Load camera calibration data"""
        fs = cv2.FileStorage(str(calib_path), cv2.FILE_STORAGE_READ)

        if not fs.isOpened():
            print(f"⚠ Could not load camera calibration: {calib_path}")
            return

        self.camera_matrix = fs.getNode('camera_matrix').mat()
        self.dist_coeffs = fs.getNode('distortion_coefficients').mat()
        fs.release()

        print(f"✓ Loaded camera calibration: {calib_path}")

    def load_image(self, image_path):
        """Load camera snapshot image"""
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Undistort if calibration is available
        if self.camera_matrix is not None:
            h, w = self.image.shape[:2]
            new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
                self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h)
            )
            self.image = cv2.undistort(
                self.image, self.camera_matrix, self.dist_coeffs, None, new_camera_matrix
            )
            print("✓ Image undistorted using camera calibration")

        print(f"✓ Loaded image: {self.image.shape[1]}x{self.image.shape[0]}")

    def detect_markers(self):
        """
        Detect ArUco markers in the image

        Returns:
            dict: {marker_id: center_point}
        """
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Detect markers
        corners, ids, rejected = self.detector.detectMarkers(gray)

        if ids is None or len(ids) == 0:
            raise ValueError("No ArUco markers detected in image")

        # Calculate center points of detected markers
        self.detected_markers = {}
        for i, marker_id in enumerate(ids.flatten()):
            marker_id = int(marker_id)
            corner_points = corners[i][0]

            # Calculate center point
            center = np.mean(corner_points, axis=0)
            self.detected_markers[marker_id] = center

        print(f"✓ Detected {len(self.detected_markers)} markers: {list(self.detected_markers.keys())}")

        return self.detected_markers

    def calculate_homography(self):
        """
        Calculate homography matrix from detected markers to jig coordinates

        Returns:
            np.ndarray: 3x3 homography matrix
        """
        # Build point correspondences
        src_points = []  # Real-world mm coordinates
        dst_points = []  # Image pixel coordinates

        for marker_id_str, marker_info in self.jig_config['markers'].items():
            marker_id = int(marker_id_str)

            if marker_id not in self.detected_markers:
                print(f"⚠ Marker {marker_id} not detected, skipping")
                continue

            # Get real-world position (in mm)
            real_pos = marker_info['position_mm']
            src_points.append(real_pos)

            # Get detected position (in pixels)
            detected_pos = self.detected_markers[marker_id]
            dst_points.append(detected_pos)

        if len(src_points) < 4:
            raise ValueError(f"Need at least 4 markers for accurate homography (found {len(src_points)})")

        src_points = np.array(src_points, dtype=np.float32)
        dst_points = np.array(dst_points, dtype=np.float32)

        # Calculate homography: maps from mm coordinates to pixel coordinates
        self.homography, mask = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 5.0)

        if self.homography is None:
            raise ValueError("Failed to calculate homography")

        print(f"✓ Homography calculated from {len(src_points)} markers")

        return self.homography

    def transform_point(self, point_mm):
        """
        Transform a point from mm coordinates to pixel coordinates

        Args:
            point_mm: (x, y) in millimeters

        Returns:
            (x, y) in pixels
        """
        if self.homography is None:
            raise ValueError("Homography not calculated yet")

        point_mm = np.array([[[point_mm[0], point_mm[1]]]], dtype=np.float32)
        point_px = cv2.perspectiveTransform(point_mm, self.homography)

        return point_px[0][0]

    def transform_rect(self, rect_mm):
        """
        Transform a rectangle from mm coordinates to pixel coordinates

        Args:
            rect_mm: (x, y, width, height) in millimeters

        Returns:
            4 corner points in pixels
        """
        x, y, w, h = rect_mm

        # Define rectangle corners in mm
        corners_mm = np.array([
            [[x, y]],
            [[x + w, y]],
            [[x + w, y + h]],
            [[x, y + h]]
        ], dtype=np.float32)

        # Transform to pixels
        corners_px = cv2.perspectiveTransform(corners_mm, self.homography)

        return corners_px.reshape(-1, 2)

    def get_board_bounds_px(self):
        """
        Get the engraving board boundaries in pixel coordinates

        Returns:
            4 corner points in pixels
        """
        board_size = self.jig_config['board_size_mm']
        return self.transform_rect((0, 0, board_size, board_size))

    def calculate_alignment_for_design(self, design_rect_mm):
        """
        Calculate alignment data for a design

        Args:
            design_rect_mm: (x, y, width, height) in millimeters
                           where (0,0) is bottom-left of engraving area

        Returns:
            dict with alignment data
        """
        # Transform design corners to pixels
        corners_px = self.transform_rect(design_rect_mm)

        # Calculate center
        center_px = np.mean(corners_px, axis=0)

        # Calculate rotation (angle of bottom edge)
        bottom_left = corners_px[0]
        bottom_right = corners_px[1]
        angle_rad = np.arctan2(
            bottom_right[1] - bottom_left[1],
            bottom_right[0] - bottom_left[0]
        )
        angle_deg = np.degrees(angle_rad)

        # Calculate size in pixels
        width_px = np.linalg.norm(bottom_right - bottom_left)
        height_px = np.linalg.norm(corners_px[3] - bottom_left)

        result = {
            'design_rect_mm': design_rect_mm,
            'center_px': center_px.tolist(),
            'corners_px': corners_px.tolist(),
            'angle_deg': float(angle_deg),
            'size_px': [float(width_px), float(height_px)],
            'image_size': [self.image.shape[1], self.image.shape[0]]
        }

        return result

    def visualize_detection(self, output_path=None, design_rect_mm=None):
        """
        Visualize detected markers and alignment

        Args:
            output_path: Optional path to save visualization
            design_rect_mm: Optional design rectangle to overlay
        """
        vis_img = self.image.copy()

        # Draw detected markers
        for marker_id, center in self.detected_markers.items():
            center_int = tuple(center.astype(int))

            # Draw marker center
            cv2.circle(vis_img, center_int, 10, (0, 255, 0), -1)

            # Draw marker ID
            cv2.putText(
                vis_img, f"ID:{marker_id}", (center_int[0] + 15, center_int[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

        # Draw board outline
        if self.homography is not None:
            board_corners = self.get_board_bounds_px()
            board_corners_int = board_corners.astype(int)
            cv2.polylines(vis_img, [board_corners_int], True, (255, 255, 0), 3)

            # Draw coordinate system
            origin_px = self.transform_point((0, 0))
            x_axis_px = self.transform_point((50, 0))  # 50mm along X
            y_axis_px = self.transform_point((0, 50))  # 50mm along Y

            origin_int = tuple(origin_px.astype(int))
            x_axis_int = tuple(x_axis_px.astype(int))
            y_axis_int = tuple(y_axis_px.astype(int))

            # X-axis (red)
            cv2.arrowedLine(vis_img, origin_int, x_axis_int, (0, 0, 255), 3, tipLength=0.3)
            cv2.putText(vis_img, "X", x_axis_int, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Y-axis (green)
            cv2.arrowedLine(vis_img, origin_int, y_axis_int, (0, 255, 0), 3, tipLength=0.3)
            cv2.putText(vis_img, "Y", y_axis_int, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Origin label
            cv2.putText(vis_img, "Origin (0,0)", (origin_int[0] - 50, origin_int[1] + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw design rectangle if provided
        if design_rect_mm is not None and self.homography is not None:
            design_corners = self.transform_rect(design_rect_mm)
            design_corners_int = design_corners.astype(int)
            cv2.polylines(vis_img, [design_corners_int], True, (255, 0, 255), 2)

            # Draw design center
            design_center = np.mean(design_corners, axis=0).astype(int)
            cv2.circle(vis_img, tuple(design_center), 8, (255, 0, 255), -1)
            cv2.putText(vis_img, "Design", (design_center[0] + 10, design_center[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

        if output_path:
            cv2.imwrite(str(output_path), vis_img)
            print(f"✓ Visualization saved: {output_path}")

        return vis_img

    def process(self, image_path, design_rect_mm=None, visualize=True):
        """
        Complete alignment process

        Args:
            image_path: Path to camera snapshot
            design_rect_mm: Optional (x, y, width, height) of design in mm
            visualize: Create visualization output

        Returns:
            dict with alignment data
        """
        print(f"\n{'='*60}")
        print(f"ArUco Alignment System")
        print(f"{'='*60}\n")

        self.load_image(image_path)
        self.detect_markers()
        self.calculate_homography()

        alignment_data = None
        if design_rect_mm:
            alignment_data = self.calculate_alignment_for_design(design_rect_mm)

            print(f"\n✓ Design alignment calculated:")
            print(f"  Position: {design_rect_mm[:2]} mm")
            print(f"  Size: {design_rect_mm[2:]} mm")
            print(f"  Center: {alignment_data['center_px']} px")
            print(f"  Rotation: {alignment_data['angle_deg']:.2f}°")
            print(f"  Size: {alignment_data['size_px'][0]:.1f}x{alignment_data['size_px'][1]:.1f} px")

        if visualize:
            vis_path = Path(image_path).parent / f"{Path(image_path).stem}_aligned.jpg"
            self.visualize_detection(vis_path, design_rect_mm)

        print(f"\n{'='*60}")
        print(f"Alignment Complete")
        print(f"{'='*60}\n")

        return alignment_data


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='ArUco-based laser engraving alignment')
    parser.add_argument('image', help='Camera snapshot image')
    parser.add_argument('--jig-config', default='config/jigs/default.json',
                       help='Jig configuration file')
    parser.add_argument('--camera-calib', default='config/camera.yml',
                       help='Camera calibration file (optional)')
    parser.add_argument('--design', nargs=4, type=float, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                       help='Design rectangle in mm (x y width height)')
    parser.add_argument('--no-viz', action='store_true',
                       help='Skip visualization output')

    args = parser.parse_args()

    # Check if camera calibration exists
    camera_calib = args.camera_calib if Path(args.camera_calib).exists() else None

    try:
        aligner = ArucoAligner(args.jig_config, camera_calib)

        design_rect = None
        if args.design:
            design_rect = tuple(args.design)

        alignment_data = aligner.process(
            args.image,
            design_rect_mm=design_rect,
            visualize=not args.no_viz
        )

        if alignment_data:
            print("\nAlignment Data:")
            print(json.dumps(alignment_data, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
