# Template System Architecture - 2025-11-14

## Template Type 層級架構

TeacherAssist 使用 **三層 Template 系統**，每層有不同用途：

### Layer 1: Presenton API Built-in Templates (API 參數)
**目的**: Presenton 服務內建的模板樣式 ID
**使用場景**: 標準簡報生成 (非增強模式)
**有效值**: 
- `general` - 一般樣式
- `modern` - 現代樣式
- `standard` - 標準樣式
- `swift` - 簡潔樣式

**程式碼位置**:
- `backend/app/models.py` - TemplateType enum (修正後只包含這 4 個值)
- `frontend/index.html` - template-select 下拉選單
- `backend/app/services/presenton_service.py` - create_presentation() template_id 參數

**API 參考**: https://docs.presenton.ai/api-reference/template/get-template-by-id

**重要**: 這些是 Presenton API 的參數值，不是實體 PPTX 檔案

### Layer 2: User-Uploaded Templates (實體檔案)
**目的**: 用戶自訂模板上傳功能 (2025-11-14 新增)
**使用場景**: 用戶需要使用自己的企業/學校模板
**儲存位置**: `{templates_dir}/uploaded/uploaded_{uuid}_{filename}.pptx`

**程式碼位置**:
- `backend/app/api/routes.py` - `/generate-with-template` 端點 (lines 221-285)
- `frontend/index.html` - 模板上傳 UI (lines 705-736)
- `backend/app/services/template_manager.py` - validate_template() 支援 uploaded/ 路徑

**檔案驗證**:
- PPTX 格式檢查
- 檔案大小限制: 20MB
- python-pptx 結構驗證
- 自動清理失敗檔案

**生命週期**:
1. 用戶上傳 → 驗證 → 儲存到 uploaded/
2. 使用 UUID 前綴避免檔名衝突
3. 失敗時自動刪除
4. 成功後用於簡報生成

### Layer 3: Enhancement Pipeline Templates (實體檔案)
**目的**: 品質增強管道使用的本地模板庫
**使用場景**: enhance=True 時，重建階段使用
**實際位置**: `ppt_templates/` (9 個模板檔案)

**程式碼位置**:
- `backend/app/services/template_manager.py` - list_templates(), get_recommended_template()
- `backend/app/services/content_processor.py` - _apply_enhancement_pipeline() (lines 113-177)
- `backend/app/services/presentation_rebuilder.py` - rebuild_presentation()

**當前狀態**: ✅ 完全正常運作
- 9 個有效的 PPTX 模板 (custom_pptx_template_1.pptx ~ 9.pptx)
- 每個模板有 11-12 個版面配置
- 已掛載到 Docker 容器 /ppt_templates
- TemplateManager 自動發現並驗證模板

**修正後的實作**:
- `get_recommended_template()` 不再硬編碼檔案名稱
- 改為返回 templates_dir 中找到的第一個可用模板
- 添加註解說明此方法已棄用

## Template 使用流程

### 標準生成 (Layer 1)
```
用戶選擇 template: "modern"
  ↓
Backend: presenton.create_presentation(template_id="modern")
  ↓
Presenton API: 使用內建 modern 樣式生成 PPTX
```

### 自訂模板生成 (Layer 2)
```
用戶上傳 company_template.pptx
  ↓
Backend: 驗證 → 儲存到 uploaded/uploaded_abc123_company_template.pptx
  ↓
Backend: content_processor.process_content(enhancement_template="uploaded/...")
  ↓
使用上傳的模板生成簡報
```

### 品質增強生成 (Layer 1 + Layer 3)
```
用戶啟用 enhance=True
  ↓
Stage 1: Presenton 使用 Layer 1 template 生成初稿
  ↓
Stage 2: LLM 優化內容
  ↓
Stage 3: 使用 Layer 3 template (或 Layer 2 上傳模板) 重建
```

## 已修正的問題

### 1. TemplateType Enum 無效值
**問題**: 包含 "administrative" 和 "educational" (Presenton API 不支援)
**修正**: backend/app/models.py - 只保留 4 個有效值
**影響**: 避免 422 Validation Error

### 2. TemplateManager 硬編碼檔案
**問題**: get_recommended_template() 引用不存在的檔案
**修正**: backend/app/services/template_manager.py - 移除硬編碼 mapping
**影響**: 向後相容，優雅處理模板缺失

### 3. Frontend 模板選項
**狀態**: ✅ 已正確 - 只有 4 個有效選項
**位置**: frontend/index.html lines 758-763

## 未來改進建議

### ~~選項 1: 建立 Enhancement Template 庫~~ (已完成)
✅ **已實作**: ppt_templates/ 目錄包含 9 個模板
- 已掛載到 Docker 容器
- TemplateManager 正確識別
- Enhancement pipeline 可立即使用

### 選項 2: 使用上傳模板作為 Enhancement Template
修改 content_processor.py 使 enhancement_template 參數接受上傳模板路徑

### 選項 3: 簡化架構
移除 Layer 3，enhancement pipeline 直接使用 Layer 2 上傳模板或空白簡報

## 相關文件

- [claudedocs/presenton_filename_limitation.md](../claudedocs/presenton_filename_limitation.md) - Presenton 檔名限制問題
- [claudedocs/enhancement_implementation_summary.md](../claudedocs/enhancement_implementation_summary.md) - Enhancement pipeline 實作細節
- Presenton API Docs: https://docs.presenton.ai/api-reference/template/get-template-by-id

## 測試驗證

```bash
# 1. 驗證 backend 健康狀態
curl http://localhost:5050/api/health

# 2. 測試標準生成 (Layer 1)
curl -X POST http://localhost:5050/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "測試內容...",
    "template": "modern",
    "title": "測試標題"
  }'

# 3. 測試模板上傳 (Layer 2)
curl -X POST http://localhost:5050/api/generate-with-template \
  -F "template_file=@path/to/template.pptx" \
  -F "content=測試內容..." \
  -F "title=測試標題"

# 4. 驗證 TemplateType enum 只有 4 個值
grep -A5 "class TemplateType" backend/app/models.py
```

## 當前系統狀態

✅ Layer 1 (Presenton Built-in): 完全正常
✅ Layer 2 (User Upload): 完全正常  
✅ Layer 3 (Enhancement Pipeline): 完全正常 (9 個模板已掛載)

系統基本功能不受影響，所有服務正常連接。
