#!/usr/bin/env python3
"""
Camera Calibration Tool
Calibrate overhead camera for precise measurements in laser engraving alignment
"""

import cv2
import numpy as np
from pathlib import Path
import json
import glob


class CameraCalibrator:
    """
    Calibrates camera using chessboard pattern
    Outputs camera matrix and distortion coefficients
    """

    def __init__(self, chessboard_size=(9, 6), square_size_mm=25.0):
        """
        Initialize calibrator

        Args:
            chessboard_size: (columns, rows) of internal corners
            square_size_mm: Size of each square in millimeters
        """
        self.chessboard_size = chessboard_size
        self.square_size_mm = square_size_mm

        # Prepare object points (0,0,0), (25,0,0), (50,0,0), etc.
        self.objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
        self.objp *= square_size_mm

        # Storage for calibration data
        self.obj_points = []  # 3D points in real world
        self.img_points = []  # 2D points in image plane
        self.image_size = None

    def generate_chessboard_pdf(self, output_path):
        """Generate printable chessboard pattern"""
        from PIL import Image, ImageDraw

        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # A4 size at 300 DPI
        dpi = 300
        a4_width_mm = 210
        a4_height_mm = 297
        width_px = int(a4_width_mm * dpi / 25.4)
        height_px = int(a4_height_mm * dpi / 25.4)

        # Calculate chessboard size
        cols, rows = self.chessboard_size
        # Need one more square for outer edge
        board_cols = cols + 1
        board_rows = rows + 1

        square_size_px = int(self.square_size_mm * dpi / 25.4)
        board_width_px = board_cols * square_size_px
        board_height_px = board_rows * square_size_px

        # Create white canvas
        img = Image.new('L', (width_px, height_px), 255)
        draw = ImageDraw.Draw(img)

        # Center the chessboard
        offset_x = (width_px - board_width_px) // 2
        offset_y = (height_px - board_height_px) // 2

        # Draw chessboard
        for row in range(board_rows):
            for col in range(board_cols):
                if (row + col) % 2 == 1:  # Black squares
                    x1 = offset_x + col * square_size_px
                    y1 = offset_y + row * square_size_px
                    x2 = x1 + square_size_px
                    y2 = y1 + square_size_px
                    draw.rectangle([x1, y1, x2, y2], fill=0)

        # Add instructions
        from PIL import ImageFont
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        except:
            font = ImageFont.load_default()

        title = f"Camera Calibration Chessboard - {cols}x{rows} corners"
        instructions = [
            f"Square size: {self.square_size_mm}mm",
            "Print at 100% scale (no scaling!)",
            "Verify square size with ruler before use",
            "Take 15-20 photos from different angles and distances",
        ]

        y_pos = 50
        draw.text((100, y_pos), title, fill=0, font=font)
        y_pos += 50

        for instruction in instructions:
            draw.text((100, y_pos), instruction, fill=0, font=font)
            y_pos += 40

        # Save as PDF
        width_points = a4_width_mm / 25.4 * 72
        height_points = a4_height_mm / 25.4 * 72

        img.save(
            str(output_path),
            "PDF",
            resolution=dpi,
            page_size=(width_points, height_points)
        )

        print(f"✓ Chessboard pattern saved: {output_path}")

    def capture_images_from_camera(self, output_dir, num_images=20):
        """
        Interactive camera capture tool
        Press SPACE to capture, ESC to finish
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Could not open camera")

        print(f"\n{'='*60}")
        print("Camera Capture Mode")
        print(f"{'='*60}")
        print(f"Target: {num_images} images")
        print("Instructions:")
        print("  - Move chessboard to different positions/angles")
        print("  - Press SPACE to capture image")
        print("  - Press ESC when done")
        print(f"{'='*60}\n")

        captured = 0

        while captured < num_images:
            ret, frame = cap.read()
            if not ret:
                break

            # Try to detect chessboard in real-time
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret_corners, corners = cv2.findChessboardCorners(
                gray, self.chessboard_size, None
            )

            # Draw corners if found
            display_frame = frame.copy()
            if ret_corners:
                cv2.drawChessboardCorners(display_frame, self.chessboard_size, corners, ret_corners)
                status = "Chessboard detected - Press SPACE"
                color = (0, 255, 0)
            else:
                status = "Move chessboard into view"
                color = (0, 0, 255)

            # Add status text
            cv2.putText(display_frame, status, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(display_frame, f"Captured: {captured}/{num_images}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            cv2.imshow('Camera Calibration', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                print("\nCapture stopped by user")
                break
            elif key == 32 and ret_corners:  # SPACE
                filename = output_dir / f"calibration_{captured:02d}.jpg"
                cv2.imwrite(str(filename), frame)
                print(f"✓ Captured image {captured + 1}/{num_images}: {filename.name}")
                captured += 1

        cap.release()
        cv2.destroyAllWindows()

        print(f"\n✓ Captured {captured} calibration images")
        return captured

    def calibrate_from_images(self, image_paths):
        """
        Calibrate camera from chessboard images

        Args:
            image_paths: List of image file paths

        Returns:
            dict with calibration results
        """
        print(f"\n{'='*60}")
        print(f"Processing {len(image_paths)} calibration images")
        print(f"{'='*60}\n")

        successful = 0

        for img_path in image_paths:
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"⚠ Could not load: {img_path}")
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            if self.image_size is None:
                self.image_size = gray.shape[::-1]

            # Find chessboard corners
            ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

            if ret:
                # Refine corner positions
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

                self.obj_points.append(self.objp)
                self.img_points.append(corners_refined)
                successful += 1
                print(f"✓ {Path(img_path).name}: Corners detected")
            else:
                print(f"✗ {Path(img_path).name}: No corners found")

        if successful < 3:
            raise ValueError(f"Not enough valid images (found {successful}, need at least 3)")

        print(f"\n✓ Successfully processed {successful}/{len(image_paths)} images")
        print("\nRunning calibration...")

        # Calibrate camera
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            self.obj_points,
            self.img_points,
            self.image_size,
            None,
            None
        )

        # Calculate reprojection error
        mean_error = 0
        for i in range(len(self.obj_points)):
            img_points2, _ = cv2.projectPoints(
                self.obj_points[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs
            )
            error = cv2.norm(self.img_points[i], img_points2, cv2.NORM_L2) / len(img_points2)
            mean_error += error

        mean_error /= len(self.obj_points)

        result = {
            'camera_matrix': camera_matrix.tolist(),
            'distortion_coefficients': dist_coeffs.tolist(),
            'image_size': self.image_size,
            'reprojection_error': float(mean_error),
            'num_images': successful,
            'chessboard_size': self.chessboard_size,
            'square_size_mm': self.square_size_mm
        }

        print(f"\n{'='*60}")
        print("Calibration Complete")
        print(f"{'='*60}")
        print(f"Reprojection error: {mean_error:.3f} pixels")
        print(f"Image size: {self.image_size[0]}x{self.image_size[1]}")
        print(f"Focal length: {camera_matrix[0, 0]:.1f}px")
        print(f"{'='*60}\n")

        return result

    def save_calibration(self, calibration_data, output_path):
        """Save calibration data to YAML format"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # OpenCV FileStorage format for compatibility
        fs = cv2.FileStorage(str(output_path), cv2.FILE_STORAGE_WRITE)
        fs.write('camera_matrix', np.array(calibration_data['camera_matrix']))
        fs.write('distortion_coefficients', np.array(calibration_data['distortion_coefficients']))
        fs.write('image_width', calibration_data['image_size'][0])
        fs.write('image_height', calibration_data['image_size'][1])
        fs.write('reprojection_error', calibration_data['reprojection_error'])
        fs.write('num_images', calibration_data['num_images'])
        fs.release()

        # Also save as JSON for easy reading
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(calibration_data, f, indent=2)

        print(f"✓ Calibration saved: {output_path}")
        print(f"✓ JSON copy saved: {json_path}")

    def test_undistortion(self, test_image_path, calibration_data, output_path):
        """Test calibration by undistorting an image"""
        img = cv2.imread(str(test_image_path))
        if img is None:
            print(f"⚠ Could not load test image: {test_image_path}")
            return

        camera_matrix = np.array(calibration_data['camera_matrix'])
        dist_coeffs = np.array(calibration_data['distortion_coefficients'])

        h, w = img.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            camera_matrix, dist_coeffs, (w, h), 1, (w, h)
        )

        # Undistort
        undistorted = cv2.undistort(img, camera_matrix, dist_coeffs, None, new_camera_matrix)

        # Crop if needed
        x, y, w, h = roi
        if w > 0 and h > 0:
            undistorted = undistorted[y:y+h, x:x+w]

        # Create side-by-side comparison
        comparison = np.hstack([
            cv2.resize(img, (640, 480)),
            cv2.resize(undistorted, (640, 480))
        ])

        cv2.imwrite(str(output_path), comparison)
        print(f"✓ Undistortion test saved: {output_path}")


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Camera Calibration Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Generate chessboard
    gen_parser = subparsers.add_parser('generate', help='Generate chessboard pattern')
    gen_parser.add_argument('--output', default='calibration_chessboard.pdf',
                           help='Output PDF file')

    # Capture images
    cap_parser = subparsers.add_parser('capture', help='Capture calibration images from camera')
    cap_parser.add_argument('--output-dir', default='calibration_images',
                           help='Output directory for images')
    cap_parser.add_argument('--num-images', type=int, default=20,
                           help='Target number of images')

    # Calibrate
    cal_parser = subparsers.add_parser('calibrate', help='Calibrate from images')
    cal_parser.add_argument('images', help='Directory with calibration images or pattern')
    cal_parser.add_argument('--output', default='config/camera.yml',
                           help='Output calibration file')

    args = parser.parse_args()

    calibrator = CameraCalibrator()

    if args.command == 'generate':
        calibrator.generate_chessboard_pdf(args.output)
        print(f"\nNext steps:")
        print(f"1. Print {args.output} at 100% scale")
        print(f"2. Verify square size with ruler")
        print(f"3. Run: python calibrate.py capture")

    elif args.command == 'capture':
        num_captured = calibrator.capture_images_from_camera(args.output_dir, args.num_images)
        if num_captured > 0:
            print(f"\nNext step:")
            print(f"python calibrate.py calibrate {args.output_dir}/*.jpg")

    elif args.command == 'calibrate':
        # Find images
        if '*' in args.images or '?' in args.images:
            image_paths = sorted(glob.glob(args.images))
        else:
            image_dir = Path(args.images)
            if image_dir.is_dir():
                image_paths = sorted(image_dir.glob('*.jpg')) + sorted(image_dir.glob('*.png'))
            else:
                image_paths = [args.images]

        if not image_paths:
            print("Error: No images found")
            return 1

        # Calibrate
        calibration_data = calibrator.calibrate_from_images(image_paths)

        # Save calibration
        calibrator.save_calibration(calibration_data, args.output)

        # Test undistortion on first image
        test_output = Path(args.output).parent / 'undistortion_test.jpg'
        calibrator.test_undistortion(image_paths[0], calibration_data, test_output)

        print(f"\nCalibration complete! Use this file with the alignment tool.")

    else:
        parser.print_help()

    return 0


if __name__ == '__main__':
    exit(main())
