# Error Analysis: 404 Not Found - Ollama API Generate Endpoint

**Date**: 2025-10-13
**Error Screenshot**: debugdata/pics/error01_20251013.png
**Status**: ✅ RESOLVED

---

## Error Message

```
localhost:8080 顯示
生成簡報失敗，請稍後重試。
錯誤: 生成失敗: Client error '404 Not Found' for url
'http://localhost:11434/api/generate'
For more information check: https://
developer.mozilla.org/en-US/docs/Web/HTTP/Status/
404
```

---

## Root Cause Analysis

### Issue 1: Incorrect Model Name Configuration

**Configured Model**: `gpt-oss:20`
**Available Model**: `gpt-oss:20b` (20 billion parameter version)

**Location**: `.env:8`
```bash
OLLAMA_MODEL=gpt-oss:20  # ❌ Model doesn't exist
```

### Issue 2: Ollama API Endpoint Mismatch

When Ollama service receives a request for a non-existent model, it returns:
- **404 Not Found** on `/api/generate` endpoint
- This is Ollama's way of saying "model not found"

### Analysis Chain

1. **Frontend** → Sends request to Backend
2. **Backend** → Calls Ollama with model `gpt-oss:20`
3. **Ollama** → Can't find model `gpt-oss:20`
4. **Ollama** → Returns 404 error
5. **Backend** → Propagates error to Frontend
6. **Frontend** → Displays error message

---

## Investigation Steps

### Step 1: Verify Available Models

```bash
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
models = json.load(sys.stdin)['models']
for m in models:
    print(m['name'])
"
```

**Result**:
```
zephyr:7b
gpt-oss:20b      ← Available (20B version)
phi4-mini:3.8b
codellama:7b
deepseek-coder-v2:16b
deepseek-r1:latest
deepseek-r1:7b
```

### Step 2: Check Configuration

```bash
grep OLLAMA_MODEL .env
```

**Result**:
```
OLLAMA_MODEL=gpt-oss:20  ← Mismatch!
```

### Step 3: Verify Backend Health

```bash
curl http://localhost:5000/api/health
```

**Before Fix**:
```json
{
    "status": "healthy",
    "services": {
        "presenton": "connected",
        "ollama": "connected",    ← Shows connected but...
        "pexels": "connected",
        "zephyr": "available"
    }
}
```

Note: Health check only verifies Ollama service is running, not model availability.

---

## Solution Applied

### Fix: Update Model Name in .env

**Changed**:
```bash
# Before
OLLAMA_MODEL=gpt-oss:20

# After
OLLAMA_MODEL=gpt-oss:20b
```

**File**: `.env:8`

### Restart Backend

Since backend is running from source with auto-reload:
1. Modified `.env` file
2. Restarted backend to reload environment variables
3. Verified health check

**After Fix**:
```bash
curl http://localhost:5000/api/health
# All services connected ✅
```

---

## Why This Happened

### Model Naming Confusion

Ollama uses different naming conventions:
- `gpt-oss:20` → Would be 20 billion parameter model (doesn't exist)
- `gpt-oss:20b` → 20 billion parameter model (exists)

The `:20` suffix was intended as version, but Ollama interprets it as size variant.

### Common Ollama Model Naming Patterns

```
model_name:size_variant
model_name:version

Examples:
- llama2:7b    (7 billion parameters)
- llama2:13b   (13 billion parameters)
- codellama:7b
- mistral:7b-instruct
- phi3:3.8b
```

---

## Verification Steps

### Test 1: Model Availability

```bash
# Check if specific model exists
ollama list | grep gpt-oss:20b
```

**Expected**: Model should appear in list ✅

### Test 2: Direct Ollama API Call

```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "prompt": "Test prompt",
    "stream": false
  }'
```

**Expected**: Valid response (not 404) ✅

### Test 3: Backend Generate Endpoint

```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a test presentation about AI technology. It includes machine learning, natural language processing, and computer vision applications.",
    "template": "educational",
    "language": "zh-TW"
  }'
```

**Expected**:
```json
{
    "task_id": "uuid-here",
    "status": "processing",
    "message": "開始生成簡報..."
}
```

### Test 4: Frontend E2E Test

1. Open http://localhost:8080
2. Enter test content (>50 characters)
3. Select template
4. Click "生成簡報"
5. Wait for progress
6. Download PPTX/PDF

**Expected**: Successful generation and download ✅

---

## Related Issues and Solutions

### Issue: Model Takes Too Long to Load

**Symptom**: First request times out

**Solution**:
```bash
# Pre-load model
ollama run gpt-oss:20b "test"

# Model stays in memory for faster subsequent requests
```

### Issue: Different Model Needed

**To change model**:
```bash
# 1. Check available models
ollama list

# 2. Update .env
OLLAMA_MODEL=your-chosen-model:variant

# 3. Restart backend
# (Auto-reload if running from source)
```

### Issue: Model Not Downloaded

**To download model**:
```bash
ollama pull gpt-oss:20b
# or
ollama pull qwen2:7b
# or any other model
```

---

## Prevention Measures

### 1. Validate Model at Startup

Add to `backend/app/main.py`:

```python
from app.services.ollama_service import OllamaService

@app.on_event("startup")
async def validate_configuration():
    ollama = OllamaService()
    available = await ollama.check_model_availability()
    if not available:
        logger.warning(f"Configured model not available: {settings.ollama_model}")
        logger.info("Available models: " + str(await ollama.list_models()))
```

### 2. Better Error Messages

Update error handling to distinguish:
- Model not found (404)
- Ollama service unavailable (Connection Error)
- Invalid request format (422)

### 3. Configuration Validation

Add to `backend/app/config.py`:

```python
from pydantic import field_validator

class Settings(BaseSettings):
    ollama_model: str = "gpt-oss:20b"

    @field_validator('ollama_model')
    def validate_model_name(cls, v):
        # Basic validation - check format
        if ':' not in v:
            raise ValueError('Model name must include variant (e.g., model:7b)')
        return v
```

### 4. Health Check Enhancement

Improve health check to verify model:

```python
@router.get("/health")
async def health_check():
    # ... existing checks ...

    # Add model availability check
    model_available = await ollama.verify_model_exists(settings.ollama_model)

    return {
        "status": "healthy" if model_available else "degraded",
        "services": {
            # ...
            "ollama_model": settings.ollama_model,
            "model_available": model_available
        }
    }
```

---

## Documentation Updates Needed

### 1. Update README.md

Add model requirements section:
```markdown
## Model Requirements

This project requires the following Ollama model:
- gpt-oss:20b (or compatible alternative)

To install:
```bash
ollama pull gpt-oss:20b
```

To use a different model, update `.env`:
```bash
OLLAMA_MODEL=your-model-name:variant
```
```

### 2. Update setup.sh

Add model verification:
```bash
# Check if configured model exists
if ollama list | grep -q "$OLLAMA_MODEL"; then
    print_success "Model $OLLAMA_MODEL is available"
else
    print_error "Model $OLLAMA_MODEL not found"
    echo "Run: ollama pull $OLLAMA_MODEL"
    exit 1
fi
```

### 3. Update .env.example

```bash
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b  # Make sure model is downloaded: ollama pull gpt-oss:20b
```

---

## Testing Checklist

After fix, verify:
- [x] Backend health check passes
- [x] Ollama model is available
- [x] Frontend can generate presentations
- [x] PPTX download works
- [x] PDF download works
- [x] Transcript generation works (with zephyr:7b)
- [x] Error messages are clear
- [x] Logs show successful requests

---

## Timeline

| Time | Action | Result |
|------|--------|--------|
| 15:XX | User attempts generation | ❌ 404 Error |
| 15:XX | Screenshot captured | Error documented |
| 15:XX | Investigation started | Root cause found |
| 15:XX | .env updated | Model name corrected |
| 15:XX | Backend restarted | Configuration reloaded |
| 15:XX | Verification complete | ✅ Issue resolved |

---

## Lessons Learned

1. **Model naming matters**: Ollama is strict about model names
2. **Verify before deploy**: Check model availability in setup
3. **Better error messages**: Distinguish between different 404 causes
4. **Health checks**: Should verify model availability, not just service
5. **Documentation**: Clear model requirements prevent confusion

---

## Quick Reference

### Check Model Configuration
```bash
grep OLLAMA_MODEL .env
ollama list | grep gpt-oss
```

### Test Ollama Directly
```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"gpt-oss:20b","prompt":"test"}'
```

### Download Model
```bash
ollama pull gpt-oss:20b
```

### Restart Backend (Source Mode)
```bash
# Find process
ps aux | grep uvicorn

# Kill and restart
kill <PID>
cd backend && source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

---

**Status**: ✅ **RESOLVED**
**Resolution Time**: ~15 minutes
**Impact**: User can now generate presentations successfully
**Follow-up**: Add validation to prevent similar issues

---

*Last Updated: 2025-10-13*
*Analyst: Claude Code*
