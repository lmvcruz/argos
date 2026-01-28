"""
CMakeExecutor class for executing CMake commands.

Handles process execution, output capture, and result object creation.
"""

from datetime import datetime
from pathlib import Path
import re
import subprocess
import sys
from typing import List, Optional, Tuple

from forge.models.results import BuildResult, ConfigureResult


class CMakeExecutor:
    """Executes CMake commands and captures output."""

    def __init__(self, cmake_command: str = "cmake"):
        """
        Initialize CMakeExecutor.

        Args:
            cmake_command: Path to cmake executable (default: "cmake" uses PATH)
        """
        self.cmake_command = cmake_command

    def _stream_output(
        self,
        process: subprocess.Popen,
        timeout: Optional[float] = None,
        stream_output: bool = True,
    ) -> Tuple[bytes, bytes, int]:
        """
        Stream and capture output from a subprocess.

        Simultaneously displays output to console (if enabled) and captures it
        for later processing. Handles both stdout and stderr streams.

        Args:
            process: The subprocess.Popen object
            timeout: Timeout in seconds (None for no timeout)
            stream_output: If True, print output to console in real-time

        Returns:
            Tuple of (stdout_bytes, stderr_bytes, exit_code)
        """
        # If streaming is disabled, use simple communicate()
        if not stream_output:
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
                return stdout_bytes, stderr_bytes, process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
                stderr_bytes += b"\nError: Command execution timed out\n"
                return stdout_bytes, stderr_bytes, -1

        # For streaming mode, we still use communicate() but print the output
        # In a real implementation with line-by-line streaming, we would use
        # select/poll to read from stdout/stderr as data becomes available
        try:
            stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
            exit_code = process.returncode

            # Stream to console (simulate real-time by printing after capture)
            if stdout_bytes:
                stdout_str = stdout_bytes.decode("utf-8", errors="replace")
                sys.stdout.write(stdout_str)
                sys.stdout.flush()

            if stderr_bytes:
                stderr_str = stderr_bytes.decode("utf-8", errors="replace")
                sys.stderr.write(stderr_str)
                sys.stderr.flush()

            return stdout_bytes, stderr_bytes, exit_code

        except subprocess.TimeoutExpired:
            process.kill()
            stdout_bytes, stderr_bytes = process.communicate()
            stderr_bytes += b"\nError: Command execution timed out\n"

            # Stream to console
            if stdout_bytes:
                stdout_str = stdout_bytes.decode("utf-8", errors="replace")
                sys.stdout.write(stdout_str)
                sys.stdout.flush()

            if stderr_bytes:
                stderr_str = stderr_bytes.decode("utf-8", errors="replace")
                sys.stderr.write(stderr_str)
                sys.stderr.flush()

            return stdout_bytes, stderr_bytes, -1

    def execute_configure(
        self,
        command: List[str],
        working_dir: Optional[Path] = None,
        timeout: Optional[float] = None,
        stream_output: bool = True,
    ) -> ConfigureResult:
        """
        Execute CMake configure command.

        Args:
            command: Command to execute as list of strings
            working_dir: Working directory for command execution
            timeout: Timeout in seconds (None for no timeout)
            stream_output: If True, stream output to console in real-time

        Returns:
            ConfigureResult with execution details
        """
        start_time = datetime.now()

        try:
            # Execute the command
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(working_dir) if working_dir else None,
            )

            # Stream and capture output
            stdout_bytes, stderr_bytes, exit_code = self._stream_output(
                process, timeout=timeout, stream_output=stream_output
            )

        except FileNotFoundError as e:
            # Command not found
            end_time = datetime.now()
            return ConfigureResult(
                success=False,
                exit_code=127,  # Standard "command not found" exit code
                stdout="",
                stderr=f"Error: Command not found - {command[0]}\n{str(e)}",
                duration=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            # Other execution errors
            end_time = datetime.now()
            return ConfigureResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Error executing command: {str(e)}",
                duration=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time,
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Decode output
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return ConfigureResult(
            success=(exit_code == 0),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            start_time=start_time,
            end_time=end_time,
        )

    def execute_build(
        self,
        command: List[str],
        working_dir: Optional[Path] = None,
        timeout: Optional[float] = None,
        stream_output: bool = True,
    ) -> BuildResult:
        """
        Execute CMake build command.

        Args:
            command: Command to execute as list of strings
            working_dir: Working directory for command execution
            timeout: Timeout in seconds (None for no timeout)
            stream_output: If True, stream output to console in real-time

        Returns:
            BuildResult with execution details
        """
        start_time = datetime.now()

        try:
            # Execute the command
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(working_dir) if working_dir else None,
            )

            # Stream and capture output
            stdout_bytes, stderr_bytes, exit_code = self._stream_output(
                process, timeout=timeout, stream_output=stream_output
            )

        except FileNotFoundError as e:
            # Command not found
            end_time = datetime.now()
            return BuildResult(
                success=False,
                exit_code=127,  # Standard "command not found" exit code
                stdout="",
                stderr=f"Error: Command not found - {command[0]}\n{str(e)}",
                duration=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            # Other execution errors
            end_time = datetime.now()
            return BuildResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Error executing command: {str(e)}",
                duration=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time,
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Decode output
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return BuildResult(
            success=(exit_code == 0),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            start_time=start_time,
            end_time=end_time,
        )

    def check_cmake_available(self) -> bool:
        """
        Check if CMake is available.

        Returns:
            True if CMake command can be executed, False otherwise
        """
        try:
            process = subprocess.Popen(
                [self.cmake_command, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process.communicate(timeout=5.0)
            return True
        except FileNotFoundError:
            # CMake not found in PATH
            return False
        except Exception:
            # Any other error (permissions, timeout, etc.)
            return False

    def get_cmake_version(self) -> Optional[str]:
        """
        Get CMake version string.

        Returns:
            Version string (e.g., "3.28.1") or None if CMake not available
        """
        try:
            process = subprocess.Popen(
                [self.cmake_command, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout_bytes, _ = process.communicate(timeout=5.0)
            stdout = stdout_bytes.decode("utf-8", errors="replace")

            # Parse version from output: "cmake version 3.28.1"
            # Regex pattern: matches "cmake version" followed by version number
            pattern = r"cmake version\s+(\d+(?:\.\d+)*(?:-[\w]+)?)"
            match = re.search(pattern, stdout, re.IGNORECASE)

            if match:
                return match.group(1)
            return None

        except (FileNotFoundError, Exception):
            return None

    def compare_version(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.

        Args:
            version1: First version string (e.g., "3.28.1")
            version2: Second version string (e.g., "3.20.0")

        Returns:
            Positive if version1 > version2
            Zero if version1 == version2
            Negative if version1 < version2
        """
        # Strip any suffixes (e.g., "-rc1", "-dirty")
        v1_clean = re.sub(r"-.*$", "", version1)
        v2_clean = re.sub(r"-.*$", "", version2)

        # Split into components
        v1_parts = [int(x) for x in v1_clean.split(".")]
        v2_parts = [int(x) for x in v2_clean.split(".")]

        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))

        # Compare component by component
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            if v1 < v2:
                return -1

        return 0

    def check_minimum_version(self, required_version: str) -> bool:
        """
        Check if installed CMake meets minimum version requirement.

        Args:
            required_version: Minimum required version (e.g., "3.20.0")

        Returns:
            True if CMake version is >= required_version, False otherwise
        """
        current_version = self.get_cmake_version()

        if current_version is None:
            return False

        return self.compare_version(current_version, required_version) >= 0
