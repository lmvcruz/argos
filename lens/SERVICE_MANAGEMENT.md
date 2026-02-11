# Lens Service Management Guide

## Quick Start

### Starting Services Manually

**Step 1: Start Backend (Port 8000)**

Open a **new PowerShell window** and run:

```powershell
cd D:\playground\argos
python -m uvicorn lens.backend.server:app --port 8000 --host 0.0.0.0
```

**Step 2: Start Frontend (Port 3000)**

Open **another new PowerShell window** and run:

```powershell
cd D:\playground\argos\lens\frontend
npm run dev -- --port 3000
```

**Step 3: Access Application**

Open your browser: **http://localhost:3000**

---

## Service Scripts

### Start Both Services (Separate Windows)

```powershell
cd D:\playground\argos\lens
.\start_services.ps1
```

This opens two separate PowerShell windows for backend and frontend.

### Kill All Services

```powershell
cd D:\playground\argos\lens
python kill_services.py
```

---

## Port Configuration

| Service  | Port | URL                      | Purpose                    |
|----------|------|--------------------------|----------------------------|
| Backend  | 8000 | http://localhost:8000    | FastAPI REST API           |
| Frontend | 3000 | http://localhost:3000    | Vite React dev server      |

---

## Troubleshooting

### Issue: "Port already in use"

**Solution 1:** Kill all services
```powershell
cd D:\playground\argos\lens
python kill_services.py
```

**Solution 2:** Manual kill
```powershell
# Kill Python processes
taskkill /F /IM python.exe

# Kill Node processes
taskkill /F /IM node.exe
```

### Issue: Backend fails to start from wrong directory

**Problem:** Backend must run from `D:\playground\argos` (not `D:\playground\argos\lens`)

**Why:** Backend needs access to `.anvil\execution.db` which is relative to the argos root

**Solution:**
```powershell
# ✓ CORRECT
cd D:\playground\argos
python -m uvicorn lens.backend.server:app --port 8000 --host 0.0.0.0

# ✗ WRONG
cd D:\playground\argos\lens
python -m uvicorn lens.backend.server:app --port 8000  # This will fail!
```

### Issue: Logs page shows "Loading logs configuration"

**Cause:** Backend is not running

**Solution:**
1. Verify backend is running: `netstat -ano | findstr :8000`
2. If not running, start backend following Step 1 above
3. Test backend: `Invoke-RestMethod -Uri "http://localhost:8000/api/logs/config"`

### Issue: Frontend shows "Failed to connect to backend"

**Cause:** Backend is not running or not responding

**Diagnosis:**
```powershell
# Check if backend is running
netstat -ano | findstr :8000

# Test backend health
Invoke-RestMethod -Uri "http://localhost:8000/api/health"

# Test logs config endpoint
Invoke-RestMethod -Uri "http://localhost:8000/api/logs/config"
```

**Solution:** Start the backend if it's not running

### Issue: Services keep shutting down

**Cause:** Running commands in the same terminal kills background processes

**Solution:** Always run backend and frontend in **separate PowerShell windows**

---

## Service Status Checks

### Check if Services are Running

```powershell
# Check both ports
netstat -ano | findstr ":8000 :3000"

# Check backend only
netstat -ano | findstr :8000

# Check frontend only
netstat -ano | findstr :3000
```

### Verify Backend is Responding

```powershell
# Check health endpoint
Invoke-RestMethod -Uri "http://localhost:8000/api/health"

# Check projects endpoint
Invoke-RestMethod -Uri "http://localhost:8000/api/projects"

# Check logs configuration
Invoke-RestMethod -Uri "http://localhost:8000/api/logs/config"
```

### Verify Frontend is Running

```powershell
# Check if frontend loads
Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
```

---

## Configuration Files

### Backend Configuration

**Location:** `D:\playground\argos\lens\lens\backend\server.py`

- Port: 8000
- Host: 0.0.0.0 (accessible from all interfaces)
- CORS: Enabled for frontend
- Database: `.anvil\execution.db` (relative to argos root)
- Logs: `~/.argos/lens/logs/backend.log`

### Frontend Configuration

**Location:** `D:\playground\argos\lens\frontend\vite.config.js`

- Port: 3000
- Proxy: `/api` → `http://localhost:8000`
- Hot reload: Enabled
- Source maps: Enabled

---

## Logs Configuration

### Log Locations

| Log Type         | Location                                | Purpose                      |
|------------------|-----------------------------------------|------------------------------|
| Backend Logs     | `~/.argos/lens/logs/backend.log`        | FastAPI server logs          |
| Frontend Logs    | `~/.argos/lens/logs/frontend.log`       | React application logs       |

**Windows Path:** `C:\Users\<YourUsername>\.argos\lens\logs\`

### View Logs via API

```powershell
# Get logs configuration
Invoke-RestMethod -Uri "http://localhost:8000/api/logs/config"

# List all available logs
Invoke-RestMethod -Uri "http://localhost:8000/api/logs/list"

# Read a specific log
Invoke-RestMethod -Uri "http://localhost:8000/api/logs/read/backend.log"
```

### View Logs via UI

1. Start both backend and frontend services
2. Navigate to: **http://localhost:3000/logs**
3. View real-time logs with auto-refresh

**Note:** If Logs page shows "Loading logs configuration", verify backend is running on port 8000.

---

## Development Workflow

### Typical Development Session

1. **Start Services**
   ```powershell
   cd D:\playground\argos\lens
   .\start_services.ps1
   ```

2. **Develop** (edit code in VS Code)
   - Backend changes: Restart backend manually (no hot reload)
   - Frontend changes: Auto-reloads via Vite HMR

3. **Test Changes**
   - Open browser: http://localhost:3000
   - Check console for errors (F12)
   - Check Network tab for API calls

4. **Stop Services** (when done)
   - Close backend PowerShell window (or Ctrl+C)
   - Close frontend PowerShell window (or Ctrl+C)
   - Or run: `python lens\kill_services.py`

### Hot Reload Behavior

| Component | Hot Reload | Restart Required |
|-----------|------------|------------------|
| Frontend (TSX, CSS) | ✅ Yes (Vite HMR) | No |
| Backend (Python) | ❌ No | Yes (manual) |
| Backend with --reload | ✅ Yes (uvicorn watches files) | No |

**Tip:** For backend hot reload, add `--reload` flag:
```powershell
python -m uvicorn lens.backend.server:app --port 8000 --host 0.0.0.0 --reload
```

---

## Advanced Configuration

### Backend with Auto-Reload (Development)

```powershell
cd D:\playground\argos
python -m uvicorn lens.backend.server:app --port 8000 --host 0.0.0.0 --reload
```

**Pros:** Auto-restarts on code changes
**Cons:** Slower startup, may miss some changes

### Frontend on Different Port

```powershell
cd D:\playground\argos\lens\frontend
npm run dev -- --port 3001
```

**Note:** Must update proxy in `vite.config.js` if backend is not on 8000

### Access from Other Devices

1. Start backend with `--host 0.0.0.0` (already default in instructions)
2. Find your IP: `ipconfig` (look for IPv4 Address)
3. Access from other device: `http://<your-ip>:3000`

---

## Common Errors and Solutions

### Error: "ECONNREFUSED" in Frontend Console

**Meaning:** Frontend can't reach backend

**Solutions:**
1. Check backend is running: `netstat -ano | findstr :8000`
2. Start backend if stopped
3. Check Vite proxy configuration in `vite.config.js`

### Error: "Failed to log to backend: 500"

**Meaning:** Backend endpoint error

**Solutions:**
1. Check backend logs: `~/.argos/lens/logs/backend.log`
2. Verify backend started without errors
3. Test endpoint manually: `Invoke-RestMethod -Uri "http://localhost:8000/api/logs/frontend"`

### Error: "Workflow fetch timeout (30000ms)"

**Meaning:** CI Inspection page trying to fetch Scout data but timing out

**Solutions:**
1. This is expected if no Scout workflows exist
2. Ignore this error - it doesn't affect other features
3. Or implement proper error handling in CIInspection.tsx

---

## Production Deployment (Future)

For production deployment, consider:

1. **Process Manager:** Use PM2 or systemd
2. **Reverse Proxy:** Nginx or Traefik
3. **HTTPS:** SSL certificates via Let's Encrypt
4. **Build Frontend:** `npm run build` → serve static files
5. **Environment Variables:** Configure ports, database paths
6. **Docker:** Container-based deployment (recommended)

---

## Quick Reference Commands

```powershell
# Start backend
cd D:\playground\argos
python -m uvicorn lens.backend.server:app --port 8000 --host 0.0.0.0

# Start frontend
cd D:\playground\argos\lens\frontend
npm run dev -- --port 3000

# Kill all services
cd D:\playground\argos\lens
python kill_services.py

# Check status
netstat -ano | findstr ":8000 :3000"

# Test backend
Invoke-RestMethod -Uri "http://localhost:8000/api/logs/config"

# View logs
Get-Content ~/.argos/lens/logs/backend.log -Tail 50 -Wait
```

---

**Last Updated:** February 9, 2026
**Maintainer:** Argos Development Team
