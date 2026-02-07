# Phase 3 Task 5-7: Backend & Testing Guide

## Current Status

✅ **Phase 3 Frontend (Tasks 1-4): COMPLETE**
- FileTree component with styling
- ValidationForm component with results display
- StatsCard component with statistics
- LocalInspection page with two-column layout
- All components compile with zero TypeScript errors

❌ **Phase 3 Backend (Task 5-6): PENDING**
⏳ **Phase 3 Testing (Task 7): PENDING**

## What Works Now

The LocalInspection page is fully functional for:
- ✅ Displaying the UI layout
- ✅ Managing component state
- ✅ Handling user interactions (clicks, selections)
- ✅ Responsive design on all screen sizes

## What Doesn't Work (Needs Backend)

- ❌ Loading files from project (backend API not implemented)
- ❌ Selecting validators (no options available)
- ❌ Running validation (backend not implemented)
- ❌ Displaying results (no data being populated)

## Phase 3 Task 5: AnvilService Backend Integration

### Objective
Create a Python service that wraps Anvil validator functionality.

### File to Create
`lens/backend/services/anvil_service.py`

### Expected Methods

```python
class AnvilService:
    """Service for running code validation using Anvil tools."""

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported programming languages.

        Returns:
            ["python", "javascript", "cpp", "java", ...]
        """

    def get_validators_for_language(self, language: str) -> List[Dict]:
        """
        Get available validators for a specific language.

        Args:
            language: Programming language (e.g., "python")

        Returns:
            [
                {
                    "id": "flake8",
                    "name": "flake8",
                    "description": "Python linter...",
                    "language": "python"
                },
                ...
            ]
        """

    def validate(
        self,
        project_path: str,
        language: str,
        validator: str,
        target_path: str
    ) -> List[Dict]:
        """
        Run validation on a file or folder.

        Args:
            project_path: Root project path
            language: Programming language
            validator: Validator to use (e.g., "flake8")
            target_path: File or folder to validate

        Returns:
            [
                {
                    "file": "src/main.py",
                    "line": 42,
                    "column": 5,
                    "severity": "error",  # "error", "warning", "info"
                    "message": "Undefined variable 'foo'",
                    "rule": "E305"
                },
                ...
            ]
        """
```

### How to Find Anvil Code

The Anvil validator is already in your workspace:
- Location: `d:\playground\argos\anvil\`
- Main module: `anvil/anvil/core/`
- Example validators in: `anvil/tests/`

### Implementation Tips

1. **Language Detection**
   - Map file extensions to languages
   - Python: .py, .pyx
   - JavaScript: .js, .ts, .jsx, .tsx
   - C++: .cpp, .cc, .h, .hpp

2. **Validator Selection**
   - Python: flake8, pylint, mypy, black
   - JavaScript: eslint, prettier
   - C++: clang-format, cppcheck
   - Can add more as needed

3. **Result Parsing**
   - Each validator has different output format
   - Parse and normalize to ValidationResult structure
   - Include file path relative to project root

4. **Error Handling**
   - Catch validator execution errors
   - Return empty results if validator not found
   - Log detailed errors for debugging

### Testing Strategy

```python
def test_anvil_service_get_languages():
    """Test that supported languages are returned."""
    service = AnvilService()
    languages = service.get_supported_languages()
    assert "python" in languages
    assert "javascript" in languages

def test_anvil_service_validate_python():
    """Test validation of Python file."""
    service = AnvilService()
    results = service.validate(
        project_path="d:\\test_project",
        language="python",
        validator="flake8",
        target_path="d:\\test_project\\main.py"
    )
    assert isinstance(results, list)
    # Each result should have required fields
    for result in results:
        assert "file" in result
        assert "line" in result
        assert "severity" in result
        assert "message" in result
```

## Phase 3 Task 6: Backend Inspection API Routes

### Objective
Create FastAPI routes that expose AnvilService functionality via HTTP API.

### File to Create
`lens/backend/routes/inspection.py`

### Routes to Implement

#### 1. GET /api/inspection/languages

**Purpose:** Get list of supported languages

**Response:**
```json
{
  "languages": ["python", "javascript", "cpp", "java"]
}
```

**Implementation:**
```python
@router.get("/languages")
async def get_languages():
    """Get supported languages."""
    service = AnvilService()
    return {"languages": service.get_supported_languages()}
```

#### 2. GET /api/inspection/validators

**Purpose:** Get list of available validators

**Response:**
```json
{
  "validators": [
    {
      "id": "flake8",
      "name": "flake8",
      "description": "Python linter",
      "language": "python"
    },
    {
      "id": "eslint",
      "name": "ESLint",
      "description": "JavaScript linter",
      "language": "javascript"
    }
  ]
}
```

**Implementation:**
```python
@router.get("/validators")
async def get_validators():
    """Get all available validators."""
    service = AnvilService()
    validators = []
    for language in service.get_supported_languages():
        validators.extend(service.get_validators_for_language(language))
    return {"validators": validators}
```

#### 3. GET /api/inspection/files

**Purpose:** Get file tree for project

**Query Parameters:**
- `path` (required): Project root path

**Response:**
```json
{
  "files": [
    {
      "id": "file-1",
      "name": "main.py",
      "type": "file"
    },
    {
      "id": "folder-1",
      "name": "src",
      "type": "folder",
      "children": [
        {
          "id": "file-2",
          "name": "utils.py",
          "type": "file"
        }
      ]
    }
  ]
}
```

**Implementation:**
```python
@router.get("/files")
async def get_files(path: str = Query(...)):
    """Get file tree for project."""
    try:
        files = _build_file_tree(path)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def _build_file_tree(path: str, max_depth: int = 5) -> List[Dict]:
    """Recursively build file tree structure."""
    # Implement directory traversal
    # Return list of FileTreeNode dicts
```

#### 4. POST /api/inspection/validate

**Purpose:** Run validation on a file or folder

**Request Body:**
```json
{
  "path": "/path/to/project",
  "language": "python",
  "validator": "flake8",
  "target": "/path/to/file.py"
}
```

**Response:**
```json
{
  "results": [
    {
      "file": "src/main.py",
      "line": 42,
      "column": 5,
      "severity": "error",
      "message": "Undefined variable 'foo'",
      "rule": "E305"
    }
  ]
}
```

**Implementation:**
```python
@router.post("/validate")
async def validate(request: ValidationRequest):
    """Run validation on target."""
    try:
        service = AnvilService()
        results = service.validate(
            project_path=request.path,
            language=request.language,
            validator=request.validator,
            target_path=request.target
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ValidationRequest(BaseModel):
    path: str
    language: str
    validator: str
    target: str
```

### Integration with Existing Backend

Add to `lens/backend/server.py`:

```python
from lens.backend.routes import inspection

# In app creation section:
app.include_router(inspection.router, prefix="/api/inspection", tags=["inspection"])
```

## Phase 3 Task 7: Testing & Validation

### Test Files to Create

#### 1. Backend Service Tests
`lens/backend/tests/test_anvil_service.py`

```python
import pytest
from lens.backend.services.anvil_service import AnvilService

class TestAnvilService:
    def setup_method(self):
        self.service = AnvilService()

    def test_get_supported_languages(self):
        """Languages should include Python."""
        languages = self.service.get_supported_languages()
        assert "python" in languages

    def test_get_validators_for_python(self):
        """Python validators should include flake8."""
        validators = self.service.get_validators_for_language("python")
        assert any(v["id"] == "flake8" for v in validators)

    def test_validate_python_file(self):
        """Validate a sample Python file."""
        # Create test file with issues
        results = self.service.validate(
            project_path="d:\\test_project",
            language="python",
            validator="flake8",
            target_path="d:\\test_project\\test.py"
        )
        assert isinstance(results, list)
        # Results should have expected fields
        for result in results:
            assert result.get("line") >= 1
            assert result.get("severity") in ["error", "warning", "info"]
```

#### 2. API Route Tests
`lens/backend/tests/test_inspection_routes.py`

```python
from fastapi.testclient import TestClient
from lens.backend.server import app

client = TestClient(app)

def test_get_languages():
    """GET /api/inspection/languages should return list."""
    response = client.get("/api/inspection/languages")
    assert response.status_code == 200
    data = response.json()
    assert "languages" in data
    assert isinstance(data["languages"], list)

def test_get_validators():
    """GET /api/inspection/validators should return list."""
    response = client.get("/api/inspection/validators")
    assert response.status_code == 200
    data = response.json()
    assert "validators" in data

def test_validate_endpoint():
    """POST /api/inspection/validate should execute validation."""
    response = client.post(
        "/api/inspection/validate",
        json={
            "path": "d:\\test_project",
            "language": "python",
            "validator": "flake8",
            "target": "d:\\test_project\\main.py"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
```

#### 3. Frontend Integration Tests
`lens/frontend/src/pages/LocalInspection.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocalInspection } from './LocalInspection';
import { ProjectProvider } from '../contexts/ProjectContext';

describe('LocalInspection', () => {
  it('renders without project', () => {
    render(
      <ProjectProvider>
        <LocalInspection />
      </ProjectProvider>
    );
    expect(screen.getByText(/No Project Selected/i)).toBeInTheDocument();
  });

  it('loads file tree on mount', async () => {
    // Mock active project
    // Mock API response
    // Verify file tree loaded
  });

  it('executes validation on button click', async () => {
    // Setup mock project
    // Click validate button
    // Verify API called with correct parameters
  });
});
```

### Coverage Goals

- Backend Service: 90%+ coverage
- API Routes: 85%+ coverage
- Frontend Components: 90%+ coverage
- Overall: 85%+ coverage

### Running Tests

```bash
# Backend tests
cd lens
python -m pytest backend/tests/

# Frontend tests
cd lens/frontend
npm test
```

## Implementation Order

### Phase 3 Task 5 First
1. Create `anvil_service.py`
2. Implement basic language/validator detection
3. Test with manual script
4. Add to backend as service

### Then Phase 3 Task 6
1. Create `inspection.py` routes
2. Implement file tree endpoint
3. Implement validation endpoint
4. Test with Postman/curl

### Then Phase 3 Task 7
1. Create test files
2. Write unit tests
3. Write integration tests
4. Verify coverage

## Verification Checklist

### Task 5 Completion
- [ ] `anvil_service.py` created
- [ ] `get_supported_languages()` works
- [ ] `get_validators_for_language()` works
- [ ] `validate()` works
- [ ] Error handling implemented
- [ ] Logging added

### Task 6 Completion
- [ ] `inspection.py` routes created
- [ ] GET /api/inspection/languages works
- [ ] GET /api/inspection/validators works
- [ ] GET /api/inspection/files works
- [ ] POST /api/inspection/validate works
- [ ] Routes registered in server.py
- [ ] CORS headers set correctly

### Task 7 Completion
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] All tests pass
- [ ] Coverage 90%+ for services
- [ ] Coverage 85%+ for routes
- [ ] No console errors

## Expected Outcome

After completing Tasks 5-7:
- ✅ LocalInspection page fully functional
- ✅ File tree loads from backend
- ✅ Validators list shows options
- ✅ Validation execution works
- ✅ Results display in UI
- ✅ Statistics update correctly
- ✅ All tests passing
- ✅ Phase 3 complete (100%)

## Troubleshooting

### Common Issues

**API returns 404:**
- Check routes registered in server.py
- Verify prefix matches in include_router call
- Test with curl: `curl http://localhost:8000/api/inspection/languages`

**File tree returns empty:**
- Check path parameter is valid
- Verify permissions on directory
- Check for exceptions in backend logs

**Validation returns no results:**
- Verify validator is installed on system
- Check target file path is correct
- Review validator command line usage

**Tests fail:**
- Run with `-vv` flag for verbose output
- Check test fixtures setup correctly
- Verify mock data matches API response format

---

**Ready to start Phase 3 Task 5?**
- Review AnvilService requirements above
- Check existing Anvil library in `anvil/` directory
- Create `lens/backend/services/anvil_service.py`
- Implement get_supported_languages() first as quick test

