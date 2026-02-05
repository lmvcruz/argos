# Phase 1 Testing - Setup Complete ✅

## 🚀 Services Running

Both backend and frontend are now running and ready for testing:

### Frontend
- **URL**: http://localhost:3000
- **Status**: ✅ Running (Vite dev server)
- **Port**: 3000
- **Features**:
  - Hot reload enabled
  - TypeScript compilation active
  - Proxy to backend on `/api`

### Backend
- **URL**: http://localhost:8000
- **Status**: ✅ Running (FastAPI)
- **Port**: 8000
- **Features**:
  - Health check at `/health`
  - API endpoints at `/api/*`
  - WebSocket ready

## 📋 What to Test

### 1. **Navigate to New Scenario Pages**
Open http://localhost:3000 and look for in the sidebar:

**New Pages Available**:
- **Local Inspection** - Code analysis interface
  - File tree explorer
  - Analysis results table
  - Run analysis button
  - Output panel

- **Local Tests** - Test execution results
  - Test results with pass/fail status
  - Execution summary stats
  - Run tests button
  - Output panel

- **CI Inspection** - CI workflow monitoring
  - Workflow history table
  - Status overview
  - Success rate metric

### 2. **Test Feature Toggles**
Edit `lens/frontend/public/config/settings.json`:

```json
{
  "features": {
    "localInspection": { "enabled": false },  // Toggle to hide/show
    "localTests": { "enabled": true },
    "ciInspection": { "enabled": true }
  }
}
```

Then refresh the page - scenarios should appear/disappear from sidebar.

### 3. **Test Components**

**FileTree**:
- Click folder icons to expand/collapse
- Click files to select them
- Selected item highlights in blue

**ResultsTable**:
- Click column headers to sort (arrows show direction)
- Use Previous/Next buttons to paginate
- Click rows to select them

**SeverityBadge**:
- Different colors for error, warning, info, success
- Numbers show count of each severity

**OutputPanel**:
- Shows execution logs
- Click Copy to copy all logs
- Click Download to save as file
- Clear button to reset logs

**CodeSnippet & CollapsibleSection**:
- Click title to expand/collapse
- Copy button in code snippet

### 4. **Run Mock Operations**

**Local Inspection**:
- Click "Run Analysis" button
- Watch output panel populate with logs
- Results appear in table

**Local Tests**:
- Click "Run Tests" button
- Watch execution output
- See test status (pass/fail/flaky)

**CI Inspection**:
- View workflow history automatically
- Click "Workflow Configuration" to expand details

## 🔧 Configuration Examples

### Enable All Features
```bash
# Edit public/config/settings.json
{
  "features": {
    "localInspection": { "enabled": true },
    "localTests": { "enabled": true },
    "localBuild": { "enabled": true },
    "localExecution": { "enabled": true },
    "ciInspection": { "enabled": true }
  }
}
```

### Use Environment Variables
```bash
VITE_LENS_FEATURE_LOCALBUILD=true
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# If in use, kill the process or use different port
```

### Frontend won't start
```bash
# Make sure npm modules are installed
cd lens/frontend
npm install

# Clear node_modules if issues persist
rmdir /s /q node_modules
npm install
```

### Configuration not loading
- Verify `lens/frontend/public/config/settings.json` exists
- Check browser DevTools Network tab for `/config/settings.json` request
- Should see 200 response

### Pages not showing in sidebar
- Edit `public/config/settings.json` and set `"enabled": true`
- Refresh browser page (Ctrl+R)
- Check browser console for errors (F12)

## 📊 API Testing

### Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Check Configuration
Open http://localhost:3000 and open DevTools (F12):
```javascript
// In browser console:
fetch('/config/settings.json').then(r => r.json()).then(c => console.log(c))
```

## 📝 Terminal Commands

### To Stop Services
```bash
# Stop frontend (in its terminal):
Ctrl+C

# Stop backend (in its terminal):
Ctrl+C
```

### To Restart Services
```bash
# Backend
cd d:\playground\argos\lens
python -m lens.backend.server

# Frontend
cd d:\playground\argos\lens\frontend
npm run dev
```

## ✅ Checklist

Use this to verify everything is working:

- [ ] Frontend loads at http://localhost:3000
- [ ] Sidebar shows "Local Inspection", "Local Tests", "CI Inspection"
- [ ] Click on each scenario page - they load without errors
- [ ] File tree expands/collapses
- [ ] Results table is sortable and has pagination
- [ ] Run buttons trigger mock execution
- [ ] Output panel shows logs
- [ ] Dark mode works (Tailwind classes render)
- [ ] No console errors (check F12 DevTools)
- [ ] Feature toggles work (enable/disable in config)

## 🎯 What's Next

Once you've tested Phase 1:

1. Review the code in `lens/frontend/src/`:
   - `config/` - Configuration system
   - `components/` - Base components
   - `pages/LocalInspection.tsx`, etc. - Scenario pages

2. Check out the documentation:
   - `PHASE_1_QUICK_START.md` - Usage guide
   - `PHASE_1_IMPLEMENTATION.md` - Technical details
   - `PHASE_2_ROADMAP.md` - What's coming next

3. When ready for Phase 2, connect to real backends:
   - Anvil for code analysis
   - Verdict for test execution
   - Scout for CI workflows

## 📞 Quick Links

- **Frontend**: http://localhost:3000
- **Backend Health**: http://localhost:8000/health
- **Project Docs**: `lens/` directory
- **Component Examples**: `lens/PHASE_1_QUICK_START.md`

---

**Both services are running! 🎉 Start testing at http://localhost:3000**
