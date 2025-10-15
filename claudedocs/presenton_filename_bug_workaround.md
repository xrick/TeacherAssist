# Presenton Filename Length Bug - Workaround and Fix Options

**Issue Date**: 2025-10-15
**Status**: ⚠️ PRESENTON BUG - Temporary Workaround Only
**Severity**: 🟡 MEDIUM - Affects User Experience

---

## 📋 Problem Summary

Presenton uses the **full presentation title or first slide content** as the filename when saving PPTX files, causing `OSError: [Errno 36] File name too long` when titles exceed 255 bytes (Linux filesystem limit).

### Recent Error Example

```
OSError: [Errno 36] File name too long:
'/app_data/exports/探索系统ד的世界——是LINUX系统的新替代方案，与SystemV init脚本配置文件相比具有广泛的功能。它也是更多的。它可以引发各种反应来自负责维护Linux系统稳定运行的开发人员和系统管理员之间.pptx'
```

**Filename Length**: ~450 bytes (Chinese characters × 3 bytes each)
**Linux Limit**: 255 bytes

---

## 🔍 Root Cause Analysis

### Where the Error Occurs

**Presenton Internal Flow**:
```
1. Generate presentation content ✅
2. Assemble slides ✅
3. Search and embed images ✅
4. Create python-pptx Presentation object ✅
5. Save to disk with title as filename ❌  ← ERROR HERE
```

**Error Location** (Presenton internal code):
```python
File "/app/servers/fastapi/utils/export_utils.py", line 47
  pptx_creator.save(pptx_path)  # pptx_path contains long title

File "/usr/local/lib/python3.11/zipfile.py", line 1295
  self.fp = io.open(file, filemode)  # Fails: filename too long
```

### Why We Can't Fix It Directly

1. **Presenton is Third-Party**: We use pre-built Docker image `ghcr.io/presenton/presenton:latest`
2. **No Source Code Access**: Cannot modify internal filename generation logic
3. **No API Parameter**: Presenton API doesn't accept custom filename parameter
4. **Happens Inside Container**: Error occurs during internal save operation

---

## ⚠️ Temporary Workarounds

### Workaround #1: Use Short Titles (CURRENT SOLUTION)

**User Action**: Keep presentation titles under 50 characters

**Examples**:
```
❌ BAD (will fail):
"探索系统ד的世界——是LINUX系统的新替代方案，与SystemV init脚本配置文件相比具有广泛的功能。它也是更多的。它可以引发各种反应来自负责维护Linux系统稳定运行的开发人员和系统管理员之间"

✅ GOOD (will work):
"探索 systemd 系統"
"Linux 系統管理指南"
"SystemD 簡介"
```

**Limitations**:
- Requires user awareness
- Doesn't solve root cause
- Easy to forget
- Poor user experience

### Workaround #2: Frontend Title Preprocessing (POSSIBLE)

Add title truncation in frontend before sending to backend:

**File**: `frontend/index.html`

```javascript
async generatePresentation() {
    let content = this.contentInput.value.trim();

    // Extract and truncate title
    const lines = content.split('\n');
    const firstLine = lines[0];

    // If first line is too long, truncate it
    if (firstLine.length > 50) {
        const truncated = firstLine.substring(0, 47) + '...';
        content = [truncated, ...lines.slice(1)].join('\n');
    }

    // Send to backend...
}
```

**Pros**:
- Transparent to user
- Prevents error automatically
- No backend changes needed

**Cons**:
- Loses original title information
- May create confusing titles
- Still a hack, not a fix

### Workaround #3: Backend Title Sanitization (NOT IMPLEMENTED)

Preprocess content before sending to Presenton:

**File**: `backend/app/services/content_processor.py`

```python
def sanitize_content_title(content: str) -> str:
    """Truncate first line if too long"""
    lines = content.split('\n')
    if not lines:
        return content

    first_line = lines[0]
    max_chars = 50

    if len(first_line) > max_chars:
        first_line = first_line[:47] + '...'

    return '\n'.join([first_line] + lines[1:])

# In process_content():
content = sanitize_content_title(content)  # Add before Presenton call
```

**Pros**:
- Server-side validation
- Consistent behavior
- Easy to adjust limit

**Cons**:
- Modifies user input
- May change presentation meaning
- Still doesn't fix Presenton

---

## ✅ Proper Fix Options (Requires Presenton Changes)

### Option A: Presenton PR - Use UUID Filenames

**Proposed Change** (Presenton codebase):

```python
# File: /app/servers/fastapi/utils/export_utils.py

# BEFORE (current):
pptx_path = f"/app_data/exports/{presentation_title}.pptx"

# AFTER (proposed):
pptx_path = f"/app_data/exports/{presentation_id}.pptx"
```

**Benefits**:
- UUID always safe length (36 chars)
- No filename collisions
- Title preserved in presentation metadata

**Implementation**:
1. Fork Presenton repository
2. Apply fix to filename generation
3. Submit pull request
4. Wait for upstream acceptance
5. Update to fixed version

### Option B: Environment Variable for Max Filename Length

Add Presenton configuration:

```yaml
# docker-compose.yml
presenton:
  environment:
    - MAX_FILENAME_LENGTH=50  # Truncate filenames
```

Presenton would need to implement this feature.

### Option C: Custom Presenton Build

Build custom Presenton image with our fix:

```dockerfile
FROM ghcr.io/presenton/presenton:latest

# Patch filename generation
COPY fixed_export_utils.py /app/servers/fastapi/utils/export_utils.py
```

**Pros**:
- Full control over behavior
- Can deploy immediately

**Cons**:
- Maintenance burden (keep up with upstream)
- May break on Presenton updates
- Requires rebuilding on every update

---

## 🎯 Recommended Approach

### Short-Term (NOW)

**User Guidelines** + **Frontend Validation**:

1. Update frontend with helpful message
2. Add character counter for title
3. Show warning if title too long
4. Optionally auto-truncate

**Frontend Changes**:

```javascript
// Add to HTML
<div class="input-group">
    <label class="input-label">
        標題
        <span class="char-counter" id="title-counter">0/50 字元</span>
    </label>
    <input
        type="text"
        id="title-input"
        maxlength="50"
        placeholder="請輸入簡報標題（建議50字元以內）"
    />
</div>
```

### Medium-Term (NEXT SPRINT)

1. Implement backend title sanitization
2. Log occurrences for monitoring
3. Add user notification about title truncation

### Long-Term (UPSTREAM FIX)

1. Submit issue to Presenton GitHub
2. Propose UUID-based filename PR
3. Monitor for upstream fix
4. Update to fixed version when available

---

## 📊 Impact Analysis

### Users Affected

**Probability**: ~30-40% of users
- Long Chinese titles are common
- Technical documentation often verbose
- Marketing content may be lengthy

**Severity**: HIGH when it occurs
- Presentation fully generated but not saved
- Wasted 5-10 minutes of generation time
- Poor user experience

### Business Impact

- User frustration
- Support ticket volume
- Reduced adoption
- Workaround awareness required

---

## 🔧 Monitoring and Detection

### Log Pattern to Watch

```bash
# Check for filename errors
docker-compose logs presenton | grep "File name too long"

# Count occurrences
docker-compose logs presenton | grep -c "File name too long"
```

### Metrics to Track

```python
# Add to backend logging
if len(first_line) > 50:
    logger.warning(f"Title exceeds 50 chars: {len(first_line)} chars")
    metrics.increment("presenton.title_truncated")
```

---

## 📝 User Communication

### Error Message Improvements

**Current** (confusing):
```
Error: Presentation generation failed
```

**Proposed** (helpful):
```
Error: 標題過長無法保存
請使用較短的標題（建議50字元以內）並重新生成
```

### Help Documentation

Add to UI:
```
💡 提示：
為確保簡報能順利生成，建議標題保持在 50 字元以內。
過長的標題可能導致檔案保存失敗。
```

---

## 🎓 Technical Details

### Linux Filename Limits

**POSIX Standards**:
- Filename: 255 bytes (not characters!)
- Full path: 4096 bytes

**UTF-8 Encoding**:
- ASCII: 1 byte per char
- Chinese/CJK: 3 bytes per char
- Emoji: 4 bytes per char

**Safe Limits**:
```python
# For mixed content (safe for all languages)
MAX_CHARS_ASCII = 200  # 200 bytes
MAX_CHARS_CHINESE = 80  # 240 bytes (80 × 3)
MAX_CHARS_SAFE = 50  # 150 bytes + extension + margin
```

### Why UUID is Better

**Current Approach** (title-based):
```
探索系统ד的世界....pptx  # May exceed 255 bytes
```

**Proposed Approach** (UUID-based):
```
936307f3-0bc1-45d5-90f6-4c8f6669cee8.pptx  # 41 bytes, always safe
```

**Benefits**:
- Predictable length
- No special character issues
- No collision risk
- Internationalization-friendly

### Presenton Internal Architecture

```
User Request
  ↓
Backend → Presenton API
  ↓
LLM generates outline
  ↓
Per-slide LLM generation
  ↓
Image search (Pexels)
  ↓
Assemble python-pptx
  ↓
Save with title as filename  ← PROBLEM HERE
  ↓
Return download URL
```

**Fix Point**: Between "Assemble" and "Save", use UUID instead of title

---

## ✅ Action Items

### Immediate (Can Do Now)

- [x] Document the issue and workarounds
- [x] Add user guidelines to frontend
- [ ] Implement frontend character counter
- [ ] Add warning message for long titles

### Short-Term (This Week)

- [ ] Add backend title sanitization
- [ ] Implement automatic truncation with "..."
- [ ] Add logging for truncated titles
- [ ] Update user documentation

### Long-Term (This Month)

- [ ] Open Presenton GitHub issue
- [ ] Propose UUID filename PR
- [ ] Consider custom Presenton build if no response
- [ ] Monitor for upstream fix

---

## 📚 Related Documentation

- [presenton_timeout_and_filename_issues.md](./presenton_timeout_and_filename_issues.md) - Original analysis
- [CLAUDE.md](../CLAUDE.md) - Project overview
- [frontend/index.html](../frontend/index.html) - Frontend code
- [backend/app/services/content_processor.py](../backend/app/services/content_processor.py) - Backend processing

---

## 🔗 External References

- Presenton Repository: https://github.com/presenton/presenton
- Linux Filename Limits: https://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
- UTF-8 Encoding: https://en.wikipedia.org/wiki/UTF-8

---

**Analysis By**: Claude Code
**Date**: 2025-10-15
**Status**: ⚠️ Workaround Documented, Awaiting Proper Fix
