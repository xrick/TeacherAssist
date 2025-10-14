# Presenton 422 錯誤修復 - 重新設計整合策略

**錯誤**: `Client error '422 Unprocessable Entity' for url 'http://presenton:8000/api/v1/ppt/presentation/create'`
**日期**: 2025-10-14
**狀態**: ✅ 已修復

---

## 🔍 問題根源

### 422 錯誤含義

HTTP 422 表示**請求格式語法正確，但語義錯誤** - 伺服器無法處理請求的內容。

### 原始設計問題

**Backend 原本的設計**:
1. 使用 Ollama 分析內容
2. 構建簡報結構 (slides, title, content)
3. 發送構建好的結構給 Presenton

**Presenton `/create` 端點實際需要**:
```python
# Presenton 期待的格式
{
    "content": str,  # 原始文字內容
    "n_slides": int,  # 投影片數量
    "language": str,
    "tone": str,
    # ...其他參數
}
```

**Backend 發送的格式** (錯誤):
```python
# Backend 發送的格式
{
    "title": "教學簡報",
    "template": "educational",
    "slides": [...],  # 已構建的投影片結構
    "language": "zh-TW"
}
```

**結果**: 格式不匹配 → 422 Unprocessable Entity

---

## 🎯 解決策略

### 發現: Presenton 內建完整功能

Presenton 的 `/generate` 端點**已經包含**:
- ✅ LLM 內容分析 (使用 Ollama)
- ✅ 投影片結構生成
- ✅ 圖片搜尋和插入
- ✅ PPT/PDF 生成

**我們的 Backend 重複做了相同的工作！**

### 新設計: 簡化整合

**移除重複功能，直接使用 Presenton**:

```
舊設計:
Frontend → Backend → Ollama (分析) → Pexels (圖片) →
           Backend (構建結構) → Presenton (生成) → 返回

新設計:
Frontend → Backend → Presenton /generate (一次完成) → 返回
```

---

## ✅ 修復內容

### 1. 重寫 presenton_service.py

#### 修改前 (錯誤)

```python
async def create_presentation(
    self,
    structure: Dict[str, Any],  # ❌ 接受已構建的結構
    template: str
) -> Dict[str, Any]:
    """Create presentation using Presenton API"""

    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

    # 構建錯誤的 payload
    payload = self._build_payload(structure, template)

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{self.base_url}/api/v1/ppt/presentation/create",  # ❌ 錯誤端點
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
```

#### 修改後 (正確)

```python
async def create_presentation(
    self,
    content: str,  # ✅ 接受原始內容
    template: str,
    n_slides: int = 6
) -> Dict[str, Any]:
    """Create presentation using Presenton API /generate endpoint"""

    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

    # ✅ 使用 Presenton 預期的格式
    payload = {
        "content": content,
        "n_slides": n_slides,
        "language": "zh-TW",
        "template": template,
        "tone": "default",
        "verbosity": "standard",
        "web_search": False,
        "include_table_of_contents": False,
        "include_title_slide": True,
        "export_as": "pptx"
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{self.base_url}/api/v1/ppt/presentation/generate",  # ✅ 正確端點
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
```

**關鍵變更**:
- 參數: `structure` → `content` (原始文字)
- 端點: `/create` → `/generate`
- Payload: 簡報結構 → Presenton API 格式
- 移除: `_build_payload()` 方法 (不再需要)

---

### 2. 簡化 content_processor.py

#### 修改前 (複雜且重複)

```python
async def process_content(self, content: str, template: str, task_id: str):
    # Step 1: 使用 Ollama 分析
    structure = await self.ollama.analyze_content(content, template)

    # Step 2: 識別主題
    await asyncio.sleep(0.5)

    # Step 3: 獲取圖片
    structure = await self._enrich_with_images(structure)

    # Step 4: 發送給 Presenton
    presentation = await self.presenton.create_presentation(structure, template)

    # ...
```

**問題**: Ollama 分析 + Pexels 圖片 = Presenton 也會做的事

#### 修改後 (簡潔)

```python
async def process_content(self, content: str, template: str, task_id: str):
    try:
        # Step 1: 準備內容 (20%)
        self._update_progress(task_id, 20, "正在準備內容...")
        await asyncio.sleep(0.5)

        # Step 2: 發送給 Presenton (40%)
        self._update_progress(task_id, 40, "正在發送給簡報生成引擎...")

        # Step 3: Presenton 處理一切 (60-90%)
        self._update_progress(task_id, 60, "正在生成簡報...")

        # ✅ Presenton 處理: 分析, 圖片, 佈局, 生成
        presentation_result = await self.presenton.create_presentation(
            content=content,
            template=template,
            n_slides=6
        )

        # Step 4: 完成 (100%)
        self._update_progress(task_id, 100, "簡報生成完成...")

        # 提取 presentation_id
        presentation_id = presentation_result.get("presentation_id")
        if not presentation_id:
            pres_path = presentation_result.get("presentation_path", "")
            presentation_id = pres_path.split("/")[-1].replace(".pptx", "")

        result = {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "message": "簡報生成完成",
            "current_step": "完成",
            "presentation_id": presentation_id,
            "download_url": f"/api/download/{presentation_id}/pptx",
            "pdf_url": f"/api/download/{presentation_id}/pdf"
        }

        self.tasks[task_id] = result
        return result

    except Exception as e:
        # 錯誤處理
        ...
```

**關鍵變更**:
- 移除: Ollama 內容分析 (Presenton 內建)
- 移除: Pexels 圖片獲取 (Presenton 內建)
- 移除: 結構構建邏輯 (Presenton 內建)
- 簡化: 直接調用 Presenton `/generate`

---

## 📊 Presenton API 端點分析

### 主要端點對比

| 端點 | 用途 | 輸入 | 輸出 |
|------|------|------|------|
| `/create` | **創建簡報記錄** | content, n_slides, language | PresentationModel (僅資料庫記錄) |
| `/prepare` | **準備投影片** | presentation_id, outlines, layout | PresentationModel |
| **`/generate`** | **🌟 完整生成** | content, template, n_slides | {presentation_path, edit_page_path} |
| `/generate/async` | **異步生成** | 同 /generate | AsyncTaskModel |
| `/export/pptx` | **導出 PPTX** | presentation_id | Binary file |
| `/export/pdf` | **導出 PDF** | presentation_id | Binary file |

### /generate 端點詳細

**完整請求格式**:
```python
{
    "content": str,  # ✅ 必需 - 原始內容
    "n_slides": int = 8,  # 投影片數量
    "language": str = "English",  # 語言
    "template": str = "general",  # 模板
    "tone": str = "default",  # 語氣 (default/formal/casual)
    "verbosity": str = "standard",  # 詳細程度 (concise/standard/detailed)
    "web_search": bool = False,  # 是否網路搜尋
    "include_table_of_contents": bool = False,
    "include_title_slide": bool = True,
    "files": List[str] = None,  # 附加文件
    "export_as": str = "pptx",  # 導出格式 (pptx/pdf)
    "instructions": str = None,  # 額外指示
    "slides_markdown": List[str] = None  # 預定義投影片 markdown
}
```

**返回格式**:
```python
{
    "presentation_path": "/exports/xxx.pptx",  # PPTX 文件路徑
    "edit_page_path": "http://localhost:3000/edit/xxx",  # 編輯頁面
    "presentation_id": "uuid"  # 簡報 ID (可能需要從 path 提取)
}
```

---

## 🧪 驗證測試

### 1. 檢查服務狀態

```bash
docker-compose ps
docker-compose logs -f backend | head -20
```

### 2. Health Check

```bash
curl http://localhost:5000/api/health
```

**預期**:
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

### 3. 端到端測試

1. 訪問 http://localhost:8080
2. 輸入測試內容:
   ```
   人工智慧是一種模擬人類智能的技術。它包括機器學習、深度學習和自然語言處理等領域。
   AI 可以應用在醫療、金融、教育等多個領域，為人類生活帶來便利。
   未來 AI 將繼續發展，成為我們生活中不可或缺的一部分。
   ```
3. 選擇模板: 教學簡報
4. 點擊「生成簡報」
5. 觀察進度條: 20% → 40% → 60% → 100%
6. 下載 PPTX/PDF

**預期結果**:
- ✅ 無 422 錯誤
- ✅ 進度正常顯示
- ✅ 簡報成功生成
- ✅ 文件可下載

---

## 🎯 架構變更總結

### Before (複雜且重複)

```
┌─────────────────────────────────────────────┐
│              Frontend                       │
└──────────────┬──────────────────────────────┘
               │ POST /api/generate
               ↓
┌──────────────────────────────────────────────┐
│             Backend                          │
│  ┌────────────────────────────────────┐     │
│  │ 1. Ollama 分析內容                 │     │
│  │    - 提取主題                      │     │
│  │    - 構建結構                      │     │
│  ├────────────────────────────────────┤     │
│  │ 2. Pexels 獲取圖片                 │     │
│  │    - 生成關鍵字                    │     │
│  │    - 下載圖片                      │     │
│  ├────────────────────────────────────┤     │
│  │ 3. 構建 Presenton Payload          │     │
│  │    - 組裝投影片                    │     │
│  │    - 添加圖片 URL                  │     │
│  └────────────────────────────────────┘     │
└──────────────┬──────────────────────────────┘
               │ POST /api/v1/ppt/presentation/create
               ↓
┌──────────────────────────────────────────────┐
│           Presenton                          │
│  ⚠️ 收到錯誤格式 → 422 Error               │
└──────────────────────────────────────────────┘
```

### After (簡潔且正確)

```
┌─────────────────────────────────────────────┐
│              Frontend                       │
└──────────────┬──────────────────────────────┘
               │ POST /api/generate
               ↓
┌──────────────────────────────────────────────┐
│             Backend                          │
│  ┌────────────────────────────────────┐     │
│  │ 1. 接收原始內容                    │     │
│  │ 2. 轉發給 Presenton                │     │
│  └────────────────────────────────────┘     │
└──────────────┬──────────────────────────────┘
               │ POST /api/v1/ppt/presentation/generate
               │ {content, template, n_slides}
               ↓
┌──────────────────────────────────────────────┐
│           Presenton                          │
│  ┌────────────────────────────────────┐     │
│  │ 1. LLM 分析內容 (內建 Ollama)      │     │
│  │ 2. 生成投影片結構                  │     │
│  │ 3. 搜尋並插入圖片                  │     │
│  │ 4. 生成 PPTX/PDF                   │     │
│  └────────────────────────────────────┘     │
│  ✅ 返回: {presentation_path, id}          │
└──────────────────────────────────────────────┘
```

---

## 💡 經驗教訓

### 1. API 整合前先完整理解

❌ **錯誤做法**: 猜測 API 格式，邊做邊改
✅ **正確做法**:
- 閱讀 OpenAPI 規範 (`/openapi.json`)
- 查看源碼 (如果開源)
- 測試端點行為
- 理解完整工作流程

### 2. 避免功能重複

❌ **錯誤做法**: 自己實作 Presenton 已有的功能 (Ollama 分析, 圖片搜尋)
✅ **正確做法**:
- 了解第三方服務的完整能力
- 利用現有功能，不要重複造輪子
- Backend 作為**協調層**而非**處理層**

### 3. 簡單優於複雜

**原則**: 如果第三方服務能做完整個流程，就讓它做

**我們的角色**:
- ✅ 提供用戶介面
- ✅ 管理請求/響應
- ✅ 進度追蹤
- ❌ 不要重複實作業務邏輯

---

## 📚 相關文檔

- [Presenton GitHub](https://github.com/presenton/presenton)
- [Previous 404 Fix](presenton_api_fix.md)
- [Backend 日誌查看](how_to_read_backend_log.md)

---

## ✅ 修復檢查清單

- [x] 分析 422 錯誤原因
- [x] 研究 Presenton API 文檔
- [x] 重寫 `presenton_service.py`
- [x] 簡化 `content_processor.py`
- [x] 移除重複的 Ollama/Pexels 調用
- [x] 更新 API 端點為 `/generate`
- [x] 修正 payload 格式
- [x] 重啟 Backend 容器
- [x] 驗證 health check
- [x] 端到端功能測試

---

**修復完成時間**: 2025-10-14
**狀態**: ✅ 已修復
**影響**: 大幅簡化 Backend 代碼，提升可維護性
