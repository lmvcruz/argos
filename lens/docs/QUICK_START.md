# Lens UI v2.0 - Quick Start Guide

## How to Access the Config Page

### Step 1: Start the Backend Server

Open a terminal and navigate to the **`lens`** directory (parent of `backend/` folder):

```bash
# From argos root directory
cd lens

# Verify you're in the right directory - you should see backend/ and frontend/ folders
ls   # macOS/Linux
dir  # Windows

# Now start the backend
python -m uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```

**Important**: Run this command from `D:\playground\argos\lens`, NOT from `D:\playground\argos\lens\backend`

The backend will start at `http://localhost:8000` and automatically creates the database at `~/.lens/projects.db`.

### Step 2: Start the Frontend Development Server

Open a new terminal in the `lens/frontend` directory:

```bash
cd lens/frontend
npm install  # Only needed first time
npm run dev
```

The frontend will start at `http://localhost:3000` (configured in `vite.config.js`).

### Step 3: Open the Application

1. Navigate to `http://localhost:3000` in your browser
2. You should see the **Lens v2.0** navigation bar at the top
3. The **Config** tab should be active (default page)

### Step 4: Create Your First Project

1. On the **Config** page, you'll see:
   - **Left column**: Empty project list (since no projects created yet)
   - **Right column**: A "Create New Project" placeholder

2. Click the placeholder or scroll down to find the create form
3. Fill in the form:
   - **Name**: e.g., "My First Project"
   - **Local Folder**: Path to your project folder (e.g., `/Users/yourname/projects/myapp`)
   - **Repository**: GitHub repo URL (e.g., `https://github.com/yourname/myapp`)
   - **Token** (optional): GitHub PAT for private repos
   - **Storage Location** (optional): Where to store analysis results

4. Click **"Create Project"** button

### Step 5: Navigate Between Pages

Once on the Config page, you can navigate to other pages using the top navigation tabs:

- ⚙️ **Configuration** (Config) - Manage projects
- 🔍 **Local Inspection** - File tree and validation
- ✓ **Local Tests** - Test discovery and execution
- 🚀 **CI Inspections** - GitHub Actions workflow inspection

Use the **project selector dropdown** (right side of navigation) to switch between your projects.

---

## Troubleshooting

### "Cannot connect to backend" error

**Problem**: Frontend shows error message about backend connection
**Solution**:
1. Make sure backend is running on port 8000
2. Check that `http://localhost:8000/api/projects` returns a response
3. Verify no other service is using port 8000

### "No projects in list" (normal)

This is expected on first run. Create a project using the form on the right.

### Form submission fails

**Problem**: "Create Project" button doesn't work
**Solution**:
1. Check browser console (F12) for error messages
2. Verify backend is running and healthy
3. Check that local folder path exists and is readable
4. Check that repo URL is valid

### Navigation tabs don't switch pages

**Problem**: Clicking tabs doesn't change the page
**Solution**: Make sure you're using the **Phase 2** version with AppLayout page switching. If using older App.tsx, pages may not switch.

---

## Architecture Overview

```
┌─────────────────────────────────────┐
│      Lens v2.0 Application          │
├─────────────────────────────────────┤
│  Navigation (Tabs + Project Selector)│  ← Click tabs to switch pages
├─────────────────────────────────────┤
│                                     │
│         AppLayout                   │
│    ┌─────────────────────────┐      │
│    │    Current Page:        │      │
│    │  - ConfigPage           │      │
│    │  - LocalInspection      │      │
│    │  - LocalTests           │      │
│    │  - CIInspection         │      │
│    └─────────────────────────┘      │
│                                     │
├─────────────────────────────────────┤
│  Footer (Lens UI v2.0)              │
└─────────────────────────────────────┘
```

### ConfigPage Components

```
ConfigPage (Two-Column Layout)
├── Left Column (35%)
│   └── ProjectList
│       └── ProjectListItem (repeated for each project)
│
└── Right Column (65%)
    ├── ProjectForm (when editing/creating)
    └── Placeholder (when nothing selected)
```

### Data Flow

1. **Load Projects**: App loads projects from backend via `ProjectContext.loadProjects()`
2. **Display List**: `ProjectList` displays all projects with action buttons
3. **Select Project**: Clicking "Select" on a project sets it active (stored in localStorage)
4. **Edit Project**: Clicking "Edit" populates form with project data
5. **Submit Form**: Form sends create/update request to backend API
6. **Update State**: `ProjectContext` updates projects array and refreshes UI

---

## API Endpoints

The backend provides these endpoints (all relative to `http://localhost:8000`):

```
GET    /api/projects           # List all projects
POST   /api/projects           # Create new project
GET    /api/projects/{id}      # Get specific project
PUT    /api/projects/{id}      # Update project
DELETE /api/projects/{id}      # Delete project
POST   /api/projects/{id}/select # Set as active project
```

Test endpoints with curl:
```bash
# List projects
curl http://localhost:8000/api/projects

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "local_folder": "/path/to/folder",
    "repo": "https://github.com/user/repo"
  }'
```

---

## Ports Reference

| Service | Port | URL |
|---------|------|-----|
| Backend (Python/FastAPI) | 8000 | http://localhost:8000 |
| Frontend (React/Vite) | 3000 | http://localhost:3000 |
| Database | N/A | ~/.lens/projects.db |
| Logs | N/A | ~/.lens/logs/ |

---

## Database & Logs

**Projects Database**: `~/.lens/projects.db` (SQLite)
- Auto-created on first backend startup
- Contains projects table and active_project table

**Backend Logs**: `~/.lens/logs/backend.log`
- Rotated daily
- Stores all API calls and operations
- Useful for debugging

**Frontend Logs**: `~/.lens/logs/frontend.log`
- Created on demand when logs are exported
- Captures console errors and API calls

---

## Next Steps

1. ✅ **Create a project** - Use the Config page form
2. ✅ **Edit a project** - Click "Edit" on any project
3. ✅ **Switch projects** - Use the project selector dropdown
4. ⏳ **Local Inspection** - Browse files and run validators (Phase 3)
5. ⏳ **Local Tests** - Discover and run tests (Phase 4)
6. ⏳ **CI Inspections** - View GitHub Actions workflows (Phase 4)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `~/.lens/logs/`
3. Check browser console (F12)
4. Refer to [PHASE_2_COMPLETE.md](PHASE_2_COMPLETE.md) for implementation details
