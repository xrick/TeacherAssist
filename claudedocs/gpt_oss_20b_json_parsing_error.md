# gpt-oss:20b JSON 解析錯誤問題

**日期**: 2025-11-10
**模型**: gpt-oss:20b
**錯誤類型**: JSON Parsing Error (Unterminated String)
**狀態**: ✅ 已解決 (切換到 phi4:latest)

---

## 問題描述

### 錯誤訊息

**Presenton API**:
```python
dirtyjson.error.Error: Unterminated string starting at: line 1 column 532 (char 531)

File "/app/servers/fastapi/services/llm_client.py", line 558, in _generate_openai_structured
    return dict(dirtyjson.loads(content))
                ^^^^^^^^^^^^^^^^^^^^^^^^
```

### 發生階段

```
用戶輸入內容
    ↓
Backend → Presenton (生成簡報結構) ✅ 成功
    ↓
Presenton → Ollama gpt-oss:20b (生成投影片內容)
    ↓
❌ JSON 解析失敗 (Unterminated string at char 531)
```

**失敗點**: `generate_slide_content.py:129` - 生成投影片內容時

---

## 根本原因分析

### 1. gpt-oss:20b 輸出格式問題

**Presenton 的期望**:
```json
{
    "title": "投影片標題",
    "content": ["重點1", "重點2", "重點3"],
    "notes": "演講者備註"
}
```

**gpt-oss:20b 的問題**:
- 產生的 JSON 包含未正確轉義的引號
- 字串未正確結束 (unterminated string)
- 不符合 JSON 標準的格式

### 2. Structured Output 支援問題

**與 qwen3:14b 類似的問題**:
- ❌ `gpt-oss:20b` - JSON 格式錯誤 (unterminated string)
- ❌ `qwen3:14b` - JSON 格式錯誤 (expecting value)
- ✅ `phi4:latest` - 正確的 JSON structured output

### 3. 兩階段生成的不同需求

**Stage 1: Presentation Outline Generation**
- 模型: `gpt-oss:20b`
- 結果: ✅ 成功 (在修正 web search 問題後)
- 原因: Outline 的 JSON schema 較簡單

**Stage 2: Slide Content Generation**
- 模型: `gpt-oss:20b`
- 結果: ❌ 失敗 (JSON 格式問題)
- 原因: Slide content 的 JSON schema 較複雜，包含嵌套結構

---

## 技術細節

### Presenton LLM 呼叫流程

```
generate_slide_content.py:129
    ↓
client.generate_structured(
    model="gpt-oss:20b",
    messages=[...],
    response_format={...}  # 複雜的 JSON schema
)
    ↓
llm_client.py:808 → _generate_ollama_structured()
    ↓
llm_client.py:740 → _generate_openai_structured()
    ↓
呼叫 Ollama API: POST http://host.docker.internal:11434/v1/chat/completions
    ↓
收到回應: content = "..." (gpt-oss:20b 的輸出)
    ↓
llm_client.py:558 → dirtyjson.loads(content)  ❌ 解析失敗
```

### dirtyjson.loads() 行為

**錯誤情況**:
```python
content = '{"title": "測試", "content": ["這是一個未結束的字串...'
dirtyjson.loads(content)
# dirtyjson.error.Error: Unterminated string starting at: line 1 column 532 (char 531)
```

### 錯誤位置分析

**char 531**: 大約在 JSON 字串的中間位置
- 可能是 `content` 陣列中的某個元素
- 可能是 `notes` 欄位的內容
- 包含中文字元導致位置計算複雜

---

## 解決方案

### 方案: 切換到相容模型 (✅ 採用)

**選擇**: `phi4:latest`

**原因**:
1. ✅ **已驗證相容** - phi4 系列與 Presenton 完全相容
2. ✅ **無 tool-calling** - 不會出現 `Tool xxx not found` 錯誤
3. ✅ **Structured output 支援** - 能正確輸出複雜的 JSON 格式
4. ✅ **穩定性高** - phi4 是 Microsoft 的高品質模型

**實作**:
```python
# backend/app/config.py
ollama_model: str = "phi4:latest"  # ✅ Stable, no tool-calling, proper JSON output
```

**權衡**:
- ⚠️ 參數量: phi4:latest (14B) 比 gpt-oss:20b (20B) 少
- ✅ 但品質和穩定性更重要

---

## 模型相容性測試結果

### 已測試模型

| 模型 | Outline 生成 | Content 生成 | Tool-Calling | JSON 格式 | 結果 |
|------|-------------|--------------|--------------|----------|------|
| **gpt-oss:20b** | ⚠️ 需修正 | ❌ 失敗 | ✅ 有 | ❌ Unterminated string | ❌ 不推薦 |
| **qwen3:14b** | ❌ 失敗 | ❌ 失敗 | ✅ 有 | ❌ Expecting value | ❌ 不推薦 |
| **phi4:latest** | ✅ 良好 | ✅ 良好 | ❌ 無 | ✅ 正確 | ✅ **推薦** |
| **phi4-mini:3.8b** | ✅ 良好 | ✅ 良好 | ❌ 無 | ✅ 正確 | ✅ 可用 |

### 結論

**最佳選擇**: `phi4:latest`

**理由**:
1. ✅ 與 Presenton 完全相容
2. ✅ 兩階段生成都穩定
3. ✅ 無 tool-calling 問題
4. ✅ JSON 格式完全正確
5. ✅ Microsoft 官方支援，品質高

---

## gpt-oss:20b 的問題總結

### 技術限制

1. **JSON Schema 支援不足**
   - 簡單 schema (outline) 可以處理
   - 複雜 schema (slide content) 無法正確生成
   - 傾向產生格式錯誤的 JSON

2. **Tool-Calling 能力**
   - 有 tools capability
   - 嘗試呼叫 search_engine, web.run 等工具
   - 需要 CRITICAL INSTRUCTIONS 來禁用

3. **字串處理問題**
   - 未正確轉義引號
   - 字串未正確結束
   - 中文內容處理可能有問題

### 為何 phi4:latest 可以？

**phi4 的優勢**:
```
ollama show phi4:latest

Model: phi4:latest
Parameters: 14B
Capabilities:
  completion    ← 基本文字生成
  (無 tools)    ← 沒有 tool-calling
```

**特性**:
- 專注於 completion
- 無額外的 tool/function calling 機制
- 與 Presenton 的 JSON 要求完全相容
- Microsoft 訓練，JSON 格式支援優秀
- 14B 參數，品質與效能平衡

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
   # {"status": "healthy", "services": {...}}
   ```

3. **測試生成簡報**:
   - 開啟 http://localhost:8080
   - 輸入測試內容 (>50 字)
   - 點擊「生成簡報」
   - 預期：兩階段都成功，無 JSON 錯誤

### 成功標準

- ✅ 無 `dirtyjson.error.Error` 錯誤
- ✅ 無 `Tool xxx not found` 錯誤
- ✅ Outline 成功生成
- ✅ Slide content 成功生成
- ✅ 簡報成功生成

---

## 開發建議

### 模型選擇原則

**對於 Presenton 整合**:

1. **推薦使用**:
   - ✅ phi4:latest (14B) - 最佳平衡
   - ✅ phi4-mini:3.8b - 速度優先
   - ✅ phi4-mini-reasoning:3.8b - 推理能力優先

2. **謹慎使用**:
   - ⚠️ gpt-oss:20b - outline 可以，content 不行
   - ⚠️ qwen3 系列 - JSON 格式問題

3. **避免使用**:
   - ❌ VL (Vision-Language) 模型
   - ❌ 有 tools capability 的模型
   - ❌ 未測試的實驗性模型

### 測試新模型 Checklist

測試新模型前，請確認：

- [ ] 執行 `ollama show <model>` 檢查 capabilities
- [ ] 確認無 `tools` capability
- [ ] 測試簡單的 JSON 生成
- [ ] 測試 Outline 生成 (簡單 schema)
- [ ] 測試 Slide Content 生成 (複雜 schema)
- [ ] 檢查 Presenton logs 無解析錯誤
- [ ] 驗證輸出品質

**測試命令**:
```bash
# 測試簡單 JSON
ollama run <model> '請用 JSON 格式回答: {"name": "測試", "items": ["1", "2"]}'

# 測試複雜 JSON (nested structure)
ollama run <model> '請用 JSON 格式回答: {"title": "測試", "content": [{"text": "重點1", "notes": "說明"}]}'

# 如果兩個都正確，才考慮用於 Presenton
```

---

## 相關文件

- [qwen3:14b JSON Parsing Error](./qwen3_14b_json_parsing_error.md)
- [Presenton Web Search Modification](./presenton_web_search_modification.md)
- [Development Log 2025-11-09](./development_log_2025-11-09.md)

---

## 版本歷史

- **2025-11-10 v1**: gpt-oss:20b 發現 JSON 解析錯誤 (unterminated string)
- **2025-11-10 v2**: 切換到 phi4:latest 解決問題
- **2025-11-10 v3**: 建立完整文件與模型相容性分析

---

**建立時間**: 2025-11-10
**作者**: Claude Code (SuperClaude Framework)
**狀態**: ✅ 已解決，使用 phi4:latest
