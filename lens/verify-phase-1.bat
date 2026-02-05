@echo off
REM Phase 1 Verification Checklist (Windows)
REM Run this script to verify Phase 1 implementation is complete

echo.
echo ======================================
echo Phase 1 Implementation Verification
echo ======================================
echo.

setlocal enabledelayedexpansion
set PASSED=0
set FAILED=0

REM Configuration System
echo Checking Configuration System...
if exist "frontend\src\config\settings.json" (
  echo [OK] settings.json exists
  set /a PASSED+=1
) else (
  echo [FAIL] settings.json missing
  set /a FAILED+=1
)

if exist "frontend\src\config\configManager.ts" (
  echo [OK] configManager.ts exists
  set /a PASSED+=1
) else (
  echo [FAIL] configManager.ts missing
  set /a FAILED+=1
)

if exist "frontend\src\config\ConfigContext.tsx" (
  echo [OK] ConfigContext.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] ConfigContext.tsx missing
  set /a FAILED+=1
)

if exist "frontend\public\config\settings.json" (
  echo [OK] public/config/settings.json exists
  set /a PASSED+=1
) else (
  echo [FAIL] public/config/settings.json missing
  set /a FAILED+=1
)

echo.
echo Checking Base Components...
if exist "frontend\src\components\FileTree.tsx" (
  echo [OK] FileTree.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] FileTree.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\components\ResultsTable.tsx" (
  echo [OK] ResultsTable.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] ResultsTable.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\components\CodeSnippet.tsx" (
  echo [OK] CodeSnippet.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] CodeSnippet.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\components\CollapsibleSection.tsx" (
  echo [OK] CollapsibleSection.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] CollapsibleSection.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\components\SeverityBadge.tsx" (
  echo [OK] SeverityBadge.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] SeverityBadge.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\components\OutputPanel.tsx" (
  echo [OK] OutputPanel.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] OutputPanel.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\components\index.ts" (
  echo [OK] components/index.ts exists
  set /a PASSED+=1
) else (
  echo [FAIL] components/index.ts missing
  set /a FAILED+=1
)

echo.
echo Checking Scenario Pages...
if exist "frontend\src\pages\LocalInspection.tsx" (
  echo [OK] LocalInspection.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] LocalInspection.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\pages\LocalTests.tsx" (
  echo [OK] LocalTests.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] LocalTests.tsx missing
  set /a FAILED+=1
)

if exist "frontend\src\pages\CIInspection.tsx" (
  echo [OK] CIInspection.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] CIInspection.tsx missing
  set /a FAILED+=1
)

echo.
echo Checking Updated Files...
if exist "frontend\src\App.tsx" (
  echo [OK] App.tsx exists
  set /a PASSED+=1
) else (
  echo [FAIL] App.tsx missing
  set /a FAILED+=1
)

echo.
echo Checking Documentation...
if exist "PHASE_1_QUICK_START.md" (
  echo [OK] PHASE_1_QUICK_START.md exists
  set /a PASSED+=1
) else (
  echo [FAIL] PHASE_1_QUICK_START.md missing
  set /a FAILED+=1
)

if exist "PHASE_1_IMPLEMENTATION.md" (
  echo [OK] PHASE_1_IMPLEMENTATION.md exists
  set /a PASSED+=1
) else (
  echo [FAIL] PHASE_1_IMPLEMENTATION.md missing
  set /a FAILED+=1
)

if exist "PHASE_1_COMPLETION_SUMMARY.md" (
  echo [OK] PHASE_1_COMPLETION_SUMMARY.md exists
  set /a PASSED+=1
) else (
  echo [FAIL] PHASE_1_COMPLETION_SUMMARY.md missing
  set /a FAILED+=1
)

if exist "PHASE_2_ROADMAP.md" (
  echo [OK] PHASE_2_ROADMAP.md exists
  set /a PASSED+=1
) else (
  echo [FAIL] PHASE_2_ROADMAP.md missing
  set /a FAILED+=1
)

if exist "README_PHASE_1.md" (
  echo [OK] README_PHASE_1.md exists
  set /a PASSED+=1
) else (
  echo [FAIL] README_PHASE_1.md missing
  set /a FAILED+=1
)

echo.
echo ======================================
echo Results: %PASSED% passed, %FAILED% failed
echo ======================================
echo.

if %FAILED% equ 0 (
  echo [SUCCESS] Phase 1 Implementation Complete!
  echo.
  echo Next steps:
  echo 1. cd lens\frontend
  echo 2. npm install
  echo 3. npm run dev
  echo 4. Visit http://localhost:3000
  echo 5. Check sidebar for new scenario pages
  echo.
  echo For more info, see PHASE_1_QUICK_START.md
  exit /b 0
) else (
  echo [ERROR] Phase 1 Implementation Incomplete
  echo Please create the missing files listed above
  exit /b 1
)
