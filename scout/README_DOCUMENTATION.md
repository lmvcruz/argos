# Scout CLI Documentation Index

Welcome to Scout! This document is your entry point to all Scout CLI documentation.

---

## Quick Links

**I want to...**

- **Use Scout immediately** → [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md)
- **Understand the architecture** → [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md)
- **Learn detailed usage** → [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md)
- **See what changed** → [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md)
- **Know implementation status** → [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

---

## Documentation Overview

### 1. 🚀 [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md)
**For: Getting started quickly**
- 2-5 minute read
- Command cheat sheet
- Common workflows
- Parameter reference
- Troubleshooting

**When to use:** You need quick answers and examples

---

### 2. 📚 [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md)
**For: Comprehensive learning**
- 15-20 minute read
- Detailed reference for all commands
- Practical workflow examples
- Tips and best practices
- Error handling guide

**When to use:** You want to understand everything deeply

---

### 3. 🏗️ [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md)
**For: Understanding design**
- 20-30 minute read
- Complete 4-stage pipeline explanation
- Case identification model
- Database schema
- Design decisions

**When to use:** You're implementing features or contributing

---

### 4. 🔄 [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md)
**For: Migration and understanding improvements**
- 10-15 minute read
- Old vs new architecture comparison
- Parameter changes
- Feature improvements
- Migration path

**When to use:** You used old Scout and want to understand changes

---

### 5. ✅ [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)
**For: Technical details**
- 20-25 minute read
- What was implemented
- What's still TODO
- Testing results
- Design decisions

**When to use:** You're contributing or managing the project

---

## Scout in 60 Seconds

Scout is a CI/CD log analysis tool with three commands:

### `scout fetch` - Get logs
```bash
scout fetch --workflow-name "Tests" --run-id 12345 --job-id abc
```

### `scout parse` - Analyze logs
```bash
scout parse --input logs.txt
```

### `scout sync` - Do both (NEW!)
```bash
scout sync --fetch-last 5 --workflow-name "Tests"
```

That's it! For more, see [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md)

---

## Architecture in 60 Seconds

Scout has a **4-stage pipeline**:

```
Stage 1: FETCH       Download logs from GitHub
    ↓
Stage 2: SAVE-CI     Store raw logs in database
    ↓
Stage 3: PARSE       Transform using Anvil parsers
    ↓
Stage 4: SAVE-ANALYSIS  Store results in analysis database
```

Each stage can:
- Run independently
- Be skipped with `--skip-*` flags
- Have flexible input/output

For more, see [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md)

---

## Reading Guide by Role

### 👤 **End User** (Using Scout)
1. Start: [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md) (5 min)
2. Deep dive: [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md) (20 min)
3. Troubleshooting: See section in User Guide

**Total time: 25 minutes**

---

### 🔧 **Developer** (Contributing code)
1. Start: [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md) (25 min)
2. Understand status: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) (20 min)
3. Review code: `scout/scout/cli.py` (lines 830-1034)
4. Check tests: `scout/tests/` directory

**Total time: 1 hour**

---

### 📊 **Project Manager** (Tracking progress)
1. Current status: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) section "Implementation Status"
2. What changed: [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md)
3. Next steps: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) section "Next Steps for Implementation"

**Total time: 15 minutes**

---

### 🚀 **Migrating from Old Scout**
1. What changed: [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md) (15 min)
2. Learn new syntax: [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md) (20 min)
3. Quick reference: Keep [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md) handy

**Total time: 35 minutes + ongoing reference**

---

## Key Features of New Scout

✅ **Standardized Parameters**
- Consistent naming: `--workflow-name`, `--run-id`, `--job-id`
- Same parameters across all commands
- No confusion about what to pass where

✅ **Dual Identifiers**
- Use numeric IDs: `--run-id 12345`
- Or human-readable: `--execution-number "21"`
- Scout automatically maps both

✅ **Flexible I/O**
- Output to stdout, file, or database
- Input from file or database
- Choose what's best for your workflow

✅ **Pipeline Control**
- Run individual stages
- Or run complete pipeline with `sync`
- Skip stages selectively with `--skip-*` flags

✅ **Batch Processing**
- `--fetch-all` - Get everything
- `--fetch-last N` - Get recent executions
- Process multiple runs in one command

✅ **Clear Error Messages**
- No silent failures
- Actionable error messages
- Suggestions for fixes

---

## Common Questions

### Q: Where is the "scout" command?
**A:** The entry point is enabled in `pyproject.toml`.
- Works: `python scout/cli.py` or `python -m scout`
- Pending: Global `scout` command (Windows permission issue)

See [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) for details.

### Q: What's new in this version?
**A:** Complete CLI redesign with:
- New `scout sync` command
- Standardized parameters
- Dual identifiers
- Skip flags for flexibility

See [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md).

### Q: Can I still use the old commands?
**A:** Yes! They still work with a deprecation warning.
Old code is kept in `scout/cli.py` for backwards compatibility.

### Q: How do I get started?
**A:** Three options:

**Fastest (5 min):**
```bash
scout sync --fetch-last 5 --workflow-name "Tests"
```

**Quick (10 min):**
Read [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md)

**Thorough (30 min):**
Read [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md)

### Q: What's the pipeline again?
**A:** Four stages:
1. **FETCH** - Download logs from GitHub
2. **SAVE-CI** - Store raw logs
3. **PARSE** - Transform with Anvil
4. **SAVE-ANALYSIS** - Store results

Run one command: `scout sync --fetch-last 5`

---

## Implementation Status

| Component | Status | Details |
|-----------|--------|---------|
| CLI Structure | ✅ Complete | Commands, parameters, parsing done |
| Handler Stubs | ✅ Complete | Placeholder functions ready for implementation |
| GitHub Integration | ❌ TODO | Needed for fetch stage |
| Database Layer | ❌ TODO | Needed for save stages |
| Anvil Parser | ❌ TODO | Needed for parse stage |
| Tests | ❌ TODO | Need comprehensive test suite |

See [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) for complete details.

---

## File Organization

```
scout/
├── README.md                          [Main project README]
├── SCOUT_CLI_QUICK_REFERENCE.md      [THIS INDEX - Start here!]
├── SCOUT_CLI_USER_GUIDE.md           [Detailed guide]
├── SCOUT_ARCHITECTURE.md             [Architecture reference]
├── BEFORE_AFTER_COMPARISON.md        [Migration guide]
├── IMPLEMENTATION_SUMMARY.md         [Technical details]
├── scout/
│   ├── cli.py                        [Main CLI code]
│   │   ├── Lines 225-390: Parser setup for fetch/parse/sync
│   │   ├── Lines 830-883: handle_fetch_command_v2()
│   │   ├── Lines 884-937: handle_parse_command_v2()
│   │   └── Lines 939-1034: handle_sync_command()
│   ├── models.py                     [Case identification model]
│   └── storage/
│       ├── __init__.py
│       └── schema.py
├── tests/
│   └── [test files]
└── pyproject.toml                    [Entry point enabled here]
```

---

## Getting Help

### For Usage Questions
→ See [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md)

### For Architecture Questions
→ See [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md)

### For Implementation Details
→ See [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

### For Quick Answers
→ See [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md)

### For Troubleshooting
→ Search troubleshooting section in [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md)

---

## Quick Command Reference

```bash
# List all commands
scout --help

# Get help for specific command
scout fetch --help
scout parse --help
scout sync --help

# One-command pipeline
scout sync --fetch-last 5 --workflow-name "Tests"

# Step-by-step
scout fetch --workflow-name "Tests" --run-id 12345 --save-ci
scout parse --workflow-name "Tests" --run-id 12345 --save-analysis

# File-based
scout fetch --workflow-name "Tests" --run-id 12345 --output logs.txt
scout parse --input logs.txt --output results.json
```

---

## Version Information

- **Scout Version**: 0.1.0 (with 0.2.0 CLI architecture)
- **Python**: 3.8+
- **Architecture**: 4-stage pipeline with skip flags
- **Documentation Updated**: February 5, 2026

---

## Next Steps

1. **For immediate use**: Go to [SCOUT_CLI_QUICK_REFERENCE.md](./SCOUT_CLI_QUICK_REFERENCE.md)
2. **For deep learning**: Go to [SCOUT_CLI_USER_GUIDE.md](./SCOUT_CLI_USER_GUIDE.md)
3. **For implementation**: Go to [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md)
4. **For migration**: Go to [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md)

---

**Happy Scouting! 🔍**
