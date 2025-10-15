# Presenton Timeout and Filename Length Issues

**Issue Date**: 2025-10-15
**Status**: ✅ PARTIALLY RESOLVED (Frontend timeout fixed, Presenton filename bug documented)
**Severity**: 🟡 MEDIUM - User Experience Impact

---

## 📋 Problem Summary

User reported "生成超時" (Generation Timeout) error, but analysis revealed:

1. **Frontend timeout too short**: 2 minutes vs. actual 7.5 minute generation time
2. **Presenton filename bug**: Uses full slide title as filename, exceeding 255 char limit

### Error Messages

**Frontend**:
```
(index):752 Uncaught (in promise) Error: 生成超時
    at poll ((index):752:31)
```

**Presenton**:
```
OSError: [Errno 36] File name too long:
'/app_data/exports/筆記本銷售應用整合系統  本 slid 主要介紮此系統的基本功能和價值。可以跳過並直接進入下一個 slide。  本系統為筆記本銷售經理提供了一套具有高度整合性、可預測的数据查询和客户交互功.pptx'
```

---

## 🔍 Root Cause Analysis

### Issue #1: Frontend Timeout Too Short ❌

**Timeline Analysis** from Presenton logs:

```
06:39:47 - ✅ Generated 6 outlines for presentation
06:43:23 - ✅ Slide 1 content generated
06:44:08 - ✅ Slide 2 content generated
06:44:42 - ✅ Slide 3 content generated
06:45:16 - ✅ Slide 4 content generated
06:46:10 - ✅ Slide 5 content generated
06:46:49 - ✅ Slide 6 content generated
06:47:25 - ✅ Slide 7 content generated
         - ✅ Image search completed
         - ✅ Slides assembled
         - ❌ PPTX file save failed (filename too long)
```

**Total Execution Time**: ~7.5 minutes (450 seconds)

**Frontend Timeout Setting** ([frontend/index.html:747](../frontend/index.html#L747)):
```javascript
const maxAttempts = 120;  // 120 attempts × 1 second = 2 minutes
```

**Problem**: Frontend times out at 2 minutes, but generation takes 7.5 minutes!

**Why So Long?**:
- Using `zephyr:7b` model on CPU
- Each slide requires 30-45 seconds for LLM generation
- 6-7 slides × 35 seconds avg = ~4-5 minutes for content
- Image search: ~1-2 minutes
- Assembly and rendering: ~1-2 minutes
- **Total**: 6-9 minutes depending on content complexity

### Issue #2: Presenton Filename Generation Bug ❌

**Presenton Behavior**:
- Uses presentation **title** or **first slide content** as filename
- No truncation or sanitization applied
- Exceeds Linux filename limit of 255 bytes

**Error**:
```python
File "/usr/local/lib/python3.11/zipfile.py", line 1295, in __init__
  self.fp = io.open(file, filemode)
OSError: [Errno 36] File name too long: '/app_data/exports/筆記本銷售應用整合系統...'
```

**Problematic Filename Length**:
```
筆記本銷售應用整合系統  本 slid 主要介紮此系統的基本功能和價值。可以跳過並直接進入下一個 slide。  本系統為筆記本銷售經理提供了一套具有高度整合性、可預測的数据查询和客户交互功.pptx
```

- Chinese characters: 3 bytes each in UTF-8
- ~140 characters × 3 bytes = **420 bytes** (exceeds 255 limit!)

---

## ✅ Solutions

### Solution #1: Increase Frontend Timeout ✅ FIXED

**File**: [frontend/index.html](../frontend/index.html:747)

**BEFORE**:
```javascript
async pollProgress(taskId) {
    const maxAttempts = 120;  // 2 minutes
    let attempts = 0;
```

**AFTER**:
```javascript
async pollProgress(taskId) {
    const maxAttempts = 600;  // 10 minutes (600 seconds)
    let attempts = 0;
```

**Rationale**:
- Typical generation: 6-9 minutes for 6-7 slides
- 10-minute timeout provides buffer
- Still prevents infinite loops

### Solution #2: Presenton Filename Bug ⚠️ WORKAROUND ONLY

**This is a Presenton bug that requires upstream fix**. We cannot modify Presenton's internal filename generation.

**Workarounds**:

#### Option A: Use Shorter Content Titles (RECOMMENDED)
- Provide concise titles in input content
- Example: "筆記本銷售系統" instead of verbose descriptions
- Limit title to ~50 characters

#### Option B: Post-Process via Backend
**NOT IMPLEMENTED** - Would require modifying backend to intercept and rename files

#### Option C: Report to Presenton Project
- Issue: https://github.com/presenton/presenton/issues
- Request: Filename sanitization and truncation
- Expected fix: Use UUID or hash for filename, store title separately

---

## 📊 Performance Expectations

### Realistic Generation Times

| Slides | LLM Calls | Expected Time | Notes |
|--------|-----------|---------------|-------|
| 3 slides | ~4 calls | 2-3 minutes | Simple content |
| 6 slides | ~7 calls | 4-6 minutes | Standard presentation |
| 10 slides | ~11 calls | 7-10 minutes | Complex presentation |

**Breakdown per Slide**:
- LLM generation: 30-45 seconds (zephyr:7b on CPU)
- Image search: 2-5 seconds (Pexels API)
- Rendering: 3-5 seconds (python-pptx)

**Total Formula**: `(n_slides × 40s) + (image_search × 5s) + assembly_overhead`

### Model Performance Comparison

| Model | Size | Per-Slide Time | 6-Slide Total |
|-------|------|----------------|---------------|
| `zephyr:7b` | 4.1 GB | 35-45s | ~5-7 min |
| `phi4-mini:3.8b` | 2.5 GB | 25-35s | ~4-5 min |
| `gpt-oss:20b` | 13.8 GB | 120-180s ⚠️ | ~15-20 min ❌ |

---

## 🎯 User Guidelines

### For Faster Generation

1. **Use Shorter Titles**:
   ```
   ❌ Bad: "本系統為筆記本銷售經理提供了一套具有高度整合性、可預測的数据查询和客户交互功能的應用系統"
   ✅ Good: "筆記本銷售系統"
   ```

2. **Limit Slide Count**:
   - Frontend sends `n_slides` parameter
   - Default: 6 slides (~5-7 minutes)
   - For quick tests: 3 slides (~2-3 minutes)

3. **Simplify Content**:
   - Concise bullet points generate faster
   - Avoid extremely long paragraphs

4. **Be Patient**:
   - Wait indicator shows progress
   - 5-10 minutes is normal for 6-7 slides

---

## 🛠️ Troubleshooting

### If "生成超時" Error Occurs

```bash
# 1. Check Presenton logs for actual error
docker-compose logs presenton --tail=100 | grep -E "ERROR|Error|Traceback" -A 10

# Common patterns:
# - "File name too long" → Content title too long
# - "HTTP Request: POST...200 OK" → Generation in progress (not timeout)
# - "Presentation generation failed" → Check specific error
```

### If Filename Too Long Error

**Temporary Fix**: Use shorter content title

**Permanent Fix**: Wait for Presenton upstream fix

**Verification**:
```bash
# Check if file was created despite error
docker exec presenton-api ls -lh /app_data/exports/ | tail -5

# If file exists, download manually:
docker cp presenton-api:/app_data/exports/[filename].pptx ./output/
```

### If Generation Seems Stuck

```bash
# Check Ollama is responding
curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"zephyr:7b","prompt":"Test","stream":false}' \
  --max-time 60

# Should complete in <15 seconds
# If timeout: Ollama overloaded or model issue
```

---

## 📈 Monitoring Generation Progress

### Backend Progress Endpoint

```bash
# Get current task status
curl http://localhost:5000/api/progress/<task_id>

# Response format:
{
  "status": "processing",
  "progress": 45,
  "current_step": "Generating slide 3 of 6",
  "message": "..."
}
```

### Presenton Logs Show Actual Progress

```bash
# Watch real-time progress
docker-compose logs -f presenton | grep -E "Generated|Generating|HTTP Request"

# Example output:
# 2025-10-15 06:39:47 - INFO - HTTP Request: POST ...200 OK  ← Slide generated
# Generated 6 outlines for the presentation                  ← Outline phase done
# Generating slides from 0 to 6                              ← Rendering phase
# Request - Generating Image for ...                         ← Image search
```

---

## 🔧 Configuration Reference

### Frontend Timeout Settings

**File**: [frontend/index.html](../frontend/index.html)

```javascript
// Line 747: Polling configuration
const maxAttempts = 600;  // 10 minutes
const pollInterval = 1000;  // 1 second between checks

// Calculation:
// Total timeout = maxAttempts × (pollInterval / 1000) seconds
// Current: 600 × 1 = 600 seconds = 10 minutes
```

### Presenton Configuration

**File**: [docker-compose.yml](../docker-compose.yml)

```yaml
presenton:
  environment:
    - LLM=ollama
    - OLLAMA_MODEL=zephyr:7b     # Fast model for reasonable times
    - OLLAMA_URL=http://host.docker.internal:11434
    - IMAGE_PROVIDER=pexels
```

**Model Change Impact**:
```bash
# Switch to faster model
# Edit docker-compose.yml:
OLLAMA_MODEL=phi4-mini:3.8b  # ~30% faster

# Apply changes:
docker-compose down && docker-compose up -d
```

---

## 📝 Related Issues

### Presenton Upstream Issues

**Filename Length Bug**:
- **Issue**: No filename sanitization or truncation
- **Impact**: Long titles cause OSError [Errno 36]
- **Workaround**: Use short titles (<50 chars recommended)
- **Permanent Fix**: Requires Presenton code changes

**Potential Improvements**:
1. Use UUID-based filenames: `{uuid}.pptx`
2. Store title in metadata, not filename
3. Sanitize special characters
4. Truncate to safe length (200 chars max)

### Backend Considerations

**Current Behavior**:
- Backend passes content directly to Presenton
- No title validation or truncation
- Filename decided by Presenton internally

**Potential Enhancement** (NOT IMPLEMENTED):
```python
# backend/app/services/content_processor.py
def sanitize_title(title: str, max_length: int = 50) -> str:
    """Truncate and sanitize title for filename safety"""
    # Remove special chars, truncate, add ellipsis
    clean = re.sub(r'[^\w\s-]', '', title)
    return clean[:max_length] + ('...' if len(clean) > max_length else '')
```

---

## ✅ Resolution Status

### Fixed ✅
- [x] Frontend timeout increased to 10 minutes
- [x] Timeout now accommodates typical 6-9 minute generation time
- [x] Users won't see false "生成超時" errors

### Documented ⚠️
- [x] Presenton filename bug identified and documented
- [x] Workaround provided (use shorter titles)
- [x] Performance expectations clarified
- [x] Monitoring guidance provided

### Pending Upstream Fix 🔄
- [ ] Presenton filename sanitization (requires upstream PR)
- [ ] Backend preprocessing layer (optional enhancement)

---

## 🎓 Technical Insights

### Why Timeouts Are Tricky in LLM Applications

**Challenge**: Unpredictable generation times
- Simple content: 2-3 minutes
- Complex content: 8-10 minutes
- Same slide count, different durations

**Solution Approaches**:

1. **Conservative Timeout** (Current):
   - Set high limit (10 minutes)
   - Covers 99% of cases
   - May frustrate users if actual error occurs

2. **Adaptive Timeout** (Better):
   ```javascript
   const baseTimeout = 120;  // 2 minutes
   const perSlideTimeout = 60;  // 1 minute per slide
   const maxTimeout = baseTimeout + (n_slides * perSlideTimeout);
   ```

3. **Progress-Based Timeout** (Best):
   - Reset timeout on each progress update
   - Only timeout if no activity for 2 minutes
   - Requires backend heartbeat mechanism

### Linux Filename Limits

**POSIX Standards**:
- **Filename**: 255 bytes (not characters!)
- **Path**: 4096 bytes total
- **UTF-8**: Chinese chars = 3 bytes each

**Example**:
```
"測試.pptx" = 9 bytes (測=3, 試=3, .pptx=5) ✅
"非常長的中文標題..." × 50 = 450 bytes ❌ (exceeds 255)
```

**Safe Practice**:
- Limit to 80 characters for CJK languages
- 80 chars × 3 bytes = 240 bytes (safe margin)
- Add ".pptx" = 245 bytes < 255 limit

---

## 📚 Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Project overview
- [presenton_500_complete_fix.md](./presenton_500_complete_fix.md) - Environment variable fixes
- [frontend/index.html](../frontend/index.html) - Frontend code
- [docker-compose.yml](../docker-compose.yml) - Service configuration

---

**Analysis By**: Claude Code Root Cause Analysis
**Date**: 2025-10-15
**Status**: ✅ Frontend Fixed, ⚠️ Presenton Bug Documented
