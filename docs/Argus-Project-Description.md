# Argus

## Project Description

**Argus** is a lightweight, cross-platform monitoring system that provides visibility into application health, performance, and logs. Named after the all-seeing giant from Greek mythology who had a hundred eyes, Argus watches over your applications without ever being noticed—observing everything while remaining completely invisible to the monitored code.

Designed for quick integration into Python and C++ applications with minimal overhead, Argus embodies the principle of non-intrusive monitoring: your applications require no code changes, no special libraries, and no build system modifications.

### Key Features

- **Simple Integration**: Add monitoring in minutes with SDKs
- **Low Overhead**: Less than 5% performance impact
- **Real-Time Monitoring**: Metrics, logs, and threshold-based alerts
- **Cross-Platform**: Windows, Linux, macOS
- **Single-Server Deployment**: Docker Compose setup

---

## Technology Stack

### Backend

**Python:**
- FastAPI for REST API and WebSocket real-time updates
- APScheduler for background alert checking
- influxdb-client and asyncpg for database connections
- psutil for system metrics collection
- smtplib for email alerts

**C++:**
- Static library SDK (compiled .a or .lib file with headers)
- cpp-httplib or libcurl for HTTP communication
- C++17 or C++20
- Minimal dependencies for easy integration

### Databases

**InfluxDB:**
- Time-series database optimized for metrics storage
- Automatic compression and efficient timestamp-based queries
- Stores CPU, memory, disk, and custom application metrics
- 30-day retention policy

**PostgreSQL:**
- Relational database for logs, users, alerts, and application registry
- JSONB columns for flexible log metadata storage
- Full-text search capability for log queries
- Stores alert rules, alert history, and API keys
- 30-day log retention with automated cleanup

### Frontend

- **React with TypeScript**: Type-safe component development with better tooling
- **Chart.js**: Line charts for metric visualizations over time
- **Bootstrap 5**: UI components via react-bootstrap for clean, responsive interface
- **WebSocket**: Real-time data updates pushed from server
- **axios**: HTTP client for REST API calls

### Infrastructure

- **Docker Compose**: Orchestrates InfluxDB and PostgreSQL containers
- **HTTPS**: TLS encryption with Let's Encrypt certificates
- **Single-server deployment**: All components run on one machine

---

## System Modules

### 1. Data Collection Module

**Responsibilities:**
- Provide SDKs for Python and C++ applications
- Collect system and application metrics automatically or manually
- Capture application logs
- Send data to AMS server via HTTP POST

**Python SDK:**
- pip-installable package
- Automatically collects system metrics using psutil (CPU percentage, memory usage, disk usage)
- Integrates with Python's logging module to capture and forward logs
- Buffers metrics in memory and flushes every 10 seconds
- Includes retry logic for network failures
- Configured via environment variables or config file

**C++ SDK:**
- Distributed as static library with header files
- Requires manual instrumentation for metrics (counters, gauges, timings)
- Thread-safe metric collection
- Sends data via HTTP POST using cpp-httplib or libcurl
- Fast linking without header-only compilation overhead

**Collected Metrics:**
- System: CPU percentage, memory used and available, disk usage
- Application: Custom counters (increments), gauges (current values), timings (durations)
- Logs: Level, timestamp, message, and flexible metadata

---

### 2. Data Ingestion Module

**Responsibilities:**
- Receive metrics and logs from SDKs via HTTP API
- Validate incoming data format and authentication
- Write data to appropriate databases

**API Endpoints:**
- POST to metrics endpoint receives JSON payload with metric data
- POST to logs endpoint receives JSON payload with log entries
- Each request authenticated via API key checked against PostgreSQL
- Input validation ensures required fields and correct data types

**Database Writers:**
- Metrics written to InfluxDB using influxdb-client library
- Logs written to PostgreSQL using asyncpg library
- Connection error handling with retry logic
- Direct writes without message queue for simplicity

---

### 3. Storage Module

**Responsibilities:**
- Persist all metrics and logs with appropriate retention policies
- Provide efficient query interface for dashboard
- Manage data lifecycle and cleanup

**InfluxDB Storage:**
- Stores time-series metrics with automatic compression
- Configurable 30-day retention policy
- Supports queries by time range, application ID, and metric name
- Built-in downsampling for older data

**PostgreSQL Storage:**
- Applications table: Stores app ID, name, API key, creation timestamp
- Logs table: Timestamp, level (DEBUG/INFO/WARN/ERROR), message, app ID, JSONB metadata
- Alert rules table: Metric name, threshold value, condition operator, notification email
- Alert history table: Triggered alerts with timestamp and metric value
- Automated cleanup job removes logs older than 30 days

---

### 4. Analytics Module

**Responsibilities:**
- Monitor metrics against configured thresholds
- Trigger notifications when thresholds are breached
- Track alert history

**Alert Checker:**
- Background job runs every 60 seconds via APScheduler
- Queries recent metrics from InfluxDB for all monitored applications
- Compares values against threshold rules stored in PostgreSQL
- Supports simple rules: single metric with single threshold (e.g., CPU greater than 80%)
- Creates alert record in PostgreSQL and triggers email notification when threshold breached

---

### 5. Notification Module

**Responsibilities:**
- Send email notifications when alerts trigger
- Maintain history of all sent notifications

**Email Notifier:**
- Uses Python smtplib or third-party service (SendGrid/Mailgun API)
- Sends formatted email with alert details to configured recipient
- Email addresses stored in PostgreSQL alert rules

**Alert History:**
- All triggered alerts stored in PostgreSQL alert_history table
- Dashboard displays recent alert history for review

---

### 6. API Module

**Responsibilities:**
- Provide REST API for dashboard queries and management operations
- Deliver real-time updates via WebSocket connection
- Automatic API documentation generation

**REST Endpoints:**
- POST /api/v1/metrics - Ingest metrics from SDKs
- POST /api/v1/logs - Ingest logs from SDKs
- GET /api/v1/metrics - Query metrics by time range and app ID
- GET /api/v1/logs - Search logs with filters
- GET /api/v1/applications - List all registered applications
- POST /api/v1/alerts - Create new alert rule
- GET /api/v1/alerts - List alert rules and history

**WebSocket Endpoint:**
- /ws/dashboard connection for real-time updates
- Server pushes new metrics and logs to connected dashboard clients as data arrives
- Reduces latency and eliminates polling overhead

---

### 7. Dashboard Module

**Responsibilities:**
- Display metrics as interactive charts
- Provide searchable log viewer
- Show active alerts and history
- Manage applications and alert rules

**Dashboard Pages (React with TypeScript):**
- **Metrics Page**: Line charts showing CPU, memory, and disk usage over time using Chart.js
- **Logs Page**: Searchable table with filters for log level, application, and time range
- **Alerts Page**: List of active alerts and historical alert events
- **Applications Page**: Registered applications with management interface
- Time range picker supporting 1 hour, 24 hours, and 7 days views

**Real-Time Updates:**
- WebSocket connection maintains live data feed from server
- Bootstrap 5 components for responsive, clean UI
- Loading states and error handling for network issues

---

### 8. Administration Module

**Responsibilities:**
- Register new applications and generate API keys
- Configure alert thresholds and notification rules
- Single admin user interface

**Application Management:**
- Registration form accepts application name and generates unique API key
- Application metadata stored in PostgreSQL
- Dashboard displays list of all registered applications

**Alert Configuration:**
- Web forms to create, edit, and delete alert rules
- Define which metric to monitor, threshold value, comparison operator, and notification email
- Rules stored in PostgreSQL and used by alert checker background job

---

## Data Flow

### Ingestion Flow
1. Application SDK collects metrics and logs from monitored application
2. SDK sends HTTP POST with JSON payload to FastAPI ingestion endpoint
3. FastAPI validates data and authenticates via API key
4. FastAPI writes metrics to InfluxDB and logs to PostgreSQL
5. FastAPI pushes updates to connected dashboard clients via WebSocket

### Alert Flow
1. APScheduler background job queries InfluxDB every 60 seconds for latest metrics
2. Alert checker compares metric values against threshold rules from PostgreSQL
3. When threshold breached: stores alert in alert_history table, sends email notification, pushes alert to dashboard via WebSocket

### Dashboard Flow
1. Dashboard loads and fetches initial historical data via REST API
2. WebSocket connection established for real-time updates
3. Charts and tables update automatically when new metrics and logs arrive

---

## Deployment Architecture

### Single-Server Setup

**Docker Compose Containers:**
- InfluxDB container with persistent volume for metrics storage
- PostgreSQL container with persistent volume for relational data

**FastAPI Server (single Python process):**
- Handles all ingestion and query REST endpoints
- WebSocket server for real-time dashboard updates
- Serves React dashboard as static files
- APScheduler background thread runs alert checking jobs
- Starts with single command

**React Dashboard:**
- TypeScript application built to static files
- Compiled files served by FastAPI
- No separate web server required

**Deployment Process:**
- Start databases with Docker Compose command
- Start FastAPI server with Python
- Access dashboard via browser on port 8000

**Server Requirements:**
- 4GB RAM minimum
- 2 CPU cores
- Supports monitoring 5-20 applications simultaneously

---

## Database Schemas

### InfluxDB Schema

**Measurement name**: metrics

**Fields:**
- value (floating-point number representing metric value)

**Tags:**
- app_id (application identifier)
- metric_name (e.g., cpu_percent, memory_used, fps)
- host (hostname or IP address)

**Timestamp**: Automatically generated by InfluxDB

### PostgreSQL Tables

**Applications Table:**
- app_id: Unique identifier (primary key)
- name: Human-readable application name
- api_key: Authentication key for SDK
- created_at: Registration timestamp

**Logs Table:**
- id: Auto-incrementing primary key
- app_id: Reference to application
- timestamp: When log was created
- level: DEBUG, INFO, WARN, or ERROR
- message: Log message text
- metadata: JSONB field for flexible additional data

**Alert Rules Table:**
- id: Auto-incrementing primary key
- app_id: Which application to monitor
- metric_name: Which metric to check (e.g., cpu_percent)
- threshold: Numeric threshold value
- condition: Comparison operator (greater than, less than, equals)
- notification_email: Where to send alerts
- enabled: Boolean to activate/deactivate rule

**Alert History Table:**
- id: Auto-incrementing primary key
- rule_id: Reference to alert_rules table
- triggered_at: When threshold was breached
- metric_value: The value that triggered the alert

---

## Non-Functional Requirements

**Performance:**
- Metric ingestion rate: 1,000 to 5,000 metrics per second
- Query response time: Under 1 second for dashboard requests
- Monitoring overhead: Less than 5% CPU and memory on monitored applications

**Scalability:**
- Supports 5 to 20 monitored applications
- Handles 1 to 5 concurrent dashboard users
- Single server deployment with 4GB RAM and 2 CPU cores

**Reliability:**
- 95% or higher uptime target
- 30-day retention for both metrics and logs
- Weekly automated database backups

**Security:**
- HTTPS encryption using Let's Encrypt certificates
- API key authentication for all SDK requests
- Single admin user (no multi-user support)

---

## Target Applications

**Python Snake Game:**
- System metrics: CPU, memory, disk usage
- Custom game metrics: player score, snake length, game duration
- Log events: game start, game over, collision events

**C++ Terrain Simulation:**
- Performance metrics: frames per second, frame render time
- Memory metrics: allocated memory, texture memory usage
- Log events: rendering errors, performance warnings

---

## SDK Integration

### Python SDK Integration

Applications import the AMSClient class from the ams-sdk package. Initialize the client with API URL, application ID, and API key. System metrics are automatically collected and sent. Python logging output is automatically captured and forwarded. Custom metrics can be recorded using increment (for counters), gauge (for current values), and timing (for durations) methods.

### C++ SDK Integration

Applications include the ams_sdk header file and link against the static library. Create a Client instance with API URL, application ID, and API key. Manually instrument code to record metrics using gauge and timing methods. The SDK handles HTTP communication and thread-safe metric collection.

---

**Last Updated:** January 26, 2026
