-- Forge Database Schema
-- SQLite database schema for storing build and configuration data

-- Configuration records
CREATE TABLE IF NOT EXISTS configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    project_name TEXT,
    source_dir TEXT NOT NULL,
    build_dir TEXT NOT NULL,
    cmake_version TEXT,
    generator TEXT,
    compiler_c TEXT,
    compiler_cxx TEXT,
    build_type TEXT,
    system_name TEXT,
    system_processor TEXT,
    cmake_args TEXT,
    environment_vars TEXT,
    duration REAL NOT NULL,
    exit_code INTEGER NOT NULL,
    success INTEGER NOT NULL,
    stdout TEXT,
    stderr TEXT,
    configuration_options TEXT,
    found_packages TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_configurations_project ON configurations(project_name);
CREATE INDEX IF NOT EXISTS idx_configurations_timestamp ON configurations(timestamp);
CREATE INDEX IF NOT EXISTS idx_configurations_success ON configurations(success);

-- Build records
CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    configuration_id INTEGER,
    timestamp TEXT NOT NULL,
    project_name TEXT NOT NULL,
    build_dir TEXT NOT NULL,
    build_args TEXT,
    duration REAL NOT NULL,
    exit_code INTEGER NOT NULL,
    success INTEGER NOT NULL,
    stdout TEXT,
    stderr TEXT,
    warnings_count INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    targets_built TEXT,
    total_files_compiled INTEGER,
    parallel_jobs INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (configuration_id) REFERENCES configurations(id)
);

CREATE INDEX IF NOT EXISTS idx_builds_project ON builds(project_name);
CREATE INDEX IF NOT EXISTS idx_builds_timestamp ON builds(timestamp);
CREATE INDEX IF NOT EXISTS idx_builds_success ON builds(success);
CREATE INDEX IF NOT EXISTS idx_builds_config ON builds(configuration_id);

-- Warning records
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    file TEXT,
    line INTEGER,
    column INTEGER,
    message TEXT NOT NULL,
    warning_type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_warnings_build ON warnings(build_id);
CREATE INDEX IF NOT EXISTS idx_warnings_file ON warnings(file);
CREATE INDEX IF NOT EXISTS idx_warnings_type ON warnings(warning_type);

-- Error records
CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    file TEXT,
    line INTEGER,
    column INTEGER,
    message TEXT NOT NULL,
    error_type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_errors_build ON errors(build_id);
CREATE INDEX IF NOT EXISTS idx_errors_file ON errors(file);
CREATE INDEX IF NOT EXISTS idx_errors_type ON errors(error_type);

-- Build targets
CREATE TABLE IF NOT EXISTS build_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    target_name TEXT NOT NULL,
    target_type TEXT,
    build_order INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_targets_build ON build_targets(build_id);
CREATE INDEX IF NOT EXISTS idx_targets_name ON build_targets(target_name);
