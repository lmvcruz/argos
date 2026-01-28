"""
Test build target extraction from various build system outputs.

Tests extraction of built targets from Ninja, Make, and MSVC output formats,
including target types, build order, and completion tracking.
"""

from forge.inspector.build_inspector import BuildInspector


class TestNinjaTargetExtraction:
    """Test target extraction from Ninja build output."""

    def test_extract_simple_ninja_target(self):
        """Test extraction of simple target from Ninja."""
        output = "[1/10] Building CXX object main.cpp.o\n[10/10] Linking CXX executable myapp"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "myapp"
        assert targets[0].target_type == "executable"

    def test_extract_ninja_library_target(self):
        """Test extraction of library target from Ninja."""
        output = "[5/10] Linking CXX static library libmylib.a"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "libmylib.a"
        assert targets[0].target_type == "static_library"

    def test_extract_ninja_shared_library(self):
        """Test extraction of shared library from Ninja."""
        output = "[8/10] Linking CXX shared library libshared.so"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "libshared.so"
        assert targets[0].target_type == "shared_library"

    def test_extract_multiple_ninja_targets(self):
        """Test extraction of multiple targets from Ninja."""
        output = """[1/20] Building CXX object main.cpp.o
[5/20] Linking CXX static library libutils.a
[10/20] Building CXX object app.cpp.o
[20/20] Linking CXX executable myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 2
        assert targets[0].name == "libutils.a"
        assert targets[1].name == "myapp"

    def test_extract_ninja_with_completion_percentage(self):
        """Test extraction includes completion percentage."""
        output = "[10/20] Linking CXX executable myapp"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        # Target completion: 10 steps done out of 20 total = 50%
        assert targets[0].completion_step == 10
        assert targets[0].total_steps == 20


class TestMakeTargetExtraction:
    """Test target extraction from Make build output."""

    def test_extract_simple_make_target(self):
        """Test extraction of simple target from Make."""
        output = """[ 50%] Building CXX object CMakeFiles/myapp.dir/main.cpp.o
[100%] Linking CXX executable myapp
[100%] Built target myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "myapp"
        assert targets[0].target_type == "executable"

    def test_extract_make_library_target(self):
        """Test extraction of library target from Make."""
        output = """[ 80%] Linking CXX static library libmylib.a
[100%] Built target mylib"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert "mylib" in targets[0].name

    def test_extract_make_shared_library(self):
        """Test extraction of shared library from Make."""
        output = """[ 90%] Linking CXX shared library libshared.so
[100%] Built target shared"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].target_type == "shared_library"

    def test_extract_multiple_make_targets(self):
        """Test extraction of multiple targets from Make."""
        output = """[ 33%] Built target utils
[ 66%] Built target core
[100%] Built target myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 3
        assert targets[0].name == "utils"
        assert targets[1].name == "core"
        assert targets[2].name == "myapp"


class TestMSVCTargetExtraction:
    """Test target extraction from MSVC build output."""

    def test_extract_simple_msvc_target(self):
        """Test extraction of simple target from MSVC."""
        output = """Building Custom Rule C:/project/CMakeLists.txt
  main.cpp
  myapp.vcxproj -> C:\\build\\Debug\\myapp.exe"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "myapp.exe"
        assert targets[0].target_type == "executable"

    def test_extract_msvc_library_target(self):
        """Test extraction of library target from MSVC."""
        output = """  mylib.vcxproj -> C:\\build\\Debug\\mylib.lib"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "mylib.lib"
        assert targets[0].target_type == "static_library"

    def test_extract_msvc_dll_target(self):
        """Test extraction of DLL target from MSVC."""
        output = """  shared.vcxproj -> C:\\build\\Debug\\shared.dll"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "shared.dll"
        assert targets[0].target_type == "shared_library"

    def test_extract_multiple_msvc_targets(self):
        """Test extraction of multiple targets from MSVC."""
        output = """  utils.vcxproj -> C:\\build\\Debug\\utils.lib
  core.vcxproj -> C:\\build\\Debug\\core.lib
  myapp.vcxproj -> C:\\build\\Debug\\myapp.exe"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 3
        assert targets[2].name == "myapp.exe"


class TestTargetTypeDetection:
    """Test detection of different target types."""

    def test_detect_executable_from_extension(self):
        """Test executable detection from file extension."""
        output = "[10/10] Linking CXX executable myapp"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets[0].target_type == "executable"

    def test_detect_executable_exe_extension(self):
        """Test executable detection for .exe files."""
        output = "myapp.vcxproj -> C:\\build\\myapp.exe"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets[0].target_type == "executable"

    def test_detect_static_library_from_extension(self):
        """Test static library detection from .a extension."""
        output = "[5/10] Linking CXX static library libmylib.a"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets[0].target_type == "static_library"

    def test_detect_static_library_lib_extension(self):
        """Test static library detection from .lib extension."""
        output = "mylib.vcxproj -> C:\\build\\mylib.lib"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets[0].target_type == "static_library"

    def test_detect_shared_library_so_extension(self):
        """Test shared library detection from .so extension."""
        output = "[8/10] Linking CXX shared library libshared.so"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets[0].target_type == "shared_library"

    def test_detect_shared_library_dll_extension(self):
        """Test shared library detection from .dll extension."""
        output = "shared.vcxproj -> C:\\build\\shared.dll"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets[0].target_type == "shared_library"

    def test_detect_shared_library_dylib_extension(self):
        """Test shared library detection from .dylib extension."""
        output = "[8/10] Linking CXX shared library libshared.dylib"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets[0].target_type == "shared_library"


class TestBuildProgressTracking:
    """Test build progress and completion tracking."""

    def test_extract_ninja_progress_steps(self):
        """Test extraction of Ninja progress steps."""
        output = """[1/100] Building CXX object file1.o
[50/100] Building CXX object file50.o
[100/100] Linking CXX executable myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Should extract the final linking target with progress
        assert len(targets) == 1
        assert targets[0].completion_step == 100
        assert targets[0].total_steps == 100

    def test_extract_make_percentage_progress(self):
        """Test extraction of Make percentage progress."""
        output = """[ 25%] Building CXX object file.o
[ 50%] Linking CXX static library libutils.a
[100%] Built target utils"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Make progress is shown as percentage, not absolute steps
        assert len(targets) == 1

    def test_track_compilation_count(self):
        """Test tracking number of compiled files."""
        output = """[1/10] Building CXX object file1.cpp.o
[2/10] Building CXX object file2.cpp.o
[3/10] Building CXX object file3.cpp.o
[10/10] Linking CXX executable myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Should detect 3 compilation steps before linking
        assert targets[0].total_steps == 10


class TestBuildOrderDetection:
    """Test detection of target build order."""

    def test_detect_build_order_from_sequence(self):
        """Test that targets maintain build order."""
        output = """[5/20] Linking CXX static library libutils.a
[10/20] Linking CXX static library libcore.a
[20/20] Linking CXX executable myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Targets should be in the order they were built
        assert len(targets) == 3
        assert targets[0].name == "libutils.a"
        assert targets[1].name == "libcore.a"
        assert targets[2].name == "myapp"

    def test_detect_dependency_order(self):
        """Test detection of library dependencies built before executables."""
        output = """[100%] Built target utils
[100%] Built target core
[100%] Built target myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Should maintain order: libraries first, then executable
        assert len(targets) == 3


class TestParallelBuildOutput:
    """Test handling of interleaved parallel build output."""

    def test_extract_from_parallel_ninja_output(self):
        """Test extraction with interleaved Ninja output."""
        output = """[1/10] Building CXX object file1.cpp.o
[2/10] Building CXX object file2.cpp.o
[3/10] Building CXX object file3.cpp.o
[4/10] Linking CXX static library libutils.a
[5/10] Building CXX object main.cpp.o
[10/10] Linking CXX executable myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Should extract both targets despite parallel compilation
        assert len(targets) == 2
        assert targets[0].name == "libutils.a"
        assert targets[1].name == "myapp"

    def test_handle_interleaved_make_output(self):
        """Test handling of interleaved Make output from parallel jobs."""
        output = """[ 10%] Building CXX object file1.o
[ 20%] Building CXX object file2.o
[ 30%] Linking CXX static library libutils.a
[ 40%] Built target utils
[ 60%] Building CXX object main.o
[100%] Linking CXX executable myapp
[100%] Built target myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 2

    def test_handle_scrambled_ninja_output(self):
        """Test handling of out-of-order Ninja output from parallel build with -j flag."""
        output = """[2/15] Building CXX object file2.cpp.o
[1/15] Building CXX object file1.cpp.o
[4/15] Building CXX object file4.cpp.o
[3/15] Building CXX object file3.cpp.o
[6/15] Linking CXX static library libcore.a
[5/15] Building CXX object file5.cpp.o
[8/15] Linking CXX static library libutils.a
[7/15] Building CXX object file6.cpp.o
[10/15] Building CXX object main.cpp.o
[9/15] Building CXX object helper.cpp.o
[15/15] Linking CXX executable myapp"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Should extract all targets despite scrambled output
        assert len(targets) == 3
        # Order reflects appearance in output, not step numbers
        assert targets[0].name == "libcore.a"
        assert targets[0].completion_step == 6
        assert targets[1].name == "libutils.a"
        assert targets[1].completion_step == 8
        assert targets[2].name == "myapp"
        assert targets[2].completion_step == 15


class TestEmptyAndInvalidOutput:
    """Test handling of empty or invalid build output."""

    def test_extract_from_empty_output(self):
        """Test extraction from empty output."""
        inspector = BuildInspector()
        targets = inspector.extract_targets("")

        assert targets == []

    def test_extract_from_output_without_targets(self):
        """Test extraction from output with no linking steps."""
        output = """Building CXX object file.cpp.o
Compiling sources
Running tests"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert targets == []

    def test_extract_from_clean_output(self):
        """Test extraction from clean build output."""
        output = """Built target clean
Cleaning build directory"""

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        # Should not include "clean" as a real target
        assert len(targets) == 0


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_target_with_spaces_in_path(self):
        """Test extraction of target with spaces in path."""
        output = 'myapp.vcxproj -> "C:\\Program Files\\build\\myapp.exe"'

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "myapp.exe"

    def test_target_with_special_characters(self):
        """Test extraction of target with special characters in name."""
        output = "[10/10] Linking CXX executable my-app_v2.0"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].name == "my-app_v2.0"

    def test_very_long_build_output(self):
        """Test extraction from very long output."""
        # Simulate output with many compilation steps
        output = "\n".join([f"[{i}/1000] Building CXX object file{i}.o" for i in range(1, 1001)])
        output += "\n[1000/1000] Linking CXX executable myapp"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert targets[0].total_steps == 1000

    def test_target_with_unicode_characters(self):
        """Test extraction of target with unicode in path."""
        output = "[10/10] Linking CXX executable café_app"

        inspector = BuildInspector()
        targets = inspector.extract_targets(output)

        assert len(targets) == 1
        assert "café" in targets[0].name
