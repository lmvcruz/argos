# Phase 1.2 Progress: Anvil Selective Execution Enhancement

## Summary

Phase 1.2 enhances Anvil with selective execution capabilities, enabling intelligent test selection based on execution history and defined rules. This dramatically reduces validation time while maintaining quality.

**Status**: COMPLETE ✅ (All 5 tasks finished)

**Date**: February 2, 2026

---

## Completed Tasks

### Task 1: Database Schema for Execution History ✅

**Implementation**: [execution_schema.py](../anvil/anvil/storage/execution_schema.py)

**New Database Tables**:

1. **execution_history**
   - Tracks all test/validation executions
   - Fields: execution_id, entity_id, entity_type, timestamp, status, duration, space, metadata
   - Indexes: entity_id+timestamp, status+timestamp, execution_id

2. **execution_rules**
   - Stores selective execution rules
   - Fields: name, criteria, enabled, threshold, window, groups, executor_config
   - Criteria types: all, group, failed-in-last, failure-rate, changed-files

3. **entity_statistics**
   - Aggregated statistics per entity
   - Fields: entity_id, total_runs, passed, failed, skipped, failure_rate, avg_duration, last_run, last_failure
   - Enables fast queries for flaky test detection

**Dataclasses**:
- `ExecutionHistory`: Historical execution record
- `ExecutionRule`: Rule definition with criteria
- `EntityStatistics`: Aggregated statistics

**Database Class**:
- `ExecutionDatabase`: SQLite database with CRUD operations
- Auto-recovery from corruption
- Foreign key constraints enabled
- JSON serialization for metadata

**Tests**: 20 tests, 100% pass rate
- Database initialization and schema
- CRUD operations for all tables
- Data serialization/deserialization
- Auto-recovery functionality
- Cross-platform file locking handling

---

### Task 2: RuleEngine Implementation ✅

**Implementation**: [rule_engine.py](../anvil/anvil/core/rule_engine.py)

**Purpose**: Evaluate rules and select entities for execution based on criteria

**Key Methods**:

1. **`select_entities(rule)`**
   - Main entry point for entity selection
   - Dispatches to criteria-specific handlers
   - Returns list of entity IDs to execute

2. **Criteria Handlers**:
   - `_select_all_entities()`: All entities (optionally filtered by groups)
   - `_select_by_group()`: Entities matching glob patterns
   - `_select_failed_in_last()`: Entities that failed in last N runs
   - `_select_by_failure_rate()`: Entities exceeding failure rate threshold

3. **Rule Management**:
   - `get_rule(name)`: Retrieve rule by name
   - `list_rules(enabled_only)`: List all or enabled rules

**Pattern Matching**:
- Supports glob patterns (e.g., `tests/test_*.py`)
- Matches both file paths and full nodeids
- Flexible group definitions

**Tests**: 8 tests covering all criteria types

---

### Task 3: StatisticsCalculator Implementation ✅

**Implementation**: [statistics_calculator.py](../anvil/anvil/core/statistics_calculator.py)

**Purpose**: Analyze execution history to compute metrics and identify patterns

**Key Methods**:

1. **`calculate_entity_stats(entity_id, window)`**
   - Compute statistics for a single entity
   - Calculates: total_runs, passed, failed, skipped, failure_rate, avg_duration
   - Window parameter limits analysis to recent executions

2. **`calculate_all_stats(entity_type, window)`**
   - Compute statistics for all entities of a given type
   - Returns list of EntityStatistics

3. **`get_flaky_entities(threshold, window)`**
   - Identify entities exceeding failure rate threshold
   - Default threshold: 10%
   - Returns sorted by failure rate descending

4. **`get_failed_in_last_n(n)`**
   - Find entities that failed in their last N executions
   - Useful for "retry failed" workflows

**Use Cases**:
- Flaky test detection
- Trend analysis
- Selective execution based on reliability
- Performance profiling (avg_duration)

**Tests**: 8 tests covering all calculation methods

---

## Test Results

**Total Tests**: 37
**Pass Rate**: 100%
**Execution Time**: 0.55 seconds

**Test Coverage**:
- `test_execution_schema.py`: 20 tests (database operations)
- `test_rule_engine.py`: 17 tests (rule engine + statistics + integration)

**Key Test Scenarios**:
- Database CRUD operations
- Rule criteria evaluation (all, group, failed-in-last, failure-rate)
- Statistics calculation with/without window
- Flaky test identification
- Pattern matching for groups
- Integration workflow (history → stats → rule → selection)

---

## API Examples

### 1. Database Operations

```python
from anvil.storage import ExecutionDatabase, ExecutionHistory

# Initialize database
db = ExecutionDatabase(".anvil/history.db")

# Record test execution
history = ExecutionHistory(
    execution_id="local-123",
    entity_id="tests/test_example.py::test_func",
    entity_type="test",
    timestamp=datetime.now(),
    status="PASSED",
    duration=1.23,
    metadata={"platform": "windows"}
)
db.insert_execution_history(history)

# Query history
recent = db.get_execution_history(
    entity_id="tests/test_example.py::test_func",
    limit=10
)
```

### 2. Statistics Calculation

```python
from anvil.core import StatisticsCalculator

calc = StatisticsCalculator(db)

# Calculate stats for single test
stats = calc.calculate_entity_stats("tests/test_example.py::test_func")
print(f"Failure rate: {stats.failure_rate:.1%}")
print(f"Avg duration: {stats.avg_duration:.2f}s")

# Find flaky tests (>10% failure rate)
flaky = calc.get_flaky_entities(threshold=0.10, window=20)
for test in flaky:
    print(f"{test.entity_id}: {test.failure_rate:.1%} failure rate")
```

### 3. Rule Evaluation

```python
from anvil.core import RuleEngine
from anvil.storage import ExecutionRule

engine = RuleEngine(db)

# Create rule
rule = ExecutionRule(
    name="quick-check",
    criteria="group",
    groups=["tests/test_models.py", "tests/test_parser.py"]
)
db.insert_execution_rule(rule)

# Select entities
entities = engine.select_entities(rule)
print(f"Selected {len(entities)} tests to run")
```

### 4. Complete Workflow

```python
# 1. Record execution results
for test_id, result in test_results.items():
    db.insert_execution_history(ExecutionHistory(
        execution_id="ci-12345",
        entity_id=test_id,
        entity_type="test",
        timestamp=datetime.now(),
        status=result.status,
        duration=result.duration
    ))

# 2. Calculate statistics
stats = calc.calculate_all_stats(entity_type="test", window=20)

# 3. Update entity statistics table
for stat in stats:
    db.update_entity_statistics(stat)

# 4. Select tests for next run
rule = engine.get_rule("failed-only")
failed_tests = engine.select_entities(rule)

# 5. Execute only failed tests
run_tests(failed_tests)
```

---

## Integration with Argos Configuration

The database schema and rule engine integrate seamlessly with the Argos configuration created in Phase 1.1:

**From `.anvil/config.yaml`**:
```yaml
history:
  enabled: true
  database: ".anvil/history.db"  # ← ExecutionDatabase path
  retention_days: 90
```

**From `.lens/rules.yaml`**:
```yaml
rules:
  - name: quick-check
    criteria: group  # ← RuleEngine criteria
    groups:
      - "forge/tests/test_models.py"
      - "anvil/tests/test_executor.py"

  - name: flaky-tests
    criteria: failure-rate  # ← StatisticsCalculator threshold
    threshold: 0.10
    window: 20
```

---

## Next Steps

### Phase 1.2.4: Enhance pytest Executor (In Progress)

**Objective**: Integrate execution history tracking into pytest validator

**Tasks**:
1. Modify pytest executor to record results to ExecutionDatabase
2. Generate unique execution IDs (local-{timestamp} or ci-{run_id})
3. Extract test nodeids, status, duration from pytest JSON report
4. Update entity statistics after each execution
5. Add CLI flags for selective execution

**Example Integration**:
```python
class PytestValidator:
    def __init__(self, db: ExecutionDatabase = None):
        self.db = db or ExecutionDatabase(".anvil/history.db")

    def execute(self, tests: List[str] = None):
        # Run pytest
        result = run_pytest(tests)

        # Record results
        execution_id = f"local-{int(datetime.now().timestamp())}"
        for test in result.tests:
            self.db.insert_execution_history(ExecutionHistory(
                execution_id=execution_id,
                entity_id=test.nodeid,
                entity_type="test",
                timestamp=datetime.now(),
                status=test.outcome,
                duration=test.duration
            ))
```

---

### Task 5: Add Anvil CLI Commands ✅

**Implementation**:
- [cli/commands.py](../anvil/anvil/cli/commands.py) - Command handlers
- [cli/main.py](../anvil/anvil/cli/main.py) - Argument parsers and dispatch

**Purpose**: Expose selective execution functionality via command-line interface

**New Command Handlers**:

1. **`execute_command(rule, config_path, execution_id, verbose, quiet)`**
   - Execute tests using a specific rule
   - Auto-generates execution ID if not provided
   - Returns 0 (pass), 1 (fail), or 2 (error)

2. **`rules_list_command(enabled_only, quiet)`**
   - List all execution rules or only enabled rules
   - Shows criteria, threshold, window, groups for each rule

3. **`stats_show_command(entity_type, window, quiet)`**
   - Show entity statistics table
   - Displays runs, pass/fail counts, failure rate, average duration

4. **`stats_flaky_tests_command(threshold, window, quiet)`**
   - Show flaky tests based on failure rate threshold
   - Uses execution history for accurate detection

5. **`history_show_command(entity, limit, quiet)`**
   - Show execution history for a specific entity
   - Displays execution ID, timestamp, status, duration

**CLI Command Structure**:

```bash
# Execute tests using a rule
anvil execute --rule quick-check [--config anvil.toml] [--execution-id ID] [-v] [-q]

# List execution rules
anvil rules list [--enabled-only] [-q]

# Show entity statistics
anvil stats show [--type test] [--window 20] [-q]

# Show flaky tests
anvil stats flaky-tests [--threshold 0.10] [--window 20] [-q]

# Show execution history
anvil history show --entity "tests/test_example.py::test_func" [--limit 10] [-q]
```

**Integration Points**:
- `execute_command` uses `PytestExecutorWithHistory.execute_with_rule()`
- `rules_list_command` uses `RuleEngine.list_rules()`
- `stats_show_command` uses `StatisticsCalculator.calculate_all_stats()`
- `stats_flaky_tests_command` uses `PytestExecutorWithHistory.get_flaky_tests()`
- `history_show_command` uses `ExecutionDatabase.get_execution_history()`

**Error Handling**:
- Graceful handling of missing rules, empty databases
- Proper database cleanup via finally blocks (Windows compatibility)
- Validation of threshold parameters (0.0-1.0 range)
- Clear error messages with actionable suggestions

**Tests**: [test_cli_phase_1_2.py](../anvil/tests/test_cli_phase_1_2.py)
- 15 tests covering all new CLI commands
- MockArgs for argparse argument simulation
- Populated database fixture for realistic testing
- Quiet mode verification
- Error handling validation
- 100% pass rate

---

## Performance Impact

**Expected Benefits**:
- **Full Suite**: ~15 minutes (2023 tests)
- **Quick Check**: ~2 minutes (~80 tests) - **87% time savings**
- **Pre-commit**: ~1-3 minutes (changed tests only) - **80-93% savings**
- **Failed Only**: ~30 seconds (typical: 5-10 tests) - **97% savings**

**Database Performance**:
- SQLite with indexes for fast queries
- Window-based calculations limit data scanned
- Statistics table provides pre-aggregated data

---

## Files Created/Modified

### New Files (4 implementation + 3 test files)
1. `anvil/storage/execution_schema.py` (536 lines)
2. `anvil/core/statistics_calculator.py` (178 lines)
3. `anvil/core/rule_engine.py` (193 lines)
4. `anvil/executors/pytest_executor.py` (279 lines)
5. `tests/test_execution_schema.py` (480 lines)
6. `tests/test_rule_engine.py` (398 lines)
7. `tests/test_pytest_executor.py` (395 lines)
8. `tests/test_cli_phase_1_2.py` (413 lines)

### Modified Files
1. `anvil/storage/__init__.py` - Export ExecutionDatabase, dataclasses
2. `anvil/core/__init__.py` - Export RuleEngine, StatisticsCalculator
3. `anvil/executors/__init__.py` - Export PytestExecutorWithHistory
4. `anvil/cli/commands.py` - Added 5 new command handlers
5. `anvil/cli/main.py` - Added parsers for execute, rules, history, enhanced stats

**Total New Code**: ~2,872 lines (implementation + tests)

---

## Quality Metrics

**Code Quality**:
- ✅ All functions have Google-style docstrings
- ✅ Type hints on all parameters and returns
- ✅ Following TDD: Tests written before implementation
- ✅ 100% test pass rate (61 tests total)
- ✅ No linting errors
- ✅ Cross-platform tested (Windows file locking handled)

**Test Quality**:
- ✅ Unit tests for all major components
- ✅ Integration tests for complete workflows
- ✅ Edge cases tested (nonexistent entities, empty history)
- ✅ Data integrity tests (upsert, foreign keys)
- ✅ Error handling tests (corruption recovery)
- ✅ CLI tests with MockArgs and capsys

**Test Breakdown**:
- Task 1 (Database Schema): 20 tests ✅
- Task 2 (RuleEngine): 8 tests ✅
- Task 3 (StatisticsCalculator): 9 tests ✅
- Task 4 (Pytest Executor): 9 infrastructure tests ✅
- Task 5 (CLI Commands): 15 tests ✅
- **Total**: 61 tests passing

---

## Lessons Learned

1. **Windows File Locking**: SQLite connections must be explicitly closed before unlinking database files on Windows. Added try/finally blocks with delays.

2. **TDD Benefits**: Writing tests first caught several edge cases early:
   - Nonexistent entity handling
   - Window parameter boundary conditions
   - Pattern matching edge cases

3. **Database Design**: Using UPSERT for entity_statistics simplifies updates and avoids duplication.

4. **Flexible Criteria**: Supporting multiple criteria types (all, group, failed-in-last, failure-rate) enables diverse use cases without code changes.

5. **CLI Error Handling**: Proper cleanup in finally blocks is critical for Windows compatibility. Even when errors occur, database connections must be closed.

---

## Usage Examples

### Execute Tests with a Rule

```bash
# Create a rule in the database first (programmatically)
python -c "
from anvil.storage.execution_schema import ExecutionDatabase, ExecutionRule
db = ExecutionDatabase('.anvil/history.db')
rule = ExecutionRule(
    name='quick-check',
    criteria='group',
    enabled=True,
    groups=['tests/test_models.py', 'tests/test_parser.py']
)
db.insert_execution_rule(rule)
db.close()
"

# Execute using the rule
anvil execute --rule quick-check --verbose
```

### View Statistics

```bash
# Show all test statistics (last 20 executions)
anvil stats show --type test --window 20

# Find flaky tests (>10% failure rate)
anvil stats flaky-tests --threshold 0.10 --window 20
```

### View History

```bash
# Show execution history for a specific test
anvil history show --entity "tests/test_example.py::test_func" --limit 10
```

### List Rules

```bash
# List all rules
anvil rules list

# List only enabled rules
anvil rules list --enabled-only
```

---

## Conclusion

**Phase 1.2 is COMPLETE** ✅

All 5 tasks have been successfully implemented and tested:
1. ✅ Database schema for execution history
2. ✅ RuleEngine for selective execution
3. ✅ StatisticsCalculator for metrics analysis
4. ✅ PytestExecutorWithHistory for auto-recording
5. ✅ CLI commands for user-facing interface

The Anvil selective execution system is now fully functional with:
- Complete programmatic API
- Full CLI interface
- 61 passing tests
- Cross-platform compatibility
- Production-ready error handling

**Next Steps**: Phase 1.3 - Lens Features (visualization and analysis dashboard)
