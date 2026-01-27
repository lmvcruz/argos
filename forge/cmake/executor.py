"""
CMakeExecutor class for executing CMake commands.

Handles process execution, output capture, and result object creation.
"""

from datetime import datetime
from pathlib import Path
import subprocess
from typing import List, Optional

from forge.models.results import BuildResult, ConfigureResult


class CMakeExecutor:
    """Executes CMake commands and captures output."""

    def execute_configure(
        self,
        command: List[str],
        working_dir: Optional[Path] = None,
        timeout: Optional[float] = None,
    ) -> ConfigureResult:
        """
        Execute CMake configure command.

        Args:
            command: Command to execute as list of strings
            working_dir: Working directory for command execution
            timeout: Timeout in seconds (None for no timeout)

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

            # Communicate with timeout
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
                exit_code = -1  # Indicate timeout with special code
                stderr_bytes += b"\nError: Command execution timed out\n"

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
    ) -> BuildResult:
        """
        Execute CMake build command.

        Args:
            command: Command to execute as list of strings
            working_dir: Working directory for command execution
            timeout: Timeout in seconds (None for no timeout)

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

            # Communicate with timeout
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
                exit_code = -1  # Indicate timeout with special code
                stderr_bytes += b"\nError: Command execution timed out\n"

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
