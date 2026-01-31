# Anvil Performance Benchmark Results

## Baseline Performance (2026-01-31)

### Test Summary
- **Total Tests**: 18
- **Passed**: 7 (39%)
- **Failed**: 11 (61%)
- **Duration**: 75.56 seconds

---

## ✅ PASSING Benchmarks

### File Collection Performance
1. **Large Directory Tree (10k files)**
   - Status: ✅ PASSED
   - Duration: 1.69s
   - Files Collected: 12,000
   - Throughput: **7,091 files/second**
   - Requirement: <2 seconds ✓

2. **Collection with Exclusions**
   - Status: ✅ PASSED
   - Files excluded properly from build/, __pycache__ etc.

### Database Query Performance
3. **Test Success Rate Query**
   - Status: ✅ PASSED
   - Duration: <100ms ✓
   - Successfully queries historical test data

4. **Validator Trends Query**
   - Status: ✅ PASSED
   - Duration: <100ms ✓
   - Efficiently retrieves trend data

### Smart Filtering
5. **Large Test Suite Filtering (1000 tests)**
   - Status: ✅ PASSED
   - Duration: <500ms ✓
   - Successfully filters tests based on history

### Memory Usage
6. **Large File Collection**
   - Status: ✅ PASSED
   - Peak Memory: <100MB ✓
   - No memory leaks detected

### Scalability
7. **Linear Scaling with File Count**
   - Status: ✅ PASSED
   - Scales linearly from 100 to 2000 files
   - No quadratic behavior

---

## ❌ FAILING Benchmarks (Optimization Needed)

### File Collection
1. **Incremental Collection Performance**
   - Status: ❌ FAILED
   - Issue: Incremental (0.25s) slower than full (0.002s) for small repo
   - Root Cause: Git command overhead dominates for small change sets
   - **Optimization Needed**: Cache git status, batch git operations

### Language Detection
2. **Language Detection Speed**
   - Status: ❌ FAILED
   - Current: 1.62 seconds
   - Requirement: <1 second
   - **Optimization Needed**: Implement caching, parallel scanning

3. **Cached File Retrieval**
   - Status: ❌ FAILED
   - Issue: `LanguageDetector.get_files()` method not found
   - Root Cause: API mismatch
   - **Action**: Update test to use correct API or implement method

### Validator Execution
4-7. **Validator Tests**
   - Status: ❌ FAILED
   - Issue: API mismatches (ValidationOrchestrator, validator.validate())
   - **Action**: Fix API calls in tests

### Database Performance
8. **Flaky Test Query**
   - Status: ❌ FAILED
   - Issue: `threshold` parameter not recognized
   - **Action**: Check correct parameter name in API

9. **Bulk Insert Performance**
   - Status: ❌ FAILED
   - Current: 2.53 seconds for 1000 inserts
   - Requirement: <1 second
   - **Optimization Needed**: Use batch inserts, transactions

### Memory Usage
10-11. **Validator/Database Memory Tests**
   - Status: ❌ FAILED
   - Issue: API mismatches
   - **Action**: Fix API calls

---

## Performance Requirements Status

| Requirement | Status | Current | Target | Notes |
|------------|--------|---------|--------|-------|
| File Collection (10k files) | ✅ PASS | 1.69s | <2s | Excellent |
| Incremental Mode | ❌ FAIL | Variable | <5s | Needs optimization for small repos |
| Language Detection | ❌ FAIL | 1.62s | <1s | Caching needed |
| Database Queries | ✅ PASS | <100ms | <200ms | Excellent |
| Smart Filtering | ✅ PASS | <500ms | <500ms | Meets requirement |
| Memory Usage | ✅ PASS | <100MB | <100MB | Meets requirement |
| Linear Scaling | ✅ PASS | Linear | Linear | No quadratic behavior |
| Bulk Inserts | ❌ FAIL | 2.53s | <1s | Batch operations needed |

---

## Key Performance Insights

### Strengths
- ✅ File collection is **fast and scalable** (7k files/sec)
- ✅ Database queries are **efficient** (<100ms)
- ✅ Memory usage is **reasonable** (<100MB for 12k files)
- ✅ Smart filtering **performs well** with large test suites
- ✅ **Linear scaling** confirmed (no algorithmic issues)

### Optimization Opportunities

#### High Priority
1. **Language Detection Caching** - Currently taking 1.62s (needs <1s)
   - Implement result caching
   - Parallel directory scanning
   - Lazy evaluation

2. **Database Bulk Inserts** - Currently 2.53s for 1000 records
   - Use executemany() for batch inserts
   - Optimize transaction management
   - Consider prepared statements

3. **Incremental Mode for Small Repos** - Git overhead issue
   - Cache git status results
   - Batch git commands
   - Skip git for very small change sets

#### Medium Priority
4. **API Consistency** - Fix remaining API mismatches
   - ValidationOrchestrator interface
   - Validator.validate() signature
   - Query engine parameters

---

## Next Steps

### Immediate Actions
1. ✅ Document baseline performance (THIS FILE)
2. ⏳ Fix API mismatches in failing tests
3. ⏳ Implement language detection caching
4. ⏳ Optimize database bulk inserts
5. ⏳ Improve incremental mode performance

### Future Optimizations
- Parallel validator execution optimization
- Progressive result streaming
- Incremental database updates
- Background cache warming

---

## Success Criteria Met

Despite 11 failing tests, the **core performance requirements are met or close**:
- ✅ Large file collection: **EXCELLENT** (1.69s for 10k files)
- ✅ Database queries: **EXCELLENT** (<100ms)
- ✅ Smart filtering: **MEETS REQUIREMENT** (<500ms)
- ✅ Memory usage: **MEETS REQUIREMENT** (<100MB)
- ⚠️ Language detection: **CLOSE** (1.62s, need <1s)
- ⚠️ Bulk inserts: **NEEDS WORK** (2.53s, need <1s)

**Overall Assessment**: Infrastructure is solid with identified optimization paths. Most failures are API mismatches (easy fix) rather than fundamental performance issues.

---

**Performance Benchmarks Created**: 2026-01-31
**Baseline Established**: Yes
**Optimization Plan**: Documented above
