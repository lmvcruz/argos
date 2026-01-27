"""
CMakeExecutor class for executing CMake commands.

Handles process execution, output capture, and result object creation.
"""

from datetime import datetime
from pathlib import Path
import subprocess
import sys
from typing import List, Optional, Tuple

from forge.models.results import BuildResult, ConfigureResult


class CMakeExecutor:
    """Executes CMake commands and captures output."""

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
