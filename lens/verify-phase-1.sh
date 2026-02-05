#!/bin/bash

# Phase 1 Verification Checklist
# Run this script to verify Phase 1 implementation is complete

echo "======================================"
echo "Phase 1 Implementation Verification"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
PASSED=0
FAILED=0

# Helper function
check() {
  if [ -f "$1" ] || [ -d "$1" ]; then
    echo -e "${GREEN}✓${NC} $2"
    ((PASSED++))
  else
    echo -e "${RED}✗${NC} $2"
    echo "  Missing: $1"
    ((FAILED++))
  fi
}

echo "Checking Configuration System..."
check "frontend/src/config/settings.json" "settings.json exists"
check "frontend/src/config/configManager.ts" "configManager.ts exists"
check "frontend/src/config/ConfigContext.tsx" "ConfigContext.tsx exists"
check "frontend/public/config/settings.json" "public/config/settings.json exists"
echo ""

echo "Checking Base Components..."
check "frontend/src/components/FileTree.tsx" "FileTree.tsx exists"
check "frontend/src/components/ResultsTable.tsx" "ResultsTable.tsx exists"
check "frontend/src/components/CodeSnippet.tsx" "CodeSnippet.tsx exists"
check "frontend/src/components/CollapsibleSection.tsx" "CollapsibleSection.tsx exists"
check "frontend/src/components/SeverityBadge.tsx" "SeverityBadge.tsx exists"
check "frontend/src/components/OutputPanel.tsx" "OutputPanel.tsx exists"
check "frontend/src/components/index.ts" "components/index.ts exists"
echo ""

echo "Checking Scenario Pages..."
check "frontend/src/pages/LocalInspection.tsx" "LocalInspection.tsx exists"
check "frontend/src/pages/LocalTests.tsx" "LocalTests.tsx exists"
check "frontend/src/pages/CIInspection.tsx" "CIInspection.tsx exists"
echo ""

echo "Checking Updated Files..."
check "frontend/src/App.tsx" "App.tsx updated"
echo ""

echo "Checking Documentation..."
check "PHASE_1_QUICK_START.md" "PHASE_1_QUICK_START.md exists"
check "PHASE_1_IMPLEMENTATION.md" "PHASE_1_IMPLEMENTATION.md exists"
check "PHASE_1_COMPLETION_SUMMARY.md" "PHASE_1_COMPLETION_SUMMARY.md exists"
check "PHASE_2_ROADMAP.md" "PHASE_2_ROADMAP.md exists"
check "README_PHASE_1.md" "README_PHASE_1.md exists"
echo ""

# Summary
TOTAL=$((PASSED + FAILED))
echo "======================================"
echo "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC} out of $TOTAL checks"
echo "======================================"

if [ $FAILED -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✓ Phase 1 Implementation Complete!${NC}"
  echo ""
  echo "Next steps:"
  echo "1. cd lens/frontend && npm install"
  echo "2. npm run dev"
  echo "3. Visit http://localhost:3000"
  echo "4. Check sidebar for new scenario pages"
  echo ""
  echo "For more info, see PHASE_1_QUICK_START.md"
  exit 0
else
  echo ""
  echo -e "${RED}✗ Phase 1 Implementation Incomplete${NC}"
  echo "Please create the missing files listed above"
  exit 1
fi
