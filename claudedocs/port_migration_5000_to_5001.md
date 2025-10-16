# Backend Port Migration: 5000 → 5001

**Date**: 2025-10-17
**Status**: ✓ Complete
**Reason**: macOS AirPlay port conflict

---

## Summary

Migrated backend API from port 5000 to port 5001 across all configuration files, scripts, and documentation to avoid conflict with macOS AirPlay Receiver service.

---

## Files Updated

### Configuration Files
| File | Line | Change |
|------|------|--------|
| `docker-compose.yml` | 26 | Port mapping: `"5000:5000"` → `"5001:5000"` |
| `frontend/index.html` | 624 | API URL: `localhost:5000` → `localhost:5001` |

### Scripts
| File | Changes | Description |
|------|---------|-------------|
| `setup.sh` | Lines 192, 218, 225 | Health checks and instructions |
| `scripts/start_system.sh` | Lines 97, 223, 229, 233, 297, 304, 318 | Port checks and health validation |
| `test.sh` | Lines 64, 103, 125, 145 | API test endpoints |

### Documentation
| File | Changes | Description |
|------|---------|-------------|
| `CLAUDE.md` | Lines 101, 134 | Setup and testing commands |

### Cleanup
| File | Action | Reason |
|------|--------|--------|
| `.gitmodules` | Deleted | No submodules needed (using Docker images) |
| `presenton/` (submodule) | Removed | Using pre-built Docker image |
| `refData/Codes/PPTAgent` | Removed | Empty reference directory |

---

## Port Allocation (Updated)

```
Port 5000:  macOS AirPlay Receiver (ControlCenter)  [Avoided]
Port 5001:  Backend API (Docker)                    [Active] ✓
Port 8000:  Presenton API (Docker)                  [Active] ✓
Port 8080:  Frontend Dev Server (manual)            [Manual]
Port 11434: Ollama LLM (host machine)               [External]
```

---

## Verification Commands

### Test Backend Access
```bash
# Should return healthy status
curl http://localhost:5001/api/health

# Expected response:
# {"status":"healthy","services":{...}}
```

### Test CORS
```bash
curl -X OPTIONS \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST" \
  -i http://localhost:5001/api/generate

# Should return CORS headers:
# access-control-allow-origin: http://localhost:8080
```

### Run Full Test Suite
```bash
./test.sh

# All tests should pass:
# ✅ Ollama: Working
# ✅ Presenton: Running
# ✅ Backend: Healthy (port 5001)
# ✅ Generation: Success
```

---

## Impact Analysis

### Services Affected
- ✓ Backend API (port changed)
- ✓ Frontend (API URL updated)
- ✓ Setup scripts (port checks updated)
- ✓ Test scripts (endpoints updated)
- ✓ Documentation (instructions updated)

### Services Unaffected
- ✓ Presenton (still on port 8000)
- ✓ Ollama (still on port 11434)
- ✓ Docker internal networking (container-to-container)

### No Breaking Changes
- Frontend automatically uses new port (hardcoded URL updated)
- All scripts check correct port
- Docker Compose maps host 5001 → container 5000 (backend code unchanged)

---

## Migration Steps Completed

1. ✓ Stopped Docker services
2. ✓ Updated `docker-compose.yml` port mapping
3. ✓ Updated `frontend/index.html` API URL
4. ✓ Updated `setup.sh` port checks and instructions
5. ✓ Updated `scripts/start_system.sh` all port references
6. ✓ Updated `test.sh` API test endpoints
7. ✓ Updated `CLAUDE.md` documentation
8. ✓ Removed obsolete git submodules
9. ✓ Restarted Docker services
10. ✓ Verified backend health on port 5001

---

## Related Documentation

- [Port 5000 Conflict & CORS Fix](port_5000_conflict_cors_fix.md) - Detailed root cause analysis
- [CLAUDE.md](../CLAUDE.md) - Updated project documentation
- [docker-compose.yml](../docker-compose.yml) - Service configuration

---

## Quick Start (After Migration)

```bash
# Start system
docker-compose up -d

# Verify backend
curl http://localhost:5001/api/health

# Start frontend
cd frontend && python3 -m http.server 8080

# Access application
open http://localhost:8080
```

---

## Backward Compatibility

### Old Port (5000)
- ✗ No longer accessible (blocked by AirPlay)
- ✗ Will return 403 Forbidden from ControlCenter

### New Port (5001)
- ✓ Accessible on all systems
- ✓ No conflicts with macOS services
- ✓ All scripts and documentation updated

### Migration Path
If you have external integrations pointing to port 5000:
1. Update URLs: `http://localhost:5000` → `http://localhost:5001`
2. Update firewall rules if applicable
3. Update any bookmarks or saved requests

---

## Prevention

Added to `scripts/start_system.sh`:
```bash
check_port() {
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port is occupied"
        # Offers to kill process or exit
    fi
}

check_port 5001 "Backend"  # Now checks 5001 instead of 5000
```

---

## Git Status

```
Modified files:
  M CLAUDE.md                   # Documentation updated
  M docker-compose.yml          # Port 5000→5001
  M frontend/index.html         # API URL updated
  M scripts/start_system.sh     # Port checks updated
  M setup.sh                    # Health checks updated
  M test.sh                     # Test endpoints updated

Deleted files:
  D .gitmodules                 # No submodules needed
  D presenton                   # Using Docker image
  D refData/Codes/PPTAgent      # Empty reference

New files:
  ?? claudedocs/port_5000_conflict_cors_fix.md
  ?? claudedocs/port_migration_5000_to_5001.md
```

---

**Status**: Migration complete. System fully operational on port 5001. ✓
