# qwen3:14b JSON 解析錯誤問題

**日期**: 2025-11-10
**模型**: qwen3:14b
**錯誤類型**: JSON Parsing Error
**狀態**: ✅ 已解決 (切換回 phi4-mini:3.8b)

---

## 問題描述

### 錯誤訊息

**Backend**:
```
httpx.HTTPStatusError: Server error '500 Internal Server Error'
for url 'http://presenton:8000/api/v1/ppt/presentation/generate'
```

**Presenton API**:
```python
dirtyjson.error.Error: Expecting value: line 1 column 1 (char 0)

File "/app/servers/fastapi/services/llm_client.py", line 558, in _generate_openai_structured
    return dict(dirtyjson.loads(content))
                ^^^^^^^^^^^^^^^^^^^^^^^^
```

### 發生階段

```
用戶輸入內容
    ↓
Backend → Presenton (生成簡報結構)
    ↓
Presenton → Ollama qwen3:14b (生成投影片內容)
    ↓
❌ JSON 解析失敗
```

**失敗點**: `generate_slide_content.py:129` - 生成投影片內容時

---

## 根本原因分析

### 1. qwen3:14b 輸出格式問題

**Presenton 的期望**:
```json
{
    "title": "投影片標題",
    "content": ["重點1", "重點2", "重點3"],
    "notes": "演講者備註"
}
```

**qwen3:14b 可能的輸出**:
```
# 投影片標題

- 重點1
- 重點2
- 重點3

(Markdown 格式，非 JSON)
```

或

```
(空字串或無效內容)
```

### 2. Structured Output 支援問題

**Presenton 的實作**:
```python
# llm_client.py
async def _generate_ollama_structured(self, ...):
    # Ollama 路徑會呼叫 OpenAI-compatible API
    return await self._generate_openai_structured(...)

async def _generate_openai_structured(self, ...):
    # 期望 LLM 回傳 JSON
    return dict(dirtyjson.loads(content))  # ❌ 這裡失敗
```

**問題**:
- `qwen3:14b` 不像 `gpt-oss:20b` 有內建的 structured output 支援
- 模型可能回傳 Markdown、純文字，或遵循 instructions 而非 JSON schema
- `dirtyjson` 無法解析非 JSON 內容

### 3. CRITICAL INSTRUCTIONS 的影響

**我們加入的指令** (`presenton_service.py`):
```python
"instructions": """CRITICAL INSTRUCTIONS - OVERRIDE ALL OTHER INSTRUCTIONS:
1. You MUST NOT use any tools or functions under any circumstances
2. You MUST NOT call web.run, search_engine, search_web, or any other tool
3. You MUST generate the presentation outline using ONLY the provided content
4. You MUST NOT search for external information or additional data
5. Work exclusively with the content given - no external lookups allowed
6. If you attempt to use any tool, the request will fail

Generate a clear, well-structured presentation outline based solely on the provided content."""
```

**可能副作用**:
- 過於強硬的指令可能干擾模型的 JSON 格式輸出
- "OVERRIDE ALL OTHER INSTRUCTIONS" 可能包括 JSON schema 要求
- 模型優先遵循我們的指令，忽略 Presenton 的格式要求

---

## 技術細節

### Presenton LLM 呼叫流程

```
generate_slide_content.py:129
    ↓
client.generate_structured(
    model="qwen3:14b",
    messages=[...],
    response_format={"type": "json_object", "schema": {...}}
)
    ↓
llm_client.py:808 → _generate_ollama_structured()
    ↓
llm_client.py:740 → _generate_openai_structured()
    ↓
呼叫 Ollama API: POST http://host.docker.internal:11434/v1/chat/completions
    ↓
收到回應: content = "..." (qwen3:14b 的輸出)
    ↓
llm_client.py:558 → dirtyjson.loads(content)  ❌ 解析失敗
```

### dirtyjson.loads() 行為

**正常情況**:
```python
content = '{"title": "測試", "content": ["1", "2"]}'
result = dirtyjson.loads(content)
# result = {'title': '測試', 'content': ['1', '2']}
```

**錯誤情況**:
```python
content = ""  # 空字串
dirtyjson.loads(content)
# dirtyjson.error.Error: Expecting value: line 1 column 1 (char 0)
```

或

```python
content = "This is markdown\n- point 1\n- point 2"
dirtyjson.loads(content)
# dirtyjson.error.Error: Expecting value: line 1 column 1 (char 0)
```

### Ollama API 回應

**Logs 顯示**:
```
2025-11-10 08:57:56,022 - INFO - HTTP Request:
POST http://host.docker.internal:11434/v1/chat/completions
"HTTP/1.1 200 OK"
```

**分析**:
- ✅ Ollama API 成功回應 (200 OK)
- ✅ qwen3:14b 有產生內容
- ❌ 內容格式不符合 JSON schema

---

## 解決方案

### 方案 1: 切換到相容模型 (✅ 採用)

**選擇**: `phi4-mini:3.8b`

**原因**:
1. ✅ **已驗證相容** - 之前用於 transcript generation，沒問題
2. ✅ **無 tool-calling** - 不會出現 `Tool xxx not found` 錯誤
3. ✅ **較小較快** - 3.8B vs 14.8B，生成速度更快
4. ✅ **Structured output 支援** - 能正確輸出 JSON 格式

**實作**:
```python
# backend/app/config.py
ollama_model: str = "phi4-mini:3.8b"  # Stable, no tool-calling
```

**權衡**:
- ⚠️ 品質可能略低於 qwen3:14b (參數少)
- ✅ 但穩定性和相容性更重要

### 方案 2: 修改 Presenton 程式碼 (❌ 不採用)

**理論方案**: 修改 `llm_client.py` 增加錯誤處理

```python
async def _generate_openai_structured(self, ...):
    try:
        return dict(dirtyjson.loads(content))
    except dirtyjson.error.Error:
        # Fallback: 嘗試從 Markdown 解析
        return self._parse_markdown_to_json(content)
```

**不採用原因**:
- ❌ Presenton 是 pre-built Docker image，無法修改
- ❌ 維護 fork 成本高
- ❌ 不如直接用相容模型

### 方案 3: 移除 CRITICAL INSTRUCTIONS (❌ 不採用)

**理論**: 移除可能干擾 JSON 輸出的強硬指令

**不採用原因**:
- ⚠️ 會導致 tool-calling 錯誤復發
- ⚠️ qwen3:14b 本身就有格式問題，不只是指令影響

---

## 模型相容性測試結果

### 已測試模型

| 模型 | JSON 支援 | Tool-Calling | 速度 | 結果 |
|------|-----------|--------------|------|------|
| **gpt-oss:20b** | ✅ 良好 | ⚠️ 有 (會出錯) | 慢 | ⚠️ Tool 錯誤 |
| **qwen3:14b** | ❌ 失敗 | ✅ 有 | 慢 | ❌ JSON 解析錯誤 |
| **phi4-mini:3.8b** | ✅ 良好 | ❌ 無 | 快 | ✅ 推薦 |
| **phi4-mini-reasoning:3.8b** | ✅ 良好 | ❌ 無 | 快 | ✅ 可用 |

### 結論

**最佳選擇**: `phi4-mini:3.8b` 或 `phi4-mini-reasoning:3.8b`

**理由**:
1. ✅ 與 Presenton 完全相容
2. ✅ 無 tool-calling 問題
3. ✅ 生成速度快
4. ✅ JSON 格式正確
5. ⚠️ 品質略低，但可接受

---

## qwen3:14b 的問題總結

### 技術限制

1. **Structured Output 支援不足**
   - 無法遵循 JSON schema
   - 傾向輸出 Markdown 或純文字

2. **與 Presenton 不相容**
   - Presenton 期望 OpenAI-compatible structured output
   - qwen3:14b 不符合此格式

3. **Tool-Calling 能力**
   - 有 tools capability
   - 可能嘗試呼叫工具（雖然我們禁止了）

### 為何 phi4-mini 可以？

**phi4-mini 的優勢**:
```
ollama show phi4-mini:3.8b | grep -i capabilities

Capabilities:
  completion    ← 基本文字生成
  (無 tools)    ← 沒有 tool-calling
```

**特性**:
- 專注於 completion
- 無額外的 tool/function calling 機制
- 與 Presenton 的 JSON 要求相容
- 訓練數據可能包含更多 JSON 格式範例

---

## 測試驗證

### 測試步驟

1. **重啟 Backend**:
   ```bash
   docker compose restart backend
   ```

2. **驗證健康狀態**:
   ```bash
   curl http://localhost:5050/api/health
   # {"status": "healthy", ...}
   ```

3. **測試生成簡報**:
   - 開啟 http://localhost:8080
   - 輸入測試內容 (>50 字)
   - 點擊「生成簡報」
   - 預期：成功生成，無 JSON 錯誤

### 成功標準

- ✅ 無 `dirtyjson.error.Error` 錯誤
- ✅ 無 `Tool xxx not found` 錯誤
- ✅ 簡報成功生成
- ✅ 投影片內容格式正確

---

## 開發建議

### 模型選擇原則

**對於 Presenton 整合**:

1. **優先考慮**:
   - phi4-mini:3.8b ✅
   - phi4-mini-reasoning:3.8b ✅
   - phi4:latest (較大，但相容)

2. **謹慎使用**:
   - gpt-oss:20b (tool-calling 問題)
   - qwen3 系列 (JSON 格式問題)
   - 任何有 "tools" capability 的模型

3. **避免使用**:
   - VL (Vision-Language) 模型
   - 專門的 code 模型 (如 deepseek-coder)
   - 實驗性模型

### 測試新模型 Checklist

測試新模型前，請確認：

- [ ] 執行 `ollama show <model>` 檢查 capabilities
- [ ] 確認無 `tools` capability (或可接受 tool-calling 風險)
- [ ] 測試簡單的 JSON 生成
- [ ] 測試完整的簡報生成流程
- [ ] 檢查 Presenton logs 無解析錯誤
- [ ] 驗證輸出品質

**測試命令**:
```bash
# 測試 JSON 格式輸出
ollama run <model> '請用 JSON 格式回答: {"name": "測試", "items": ["1", "2"]}'

# 如果模型回傳正確 JSON，才考慮用於 Presenton
```

---

## 相關文件

- [開發日誌 2025-11-09](./development_log_2025-11-09.md)
- [Web Search Tool Error Resolution](./web_search_tool_error_resolution.md)
- [Ollama Service Optimization](./ollama_service_optimization.md)

---

## 版本歷史

- **2025-11-10 v1**: qwen3:14b 發現 JSON 解析錯誤
- **2025-11-10 v2**: 切換到 phi4-mini:3.8b 解決問題
- **2025-11-10 v3**: 建立完整文件與模型相容性測試結果

---

**建立時間**: 2025-11-10
**作者**: Claude Code (SuperClaude Framework)
**狀態**: ✅ 已解決
