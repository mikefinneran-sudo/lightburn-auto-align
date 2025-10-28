#!/usr/bin/env python3
"""
Test Alignment System
Create synthetic test images and validate the complete workflow
"""

import cv2
import numpy as np
from pathlib import Path
import json


def create_test_image_with_markers(output_path, image_size=(1920, 1080),
                                   board_size_mm=200, marker_size_mm=40):
    """
    Create a synthetic camera image with ArUco markers

    Args:
        output_path: Where to save the test image
        image_size: Image dimensions in pixels
        board_size_mm: Board size in mm
        marker_size_mm: Marker size in mm

    Returns:
        Path to created image
    """
    print(f"\n{'='*60}")
    print("Creating Test Image")
    print(f"{'='*60}\n")

    # Create white background
    img = np.ones((image_size[1], image_size[0], 3), dtype=np.uint8) * 240

    # Simulate camera view with some perspective
    # Center the board in the image
    center_x = image_size[0] // 2
    center_y = image_size[1] // 2

    # Scale: pixels per mm (simulate camera at certain height)
    scale = 3.5  # pixels per mm

    # Calculate marker positions in pixels
    marker_size_px = int(marker_size_mm * scale)
    board_size_px = int(board_size_mm * scale)

    # Board corners (centered)
    offset_x = center_x - board_size_px // 2
    offset_y = center_y - board_size_px // 2

    # Draw board outline
    cv2.rectangle(img,
                 (offset_x, offset_y),
                 (offset_x + board_size_px, offset_y + board_size_px),
                 (200, 200, 200), 2)

    # Generate ArUco markers
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    # Marker positions (corners of board)
    positions = {
        0: (offset_x, offset_y + board_size_px - marker_size_px),  # Bottom-left
        1: (offset_x + board_size_px - marker_size_px,
            offset_y + board_size_px - marker_size_px),  # Bottom-right
        2: (offset_x + board_size_px - marker_size_px, offset_y),  # Top-right
        3: (offset_x, offset_y),  # Top-left
    }

    # Place markers
    for marker_id, (x, y) in positions.items():
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size_px)

        # Convert to BGR
        marker_bgr = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)

        # Place on image
        img[y:y+marker_size_px, x:x+marker_size_px] = marker_bgr

        # Label
        label = f"ID:{marker_id}"
        cv2.putText(img, label, (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # Add some texture/noise to simulate real camera
    noise = np.random.normal(0, 5, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Add title
    cv2.putText(img, "Test Camera Image", (20, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    cv2.putText(img, f"Board: {board_size_mm}mm, Markers: {marker_size_mm}mm", (20, 80),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img)

    print(f"✓ Test image created: {output_path}")
    print(f"  Size: {image_size[0]}x{image_size[1]}px")
    print(f"  Board size: {board_size_mm}mm ({board_size_px}px)")
    print(f"  Scale: {scale:.1f} px/mm")

    return output_path


def test_marker_detection(image_path, jig_config_path):
    """
    Test ArUco marker detection

    Args:
        image_path: Path to test image
        jig_config_path: Path to jig config

    Returns:
        bool: True if test passes
    """
    print(f"\n{'='*60}")
    print("Test: Marker Detection")
    print(f"{'='*60}\n")

    from aruco_align import ArucoAligner

    try:
        aligner = ArucoAligner(jig_config_path)
        aligner.load_image(image_path)
        markers = aligner.detect_markers()

        # Check if all 4 markers detected
        if len(markers) == 4:
            print("✓ PASS: All 4 markers detected")
            return True
        else:
            print(f"✗ FAIL: Only {len(markers)}/4 markers detected")
            return False

    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def test_homography_calculation(image_path, jig_config_path):
    """
    Test homography calculation

    Args:
        image_path: Path to test image
        jig_config_path: Path to jig config

    Returns:
        bool: True if test passes
    """
    print(f"\n{'='*60}")
    print("Test: Homography Calculation")
    print(f"{'='*60}\n")

    from aruco_align import ArucoAligner

    try:
        aligner = ArucoAligner(jig_config_path)
        aligner.load_image(image_path)
        aligner.detect_markers()
        H = aligner.calculate_homography()

        if H is not None and H.shape == (3, 3):
            print("✓ PASS: Homography calculated")
            print(f"  Matrix shape: {H.shape}")
            return True
        else:
            print("✗ FAIL: Invalid homography matrix")
            return False

    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def test_alignment_workflow(image_path, jig_config_path):
    """
    Test complete alignment workflow

    Args:
        image_path: Path to test image
        jig_config_path: Path to jig config

    Returns:
        bool: True if test passes
    """
    print(f"\n{'='*60}")
    print("Test: Complete Alignment Workflow")
    print(f"{'='*60}\n")

    from aruco_align import ArucoAligner

    try:
        aligner = ArucoAligner(jig_config_path)

        # Test with a design at center of board
        design_rect_mm = (75, 75, 50, 50)  # 50x50mm design centered at (75, 75)

        alignment_data = aligner.process(
            image_path,
            design_rect_mm=design_rect_mm,
            visualize=True
        )

        if alignment_data is not None:
            print("✓ PASS: Alignment workflow complete")
            print(f"  Design center: {alignment_data['center_px']}")
            print(f"  Rotation: {alignment_data['angle_deg']:.2f}°")
            return True
        else:
            print("✗ FAIL: No alignment data returned")
            return False

    except Exception as e:
        print(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_design_export():
    """
    Test design export functionality

    Returns:
        bool: True if test passes
    """
    print(f"\n{'='*60}")
    print("Test: Design Export")
    print(f"{'='*60}\n")

    from design_warp import DesignWarper

    try:
        # Create mock alignment data
        alignment_data = {
            'design_rect_mm': (50, 50, 100, 80),
            'center_px': [960, 540],
            'corners_px': [[910, 580], [1010, 580], [1010, 500], [910, 500]],
            'angle_deg': 0.0,
            'size_px': [100, 80],
            'image_size': [1920, 1080]
        }

        warper = DesignWarper(alignment_data, dpi=300)

        # Create simple text design
        warper.create_design_from_text("TEST", (100, 80))

        # Export
        output_path = Path('test_output/test_export.png')
        warper.export_for_lightburn(output_path, format='png')

        if output_path.exists():
            print("✓ PASS: Design exported successfully")
            return True
        else:
            print("✗ FAIL: Export file not created")
            return False

    except Exception as e:
        print(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run complete test suite"""
    print(f"\n{'='*60}")
    print("LightBurn Auto-Align - Test Suite")
    print(f"{'='*60}\n")

    # Create test image
    test_image_path = create_test_image_with_markers(
        'test_output/test_camera_image.jpg',
        image_size=(1920, 1080),
        board_size_mm=200,
        marker_size_mm=40
    )

    jig_config = 'config/jigs/default.json'

    # Run tests
    tests = [
        ("Marker Detection", lambda: test_marker_detection(test_image_path, jig_config)),
        ("Homography Calculation", lambda: test_homography_calculation(test_image_path, jig_config)),
        ("Alignment Workflow", lambda: test_alignment_workflow(test_image_path, jig_config)),
        ("Design Export", test_design_export),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")

    return passed == total


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Test alignment system')
    parser.add_argument('--create-test-image', action='store_true',
                       help='Create test image only')
    parser.add_argument('--output', default='test_output/test_camera_image.jpg',
                       help='Test image output path')

    args = parser.parse_args()

    if args.create_test_image:
        create_test_image_with_markers(args.output)
        print(f"\nTest image created: {args.output}")
        print("Use this image with: python aruco_align.py {args.output}")
        return 0

    # Run all tests
    success = run_all_tests()
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
