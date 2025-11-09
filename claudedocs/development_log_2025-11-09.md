# 開發日誌 - 2025-11-09

**專案**: TeacherAssist PPT 生成系統
**主要任務**: 解決 Tool 呼叫錯誤、模型切換、系統優化

---

## 📋 今日工作摘要

1. ✅ 解決 Web Search Tool 錯誤問題
2. ✅ 修復 Pydantic 配置驗證錯誤
3. ✅ 模型切換：從 gpt-oss:20b 改為 qwen3:14b
4. ✅ 建立完整的問題診斷文件
5. ✅ 優化 Ollama Service 程式碼建議

---

## 🐛 問題 1: Web Search Tool 持續錯誤

### 問題演進歷程

#### v1: 初始錯誤 - `Tool search not found`
**時間**: 2025-11-09 上午

**錯誤訊息**:
```
fastapi.exceptions.HTTPException: 500: Tool search not found
```

**原因**: Presenton API 的 LLM 嘗試呼叫 search tool，但沒有設定 search provider

**解決方案**: 新增環境變數
```yaml
# docker-compose.yml & docker-compose.override.yml
environment:
  - ENABLE_WEB_SEARCH=false
```

**結果**: ⚠️ 部分修復，但問題持續

---

#### v2: 錯誤變化 - `Tool search_engine not found`

**錯誤訊息**:
```
fastapi.exceptions.HTTPException: 500: Tool search_engine not found
```

**觀察**: LLM 換了不同的 tool 名稱嘗試呼叫

**根本原因發現**:
經過深入調查 Presenton 原始碼，發現問題出在：

**檔案**: `/app/servers/fastapi/utils/llm_calls/generate_presentation_outlines.py`

**硬編碼的 System Prompt**:
```python
**Search web to get latest information about the topic**
```

這個指令是**寫死在 system prompt 中**，無論 `web_search` 參數或 `ENABLE_WEB_SEARCH` 環境變數如何設定，LLM 都會看到這個指令。

**Tool 註冊邏輯**:
```python
tools=(
    [SearchWebTool]
    if (client.enable_web_grounding() and web_search)
    else None
),
```

- `client.enable_web_grounding()` 對 Ollama 回傳 `False` ✓
- `web_search` 參數設為 `False` ✓
- 結果：`tools = None` (正確)

**矛盾點**:
- System prompt 說：「請搜尋網路獲取最新資訊」
- Tools 實際上：None (沒有提供任何工具)
- LLM 行為：遵循 prompt 指令，嘗試呼叫工具 → 錯誤

---

#### v3: 解決方案 - 覆寫 System Prompt

**發現**: Presenton API 接受 `instructions` 參數可以覆寫預設的 system prompt

**API Request Model**:
```python
class GeneratePresentationRequest(BaseModel):
    instructions: Optional[str] = Field(
        default=None,
        description="The instruction for generating the presentation"
    )
    web_search: bool = Field(
        default=False,
        description="Whether to enable web search"
    )
```

**實作方案 v1** (溫和指令):
```python
# backend/app/services/presenton_service.py
payload = {
    # ... 其他欄位 ...
    "instructions": "Generate presentation outline based on provided content only. Do not search for external information. Focus on structuring the content into clear, well-organized slides."
}
```

**結果**: ❌ 失敗，LLM 仍嘗試呼叫工具

---

#### v4: 錯誤再變化 - `Tool web.run not found`

**錯誤訊息**:
```
fastapi.exceptions.HTTPException: 500: Tool web.run not found
```

**觀察**: LLM 又換了另一個 tool 名稱

**Tool 錯誤演進模式**:
1. `search` (初始嘗試)
2. `search_engine` (第一次修復後)
3. `web.run` (第二次修復後)

**結論**: LLM 有強烈的 tool-calling 傾向，簡單的指令無法阻止

---

#### v5: 強化指令 - CRITICAL INSTRUCTIONS

**最終實作**:
```python
# backend/app/services/presenton_service.py:46-54
"instructions": """CRITICAL INSTRUCTIONS - OVERRIDE ALL OTHER INSTRUCTIONS:
1. You MUST NOT use any tools or functions under any circumstances
2. You MUST NOT call web.run, search_engine, search_web, or any other tool
3. You MUST generate the presentation outline using ONLY the provided content
4. You MUST NOT search for external information or additional data
5. Work exclusively with the content given - no external lookups allowed
6. If you attempt to use any tool, the request will fail

Generate a clear, well-structured presentation outline based solely on the provided content."""
```

**策略**:
- 全大寫關鍵字：CRITICAL, MUST NOT, OVERRIDE
- 明確列出禁止的 tool 名稱
- 多重強調相同限制
- 警告後果：「嘗試使用工具會導致失敗」

**狀態**: ⏳ 等待測試驗證

---

### 為什麼會有這個問題？

#### gpt-oss:20b 模型分析

**模型特性**:
```
Capabilities:
  completion
  tools         ← 支援 tool calling
  thinking
```

**內建 Tool 支援**:
從 modelfile 可以看到模型內建支援：
- `browser.search` - 網頁搜尋
- `browser.open` - 開啟連結
- `browser.find` - 尋找內容
- `python` - Python 程式執行
- Custom functions - 自訂函數工具

**Template 結構**:
```
{{- if .Tools -}}
  {{- range .Tools }}
    {{- if eq .Function.Name "browser.search" -}}{{- $hasBrowserSearch = true -}}
    {{- else if eq .Function.Name "python" -}}{{- $hasPython = true -}}
    {{- else }}{{ $hasNonBuiltinTools = true -}}
  {{- end }}
{{- end }}
```

**結論**: gpt-oss:20b 是專門為 tool-calling 設計的模型，有強烈的工具呼叫傾向

---

## 🐛 問題 2: Pydantic 驗證錯誤

### 錯誤描述

**時間**: 切換模型到 qwen3-vl:4b-instruct-bf16 時

**錯誤訊息**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
ollama_model
  Extra inputs are not permitted [type=extra_forbidden, input_value='phi4:latest', input_type=str]
```

### 根本原因

**檔案**: `backend/app/config.py` 第 14 行

**錯誤程式碼**:
```python
ollama_mode: str = "qwen3-vl:4b-instruct-bf16"  # ❌ 錯字！
```

**正確應為**:
```python
ollama_model: str = "qwen3-vl:4b-instruct-bf16"  # ✅
```

### 問題分析

1. **Pydantic Settings 行為**:
   - `Settings` class 定義了 `ollama_model` 欄位
   - 環境變數或其他來源提供了 `ollama_mode` 值
   - Pydantic 發現未定義的欄位 → 拋出 validation error

2. **錯誤訊息誤導**:
   - 錯誤訊息顯示 `input_value='phi4:latest'`
   - 實際問題是欄位名稱錯誤，不是值的問題

### 解決方案

**修復**:
```python
# backend/app/config.py:14
ollama_model: str = "qwen3-vl:4b-instruct-bf16"  # mode → model
```

**驗證**:
```bash
docker compose restart backend
curl http://localhost:5050/api/health
# {"status": "healthy", ...} ✓
```

---

## 🔄 問題 3: Vision-Language 模型不適用

### 模型選擇錯誤

**初始選擇**: `qwen3-vl:4b-instruct-bf16`

**問題**:
- `vl` 代表 Vision-Language (視覺語言模型)
- 設計用於處理**圖片 + 文字**的任務
- TeacherAssist 只處理**純文字**任務

**後果**:
- VL 模型在純文字任務上表現較差
- 可能產生不相關或品質低落的內容
- 浪費運算資源（VL 模型通常更大、更慢）

### 建議方案

**可用的純語言模型**:
```bash
$ ollama list | grep -v "vl"

deepseek-r1:1.5b         1.1 GB  # 太小，品質可能不足
phi4-mini:3.8b           2.5 GB  # 小而快，無 tool-calling
qwen3:4b                 2.6 GB  # 中等品質，Qwen 系列
qwen3:14b                9.3 GB  # 大模型，高品質 ← 最終選擇
deepseek-r1:7b           4.7 GB  # 推理能力強
phi4:latest              9.1 GB  # 大型 Phi 模型
```

**最終選擇**: `qwen3:14b`

**選擇理由**:
1. ✅ **大參數量** (14.8B) - 高品質生成
2. ✅ **Qwen 系列** - 專門優化中文能力
3. ✅ **大 Context Window** (40,960 tokens) - 處理長內容
4. ✅ **純語言模型** - 適合文字任務
5. ⚠️ **有 Tool Capability** - 需要強指令防止 tool calling

---

## ⚙️ 最終配置

### Backend 配置

**檔案**: `backend/app/config.py`

```python
class Settings(BaseSettings):
    # Presenton Configuration
    presenton_api_url: str = "http://presenton:8000"
    presenton_api_key: str

    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:14b"  # ← 最終模型選擇

    # Pexels Configuration
    pexels_api_key: str

    # Backend Configuration
    backend_port: int = 5000
    cors_origins: str = "*"
    debug: bool = True

    # File paths
    output_dir: str = "./output"
```

### Presenton Service 配置

**檔案**: `backend/app/services/presenton_service.py`

```python
payload = {
    "content": content,
    "n_slides": n_slides,
    "language": "zh-TW",
    "tone": "default",
    "verbosity": "standard",
    "web_search": False,
    "include_table_of_contents": False,
    "include_title_slide": True,
    "export_as": "pptx",

    # ← 關鍵修復：覆寫 system prompt
    "instructions": """CRITICAL INSTRUCTIONS - OVERRIDE ALL OTHER INSTRUCTIONS:
1. You MUST NOT use any tools or functions under any circumstances
2. You MUST NOT call web.run, search_engine, search_web, or any other tool
3. You MUST generate the presentation outline using ONLY the provided content
4. You MUST NOT search for external information or additional data
5. Work exclusively with the content given - no external lookups allowed
6. If you attempt to use any tool, the request will fail

Generate a clear, well-structured presentation outline based solely on the provided content."""
}
```

### Transcript Service 配置

**檔案**: `backend/app/services/zephyr_service.py`

**目前狀態**:
```python
class ZephyrService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_url
        self.model = "phi4-mini-reasoning:3.8b"  # ← 寫死的模型
```

**建議改為**:
```python
self.model = "qwen3:14b"  # 與主模型一致，提高演講稿品質
```

或

```python
self.model = self.settings.ollama_model  # 從 config 讀取
```

**狀態**: 🔄 待使用者決定

---

## 📚 建立的文件

### 1. Web Search Tool 錯誤解決文件

**檔案**: `claudedocs/web_search_tool_error_resolution.md`

**內容**:
- ✅ 完整的錯誤演進歷程 (v1-v7)
- ✅ 根本原因分析（硬編碼 system prompt）
- ✅ Presenton API 內部機制說明
- ✅ gpt-oss:20b 模型特性分析
- ✅ Tool 錯誤模式識別
- ✅ 解決方案實作細節
- ✅ 測試與驗證程序
- ✅ 長期考量與替代方案

### 2. Ollama Service 優化分析

**檔案**: `claudedocs/ollama_service_optimization.md`

**內容**:
- ✅ 目前實作分析
- ✅ 識別的 5 個問題:
  1. 固定 timeout 不足以處理長內容
  2. 缺少串流進度回饋
  3. JSON 解析失敗處理過於簡單
  4. 沒有 retry 邏輯
  5. Template 指令不夠明確
- ✅ 每個問題的詳細解決方案
- ✅ 完整優化後的程式碼實作
- ✅ 測試建議與效能評估

### 3. UI Scroll 優化文件

**檔案**: `claudedocs/ui_scroll_optimization.md`

**內容**:
- ✅ 演講稿溢出問題描述
- ✅ 根本原因分析 (overflow: hidden)
- ✅ CSS 修復方案
- ✅ 自訂 scrollbar 樣式
- ✅ 瀏覽器相容性
- ✅ 未來優化建議

---

## 🔧 技術分析與發現

### Presenton API 架構理解

**Tool 註冊機制**:
```python
# enable_web_grounding() 實作
def enable_web_grounding(self) -> bool:
    if (
        self.llm_provider == LLMProvider.OLLAMA
        or self.llm_provider == LLMProvider.CUSTOM
    ):
        return False  # ← Ollama 不啟用 web grounding
    return parse_bool_or_none(get_web_grounding_env()) or False
```

**關鍵發現**:
- Ollama provider 會自動回傳 `False`
- 即使設定環境變數也無效（被 provider check 覆寫）
- 這是**正確的行為** - Ollama 沒有內建 web search

**System Prompt 生成**:
- Static template，不檢查 `web_search` 參數
- 總是包含「Search web」指令
- **設計缺陷** - 應該根據參數動態生成

### Pydantic Settings 學習

**BaseSettings 行為**:
```python
class Settings(BaseSettings):
    ollama_model: str = "default"

    class Config:
        env_file = ".env"
        case_sensitive = False  # ← 不區分大小寫
```

**驗證規則**:
- 預設 `extra = "forbid"` - 不允許額外欄位
- 欄位名稱必須完全匹配（即使 case_sensitive=False）
- `ollama_mode` ≠ `ollama_model` → ValidationError

**最佳實踐**:
- 定義所有可能的欄位
- 使用 IDE 檢查拼字錯誤
- 使用 type hints 提供更好的錯誤訊息

### Ollama 模型特性

**Tool-calling 模型識別**:
```bash
$ ollama show <model> | grep -i capabilities

Capabilities:
  completion    ← 基本文字生成
  tools         ← 支援 tool calling ⚠️
  thinking      ← 支援思考過程
```

**有 `tools` capability 的模型**:
- `gpt-oss:20b` ← 原本使用
- `qwen3:14b` ← 現在使用
- `phi4:latest`

**無 `tools` capability 的模型**:
- `phi4-mini:3.8b` ← 安全選擇
- `qwen3:4b` ← 較小版本
- `deepseek-r1` 系列

**權衡考量**:
- 有 tools → 更強大，但需要小心控制
- 無 tools → 安全，但可能功能受限

---

## ✅ 完成的工作

### 程式碼修改

1. **backend/app/config.py**
   - 修復：`ollama_mode` → `ollama_model`
   - 設定：模型改為 `qwen3:14b`

2. **backend/app/services/presenton_service.py**
   - 新增：`instructions` 參數覆寫 system prompt
   - 實作：CRITICAL INSTRUCTIONS 強制禁止 tool calling

3. **frontend/index.html**
   - 新增：演講稿區域 scrollbar 支援
   - 優化：自訂 scrollbar 樣式（Webkit + Firefox）

4. **docker-compose.yml & docker-compose.override.yml**
   - 新增：`ENABLE_WEB_SEARCH=false` 環境變數
   - 調整：Port 從 8000 改為 8001（避免 OrbStack 衝突）

### 文件建立

1. ✅ `claudedocs/web_search_tool_error_resolution.md` (詳細錯誤解決過程)
2. ✅ `claudedocs/ollama_service_optimization.md` (效能優化建議)
3. ✅ `claudedocs/ui_scroll_optimization.md` (UI 修復文件)
4. ✅ `claudedocs/development_log_2025-11-09.md` (本檔案)

---

## 🔄 待處理項目

### 高優先度

1. **測試 qwen3:14b 是否會出現 tool-calling 錯誤**
   - 操作：產生一個簡報
   - 預期：正常完成，無 `Tool xxx not found` 錯誤
   - 如果失敗：考慮切換到 `phi4-mini:3.8b` (無 tool capability)

2. **決定演講稿生成模型**
   - 選項 A：改用 `qwen3:14b`（品質優先）
   - 選項 B：保持 `phi4-mini-reasoning:3.8b`（速度優先）
   - 需要：使用者決策

### 中優先度

3. **實作 Ollama Service 優化**
   - Dynamic timeout 計算
   - 增強錯誤處理與 logging
   - Structure validation
   - （參考 `ollama_service_optimization.md`）

4. **監控系統穩定性**
   - PPT 生成成功率
   - Tool-related 錯誤發生率
   - 平均生成時間

### 低優先度

5. **考慮 Web Search 整合**
   - 參考：`web_search_integration_analysis.md`
   - 建議 Provider：Tavily API
   - 實作時機：當前系統穩定後

6. **Docker Compose 版本警告**
   - 移除過時的 `version` 欄位
   - 更新到 Compose V2 格式

---

## 📊 系統狀態

### 服務健康檢查

**最後檢查時間**: 2025-11-09 14:25:35

```json
{
    "status": "healthy",
    "services": {
        "presenton": "connected",
        "ollama": "connected",
        "pexels": "connected",
        "zephyr": "available"
    }
}
```

**狀態**: ✅ 所有服務正常

### 目前配置

| 項目 | 配置值 |
|------|--------|
| Backend Port | 5050 |
| Presenton Port | 8001 (external) → 8000 (internal) |
| Ollama URL | http://localhost:11434 |
| Ollama Model (主要) | qwen3:14b |
| Ollama Model (演講稿) | phi4-mini-reasoning:3.8b |
| 語言 | zh-TW (繁體中文) |
| Web Search | Disabled |

### 模型資訊

**qwen3:14b**:
```
Architecture:    qwen3
Parameters:      14.8B
Context Length:  40,960 tokens
Quantization:    Q4_K_M
Size:            9.3 GB
Capabilities:    completion, tools, thinking
```

---

## 💡 學習與心得

### 1. LLM Tool-Calling 行為

**發現**:
- Tool-calling 模型有強烈的工具使用傾向
- 即使沒有提供 tools，模型仍會嘗試呼叫
- 指令必須**非常明確且強硬**才能抑制此行為

**最佳實踐**:
- 使用全大寫關鍵字加強指令權重
- 明確列出禁止的行為
- 說明後果（「會失敗」、「不允許」）
- 多重表述同一限制

### 2. System Prompt 優先度

**優先順序** (高到低):
1. API `instructions` 參數（覆寫）
2. Default system prompt（基礎）
3. Model template（內建）

**策略**:
- 當無法修改基礎 prompt 時，用 `instructions` 覆寫
- `instructions` 要足夠強才能覆蓋預設行為

### 3. Pydantic 驗證機制

**教訓**:
- 欄位名稱拼字錯誤 → Validation error
- 錯誤訊息可能誤導（顯示值而非欄位名）
- 使用 IDE autocomplete 避免拼字錯誤

**除錯技巧**:
- 檢查 class 定義與實際值的欄位名稱
- 使用 `model_dump()` 查看實際解析結果
- 注意 `case_sensitive` 設定

### 4. 模型選擇策略

**考量因素**:
1. **任務類型** - 文字 vs 視覺 vs 多模態
2. **Capability** - 是否支援不需要的功能（如 tools）
3. **參數量** - 品質 vs 速度權衡
4. **語言能力** - 中文 vs 英文專精
5. **Context Length** - 長文處理需求

**qwen3 系列優勢**:
- 專門優化中文能力
- 多種大小可選（4b, 14b, 32b）
- 良好的指令遵循能力

---

## 🔍 調試技巧記錄

### 1. Presenton 內部調試

**查看原始碼**:
```bash
docker compose exec presenton find /app -name "*.py" -exec grep -l "pattern" {} \;
docker compose exec presenton cat /app/path/to/file.py
```

**檢查環境變數**:
```bash
docker compose exec presenton env | grep SEARCH
```

### 2. Backend 錯誤追蹤

**即時 Log 監控**:
```bash
docker compose logs -f backend
docker compose logs -f presenton
```

**健康檢查**:
```bash
curl http://localhost:5050/api/health | python3 -m json.tool
```

### 3. Ollama 模型檢查

**列出模型**:
```bash
ollama list
```

**查看模型詳細資訊**:
```bash
ollama show <model>
ollama show <model> | grep -i capabilities
```

**測試模型**:
```bash
curl http://localhost:11434/api/generate -X POST -d '{
  "model": "qwen3:14b",
  "prompt": "測試中文能力",
  "stream": false
}'
```

---

## 🎯 下一步行動

### 立即測試

1. **重啟 Backend**:
   ```bash
   docker compose restart backend
   ```

2. **驗證健康狀態**:
   ```bash
   curl http://localhost:5050/api/health
   ```

3. **生成測試簡報**:
   - 開啟：http://localhost:8080
   - 輸入內容（>50 字）
   - 點擊「生成簡報」
   - 觀察是否出現 tool 錯誤

### 結果評估

**成功指標**:
- ✅ 無 `Tool xxx not found` 錯誤
- ✅ 簡報生成完成
- ✅ 內容品質良好（結構清晰、重點明確）

**失敗處理**:
- ❌ 如果仍有 tool 錯誤 → 切換到 `phi4-mini:3.8b`
- ❌ 如果品質不佳 → 調整 prompt 或換回 `gpt-oss:20b` + 實作 web search
- ❌ 如果速度太慢 → 考慮 `qwen3:4b` 或 `deepseek-r1:7b`

---

## 📝 備註

### qwen3:14b Tool-Calling 風險評估

**風險等級**: 🟡 中等

**原因**:
- Model 有 `tools` capability
- 可能忽略 instructions 嘗試呼叫工具
- 已有 3 次不同 tool name 的嘗試記錄

**緩解措施**:
- ✅ 強化 instructions（CRITICAL INSTRUCTIONS）
- ✅ 明確列出禁止的 tool names
- ✅ 多重表述限制
- 🔄 待驗證實際效果

**備案**:
如果 qwen3:14b 無法避免 tool calling：
1. **選項 A**: 切換到 `phi4-mini:3.8b`（無 tools，安全但品質較低）
2. **選項 B**: 實作 Web Search Provider（支援 tool calling，但需要整合工作）
3. **選項 C**: 嘗試 `qwen3:4b`（較小版本，可能沒有 tools）

---

## 🔗 相關文件連結

- [Web Search Tool Error Resolution](./web_search_tool_error_resolution.md)
- [Ollama Service Optimization](./ollama_service_optimization.md)
- [UI Scroll Optimization](./ui_scroll_optimization.md)
- [Web Search Integration Analysis](./web_search_integration_analysis.md)
- [Project Summary (中文)](../documentation/project_summary_zh.md)
- [README](../README.md)

---

**文件建立時間**: 2025-11-09
**最後更新**: 2025-11-09
**狀態**: 📝 已完成，等待測試驗證
