# Iterative Planning Template: Forge Implementation with TDD

This plan follows Test-Driven Development (TDD) principles, where tests are written before implementation code. Each step includes specific test requirements to ensure verifiable progress.

---

## Guiding Principles

1. **Test-First Development**: Write tests before implementation for all functionality
2. **Small Iterations**: Each iteration should take 1-2 weeks and have a single, clear goal
3. **Verifiable Steps**: Every step has clear, objective test criteria
4. **Build on Success**: Each iteration builds upon validated success of the previous one
5. **Red-Green-Refactor**: Follow TDD cycle (failing test → passing test → refactor)

---

# Project Plan: Forge - CMake Build Wrapper

## Iteration 1: Foundation & Data Models

**Goal:** Establish project structure, data models, and database schema with comprehensive test coverage. Create the foundation for all other components.

### Steps

#### Step 1.1: Project Structure Setup
- **Description:** Create the complete directory structure for Forge with all necessary folders and initial files (see forge-architecture.md). Set up pytest configuration, create requirements.txt with testing dependencies (pytest, pytest-cov, pytest-mock).

- **Testing Approach:**
  - **Test Type:** Integration test
  - **Test Description:** Verify that the project structure exists and can be imported
  - **Test File:** `tests/test_project_structure.py`
  - **Test Cases:**
    - Test that all required directories exist (cli, cmake, inspector, storage, models, utils)
    - Test that all `__init__.py` files are present and can be imported
    - Test that pytest can discover the tests directory
  - **Success Criteria:** All imports work, pytest discovers test directory, no ImportError

#### Step 1.2: Data Models Implementation
- **Description:** Implement all dataclasses in `models/` directory: ForgeArguments, ConfigureResult, BuildResult, ConfigureMetadata, BuildMetadata, Warning, Error.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test data model instantiation, validation, and serialization
  - **Test File:** `tests/test_models.py`
  - **Test Cases:**
    - Test ForgeArguments creation with valid data
    - Test ForgeArguments with missing required fields (should fail)
    - Test ForgeArguments with invalid types (should fail)
    - Test ConfigureResult and BuildResult with all fields
    - Test metadata models with optional fields
    - Test Warning and Error models with partial data
    - Test JSON serialization/deserialization (for database storage)
    - Test Path handling in ForgeArguments
  - **Success Criteria:** 100% test coverage on models, all tests pass, models can be serialized to/from JSON

#### Step 1.3: Database Schema Implementation
- **Description:** Create SQLite database schema with all tables (configurations, builds, warnings, errors, build_targets). Implement schema creation and migration logic.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test database schema creation and structure validation
  - **Test File:** `tests/test_database_schema.py`
  - **Test Cases:**
    - Test database creation in temporary location
    - Test that all tables are created with correct columns
    - Test that all indexes are created
    - Test foreign key constraints are enforced
    - Test default values are set correctly
    - Test schema version tracking (for future migrations)
    - Test database creation is idempotent (can run multiple times)
  - **Success Criteria:** Schema creates successfully, all constraints work, foreign keys are enforced, 100% test coverage

### Success Criteria

- **Criterion 1.1:** Project structure is complete, all imports work, pytest can run tests
- **Criterion 1.2:** All data models are implemented and pass unit tests with 100% coverage
- **Criterion 1.3:** Database schema is created successfully and passes all structure validation tests
- **Overall:** Foundation is complete with all data structures tested and ready for use. Test coverage ≥95%.

---

## Iteration 2: Argument Parsing & Validation

**Goal:** Implement robust command-line argument parsing with comprehensive validation, following TDD principles.

### Steps

#### Step 2.1: ArgumentParser Basic Implementation
- **Description:** Implement ArgumentParser class to handle all command-line arguments defined in the architecture (--source-dir, --build-dir, --cmake-args, --build-args, etc.).

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test argument parsing with various input combinations
  - **Test File:** `tests/test_argument_parser.py`
  - **Test Cases:**
    - Test parsing with only required argument (--build-dir)
    - Test parsing with source-dir and build-dir
    - Test parsing with all optional arguments
    - Test parsing --cmake-args with multiple values
    - Test parsing --build-args with multiple values
    - Test parsing with --verbose flag
    - Test parsing with --project-name override
    - Test help message generation (--help)
    - Test version output (--version)
    - Test argument parsing with sys.argv simulation
  - **Success Criteria:** All valid argument combinations are parsed correctly, returns ForgeArguments object, 100% coverage

#### Step 2.2: Argument Validation Logic
- **Description:** Implement validate_arguments() method to ensure logical consistency (e.g., build-dir must exist if source-dir not provided, paths are valid, mutually exclusive options).

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test validation logic with valid and invalid argument combinations
  - **Test File:** `tests/test_argument_validation.py`
  - **Test Cases:**
    - Test validation passes with valid arguments
    - Test error when build-dir doesn't exist and source-dir not provided
    - Test error when source-dir doesn't exist
    - Test error when source-dir doesn't contain CMakeLists.txt
    - Test warning when build-dir already exists
    - Test error with invalid database path
    - Test error with invalid server URL format
    - Test validation of mutually exclusive options
    - Test path normalization (relative to absolute)
  - **Success Criteria:** All validation cases pass, appropriate exceptions raised with clear messages, 100% coverage

#### Step 2.3: Error Handling & User Feedback
- **Description:** Implement custom ArgumentError exception class and user-friendly error messages.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test error messages and exception handling
  - **Test File:** `tests/test_argument_errors.py`
  - **Test Cases:**
    - Test ArgumentError is raised with descriptive message
    - Test error messages include suggestions for fixes
    - Test error messages reference help command
    - Test multiple validation errors are collected and reported together
    - Test colored output (if verbose) vs plain output
  - **Success Criteria:** All error paths tested, messages are helpful, exceptions include context

### Success Criteria

- **Criterion 2.1:** ArgumentParser parses all valid argument combinations correctly, 100% test coverage
- **Criterion 2.2:** Validation logic catches all invalid inputs with clear error messages, 100% coverage
- **Criterion 2.3:** Error handling provides helpful feedback to users, all edge cases tested
- **Overall:** Command-line interface is fully functional and robust. Can parse and validate arguments from command line. Test coverage ≥98%.

---

## Iteration 3: CMake Parameter Management

**Goal:** Implement CMake command building with proper parameter handling and environment setup.

### Steps

#### Step 3.1: CMakeParameterManager Basic Implementation
- **Description:** Implement CMakeParameterManager class that takes ForgeArguments and builds CMake command strings.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test CMake command generation with various parameter combinations
  - **Test File:** `tests/test_parameter_manager.py`
  - **Test Cases:**
    - Test get_configure_command() with minimal arguments
    - Test get_configure_command() with cmake-args
    - Test get_configure_command() with generator specification
    - Test get_configure_command() with build type
    - Test get_build_command() with minimal arguments
    - Test get_build_command() with build-args (e.g., -j8)
    - Test get_build_command() with --target specification
    - Test command generation with absolute vs relative paths
    - Test environment variable handling
  - **Success Criteria:** Commands are properly formatted, all parameters are included correctly, 100% coverage

#### Step 3.2: Parameter Addition & Override
- **Description:** Implement add_parameter() method to add or override CMake parameters programmatically.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test dynamic parameter addition and override behavior
  - **Test File:** `tests/test_parameter_override.py`
  - **Test Cases:**
    - Test adding new parameter
    - Test overriding existing parameter
    - Test parameter precedence (CLI args vs programmatic)
    - Test get_parameters() returns all parameters
    - Test parameter formatting (-D prefix for CMake)
    - Test special characters in parameter values
    - Test environment variable substitution in parameters
  - **Success Criteria:** Parameters can be added/overridden, precedence rules work correctly, 100% coverage

#### Step 3.3: Generator & Compiler Detection
- **Description:** Implement detect_generator() method that intelligently detects or selects appropriate CMake generator.

- **Testing Approach:**
  - **Test Type:** Unit tests with mocking
  - **Test Description:** Test generator detection logic on different platforms
  - **Test File:** `tests/test_generator_detection.py`
  - **Test Cases:**
    - Test Ninja detection when available
    - Test fallback to Unix Makefiles on Linux
    - Test Visual Studio detection on Windows
    - Test explicit generator specification (overrides detection)
    - Test generator validation (error on invalid generator)
    - Mock platform detection for cross-platform testing
    - Test generator availability checking
  - **Success Criteria:** Generator detection works on all platforms (mock tested), explicit specification honored, 100% coverage

### Success Criteria

- **Criterion 3.1:** CMake commands are generated correctly for all parameter combinations, 100% coverage
- **Criterion 3.2:** Parameters can be added and overridden with correct precedence, 100% coverage
- **Criterion 3.3:** Generator detection works reliably with proper fallbacks, 100% coverage (with mocking)
- **Overall:** CMake command building is complete and tested. Commands can be generated for any valid configuration. Test coverage ≥98%.

---

## Iteration 4: CMake Execution & Output Capture

**Goal:** Implement CMake execution with real-time output streaming and complete capture.

### Steps

#### Step 4.1: Basic Process Execution
- **Description:** Implement execute_configure() and execute_build() methods in CMakeExecutor that spawn subprocess and capture exit codes.

- **Testing Approach:**
  - **Test Type:** Integration tests with mock CMake
  - **Test Description:** Test process execution and exit code capture
  - **Test File:** `tests/test_executor_basic.py`
  - **Test Cases:**
    - Test successful command execution (exit code 0)
    - Test failed command execution (non-zero exit code)
    - Test command not found error
    - Test execution timeout handling
    - Test working directory is set correctly
    - Mock CMake command for predictable testing
    - Test with simple shell commands (echo, etc.)
  - **Success Criteria:** Processes execute, exit codes captured correctly, errors handled gracefully, 90% coverage

#### Step 4.2: Output Streaming & Capture
- **Description:** Implement _stream_output() method that simultaneously displays output to console and captures it to string.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test output capture and streaming
  - **Test File:** `tests/test_executor_output.py`
  - **Test Cases:**
    - Test stdout is captured completely
    - Test stderr is captured completely
    - Test mixed stdout/stderr ordering is preserved
    - Test real-time streaming (output appears immediately)
    - Test large output handling (memory efficiency)
    - Test Unicode/special characters in output
    - Test line buffering vs full buffering
    - Test output capture can be disabled (performance mode)
    - Use mock subprocess with known output
  - **Success Criteria:** Output is captured completely and streamed in real-time, no data loss, 95% coverage

#### Step 4.3: Timing & Result Objects
- **Description:** Implement timing measurement (start_time, end_time, duration) and populate ConfigureResult/BuildResult objects.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test timing accuracy and result object population
  - **Test File:** `tests/test_executor_results.py`
  - **Test Cases:**
    - Test start_time is recorded accurately
    - Test end_time is recorded accurately
    - Test duration is calculated correctly (end - start)
    - Test timing with sub-millisecond precision
    - Test ConfigureResult contains all expected fields
    - Test BuildResult contains all expected fields
    - Test result objects are populated from execution
    - Test timing for quick commands (< 1 second)
    - Test timing for longer commands (mock sleep)
  - **Success Criteria:** Timing is accurate, result objects complete, all fields populated, 100% coverage

#### Step 4.4: CMake Availability Check
- **Description:** Implement check_cmake_available() and get_cmake_version() methods.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test CMake detection and version extraction
  - **Test File:** `tests/test_cmake_detection.py`
  - **Test Cases:**
    - Test CMake is detected when available
    - Test CMake not found returns False
    - Test get_cmake_version() extracts version correctly
    - Test version parsing with different formats (3.28.1, 3.20, etc.)
    - Test version comparison (for minimum version check)
    - Mock CMake command for predictable testing
    - Test PATH environment variable handling
  - **Success Criteria:** CMake detection works reliably, version extracted accurately, 100% coverage

### Success Criteria

- **Criterion 4.1:** Process execution works with proper exit code handling, 90% coverage
- **Criterion 4.2:** Output streaming and capture work simultaneously without data loss, 95% coverage
- **Criterion 4.3:** Timing is accurate and result objects are complete, 100% coverage
- **Criterion 4.4:** CMake detection and versioning work reliably, 100% coverage
- **Overall:** CMake execution is fully functional. Can run real CMake commands and capture all output. Test coverage ≥95%.

---

## Iteration 5: Build Output Inspection

**Goal:** Implement intelligent parsing of CMake/compiler output to extract meaningful metadata.

### Steps

#### Step 5.1: Project Name Detection
- **Description:** Implement detect_project_name() method that parses CMakeLists.txt to find project() call.

- **Testing Approach:**
  - **Test Type:** Unit tests with fixtures
  - **Test Description:** Test project name extraction from various CMakeLists.txt formats
  - **Test File:** `tests/test_project_detection.py`
  - **Test Fixtures:** `tests/fixtures/cmakelists/` with sample files
  - **Test Cases:**
    - Test simple project() call: `project(MyProject)`
    - Test project with language: `project(MyProject CXX)`
    - Test project with version: `project(MyProject VERSION 1.0.0)`
    - Test multiline project call
    - Test project with variables: `project(${PROJECT_NAME})`
    - Test nested project calls (use outermost)
    - Test CMakeLists.txt not found
    - Test CMakeLists.txt without project() call
    - Test comments in project call
  - **Success Criteria:** Project name extracted correctly from all valid formats, 100% coverage

#### Step 5.2: Configuration Metadata Extraction
- **Description:** Implement inspect_configure_output() to extract CMake version, generator, compiler info, found packages from configuration output.

- **Testing Approach:**
  - **Test Type:** Unit tests with output fixtures
  - **Test Description:** Test metadata extraction from real CMake configure output
  - **Test File:** `tests/test_configure_inspection.py`
  - **Test Fixtures:** `tests/fixtures/outputs/configure_*.txt` with real CMake outputs
  - **Test Cases:**
    - Test CMake version extraction from output
    - Test generator detection from output
    - Test C compiler detection (gcc, clang, msvc)
    - Test C++ compiler detection
    - Test system name/processor extraction
    - Test found packages list (via find_package outputs)
    - Test build type detection
    - Test multiple find_package calls
    - Test configure output from different platforms (Linux, Windows, macOS)
    - Test partial/missing information handling
  - **Success Criteria:** All metadata extracted correctly from real outputs, graceful handling of missing data, 100% coverage

#### Step 5.3: Warning & Error Extraction
- **Description:** Implement extract_warnings() and extract_errors() to parse compiler warnings and errors with file/line/column information.

- **Testing Approach:**
  - **Test Type:** Unit tests with output fixtures
  - **Test Description:** Test warning/error parsing from various compilers
  - **Test File:** `tests/test_warning_error_extraction.py`
  - **Test Fixtures:** `tests/fixtures/outputs/` with gcc, clang, msvc outputs
  - **Test Cases:**
    - Test GCC warning format: `file.cpp:10:5: warning: unused variable`
    - Test Clang warning format
    - Test MSVC warning format: `file.cpp(10): warning C4101:`
    - Test error extraction with same formats
    - Test warning type extraction (unused-variable, etc.)
    - Test multiline warnings/errors
    - Test warnings without file/line info
    - Test colored output handling (ANSI codes)
    - Test warning counting
    - Test deduplication of identical warnings
  - **Success Criteria:** Warnings/errors extracted from all major compilers, structured correctly, 100% coverage

#### Step 5.4: Build Target Extraction
- **Description:** Implement extract_targets() to identify built targets from build output.

- **Testing Approach:**
  - **Test Type:** Unit tests with output fixtures
  - **Test Description:** Test target extraction from build output
  - **Test File:** `tests/test_target_extraction.py`
  - **Test Fixtures:** `tests/fixtures/outputs/build_*.txt`
  - **Test Cases:**
    - Test target extraction from Ninja output
    - Test target extraction from Make output
    - Test target extraction from MSVC output
    - Test executable vs library differentiation
    - Test build order detection
    - Test parallel build output handling
    - Test percentage completion extraction
    - Test file compilation count
  - **Success Criteria:** Targets extracted correctly from all build systems, 95% coverage

#### Step 5.5: Complete Metadata Assembly
- **Description:** Implement inspect_build_output() that combines all extraction methods into complete BuildMetadata object.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test complete metadata extraction pipeline
  - **Test File:** `tests/test_build_inspection_integration.py`
  - **Test Cases:**
    - Test complete successful build inspection
    - Test failed build inspection (with errors)
    - Test build with warnings but success
    - Test build with partial output
    - Test metadata completeness validation
    - Test BuildMetadata object population
    - Test integration of all extraction methods
  - **Success Criteria:** Complete metadata objects created, all components integrated, 100% coverage

### Success Criteria

- **Criterion 5.1:** Project names detected from all CMakeLists.txt formats, 100% coverage
- **Criterion 5.2:** Configuration metadata extracted from real CMake output, 100% coverage
- **Criterion 5.3:** Warnings and errors extracted from all major compilers, 100% coverage
- **Criterion 5.4:** Build targets extracted from all build systems, 95% coverage
- **Criterion 5.5:** Complete inspection pipeline works end-to-end, 100% coverage
- **Overall:** Build inspection is complete and accurate. Can extract all meaningful data from CMake/compiler output. Test coverage ≥98%.

---

## Iteration 6: Data Persistence

**Goal:** Implement complete database operations with transaction handling and data integrity.

### Steps

#### Step 6.1: Database Initialization
- **Description:** Implement DataPersistence class with initialize_database() method, connection management, and schema version tracking.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test database creation and initialization
  - **Test File:** `tests/test_persistence_init.py`
  - **Test Cases:**
    - Test database creation in default location
    - Test database creation in custom location
    - Test schema creation on first run
    - Test idempotent initialization (multiple calls)
    - Test database connection handling
    - Test connection pooling
    - Test schema version tracking
    - Test migration readiness
    - Test file permissions
    - Test concurrent access handling
  - **Success Criteria:** Database initializes correctly, schema created, idempotent operation, 100% coverage

#### Step 6.2: Configuration Data Persistence
- **Description:** Implement save_configuration() method to store complete configuration data with all metadata.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test configuration record creation and retrieval
  - **Test File:** `tests/test_persistence_configure.py`
  - **Test Cases:**
    - Test save complete ConfigureResult
    - Test save with all metadata fields
    - Test JSON serialization of complex fields
    - Test timestamp formatting (ISO 8601)
    - Test NULL handling for optional fields
    - Test foreign key creation for subsequent builds
    - Test return of configuration ID
    - Test duplicate configuration handling
    - Test transaction rollback on error
    - Test data integrity constraints
  - **Success Criteria:** Configuration data persisted correctly, ID returned, data retrievable, 100% coverage

#### Step 6.3: Build Data Persistence
- **Description:** Implement save_build() method to store build data with association to configuration.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test build record creation with relationships
  - **Test File:** `tests/test_persistence_build.py`
  - **Test Cases:**
    - Test save BuildResult with all fields
    - Test association with configuration_id
    - Test save build without configuration (build-only mode)
    - Test JSON serialization of targets list
    - Test warning/error count storage
    - Test return of build ID
    - Test transaction handling
    - Test foreign key relationships
  - **Success Criteria:** Build data persisted correctly, relationships maintained, 100% coverage

#### Step 6.4: Warning & Error Persistence
- **Description:** Implement save_warnings() and save_errors() methods to store detailed diagnostic information.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test bulk insertion of warnings and errors
  - **Test File:** `tests/test_persistence_diagnostics.py`
  - **Test Cases:**
    - Test save single warning
    - Test save multiple warnings (bulk insert)
    - Test save warnings with complete information
    - Test save warnings with partial information
    - Test save errors with same patterns
    - Test foreign key relationship to build
    - Test cascade delete when build is deleted
    - Test transaction handling for bulk operations
    - Test handling of very large warning lists (1000+)
  - **Success Criteria:** Warnings/errors saved efficiently, relationships maintained, bulk operations work, 100% coverage

#### Step 6.5: Query Methods
- **Description:** Implement get_recent_builds() and get_build_statistics() for data retrieval.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test data querying and aggregation
  - **Test File:** `tests/test_persistence_queries.py`
  - **Test Cases:**
    - Test get_recent_builds() with default limit
    - Test get_recent_builds() with custom limit
    - Test filtering by project name
    - Test ordering by timestamp (newest first)
    - Test get_build_statistics() calculations
    - Test statistics with no data
    - Test statistics with multiple builds
    - Test success rate calculation
    - Test average duration calculation
    - Test query performance with large datasets
  - **Success Criteria:** Queries return correct data, statistics accurate, performance acceptable, 100% coverage

### Success Criteria

- **Criterion 6.1:** Database initialization is robust and idempotent, 100% coverage
- **Criterion 6.2:** Configuration data is persisted completely and correctly, 100% coverage
- **Criterion 6.3:** Build data is persisted with proper relationships, 100% coverage
- **Criterion 6.4:** Warnings and errors are saved efficiently in bulk, 100% coverage
- **Criterion 6.5:** Query methods return accurate data and statistics, 100% coverage
- **Overall:** Data persistence is complete and robust. All data can be saved and retrieved correctly. Test coverage ≥98%.

---

## Iteration 7: Main Application Integration

**Goal:** Integrate all components into working CLI application with complete workflow.

### Steps

#### Step 7.1: Main Entry Point Implementation
- **Description:** Implement __main__.py with main() function that orchestrates all components.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test complete application flow from command line to database
  - **Test File:** `tests/test_main_integration.py`
  - **Test Cases:**
    - Test complete configure + build workflow
    - Test build-only workflow (no configure)
    - Test with minimal arguments
    - Test with all arguments
    - Test with invalid arguments (error handling)
    - Test exit code propagation
    - Test component initialization
    - Test database path handling
    - Test verbose output mode
    - Mock CMake for predictable testing
  - **Success Criteria:** Complete workflow works end-to-end, all components integrated, 95% coverage

#### Step 7.2: Error Handling & Recovery
- **Description:** Implement comprehensive error handling at application level with proper cleanup.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test error scenarios and recovery
  - **Test File:** `tests/test_main_errors.py`
  - **Test Cases:**
    - Test CMake not found error
    - Test configuration failure handling
    - Test build failure handling
    - Test database connection error
    - Test disk full scenario
    - Test keyboard interrupt (Ctrl+C) handling
    - Test cleanup on error (close connections, etc.)
    - Test partial data handling (config succeeds, build fails)
    - Test error message clarity
  - **Success Criteria:** All error scenarios handled gracefully, resources cleaned up, clear error messages, 95% coverage

#### Step 7.3: Output Formatting & User Feedback
- **Description:** Implement print_build_summary() and formatted output for user-friendly console display.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test output formatting and user messages
  - **Test File:** `tests/test_output_formatting.py`
  - **Test Cases:**
    - Test summary output for successful build
    - Test summary output for failed build
    - Test summary output with warnings
    - Test summary output with errors
    - Test timing display formatting
    - Test color output (when supported)
    - Test plain output (when colors not supported)
    - Test progress indicators
    - Test verbose vs normal output modes
  - **Success Criteria:** Output is clear and helpful, formatting consistent, 100% coverage

#### Step 7.4: Logging Configuration
- **Description:** Implement logging configuration with appropriate levels and output destinations.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test logging configuration and output
  - **Test File:** `tests/test_logging.py`
  - **Test Cases:**
    - Test default logging level (INFO)
    - Test verbose mode logging level (DEBUG)
    - Test log output to console
    - Test log output to file (when configured)
    - Test log message formatting
    - Test exception logging with stack traces
    - Test performance logging (timing info)
    - Test log rotation (if implemented)
  - **Success Criteria:** Logging works at all levels, output formatted correctly, 100% coverage

### Success Criteria

- **Criterion 7.1:** Complete application workflow functions correctly, 95% coverage
- **Criterion 7.2:** All error scenarios are handled with proper cleanup, 95% coverage
- **Criterion 7.3:** User output is clear, helpful, and well-formatted, 100% coverage
- **Criterion 7.4:** Logging is properly configured and functional, 100% coverage
- **Overall:** Forge is a fully functional CLI application. Can execute real CMake builds and store data in database. Test coverage ≥95%.

---

## Iteration 8: End-to-End Testing & Real-World Validation

**Goal:** Validate Forge with real CMake projects and edge cases.

### Steps

#### Step 8.1: Sample Project Testing
- **Description:** Create sample CMake projects and test Forge against them.

- **Testing Approach:**
  - **Test Type:** End-to-end tests
  - **Test Description:** Test Forge with real, working CMake projects
  - **Test File:** `tests/test_e2e_samples.py`
  - **Test Fixtures:** `tests/fixtures/projects/` with sample CMake projects
  - **Test Cases:**
    - Test simple C++ executable project
    - Test project with multiple targets
    - Test project with external dependencies
    - Test project with different build types (Debug, Release)
    - Test project with custom CMake modules
    - Test header-only library project
    - Test project with subdirectories
    - Test project with tests
  - **Success Criteria:** Forge successfully builds all sample projects, data stored correctly, no crashes

#### Step 8.2: Edge Case Testing
- **Description:** Test Forge with problematic or unusual scenarios.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test edge cases and unusual scenarios
  - **Test File:** `tests/test_edge_cases.py`
  - **Test Cases:**
    - Test very long build output (memory efficiency)
    - Test build with 1000+ warnings
    - Test build with Unicode in output
    - Test build in path with spaces
    - Test build in path with special characters
    - Test very quick build (< 1 second)
    - Test very long build (mock long-running process)
    - Test concurrent Forge invocations
    - Test database file locked scenario
  - **Success Criteria:** All edge cases handled correctly, no crashes, data integrity maintained

#### Step 8.3: Cross-Platform Testing
- **Description:** Validate Forge on different operating systems (Windows, Linux, macOS).

- **Testing Approach:**
  - **Test Type:** Integration tests (CI/CD)
  - **Test Description:** Run test suite on multiple platforms
  - **Test File:** All existing tests
  - **Test Cases:**
    - Run complete test suite on Linux
    - Run complete test suite on Windows
    - Run complete test suite on macOS (if available)
    - Test path handling differences (/ vs \\)
    - Test line ending differences (LF vs CRLF)
    - Test shell differences (bash vs cmd vs powershell)
    - Test CMake generator differences
  - **Success Criteria:** All tests pass on all platforms, no platform-specific failures

#### Step 8.4: Performance Testing
- **Description:** Test Forge performance and overhead.

- **Testing Approach:**
  - **Test Type:** Performance tests
  - **Test Description:** Measure Forge overhead and performance characteristics
  - **Test File:** `tests/test_performance.py`
  - **Test Cases:**
    - Test Forge overhead vs native CMake (< 5% additional time)
    - Test memory usage during large builds
    - Test database insert performance (1000+ records)
    - Test output capture overhead
    - Test query performance with large datasets
    - Test startup time
  - **Success Criteria:** Forge adds < 5% overhead to build time, memory usage reasonable, queries fast

### Success Criteria

- **Criterion 8.1:** Forge works with all sample projects, data correctly stored
- **Criterion 8.2:** All edge cases handled without crashes or data corruption
- **Criterion 8.3:** Test suite passes on all target platforms (Linux, Windows, macOS)
- **Criterion 8.4:** Performance overhead is acceptable (< 5% additional build time)
- **Overall:** Forge is production-ready. Works reliably with real projects on all platforms. Test coverage ≥95%.

---

## Iteration 9: Documentation & Distribution

**Goal:** Create comprehensive documentation and prepare for distribution.

### Steps

#### Step 9.1: API Documentation
- **Description:** Write complete docstrings for all classes and methods, generate API documentation.

- **Testing Approach:**
  - **Test Type:** Documentation tests
  - **Test Description:** Validate documentation completeness and examples
  - **Test File:** `tests/test_documentation.py`
  - **Test Cases:**
    - Test all public classes have docstrings
    - Test all public methods have docstrings
    - Test docstring format compliance (Google/NumPy style)
    - Test example code in docstrings executes correctly (doctest)
    - Test parameter documentation matches function signature
    - Test return type documentation is accurate
    - Test exception documentation is complete
  - **Success Criteria:** 100% of public API is documented, all examples work, documentation generates without errors

#### Step 9.2: User Guide & Tutorial
- **Description:** Write user-facing documentation with examples and tutorials.

- **Testing Approach:**
  - **Test Type:** Documentation validation
  - **Test Description:** Test all examples in user documentation
  - **Test File:** Manual testing + automated extraction
  - **Test Cases:**
    - Test quick start example works
    - Test all usage examples execute correctly
    - Test configuration examples are valid
    - Test troubleshooting steps resolve common issues
    - Test installation instructions work
    - Test upgrade instructions work
  - **Success Criteria:** All examples in documentation are tested and work correctly

#### Step 9.3: Packaging & Installation
- **Description:** Create setup.py/pyproject.toml for pip installation, test installation process.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test installation and package integrity
  - **Test File:** `tests/test_installation.py`
  - **Test Cases:**
    - Test pip install in clean virtual environment
    - Test forge command is available after install
    - Test --version shows correct version
    - Test --help shows documentation
    - Test uninstall removes all files
    - Test upgrade from previous version
    - Test dependency installation
    - Test entry point configuration
  - **Success Criteria:** Package installs cleanly, all commands work, uninstall is clean

#### Step 9.4: CI/CD Pipeline
- **Description:** Set up GitHub Actions (or similar) for automated testing and release.

- **Testing Approach:**
  - **Test Type:** CI/CD validation
  - **Test Description:** Validate CI/CD pipeline configuration
  - **Test Cases:**
    - Test CI runs on all commits
    - Test CI runs on all platforms
    - Test CI fails on test failures
    - Test coverage reporting works
    - Test automatic release creation
    - Test package publication to PyPI (test)
    - Test badge generation for README
  - **Success Criteria:** CI/CD pipeline runs automatically, all tests pass, releases automated

**Note:** Steps 9.3 and 9.4 have been moved to Iteration 2 (see forge-implementation-plan-iter2.md). Forge Iteration 1 focuses on core functionality and manual validation before automating distribution.

### Success Criteria

- **Criterion 9.1:** Complete API documentation with working examples, 100% coverage
- **Criterion 9.2:** User guide is comprehensive and all examples work
- **Criterion 9.3:** ~~Package installs cleanly and works in all environments~~ (Moved to Iteration 2)
- **Criterion 9.4:** ~~CI/CD pipeline is functional and fully automated~~ (Moved to Iteration 2)
- **Overall:** Forge is documented and ready for manual distribution. Core functionality is complete and validated.

---

## Summary

### Development Timeline

- **Iteration 1-2**: 2 weeks (Foundation + CLI)
- **Iteration 3-4**: 2 weeks (CMake management + Execution)
- **Iteration 5-6**: 3 weeks (Inspection + Persistence)
- **Iteration 7-8**: 2 weeks (Integration + Validation)
- **Iteration 9**: 1 week (Documentation)

**Total Estimated Time**: 10 weeks

**Note:** Packaging, distribution, and CI/CD automation are now in Iteration 2. This allows Forge to be validated manually before automating the release process.

### Test Coverage Goals

- **Unit Tests**: ≥98% coverage
- **Integration Tests**: ≥95% coverage
- **End-to-End Tests**: All critical workflows
- **Overall**: ≥95% coverage

### Key Metrics

- **Total Test Cases**: ~200+
- **Test Execution Time**: < 5 minutes for full suite
- **Performance Overhead**: < 5% vs native CMake
- **Supported Platforms**: Linux, Windows, macOS
- **Python Version**: 3.8+

### TDD Benefits

1. **Confidence**: Every feature is tested before implementation
2. **Documentation**: Tests serve as executable documentation
3. **Regression Prevention**: Changes immediately show failures
4. **Design Quality**: TDD forces good API design
5. **Refactoring Safety**: Can refactor with confidence

---

## Next Steps

1. Review this plan with team
2. Set up project repository
3. Configure development environment
4. Begin Iteration 1, Step 1.1
5. Follow red-green-refactor cycle for each step
6. Review and adjust plan as needed based on findings

---

**Plan Version**: 1.0
**Created**: 2026-01-27
**Status**: Ready for implementation
