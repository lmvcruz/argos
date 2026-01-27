# Gaze - Runtime Inspector Daemon Specification

## Overview

**Gaze** is Argus's runtime monitoring daemon that observes running applications, collecting performance metrics and log entries without requiring any modifications to the monitored processes. It attaches to processes externally, captures CPU/memory/thread metrics at regular intervals, and tails log files in real-time, transparently recording all information to a local SQLite database.

Named to complement Argus (the all-seeing watcher) and forge (the builder), gaze represents continuous observation—watching applications while they run, just as Argus watched over Io with his hundred eyes.

## Design Principles

1. **Non-Intrusive**: Zero modifications required to application code or configuration
2. **External Observation**: Attaches to processes via OS-level APIs (psutil)
3. **Continuous Monitoring**: Runs as a daemon until the process terminates
4. **Real-Time**: Captures metrics and logs as they happen
5. **Local-First**: Stores data locally in SQLite (v0.2), with optional server upload in later versions
6. **Lightweight**: Minimal overhead on monitored applications

## Command-Line Interface

### Basic Usage

```bash
# Monitor a process by name
python gaze --process <name>

# Monitor a process by PID
python gaze --pid <pid>

# Monitor with log file tailing
python gaze --process <name> --logfile <path>
```

### Parameters

- `--process <name>` (semi-optional): Process name to monitor (e.g., "terrain_sim", "python", "notepad")
- `--pid <pid>` (semi-optional): Process ID to monitor (mutually exclusive with --process)
- `--logfile <path>` (optional): Path to log file to tail in real-time
- `--interval <seconds>` (optional): Metric collection interval in seconds (default: 5)
- `--server <url>` (optional, v0.3+): Argus server URL for data upload
- `--app-name <name>` (optional): Override application name (useful when process name is generic like "python")
- `--verbose` (optional): Enable detailed logging from gaze itself

**Note**: Either `--process` or `--pid` must be provided.

### Examples

```bash
# Monitor Notepad by process name
python gaze --process notepad

# Monitor a C++ application with log tailing
python gaze --process terrain_sim --logfile ./terrain_sim.log

# Monitor a Python app by PID with custom name
python gaze --pid 12345 --app-name SnakeGame --logfile snake_game.log

# Monitor with 10-second interval instead of default 5
python gaze --process myapp --interval 10

# Monitor and upload to Argus server (v0.3+)
python gaze --process terrain_sim --logfile terrain_sim.log --server http://localhost:8000

# Monitor with custom collection interval and verbose output
python gaze --process loom_backend --logfile loom.log --interval 3 --verbose
```

## Functionality

### Process Attachment

1. **Process Discovery**: Locates the process by name or PID using `psutil`
2. **Validation**: Confirms process exists and is accessible
3. **Handle Acquisition**: Maintains a reference to the process for monitoring
4. **Multiple Instances**: If multiple processes match name, attaches to the first found (warns user)

### Performance Metrics Collection

**Collection Loop** (runs every `--interval` seconds, default 5):

1. **CPU Usage**: Percentage of CPU used by the process (0-100% per core)
2. **Memory Consumption**: RSS (Resident Set Size) in megabytes
3. **Thread Count**: Number of active threads in the process
4. **Timestamp**: Exact collection time with millisecond precision

**Optional Future Metrics** (v0.4+):
- Disk I/O (read/write bytes per second)
- Network I/O (sent/received bytes per second)
- Open file descriptors count
- Child process count

### Log File Tailing

When `--logfile` is provided:

1. **File Monitoring**: Opens the log file and seeks to the end
2. **Real-Time Detection**: Watches for new lines appended to the file
3. **Line Capture**: Reads new lines within ~1 second of being written
4. **Timestamp Association**: Records the exact time each line was captured
5. **File Rotation Handling** (v0.3+): Detects log rotation and reopens the new file

**Implementation Details**:
- Uses file polling or OS-specific file watch APIs (inotify on Linux, ReadDirectoryChangesW on Windows)
- Handles partial line reads (waits for complete lines)
- Preserves original log formatting

### Process Lifecycle Management

1. **Startup Detection**: Confirms process is running before beginning monitoring
2. **Continuous Health Check**: Periodically verifies process is still alive
3. **Termination Detection**: Detects when monitored process exits
4. **Graceful Shutdown**: Saves final metrics and logs exit event when process terminates
5. **Auto-Exit**: Gaze terminates itself within 5 seconds of process termination

### Data Storage

#### SQLite Schema (v0.2)

**Database File**: `argus_runtime.db` (created in user's home directory or `~/.argus/`)

**Table: performance_metrics**

```sql
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                  -- ISO 8601 format: 2026-01-27T14:23:45.123Z
    app_name TEXT NOT NULL,                   -- Application name
    process_name TEXT NOT NULL,               -- OS process name
    process_id INTEGER NOT NULL,              -- PID at time of collection
    cpu_percent REAL NOT NULL,                -- CPU usage 0-100% (per core)
    memory_mb REAL NOT NULL,                  -- RSS memory in megabytes
    thread_count INTEGER NOT NULL,            -- Number of threads
    hostname TEXT,                            -- Machine name
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_metrics_app ON performance_metrics(app_name);
CREATE INDEX idx_metrics_process_id ON performance_metrics(process_id);
```

**Table: log_entries**

```sql
CREATE TABLE log_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                  -- ISO 8601 format: 2026-01-27T14:23:45.123Z
    app_name TEXT NOT NULL,                   -- Application name
    process_name TEXT NOT NULL,               -- OS process name
    process_id INTEGER NOT NULL,              -- PID at time of capture
    log_line TEXT NOT NULL,                   -- Complete log line (preserves formatting)
    logfile_path TEXT,                        -- Source log file path
    hostname TEXT,                            -- Machine name
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_timestamp ON log_entries(timestamp);
CREATE INDEX idx_logs_app ON log_entries(app_name);
CREATE INDEX idx_logs_process_id ON log_entries(process_id);
```

**Table: process_events**

```sql
CREATE TABLE process_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                  -- ISO 8601 format
    app_name TEXT NOT NULL,                   -- Application name
    process_name TEXT NOT NULL,               -- OS process name
    process_id INTEGER NOT NULL,              -- PID
    event_type TEXT NOT NULL,                 -- 'started', 'terminated', 'monitoring_started', 'monitoring_stopped'
    exit_code INTEGER,                        -- Exit code (only for 'terminated' events)
    hostname TEXT,                            -- Machine name
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_timestamp ON process_events(timestamp);
CREATE INDEX idx_events_app ON process_events(app_name);
CREATE INDEX idx_events_type ON process_events(event_type);
```

#### Server Upload (v0.3+)

When `--server` is provided, gaze will POST data to the Argus server:

**Endpoint**: `POST /api/ingest`

**Performance Metric Payload**:
```json
{
    "event_type": "performance_metric",
    "timestamp": "2026-01-27T14:23:45.123Z",
    "app_name": "TerrainSimulation",
    "process_name": "terrain_sim",
    "process_id": 12345,
    "cpu_percent": 45.2,
    "memory_mb": 256.8,
    "thread_count": 4,
    "hostname": "dev-machine"
}
```

**Log Entry Payload**:
```json
{
    "event_type": "log_entry",
    "timestamp": "2026-01-27T14:23:45.500Z",
    "app_name": "TerrainSimulation",
    "process_name": "terrain_sim",
    "process_id": 12345,
    "log_line": "[INFO] Terrain generation completed in 2.5s",
    "logfile_path": "/home/user/projects/terrain/terrain_sim.log",
    "hostname": "dev-machine"
}
```

**Process Event Payload**:
```json
{
    "event_type": "process_event",
    "timestamp": "2026-01-27T14:23:50.000Z",
    "app_name": "TerrainSimulation",
    "process_name": "terrain_sim",
    "process_id": 12345,
    "process_event_type": "terminated",
    "exit_code": 0,
    "hostname": "dev-machine"
}
```

## Implementation Details

### Language and Dependencies

- **Language**: Python 3.8+
- **Core Libraries**:
  - `psutil`: Process discovery and metrics collection
  - `sqlite3`: Database operations (standard library)
  - `argparse`: Command-line argument parsing
  - `datetime`: Timestamp handling
  - `pathlib`: Path manipulation
  - `socket`: Hostname detection
  - `time`: Sleep intervals for collection loop
  - `threading`: Concurrent log tailing and metric collection
- **Optional Dependencies** (v0.3+):
  - `requests` or `httpx`: HTTP client for server communication
  - `watchdog`: Advanced file watching (cross-platform)

### Application Name Detection

Priority order for determining application name:

1. `--app-name` CLI argument (if provided)
2. Use process name from `psutil.Process().name()`
3. Default to "UnknownApp" if all else fails

### Multi-Threading Architecture

Gaze uses two concurrent threads:

1. **Metrics Collection Thread**:
   - Runs every `--interval` seconds
   - Collects CPU, memory, thread count
   - Saves to database
   - Checks process health

2. **Log Tailing Thread** (if `--logfile` provided):
   - Continuously watches log file
   - Captures new lines immediately
   - Saves to database
   - Independent of metrics collection timing

### Error Handling

- **Process Not Found**: Exit with error message, code 1
- **Process Terminated**: Log termination event, save final data, exit gracefully with code 0
- **Log File Not Found**: Warn user but continue monitoring metrics
- **Log File Permissions Denied**: Warn user but continue monitoring metrics
- **Database Write Failure**: Log warning, continue execution
- **Server Upload Failure** (v0.3+): Log warning, store locally, continue monitoring
- **psutil Not Available**: Exit with error message, code 2

### Output Format

#### Console Output (Standard Mode)

```
[Gaze] Starting monitoring: TerrainSimulation
[Gaze] Process: terrain_sim (PID: 12345)
[Gaze] Log file: /home/user/projects/terrain/terrain_sim.log
[Gaze] Collection interval: 5 seconds
[Gaze] Timestamp: 2026-01-27 14:23:40

[Gaze] Metrics: CPU=45.2% | Memory=256.8MB | Threads=4
[Gaze] Log: [INFO] Terrain generation started
[Gaze] Log: [INFO] Perlin noise seed: 42
[Gaze] Metrics: CPU=52.1% | Memory=312.4MB | Threads=4
[Gaze] Log: [INFO] Terrain generation completed in 2.5s
[Gaze] Metrics: CPU=38.5% | Memory=310.2MB | Threads=4

[Gaze] Process terminated (exit code: 0)
[Gaze] Total monitoring time: 45.6 seconds
[Gaze] Metrics collected: 10
[Gaze] Log entries captured: 15
[Gaze] Data saved to: ~/.argus/argus_runtime.db
```

#### Verbose Mode

When `--verbose` is enabled:
```
[Gaze] Verbose mode enabled
[Gaze] Python version: 3.11.2
[Gaze] psutil version: 5.9.4
[Gaze] Database path: /home/user/.argus/argus_runtime.db
[Gaze] Detected application name: TerrainSimulation (from process name)
[Gaze] Starting metrics collection thread...
[Gaze] Starting log tailing thread...
[Gaze] Both threads started successfully
[Gaze] [Metrics Thread] Collecting data...
[Gaze] [Metrics Thread] CPU: 45.2%, Memory: 256.8MB, Threads: 4
[Gaze] [Metrics Thread] Saved to database (row ID: 1234)
[Gaze] [Log Thread] New line detected: [INFO] Terrain generation started
[Gaze] [Log Thread] Saved to database (row ID: 5678)
...
```

## Usage Workflow

### Development Workflow Integration

```bash
# Build application with forge
python forge --source-dir . --build-dir ./build

# Run the application
./build/terrain_sim &

# Monitor it with gaze (in another terminal)
python gaze --process terrain_sim --logfile terrain_sim.log

# Or combine build + run + monitor in a script
python forge --source-dir . --build-dir ./build && \
./build/terrain_sim &
TERRAIN_PID=$!
python gaze --pid $TERRAIN_PID --logfile terrain_sim.log
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run application with monitoring
  run: |
    ./myapp &
    APP_PID=$!
    python gaze --pid $APP_PID --logfile app.log --server ${{ secrets.ARGUS_SERVER }} &
    GAZE_PID=$!

    # Run tests while monitoring
    pytest tests/

    # Stop application
    kill $APP_PID

    # Wait for gaze to finish
    wait $GAZE_PID
```

### Production Monitoring

```bash
# Monitor a production service
python gaze --process nginx --app-name NginxWebServer --logfile /var/log/nginx/access.log --server https://argus.company.com

# Monitor as a systemd service
# /etc/systemd/system/gaze-myapp.service
[Unit]
Description=Gaze monitoring for MyApp
After=myapp.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/argus/gaze --process myapp --logfile /var/log/myapp/app.log --server https://argus.company.com
Restart=always

[Install]
WantedBy=multi-user.target
```

## Future Enhancements (v0.3+)

### Planned Features

- **Log Parsing**: Extract structured data from log lines (log levels, timestamps, error codes)
- **Alerting**: Trigger alerts based on metric thresholds or log patterns
- **Multi-Process Tracking**: Automatically discover and monitor child processes
- **Process Restart Detection**: Detect and handle process restarts with same name
- **Custom Metrics**: Plugin system for application-specific metrics
- **Correlation IDs**: Link log entries across distributed systems
- **Sampling Modes**: Adaptive sampling (increase frequency during high activity)

### Potential Options

```bash
# Parse log levels from output
python gaze --process myapp --logfile app.log --parse-logs

# Monitor with alerting
python gaze --process myapp --alert-cpu 80 --alert-memory 1024

# Auto-discover child processes
python gaze --process parent_process --follow-children

# Custom metric collection via plugin
python gaze --process myapp --plugin custom_metrics.py
```

## Compatibility

### Supported Process Types

- **Native Applications**: C/C++ executables
- **Python Applications**: Python scripts and servers
- **Java Applications**: JVM processes
- **Node.js Applications**: Node.js processes
- **Web Servers**: nginx, Apache, etc.
- **Databases**: PostgreSQL, MySQL, MongoDB (via process monitoring)

### Supported Platforms

- Linux (Ubuntu 20.04+, Fedora 35+, Arch)
- macOS (11.0+)
- Windows (10/11 with Python 3.8+)

### Platform-Specific Notes

**Linux**:
- Uses `/proc` filesystem via psutil
- inotify for efficient log file watching
- Best performance for high-frequency monitoring

**macOS**:
- Uses BSD kqueue via psutil
- FSEvents for log file watching
- May require elevated permissions for some processes

**Windows**:
- Uses Windows API via psutil
- ReadDirectoryChangesW for log file watching
- May require administrator privileges for system processes

## Testing Strategy

### Unit Tests

- Argument parsing validation
- Application name detection logic
- Database schema creation
- Timestamp formatting
- Metric calculation correctness

### Integration Tests

- Attach to a running process successfully
- Attach to a process by PID
- Collect metrics for 30 seconds (verify 6+ snapshots)
- Tail a log file and capture new lines
- Detect process termination gracefully
- Handle non-existent process gracefully
- Handle non-existent log file gracefully

### End-to-End Tests

- Monitor Terrain Simulation and verify database records
- Monitor Python application and capture log entries
- Simulate server upload (v0.3+)
- Test on all supported platforms
- Monitor process with high CPU/memory load
- Monitor process that spawns child processes

## Performance Considerations

### Overhead

- **Expected Overhead**: < 1% CPU, < 50MB memory for typical monitoring
- **Measurement**: Gaze's own resource usage vs. monitored application
- **Target**: Negligible impact even on resource-constrained systems

### Scalability

- **Collection Frequency**: 5-second default balances accuracy and overhead
- **Large Log Files**: Streaming tail implementation (constant memory usage)
- **Database Size**: Metrics accumulate over time; implement rotation strategy in production
- **Long-Running Processes**: Tested with processes running for hours/days

### Optimization Strategies

- Use threading to prevent blocking between metrics and logs
- Batch database writes (every N entries or every M seconds)
- Implement local buffering when server is unreachable
- Configurable collection intervals for different use cases

## Security Considerations

- **Process Access**: Requires appropriate permissions to read process information
- **Log File Access**: Must have read permissions for specified log files
- **Database Permissions**: Created with user-only read/write permissions
- **Server Communication** (v0.3+): HTTPS recommended, API key authentication
- **Sensitive Data**: Logs may contain sensitive information; no sanitization in v0.2
- **Privilege Escalation**: Never run gaze with unnecessary elevated privileges

## Success Criteria (from Project Plan)

1. ✅ Running `python gaze --process notepad` successfully locates and attaches to the process
2. ✅ Daemon prints CPU, memory, and thread count to console every 5 seconds
3. ✅ SQLite `performance_metrics` table contains data queryable with `SELECT * FROM performance_metrics;`
4. ✅ After 30 seconds, at least 6 metric snapshots are stored in the database
5. ✅ New log lines are detected within 1 second and printed to console
6. ✅ SQLite `log_entries` table contains captured log lines
7. ✅ After application writes 10 log lines, all 10 appear in database
8. ✅ When monitored process terminates, gaze detects it within 5 seconds and exits gracefully
9. ✅ All metrics and logs stored locally for later analysis

---

**Version**: 0.2.0 (Specification)
**Status**: Design Phase
**Last Updated**: 2026-01-27
