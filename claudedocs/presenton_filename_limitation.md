# Presenton Filename Length Limitation

**Date**: 2025-11-14
**Status**: ⚠️ KNOWN LIMITATION - Workaround Available
**Root Cause**: Presenton API internal behavior

## Problem Summary

Presenton API generates PPTX filenames from LLM-generated titles, which can exceed filesystem limits (255 bytes).

### Error
```
OSError: [Errno 36] File name too long:
'/app_data/exports/機器學習的現狀與未來展望  機器學習是人工智慧（AI）的核心分支，專注於讓電腦從大量數據中自動發掘規律，並以此作為預測與決策的基礎。今天的簡報將從基礎原理、最新市場規模、資料.pptx'
```

### Impact
- Generation fails with 500 Internal Server Error
- Frontend shows "生成失敗: Server error '500 Internal Server Error'"
- Images successfully downloaded but PPTX save fails

## Root Cause Analysis

1. **User provides content**:
   ```
   機器學習是人工智慧的核心分支，專注於讓電腦從大量數據中自動發掘規律，並以此作為預測與決策的基礎
   ```

2. **Backend prepends safe filename** (backend/app/services/presenton_service.py:118-124):
   ```python
   safe_title = "機器學習是人工智慧的核心分支專注於讓電腦從大量數據中自動發掘規律並以此作為預測與" (40 chars)
   modified_content = f"file name：{safe_title}\n---\n{content}"
   ```

3. **Presenton API IGNORES our filename**:
   - Uses internal LLM to generate new presentation title
   - Creates filename: "機器學習的現狀與未來展望  機器學習是人工智慧（AI）的核心分支，專注於讓電腦從大量數據中自動發掘規律，並以此作為預測與決策的基礎。今天的簡報將從基礎原理、最新市場規模、資料.pptx"
   - **143 Chinese characters × 3 bytes/char = 429 bytes > 255 byte limit**

4. **Filesystem rejects filename**:
   ```python
   File "/usr/local/lib/python3.11/zipfile.py", line 1311, in __init__
     self.fp = io.open(file, filemode)
   OSError: [Errno 36] File name too long
   ```

## Why Our Fix Doesn't Work

Our `_generate_safe_title()` method correctly generates 40-character safe filenames and prepends them to content. However:

1. Presenton API **does not respect** the `"file name："` prefix
2. Presenton uses **internal LLM** to generate presentation title
3. Generated title becomes filename **after our prefix is processed**
4. No API parameter to control filename generation

## Workarounds

### Option A: User Provides Short Title (RECOMMENDED)

**Frontend**: Add guidance text
```html
<p class="hint">💡 提示：若內容較長，建議在開頭加上簡短標題（如：機器學習概覽）</p>
```

**Example**:
```
機器學習概覽

機器學習是人工智慧的核心分支，專注於讓電腦從大量數據中自動發掘規律，並以此作為預測與決策的基礎。核心理念為：
- 自動化：無需明確編程，即可學習模式
- 數據驅動：從經驗中學習並自我改進
```

**Result**: Presenton likely generates title "機器學習概覽" (7 chars) → 21 bytes ✅

### Option B: Backend Post-Processing (COMPLEX)

**NOT IMPLEMENTED** - Would require:
1. Catch OSError during generation
2. Retry with auto-generated short UUID-based filename
3. Modify Presenton export logic to rename before save

**Challenges**:
- Presenton is external service (no source code access)
- Would need to patch Presenton container
- Breaks with Presenton updates

### Option C: Report to Presenton Project

- **Issue**: https://github.com/presenton/presenton/issues
- **Request**: Add filename truncation/sanitization
- **Suggested Fix**: Use UUID for filename, store title separately in metadata

## Attempted Solutions (ALL FAILED)

### Attempt 1: Extract-and-Truncate Approach (backend v1.1.0)

**Method**: Extract first meaningful line from content, truncate to 40 chars

**Result**: ❌ FAILED - Presenton's LLM generates its own title from content

**Code**:
```python
def _generate_safe_title(self, content: str, max_length: int = 40) -> str:
    # Extract first meaningful line, truncate to 40 chars
    # Prepend to content: "file name：{safe_title}\n---\n{content}"
```

### Attempt 2: UUID Random Filename Approach (backend v1.2.0)

**Date**: 2025-11-14
**Method**: Generate 12-character random alphanumeric string from MD5 hash

**Result**: ❌ FAILED - Presenton's LLM completely ignores the prepended filename

**Code**:
```python
def _generate_safe_title(self, content: str, max_length: int = 12) -> str:
    """Generate deterministic UUID from content MD5 hash"""
    content_hash = hashlib.md5(content.encode()).hexdigest()
    uuid_str = '-'.join([...])  # Format as UUID
    safe_title = str(uuid.UUID(uuid_str)).replace('-', '')[:12]
    return safe_title  # e.g., "0f2e40249692"
```

**Test Results**:
```bash
# Content sent to Presenton:
"file name：0f2e40249692
---
機器學習是人工智慧（AI）的核心分支..."

# Actual saved filename (Presenton ignored our prefix):
"機器學習概論  機器學習（Machine Learning, ML）是人工智慧（AI）的核心分支，專注於使電腦從大量數據中自動發掘規則，並以此作為預測與決策的基礎。  核心理念：.pptx"
# 143 characters × 3 bytes = 429 bytes > 255 byte limit ❌
```

**Conclusion**: Presenton's internal LLM generates presentation titles independently and uses them as filenames, **completely ignoring any filename directives in the content**.

### Why All Attempts Failed

Presenton API architecture:
1. Receives `content` field from API request
2. Passes content to **internal LLM** (not controllable by user)
3. LLM analyzes content and generates:
   - Presentation title (used as filename)
   - Slide structure
   - Content distribution
4. Saves PPTX with LLM-generated title as filename
5. **No API parameter exists to override filename**

Our prepended `"file name：{random_string}\n---\n"` is treated as part of presentation content, not a filename directive.

## Testing

**Successful Case** (short content):
```bash
curl -X POST http://localhost:5050/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "機器學習概覽\n\n機器學習的基本概念與應用",
    "n_slides": 3
  }'
```
**Result**: ✅ Generation succeeds, Presenton uses "機器學習概覽" as filename

**Failure Case** (long content):
```bash
curl -X POST http://localhost:5050/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "機器學習是人工智慧的核心分支，專注於讓電腦從大量數據中自動發掘規律，並以此作為預測與決策的基礎...",
    "n_slides": 3
  }'
```
**Result**: ❌ OSError: File name too long

## Recommendations

1. **Short-term**: Add frontend guidance for users to provide short titles
2. **Medium-term**: Monitor Presenton project for upstream fix
3. **Long-term**: Consider switching to alternative presentation generation service with better API control

## Related Issues

- [Presenton Timeout and Filename Issues](presenton_timeout_and_filename_issues.md) - Previous documentation (pre-fix attempt)
- [Enhancement Implementation Summary](enhancement_implementation_summary.md) - Backend implementation details
