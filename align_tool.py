#!/usr/bin/env python3
"""
LightBurn Auto-Align Tool
Complete workflow for camera-based laser engraving alignment
"""

import sys
import cv2
import json
from pathlib import Path
import argparse

# Import local modules
from aruco_align import ArucoAligner
from design_warp import DesignWarper
from lightburn_udp import LightBurnController


class AlignmentWorkflow:
    """
    Complete alignment workflow from camera to LightBurn
    """

    def __init__(self, jig_config='config/jigs/default.json',
                 camera_config='config/camera.yml',
                 output_dir='output',
                 dpi=300):
        """
        Initialize workflow

        Args:
            jig_config: Path to jig configuration
            camera_config: Path to camera calibration
            output_dir: Output directory for exports
            dpi: Export DPI
        """
        self.jig_config = Path(jig_config)
        self.camera_config = Path(camera_config) if Path(camera_config).exists() else None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi

        # Workflow state
        self.camera_image_path = None
        self.alignment_data = None
        self.export_path = None

    def capture_camera_image(self, output_name='camera_snapshot.jpg'):
        """
        Capture image from camera

        Returns:
            Path to captured image
        """
        print(f"\n{'='*60}")
        print("Camera Capture")
        print(f"{'='*60}\n")
        print("Press SPACE to capture, ESC to cancel")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Could not open camera")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Show preview
            cv2.imshow('Camera Preview', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                print("Capture cancelled")
                cap.release()
                cv2.destroyAllWindows()
                return None

            elif key == 32:  # SPACE
                output_path = self.output_dir / output_name
                cv2.imwrite(str(output_path), frame)
                print(f"✓ Captured: {output_path}")
                cap.release()
                cv2.destroyAllWindows()
                return output_path

        cap.release()
        cv2.destroyAllWindows()
        return None

    def detect_alignment(self, camera_image_path, design_rect_mm=None):
        """
        Detect ArUco markers and calculate alignment

        Args:
            camera_image_path: Path to camera snapshot
            design_rect_mm: Optional (x, y, width, height) in mm

        Returns:
            Alignment data dict
        """
        print(f"\n{'='*60}")
        print("ArUco Detection & Alignment")
        print(f"{'='*60}\n")

        aligner = ArucoAligner(self.jig_config, self.camera_config)
        alignment_data = aligner.process(
            camera_image_path,
            design_rect_mm=design_rect_mm,
            visualize=True
        )

        # Save alignment data
        alignment_json = self.output_dir / 'alignment_data.json'
        with open(alignment_json, 'w') as f:
            json.dump(alignment_data, f, indent=2)

        print(f"✓ Alignment data saved: {alignment_json}")

        return alignment_data

    def warp_and_export(self, alignment_data, design_path=None, text=None,
                       format='png', output_name=None):
        """
        Warp design and export for LightBurn

        Args:
            alignment_data: Alignment data from detection
            design_path: Path to design image (or None for text)
            text: Text to render (if design_path is None)
            format: 'png' or 'svg'
            output_name: Custom output filename

        Returns:
            Path to exported file
        """
        print(f"\n{'='*60}")
        print("Design Export")
        print(f"{'='*60}\n")

        warper = DesignWarper(alignment_data, dpi=self.dpi)

        # Load or create design
        if text:
            design_rect = alignment_data['design_rect_mm']
            size_mm = (design_rect[2], design_rect[3])
            warper.create_design_from_text(text, size_mm)
        elif design_path:
            warper.load_design(design_path)
        else:
            raise ValueError("Must provide either design_path or text")

        # Generate output filename
        if output_name is None:
            output_name = f'aligned_design.{format}'

        export_path = self.output_dir / output_name

        # Export
        warper.export_for_lightburn(export_path, format=format)

        # Create preview
        if self.camera_image_path and Path(self.camera_image_path).exists():
            camera_img = cv2.imread(str(self.camera_image_path))
            if camera_img is not None:
                preview = warper.warp_to_alignment(camera_img)
                preview_path = self.output_dir / 'preview.jpg'
                cv2.imwrite(str(preview_path), preview)
                print(f"✓ Preview saved: {preview_path}")

        return export_path

    def send_to_lightburn(self, file_path, auto_start=False):
        """
        Send file to LightBurn via UDP

        Args:
            file_path: Path to file to load
            auto_start: Automatically start the job

        Returns:
            bool: True if successful
        """
        print(f"\n{'='*60}")
        print("LightBurn Integration")
        print(f"{'='*60}\n")

        controller = LightBurnController()

        # Check if LightBurn is running
        if not controller.ping():
            print("\n⚠ LightBurn is not running or UDP is disabled")
            print("  Enable UDP in LightBurn: Edit → Device Settings → Enable UDP")
            return False

        # Load file
        if not controller.load_file(file_path, force=True):
            return False

        # Start if requested
        if auto_start:
            print("\nStarting job...")
            import time
            time.sleep(0.5)
            controller.start_job()

        return True

    def run_complete_workflow(self, design_rect_mm, design_path=None, text=None,
                             use_camera=True, camera_image_path=None,
                             send_to_lb=False, auto_start=False, format='png'):
        """
        Run the complete workflow from start to finish

        Args:
            design_rect_mm: (x, y, width, height) in mm
            design_path: Path to design image
            text: Text to render
            use_camera: Capture new image from camera
            camera_image_path: Use existing camera image
            send_to_lb: Send to LightBurn
            auto_start: Auto-start job in LightBurn
            format: Export format

        Returns:
            Path to exported file
        """
        print(f"\n{'='*60}")
        print("LightBurn Auto-Align - Complete Workflow")
        print(f"{'='*60}\n")

        # Step 1: Get camera image
        if use_camera:
            self.camera_image_path = self.capture_camera_image()
            if self.camera_image_path is None:
                print("Workflow cancelled")
                return None
        elif camera_image_path:
            self.camera_image_path = Path(camera_image_path)
        else:
            raise ValueError("Must provide camera image or enable camera capture")

        # Step 2: Detect markers and calculate alignment
        self.alignment_data = self.detect_alignment(
            self.camera_image_path,
            design_rect_mm=design_rect_mm
        )

        if self.alignment_data is None:
            print("Alignment failed")
            return None

        # Step 3: Warp and export design
        self.export_path = self.warp_and_export(
            self.alignment_data,
            design_path=design_path,
            text=text,
            format=format
        )

        # Step 4: Send to LightBurn (optional)
        if send_to_lb:
            success = self.send_to_lightburn(self.export_path, auto_start=auto_start)
            if not success:
                print("\n⚠ Failed to send to LightBurn, but file is exported")

        print(f"\n{'='*60}")
        print("Workflow Complete!")
        print(f"{'='*60}")
        print(f"\nExported file: {self.export_path}")
        print(f"Design position: ({design_rect_mm[0]:.1f}, {design_rect_mm[1]:.1f})mm")
        print(f"Design size: {design_rect_mm[2]:.1f}x{design_rect_mm[3]:.1f}mm")
        print(f"\n{'='*60}\n")

        return self.export_path


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description='LightBurn Auto-Align - Camera-based laser engraving alignment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete workflow with camera capture
  %(prog)s --design mylogo.png --rect 50 50 100 80 --send

  # Use existing camera image
  %(prog)s --camera-image snapshot.jpg --text "TEST" --rect 60 60 80 40

  # Export only, no LightBurn integration
  %(prog)s --camera-image test.jpg --text "Hello" --rect 50 50 120 30 --format svg

Design placement:
  --rect X Y WIDTH HEIGHT (all in millimeters)
  - X, Y: Position from bottom-left corner (0,0)
  - WIDTH, HEIGHT: Design dimensions
        """
    )

    # Input options
    input_group = parser.add_argument_group('Input')
    input_group.add_argument('--camera', action='store_true',
                            help='Capture from camera (default if no --camera-image)')
    input_group.add_argument('--camera-image', type=str,
                            help='Use existing camera snapshot')

    # Design options
    design_group = parser.add_argument_group('Design')
    design_group.add_argument('--design', type=str,
                             help='Design image file (PNG)')
    design_group.add_argument('--text', type=str,
                             help='Text to engrave (alternative to --design)')
    design_group.add_argument('--rect', nargs=4, type=float, required=True,
                             metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                             help='Design rectangle in mm (x y width height)')

    # Export options
    export_group = parser.add_argument_group('Export')
    export_group.add_argument('--format', choices=['png', 'svg'], default='png',
                             help='Export format (default: png)')
    export_group.add_argument('--dpi', type=int, default=300,
                             help='Export DPI (default: 300)')
    export_group.add_argument('--output-dir', default='output',
                             help='Output directory (default: output/)')

    # Configuration
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument('--jig-config', default='config/jigs/default.json',
                             help='Jig configuration file')
    config_group.add_argument('--camera-calib', default='config/camera.yml',
                             help='Camera calibration file')

    # LightBurn integration
    lb_group = parser.add_argument_group('LightBurn')
    lb_group.add_argument('--send', action='store_true',
                         help='Send to LightBurn after export')
    lb_group.add_argument('--start', action='store_true',
                         help='Auto-start job in LightBurn (requires --send)')

    args = parser.parse_args()

    # Validate arguments
    if not args.design and not args.text:
        parser.error("Must specify either --design or --text")

    if args.start and not args.send:
        parser.error("--start requires --send")

    # Determine if using camera
    use_camera = args.camera or (args.camera_image is None)

    try:
        # Create workflow
        workflow = AlignmentWorkflow(
            jig_config=args.jig_config,
            camera_config=args.camera_calib,
            output_dir=args.output_dir,
            dpi=args.dpi
        )

        # Run workflow
        export_path = workflow.run_complete_workflow(
            design_rect_mm=tuple(args.rect),
            design_path=args.design,
            text=args.text,
            use_camera=use_camera,
            camera_image_path=args.camera_image,
            send_to_lb=args.send,
            auto_start=args.start,
            format=args.format
        )

        return 0 if export_path else 1

    except KeyboardInterrupt:
        print("\n\nWorkflow cancelled by user")
        return 1

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
