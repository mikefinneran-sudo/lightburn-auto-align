#!/usr/bin/env python3
"""
LightBurn UDP Interface
Send commands to LightBurn via UDP protocol
"""

import socket
import time
from pathlib import Path


class LightBurnController:
    """
    Interface for controlling LightBurn via UDP commands
    """

    def __init__(self, host='127.0.0.1', port=19840, reply_port=19841, timeout=2.0):
        """
        Initialize LightBurn controller

        Args:
            host: LightBurn host (default: localhost)
            port: LightBurn command port (default: 19840, fixed)
            reply_port: LightBurn reply port (default: 19841)
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.reply_port = reply_port
        self.timeout = timeout

    def send_command(self, command):
        """
        Send a command to LightBurn

        Args:
            command: Command string to send

        Returns:
            Reply from LightBurn or None if timeout
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)

        try:
            # Send command
            sock.sendto(command.encode('utf-8'), (self.host, self.port))

            # Wait for reply
            try:
                reply, addr = sock.recvfrom(1024)
                return reply.decode('utf-8').strip()
            except socket.timeout:
                return None

        finally:
            sock.close()

    def ping(self):
        """
        Check if LightBurn is running

        Returns:
            bool: True if LightBurn responds
        """
        reply = self.send_command('PING')
        success = reply is not None and 'OK' in reply

        if success:
            print("✓ LightBurn is running")
        else:
            print("✗ LightBurn is not responding")

        return success

    def get_status(self):
        """
        Get current LightBurn status

        Returns:
            str: Status message or None
        """
        reply = self.send_command('STATUS')

        if reply:
            print(f"✓ Status: {reply}")
        else:
            print("✗ No status response")

        return reply

    def load_file(self, file_path, force=False):
        """
        Load a file into LightBurn

        Args:
            file_path: Path to file to load
            force: Force load (close current file if needed)

        Returns:
            bool: True if successful
        """
        file_path = Path(file_path).resolve()

        if not file_path.exists():
            print(f"✗ File not found: {file_path}")
            return False

        # Convert to URI format
        file_uri = f"file://{file_path}"

        # Choose command
        command = f"FORCELOAD:{file_uri}" if force else f"LOADFILE:{file_uri}"

        reply = self.send_command(command)
        success = reply is not None and 'OK' in reply

        if success:
            print(f"✓ Loaded file: {file_path.name}")
        else:
            print(f"✗ Failed to load file: {file_path.name}")
            if reply:
                print(f"  Response: {reply}")

        return success

    def start_job(self):
        """
        Start the current job

        Returns:
            bool: True if successful
        """
        reply = self.send_command('START')
        success = reply is not None and 'OK' in reply

        if success:
            print("✓ Job started")
        else:
            print("✗ Failed to start job")
            if reply:
                print(f"  Response: {reply}")

        return success

    def close_file(self, force=False):
        """
        Close the current file

        Args:
            force: Force close

        Returns:
            bool: True if successful
        """
        command = 'FORCECLOSE' if force else 'CLOSE'
        reply = self.send_command(command)
        success = reply is not None and 'OK' in reply

        if success:
            print("✓ File closed")
        else:
            print("✗ Failed to close file")

        return success

    def wait_for_ready(self, max_wait=10, poll_interval=0.5):
        """
        Wait for LightBurn to be ready

        Args:
            max_wait: Maximum seconds to wait
            poll_interval: Seconds between polls

        Returns:
            bool: True if ready
        """
        print(f"Waiting for LightBurn to be ready...")

        elapsed = 0
        while elapsed < max_wait:
            if self.ping():
                return True

            time.sleep(poll_interval)
            elapsed += poll_interval

        print(f"✗ LightBurn not ready after {max_wait}s")
        return False


def load_and_start(file_path, wait_for_ready=True, auto_start=False):
    """
    Convenience function to load a file and optionally start

    Args:
        file_path: Path to file
        wait_for_ready: Wait for LightBurn to be ready
        auto_start: Automatically start the job

    Returns:
        bool: True if successful
    """
    controller = LightBurnController()

    print(f"\n{'='*60}")
    print(f"LightBurn UDP Interface")
    print(f"{'='*60}\n")

    # Check if LightBurn is running
    if wait_for_ready and not controller.wait_for_ready():
        return False

    # Load file
    if not controller.load_file(file_path, force=True):
        return False

    # Start if requested
    if auto_start:
        print("\nStarting job...")
        time.sleep(0.5)  # Brief delay
        if not controller.start_job():
            return False

    print(f"\n{'='*60}")
    print(f"{'Success!' if not auto_start else 'Job Running'}")
    print(f"{'='*60}\n")

    return True


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='LightBurn UDP Control Interface')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Ping command
    ping_parser = subparsers.add_parser('ping', help='Check if LightBurn is running')

    # Status command
    status_parser = subparsers.add_parser('status', help='Get LightBurn status')

    # Load command
    load_parser = subparsers.add_parser('load', help='Load a file')
    load_parser.add_argument('file', help='File to load')
    load_parser.add_argument('--force', action='store_true', help='Force load (close current)')
    load_parser.add_argument('--start', action='store_true', help='Start job after loading')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start current job')

    # Close command
    close_parser = subparsers.add_parser('close', help='Close current file')
    close_parser.add_argument('--force', action='store_true', help='Force close')

    # Send raw command
    raw_parser = subparsers.add_parser('send', help='Send raw command')
    raw_parser.add_argument('raw_command', help='Raw command to send')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    controller = LightBurnController()

    try:
        if args.command == 'ping':
            success = controller.ping()
            return 0 if success else 1

        elif args.command == 'status':
            status = controller.get_status()
            return 0 if status else 1

        elif args.command == 'load':
            success = controller.load_file(args.file, force=args.force)
            if success and args.start:
                time.sleep(0.5)
                controller.start_job()
            return 0 if success else 1

        elif args.command == 'start':
            success = controller.start_job()
            return 0 if success else 1

        elif args.command == 'close':
            success = controller.close_file(force=args.force)
            return 0 if success else 1

        elif args.command == 'send':
            reply = controller.send_command(args.raw_command)
            if reply:
                print(f"Reply: {reply}")
                return 0
            else:
                print("No reply received")
                return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
