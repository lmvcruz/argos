# Anvil Data Handling Documentation Index

## Overview

This documentation explains how Anvil processes, stores, queries, and visualizes parsed data from CI tools, and how Verdict validates this parsing.

---

## Core Documents

### 1. **ANVIL_COMPLETE_OVERVIEW.md**
**Best for**: Quick understanding of the entire system

- ✓ Quick summary of how data flows
- ✓ Answers the three key questions
- ✓ Complete architecture overview
- ✓ Data models explained
- ✓ Database schema (simplified)
- ✓ API endpoints listed
- ✓ Decision tree for choosing methods
- **Read this first** if you want a complete picture

### 2. **ANVIL_DATA_FLOW_GUIDE.md**
**Best for**: Deep technical understanding

- ✓ Detailed part-by-part explanation
- ✓ How Anvil handles parsed data
- ✓ Two database types (ExecutionDatabase vs StatisticsDatabase)
- ✓ Data persistence mechanisms
- ✓ Complete Verdict → Anvil integration flow
- ✓ Test case structure explained
- ✓ Programmatic access examples
- **Read this** when you want to understand each component in detail

### 3. **ANVIL_ARCHITECTURE_VISUAL.md**
**Best for**: Visual learners

- ✓ Complete pipeline diagram
- ✓ Detailed Verdict execution flow
- ✓ Data structure transformations
- ✓ Step-by-step execution walkthrough
- ✓ Three methods to access parsed data
- **Read this** if you prefer visual representations with ASCII diagrams

### 4. **ANVIL_PRACTICAL_GUIDE.md**
**Best for**: Implementation and code examples

- ✓ Working code examples for all scenarios
- ✓ How to use Anvil parsers directly
- ✓ How to query the database
- ✓ How to access via Verdict adapters
- ✓ How to access via REST API
- ✓ JavaScript/React examples
- ✓ Common scenarios with code
- **Read this** when you need code you can copy and adapt

---

## Quick Navigation by Use Case

### "I want to parse tool output immediately"
→ **ANVIL_PRACTICAL_GUIDE.md** → Section 1: Using Anvil Parsers Directly

### "I want to store parsed data and query it later"
→ **ANVIL_PRACTICAL_GUIDE.md** → Section 2: Querying Anvil Database

### "I want to understand how Verdict validates parsing"
→ **ANVIL_DATA_FLOW_GUIDE.md** → Part 2: How Verdict Calls Anvil & Retrieves Data

### "I want to visualize parsed data"
→ **ANVIL_COMPLETE_OVERVIEW.md** → Section "How can we visualize the parsed data?"

### "I want to see database schema details"
→ **ANVIL_DATA_FLOW_GUIDE.md** → Part 1.3: Storage Layer - Two Database Types

### "I want to build a REST API endpoint"
→ **ANVIL_PRACTICAL_GUIDE.md** → Section 4: Accessing via REST API

### "I want to build a React component"
→ **ANVIL_PRACTICAL_GUIDE.md** → Section 4: Accessing via REST API (JavaScript examples)

### "I want a complete end-to-end example"
→ **ANVIL_ARCHITECTURE_VISUAL.md** → "Verdict Execution Flow (Detailed)" section

---

## Documentation Map

```
ANVIL_COMPLETE_OVERVIEW.md (Start Here)
├─ Quick Summary
├─ Three Core Questions Answered
├─ Architecture Components
├─ Data Models
├─ Complete Example
├─ Database Schema
├─ API Endpoints
├─ Usage Patterns
├─ Decision Tree
└─ Summary Table

ANVIL_DATA_FLOW_GUIDE.md (Deep Dive)
├─ Part 1: How Anvil Handles Parsed Data
│  ├─ Data Flow (Input → Parse → Store)
│  ├─ Parsing Layer
│  ├─ Storage Layer (ExecutionDatabase vs StatisticsDatabase)
│  ├─ Data Persistence
│  └─ Query Methods
├─ Part 2: How Verdict Calls Anvil
│  ├─ Integration Flow
│  ├─ Configuration
│  ├─ Adapter Functions
│  ├─ Executor Implementation
│  ├─ Validator Comparison
│  └─ Test Case Structure
├─ Part 3: Visualizing Parsed Data
│  ├─ Query Methods Available
│  ├─ Programmatic Access
│  ├─ REST API Access
│  └─ Frontend Visualization
└─ Part 4: Complete Example
   └─ Black Parser Flow

ANVIL_ARCHITECTURE_VISUAL.md (Visual Understanding)
├─ Complete Data Journey (Tier by Tier)
├─ Verdict Execution Flow (Detailed Step-by-Step)
├─ How Verdict Gets Parsed Data from Anvil
└─ Data Structure Example Walkthrough

ANVIL_PRACTICAL_GUIDE.md (Code & Examples)
├─ 0. Using Anvil CLI Parse Command
│  ├─ What is the Parse Command?
│  ├─ Basic Usage
│  ├─ Supported Tools
│  ├─ Examples
│  ├─ Output Format
│  └─ Use Cases
├─ 1. Using Anvil Parsers Directly
│  ├─ Parsing Black Output
│  ├─ Parsing Flake8 Output
│  └─ Parsing isort Output
├─ 2. Querying Anvil Database
│  ├─ Basic Setup
│  ├─ Get All Validation Runs
│  ├─ Get Tests for a Run
│  ├─ Get Lint Results
│  ├─ Get Coverage Data
│  ├─ Get Validator Results
│  └─ Advanced Queries
├─ 3. Accessing via Verdict Adapters
│  ├─ Using Adapters Programmatically
│  └─ Using Adapters with Verdict
├─ 4. Accessing via REST API
│  ├─ Setup Backend
│  ├─ Available Endpoints
│  ├─ Example JavaScript Calls
│  └─ Example React Component
└─ 5. Common Scenarios
   ├─ Scenario 1: Process Immediately
   ├─ Scenario 2: Store & Query
   ├─ Scenario 3: Validate Output
   ├─ Scenario 4: Build a Report
   └─ Scenario 5: Monitor Trends
```

---

## Key Concepts

### Parsing
**What**: Converting raw tool output (string) to structured data (object)
**Where**: `anvil/parsers/`
**Example**: `LintParser.parse_flake8_output(text)` → `LintData` object

### Storage
**What**: Saving parsed data to SQLite database
**Where**: `anvil/storage/`
**Table Types**:
- `validation_runs` - Run metadata
- `test_case_records` - Test results
- `lint_summary` - Lint aggregates
- `lint_violations` - Detailed violations
- `coverage_summary` - Coverage stats

### Validation
**What**: Comparing actual parsed output with expected output
**Where**: `verdict/`
**Tool**: `OutputValidator.validate(actual, expected)` → `(bool, differences)`

### Adaptation
**What**: Converting parsed data to dictionaries for Verdict
**Where**: `anvil/validators/adapters.py`
**Contract**: `str → dict` (string input, dictionary output)

### Querying
**What**: Retrieving stored parsed data from database
**Where**: `anvil/storage/statistics_queries.py`
**API**: `StatisticsQueryEngine.get_*()`

### Exposure
**What**: Making parsed data accessible via web API
**Where**: `lens/backend/server.py`
**Protocol**: REST API endpoints (`GET /api/...`)

### Visualization
**What**: Displaying parsed data in a user interface
**Where**: `lens/frontend/`
**Framework**: React components

---

## Common Code Patterns

### Pattern 1: Parse & Use Immediately
```python
from anvil.parsers.lint_parser import LintParser
parser = LintParser()
result = parser.parse_flake8_output(tool_output, Path("."))
# Use result immediately
```
**Document**: ANVIL_PRACTICAL_GUIDE.md - Section 1

### Pattern 2: Parse, Store, Query Later
```python
# Save
persistence.save_lint_summary(parsed_data)

# Query
query_engine.get_lint_violations(run_id=1)
```
**Document**: ANVIL_PRACTICAL_GUIDE.md - Section 2

### Pattern 3: Validate with Verdict
```python
actual = validate_flake8_parser(tool_output)
expected = load_expected_output()
is_valid, diffs = validator.validate(actual, expected)
```
**Document**: ANVIL_PRACTICAL_GUIDE.md - Section 3

### Pattern 4: Access via REST API
```javascript
const data = await fetch('/api/validation/runs/{id}/lint')
  .then(res => res.json());
```
**Document**: ANVIL_PRACTICAL_GUIDE.md - Section 4

---

## File References

| Component | File | Purpose |
|-----------|------|---------|
| Parsing | `anvil/parsers/lint_parser.py` | Parse tool outputs |
| Storage (Schema) | `anvil/storage/statistics_database.py` | Database tables |
| Storage (Persistence) | `anvil/storage/statistics_persistence.py` | Save data |
| Storage (Query) | `anvil/storage/statistics_queries.py` | Retrieve data |
| Validation | `anvil/validators/adapters.py` | Convert to dicts |
| Verdict | `verdict/executor.py` | Call adapters |
| Verdict | `verdict/validator.py` | Compare outputs |
| Verdict | `verdict/runner.py` | Orchestrate tests |
| REST API | `lens/backend/server.py` | Expose endpoints |
| Frontend | `lens/frontend/src/` | Display data |

---

## Reading Order Recommendations

### For Quick Start (15 minutes)
1. ANVIL_COMPLETE_OVERVIEW.md - Read sections:
   - Quick Summary
   - Three Core Questions Answered
   - Decision Tree: Which Method to Use

### For Understanding Flow (30 minutes)
1. ANVIL_ARCHITECTURE_VISUAL.md - Read:
   - Complete Data Journey
   - Verdict Execution Flow
2. ANVIL_COMPLETE_OVERVIEW.md - Read:
   - Architecture Components
   - Complete Example

### For Implementation (1 hour)
1. ANVIL_PRACTICAL_GUIDE.md - Choose relevant sections based on use case
2. Copy code examples and adapt
3. Refer back to other docs for clarification

### For Complete Mastery (2-3 hours)
1. Start with ANVIL_COMPLETE_OVERVIEW.md
2. Deep dive with ANVIL_DATA_FLOW_GUIDE.md
3. Visual understanding with ANVIL_ARCHITECTURE_VISUAL.md
4. Practical examples with ANVIL_PRACTICAL_GUIDE.md

---

## FAQ

**Q: Can I use just the parser without the database?**
A: Yes! Use the parser directly. See ANVIL_PRACTICAL_GUIDE.md Section 1.

**Q: How do I query the database?**
A: Use StatisticsQueryEngine. See ANVIL_PRACTICAL_GUIDE.md Section 2.

**Q: How does Verdict get data from Anvil?**
A: Through adapters. See ANVIL_DATA_FLOW_GUIDE.md Part 2.

**Q: How do I expose parsed data to a frontend?**
A: Via REST API. See ANVIL_PRACTICAL_GUIDE.md Section 4.

**Q: What's the difference between ExecutionDatabase and StatisticsDatabase?**
A: ExecutionDatabase tracks execution history for selective execution. StatisticsDatabase stores parsed results. See ANVIL_DATA_FLOW_GUIDE.md Part 1.3.

**Q: Can I visualize data without running Lens backend?**
A: Yes, query the database directly in Python. See ANVIL_PRACTICAL_GUIDE.md Section 2.

---

## Additional Resources

- **Source Code**: See file references table above
- **Test Examples**: `anvil/tests/` and `verdict/tests/`
- **Test Cases**: `anvil/tests/validation/cases/`
- **Configuration**: `anvil/tests/validation/config.yaml`

---

## Document Status

- ✅ ANVIL_COMPLETE_OVERVIEW.md - Complete
- ✅ ANVIL_DATA_FLOW_GUIDE.md - Complete
- ✅ ANVIL_ARCHITECTURE_VISUAL.md - Complete
- ✅ ANVIL_PRACTICAL_GUIDE.md - Complete
- ✅ This index document - Complete

Last updated: 2026-02-05
