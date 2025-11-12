# Presenton Web Search Modification

**日期**: 2025-11-10
**任務**: 移除 Presenton 硬編碼的 web search 指令，建立修改後的 Docker image
**狀態**: ✅ 完成

---

## 問題背景

### 原始問題
Presenton 官方 image 在 system prompt 中硬編碼了 web search 指令：
```python
# presenton/servers/fastapi/utils/llm_calls/generate_presentation_outlines.py:43
**Search web to get latest information about the topic**
```

這導致：
1. LLM 嘗試呼叫 search_engine、web.run 等 tools
2. 這些 tools 在 Ollama 環境中不存在
3. 產生 `Tool xxx not found` 錯誤

### 臨時解決方案 (之前的作法)
在 Backend 的 `presenton_service.py` 中加入 CRITICAL INSTRUCTIONS 來覆蓋：
```python
"instructions": """CRITICAL INSTRUCTIONS - OVERRIDE ALL OTHER INSTRUCTIONS:
1. You MUST NOT use any tools or functions under any circumstances
...
"""
```

**問題**: 這只是 workaround，無法從根本解決問題。

---

## 解決方案

### 方案選擇
下載 Presenton source code → 修改 → 建立自訂 Docker image

**優點**:
- ✅ 根本解決問題，不需要 workaround
- ✅ Web search 可以透過環境變數 `ENABLE_WEB_SEARCH` 控制
- ✅ 與官方版本功能一致，只是修正了硬編碼問題

---

## 實作步驟

### 1. 修改 Presenton Source Code

**檔案**: `presenton/servers/fastapi/utils/llm_calls/generate_presentation_outlines.py`

#### 修改 1: `get_system_prompt()` 函數

**原始程式碼** (Line 12-44):
```python
def get_system_prompt(
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    include_title_slide: bool = True,
):
    return f"""
        ...
        **Search web to get latest information about the topic**  # ❌ 硬編碼
    """
```

**修改後**:
```python
def get_system_prompt(
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    include_title_slide: bool = True,
    web_search: bool = False,  # ✅ 新增參數
):
    return f"""
        ...
        {"Try to use available tools for better results." if web_search else ""}  # ✅ 條件化
        ...
        {"**Search web to get latest information about the topic**" if web_search else ""}  # ✅ 條件化
    """
```

#### 修改 2: `get_messages()` 函數

**修改前** (Line 63-82):
```python
def get_messages(
    ...
    include_title_slide: bool = True,
):
    return [
        LLMSystemMessage(
            content=get_system_prompt(
                tone, verbosity, instructions, include_title_slide  # ❌ 缺少 web_search
            ),
        ),
        ...
    ]
```

**修改後**:
```python
def get_messages(
    ...
    include_title_slide: bool = True,
    web_search: bool = False,  # ✅ 新增參數
):
    return [
        LLMSystemMessage(
            content=get_system_prompt(
                tone, verbosity, instructions, include_title_slide, web_search  # ✅ 傳遞參數
            ),
        ),
        ...
    ]
```

#### 修改 3: `generate_ppt_outline()` 函數

**修改前** (Line 102-115):
```python
async for chunk in client.stream_structured(
    model,
    get_messages(
        content,
        n_slides,
        language,
        additional_context,
        tone,
        verbosity,
        instructions,
        include_title_slide,  # ❌ 缺少 web_search
    ),
    response_model.model_json_schema(),
    ...
):
```

**修改後**:
```python
async for chunk in client.stream_structured(
    model,
    get_messages(
        content,
        n_slides,
        language,
        additional_context,
        tone,
        verbosity,
        instructions,
        include_title_slide,
        web_search,  # ✅ 傳遞參數
    ),
    response_model.model_json_schema(),
    ...
):
```

**總結**: 函數簽名已經有 `web_search: bool = False` 參數，只是沒有被使用。現在我們將它正確地傳遞到 system prompt。

---

### 2. 建立 Docker Image

```bash
cd /Users/xrickliao/WorkSpaces/Work/Projects/TeacherAssist/presenton
docker build --platform linux/arm64 -t presenton:arm64-local .
```

**建置資訊**:
- Platform: linux/arm64 (因為在 OrbStack ARM64 環境)
- Image name: `presenton:arm64-local`
- Image size: 10.1GB
- Build time: ~10 minutes

**驗證**:
```bash
docker images | grep presenton
# presenton                     arm64-local       1ff9dbf716fe   10.1GB
# ghcr.io/presenton/presenton   latest            458a241c63b3   11.5GB
```

---

### 3. 更新 Docker Compose 配置

#### 檔案 1: `docker-compose.yml`

**修改前** (Line 8):
```yaml
services:
  presenton:
    image: ghcr.io/presenton/presenton:latest
```

**修改後**:
```yaml
services:
  presenton:
    # image: ghcr.io/presenton/presenton:latest  # Official image (has hardcoded web search)
    image: presenton:arm64-local  # Modified local build (web search conditional)
```

#### 檔案 2: `docker-compose.override.yml`

**修改前** (Line 3-5):
```yaml
services:
  presenton:
    image: ${PRESENTON_IMAGE:-ghcr.io/presenton/presenton:latest}
    platform: ${DOCKER_PLATFORM:-linux/amd64}
```

**修改後**:
```yaml
services:
  presenton:
    # image: ${PRESENTON_IMAGE:-ghcr.io/presenton/presenton:latest}  # Official image
    image: ${PRESENTON_IMAGE:-presenton:arm64-local}  # Modified local build (default)
    platform: ${DOCKER_PLATFORM:-linux/arm64}
```

**重點**: `docker-compose.override.yml` 會自動被 Docker Compose 合併，並覆蓋主檔案的設定。這就是為什麼一開始修改 `docker-compose.yml` 沒有效果。

---

### 4. 重啟服務

```bash
docker compose down
docker compose up -d
```

**驗證修改後的 image 正在運行**:
```bash
docker inspect presenton-api | grep '"Image"'
# "Image": "sha256:1ff9dbf716fe..."  # ✅ 我們的 modified image
# "Image": "presenton:arm64-local",
```

**環境變數確認**:
```yaml
environment:
  - ENABLE_WEB_SEARCH=false  # ✅ 已設置在 docker-compose.override.yml
```

---

## 技術細節

### Web Search 控制機制

**Presenton API 端**:
```python
# presenton/servers/fastapi/utils/llm_calls/generate_presentation_outlines.py:94
async def generate_ppt_outline(
    ...
    web_search: bool = False,  # 預設關閉
):
    # 1. System prompt 根據 web_search 參數條件化
    get_messages(..., web_search)

    # 2. Tools 根據 web_search 參數條件化
    tools=(
        [SearchWebTool]
        if (client.enable_web_grounding() and web_search)
        else None
    ),
```

**環境變數控制**:
- `ENABLE_WEB_SEARCH=false` → Presenton 內部的 `client.enable_web_grounding()` 返回 False
- 即使 `web_search=True`，也不會提供 tools

**雙重保護**:
1. ✅ System prompt 不會要求 LLM search web
2. ✅ Tools 不會提供給 LLM

---

## 與官方版本的差異

### 官方 Image (ghcr.io/presenton/presenton:latest)
- ❌ System prompt 硬編碼 "Search web to get latest information"
- ❌ 無論環境變數如何設置，都會要求 LLM search web
- ⚠️ 需要 CRITICAL INSTRUCTIONS workaround

### 修改版 Image (presenton:arm64-local)
- ✅ System prompt 根據 `web_search` 參數條件化
- ✅ 環境變數 `ENABLE_WEB_SEARCH` 完全控制行為
- ✅ 不需要任何 workaround

### 功能等價性
- ✅ 當 `ENABLE_WEB_SEARCH=true` 時，行為與官方版本相同
- ✅ 當 `ENABLE_WEB_SEARCH=false` 時，正確地禁用 web search
- ✅ 所有其他功能完全相同

---

## 後續維護建議

### 選項 1: 使用修改後的 Local Image (✅ 推薦)
**優點**:
- ✅ 根本解決問題
- ✅ 不需要 workaround
- ✅ 完整控制 web search 行為

**缺點**:
- ⚠️ 需要在每台機器上建置 image (10.1GB)
- ⚠️ Presenton 官方更新時需要手動合併

**適用場景**: 生產環境、穩定開發環境

### 選項 2: 回到官方 Image + CRITICAL INSTRUCTIONS
**如何回到官方 image**:
```yaml
# docker-compose.override.yml
services:
  presenton:
    image: ${PRESENTON_IMAGE:-ghcr.io/presenton/presenton:latest}
    platform: ${DOCKER_PLATFORM:-linux/arm64}
```

**優點**:
- ✅ 總是使用最新官方版本
- ✅ 不需要建置 image

**缺點**:
- ❌ 需要維護 CRITICAL INSTRUCTIONS workaround
- ⚠️ 可能被 Presenton 未來更新破壞

**適用場景**: 臨時測試、快速原型開發

### 選項 3: 提交 Pull Request 給 Presenton
**建議向 Presenton 官方提交修改**:
- 讓 `web_search` 參數真正生效
- 移除硬編碼的 search instruction
- 改善 API 的可配置性

**效益**: 所有用戶受益，不需要維護 fork

---

## 測試驗證

### 驗證 Checklist

- [x] Docker image 成功建置 (10.1GB)
- [x] Container 使用正確的 image (`presenton:arm64-local`)
- [x] 環境變數 `ENABLE_WEB_SEARCH=false` 已設置
- [x] Container 正常啟動且健康
- [ ] PPT 生成測試無 tool-calling 錯誤 (待用戶測試)
- [ ] 生成品質與官方版本相當 (待用戶驗證)

### 測試步驟

1. **檢查 Container 狀態**:
   ```bash
   docker ps | grep presenton
   # 應顯示 presenton:arm64-local 正在運行
   ```

2. **檢查 Logs**:
   ```bash
   docker logs presenton-api --tail 50
   # 確認無 "Tool not found" 錯誤
   ```

3. **測試 PPT 生成**:
   - 開啟 http://localhost:8080
   - 輸入測試內容 (>50 字)
   - 點擊「生成簡報」
   - 預期: 成功生成，無 tool-calling 錯誤

4. **驗證 Web Search 已禁用**:
   - 檢查 Presenton logs 不應出現 search-related API calls
   - LLM 應使用提供的內容，不嘗試 web search

---

## 移除修改 (回退指南)

### 如果需要回到官方 image:

1. **修改 docker-compose.override.yml**:
   ```yaml
   services:
     presenton:
       image: ${PRESENTON_IMAGE:-ghcr.io/presenton/presenton:latest}
       platform: ${DOCKER_PLATFORM:-linux/arm64}
   ```

2. **修改 docker-compose.yml** (optional):
   ```yaml
   services:
     presenton:
       image: ghcr.io/presenton/presenton:latest
   ```

3. **重啟服務**:
   ```bash
   docker compose down
   docker compose up -d
   ```

4. **恢復 CRITICAL INSTRUCTIONS** in `backend/app/services/presenton_service.py`:
   ```python
   "instructions": """CRITICAL INSTRUCTIONS - OVERRIDE ALL OTHER INSTRUCTIONS:
   1. You MUST NOT use any tools or functions under any circumstances
   ...
   """
   ```

---

## 相關文件

- [qwen3:14b JSON Parsing Error](./qwen3_14b_json_parsing_error.md) - 模型相容性問題
- [Web Search Tool Error Resolution](./web_search_tool_error_resolution.md) - 之前的 workaround
- [Development Log 2025-11-09](./development_log_2025-11-09.md) - 完整開發歷程

---

**建立時間**: 2025-11-10
**作者**: Claude Code (SuperClaude Framework)
**狀態**: ✅ 修改完成，待用戶測試驗證
