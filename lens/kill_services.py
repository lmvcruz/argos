"""
Kill all backend and frontend processes for Lens development services.

This script terminates:
- Python processes running uvicorn (backend server)
- Node.js processes running Vite dev server (frontend)
- Any processes using ports 8000, 3000, 5173, 3001
"""

import subprocess
import sys
import time
from typing import List, Set


def get_processes_by_name(process_names: List[str]) -> Set[int]:
    """
    Get PIDs of processes matching the given names.

    Args:
        process_names: List of process names to search for

    Returns:
        Set of process IDs found
    """
    pids = set()
    for name in process_names:
        try:
            # Use tasklist to find processes
            result = subprocess.run(
                ["tasklist", "/FI",
                    f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and name.lower() in line.lower():
                        # Parse CSV: "python.exe","12345","Console","1","123,456 K"
                        parts = line.split('","')
                        if len(parts) >= 2:
                            pid_str = parts[1].strip('"')
                            try:
                                pids.add(int(pid_str))
                            except ValueError:
                                pass
        except Exception as e:
            print(f"Error finding processes for {name}: {e}")
    return pids


def get_processes_by_port(ports: List[int]) -> Set[int]:
    """
    Get PIDs of processes using the specified ports.

    Args:
        ports: List of port numbers to check

    Returns:
        Set of process IDs found
    """
    pids = set()
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                for port in ports:
                    if f":{port}" in line and "LISTENING" in line:
                        # Extract PID from last column
                        parts = line.split()
                        if parts:
                            try:
                                pids.add(int(parts[-1]))
                            except (ValueError, IndexError):
                                pass
    except Exception as e:
        print(f"Error checking ports: {e}")
    return pids


def get_uvicorn_processes() -> Set[int]:
    """
    Get PIDs of Python processes running uvicorn.

    Returns:
        Set of process IDs running uvicorn
    """
    pids = set()
    try:
        # Use WMIC to get Python processes with command line
        result = subprocess.run(
            [
                "wmic",
                "process",
                "where",
                "name='python.exe'",
                "get",
                "ProcessId,CommandLine",
                "/format:csv",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "uvicorn" in line.lower():
                    # Parse CSV output
                    parts = line.split(",")
                    if len(parts) >= 2:
                        try:
                            pids.add(int(parts[-1].strip()))
                        except (ValueError, IndexError):
                            pass
    except Exception as e:
        print(f"Error finding uvicorn processes: {e}")
    return pids


def kill_processes(pids: Set[int], process_type: str) -> int:
    """
    Kill processes by PID.

    Args:
        pids: Set of process IDs to kill
        process_type: Description of process type for logging

    Returns:
        Number of processes killed
    """
    killed = 0
    for pid in pids:
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print(f"✓ Killed {process_type} process (PID {pid})")
                killed += 1
            else:
                # Process might already be terminated
                if "not found" not in result.stderr.lower():
                    print(
                        f"✗ Failed to kill PID {pid}: {result.stderr.strip()}")
        except Exception as e:
            print(f"✗ Error killing PID {pid}: {e}")
    return killed


def main():
    """Main execution function."""
    print("=" * 60)
    print("Lens Service Terminator")
    print("=" * 60)
    print()

    # Define what we're looking for
    process_names = ["python.exe", "node.exe"]
    ports = [8000, 3000, 3001, 5173]

    all_pids = set()

    # Find processes by name
    print("Searching for Python and Node.js processes...")
    name_pids = get_processes_by_name(process_names)
    if name_pids:
        print(f"  Found {len(name_pids)} process(es): {sorted(name_pids)}")
        all_pids.update(name_pids)
    else:
        print("  No Python or Node.js processes found")

    # Find processes by port
    print("\nSearching for processes on ports 8000, 3000, 3001, 5173...")
    port_pids = get_processes_by_port(ports)
    if port_pids:
        print(
            f"  Found {len(port_pids)} process(es) using ports: {sorted(port_pids)}")
        all_pids.update(port_pids)
    else:
        print("  No processes found on target ports")

    # Find uvicorn specifically
    print("\nSearching for uvicorn backend processes...")
    uvicorn_pids = get_uvicorn_processes()
    if uvicorn_pids:
        print(
            f"  Found {len(uvicorn_pids)} uvicorn process(es): {sorted(uvicorn_pids)}")
        all_pids.update(uvicorn_pids)
    else:
        print("  No uvicorn processes found")

    # Initialize remaining variables
    remaining_pids = set()
    remaining_ports = set()

    # Kill all found processes
    print("\n" + "=" * 60)
    if all_pids:
        print(f"Terminating {len(all_pids)} process(es)...")
        print()
        killed = kill_processes(all_pids, "service")
        print()
        print(
            f"✓ Successfully terminated {killed} out of {len(all_pids)} process(es)")

        # Wait a moment for processes to terminate
        print("\nWaiting for processes to terminate...")
        time.sleep(3)

        # Verify termination
        print("\nVerifying termination...")
        remaining_pids = get_processes_by_name(process_names)
        remaining_ports = get_processes_by_port(ports)

        if not remaining_pids and not remaining_ports:
            print("✓ All services terminated successfully")
        else:
            if remaining_pids:
                print(
                    f"⚠ Warning: {len(remaining_pids)} process(es) still running: {sorted(remaining_pids)}")
            if remaining_ports:
                print(
                    f"⚠ Warning: Ports still in use by {len(remaining_ports)} process(es): {sorted(remaining_ports)}")

            # Try one more time to kill remaining processes
            if remaining_pids or remaining_ports:
                print("\nAttempting second termination pass...")
                retry_pids = remaining_pids | remaining_ports
                killed_retry = kill_processes(retry_pids, "remaining")
                print(f"✓ Terminated {killed_retry} additional process(es)")

                # Final wait
                time.sleep(2)
    else:
        print("No processes found to terminate")
        print("Backend and frontend services are not running")

    print("=" * 60)
    return 0 if not (remaining_pids or remaining_ports) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        sys.exit(1)
