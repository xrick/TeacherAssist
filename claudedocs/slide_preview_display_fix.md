# 投影片預覽內容顯示不清楚問題診斷

## 問題描述

### 症狀
- **用戶反饋**: "the right most part still doesn't show a clear content of choosed ppt slide"
- **位置**: 前端右側預覽面板
- **影響**: 點擊投影片縮圖後，右側預覽區域無法清楚顯示投影片的完整內容

## 程式碼分析

### 1. 投影片預覽功能架構

#### 數據流程
```
用戶點擊投影片縮圖
    ↓
selectSlide(index, slide) 函數被觸發
    ↓
如果有 presentationId → fetchSlideDetails(presentationId)
    ↓                           ↓
    No                        Yes - API 呼叫
    ↓                           ↓
使用基本 slide 數據      使用詳細的 detailedSlide 數據
    ↓                           ↓
顯示 slide.content[]    renderSlideContent(detailedSlide.content)
(文字要點列表)              ↓
                        渲染完整 content 物件
```

#### 前端關鍵函數

**1. `selectSlide(index, slide)` - 主要顯示邏輯** ([frontend/index.html:994-1104](frontend/index.html#L994-L1104))

```javascript
async selectSlide(index, slide) {
    // 1. 更新選中狀態
    document.querySelectorAll('.slide-card').forEach(card => {
        card.classList.remove('selected');
    });
    document.querySelector(`.slide-card[data-slide-index="${index}"]`)?.classList.add('selected');

    this.selectedSlideIndex = index;

    // 2. 嘗試獲取詳細數據
    let detailedSlide = null;
    if (this.presentationId) {
        const detailedData = await this.fetchSlideDetails(this.presentationId);
        if (detailedData && detailedData.slides && detailedData.slides[index]) {
            detailedSlide = detailedData.slides[index];
        }
    }

    // 3. 建立預覽 HTML
    let previewHtml = `...`; // 標題區域

    // 4. 顯示內容 (兩種模式)
    if (detailedSlide) {
        // 模式 A: 詳細模式 (從 API 取得)
        if (detailedSlide.layout) {
            // 顯示佈局樣式
        }

        if (detailedSlide.content) {
            const renderedContent = this.renderSlideContent(detailedSlide.content);
            previewHtml += `
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">投影片內容</div>
                    <div style="padding: 1rem; background: var(--bg-secondary); border-radius: 6px; font-size: 0.875rem; max-height: 400px; overflow-y: auto;">
                        ${renderedContent}  // ← 這裡可能是問題所在！
                    </div>
                </div>
            `;
        }

        if (detailedSlide.speaker_note) {
            // 顯示演講者備註
        }
    } else {
        // 模式 B: 基本模式 (使用生成時的數據)
        if (slide.content && slide.content.length > 0) {
            previewHtml += `
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">內容要點</div>
                    <ul style="padding-left: 1.5rem; margin: 0;">
                        ${slide.content.map(point => `<li style="margin-bottom: 0.5rem;">${point}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (slide.image_url) {
            // 顯示投影片圖片
        }
    }
}
```

**2. `renderSlideContent(content)` - 內容渲染邏輯** ([frontend/index.html:1109-1180](frontend/index.html#L1109-L1180))

```javascript
renderSlideContent(content) {
    if (!content || typeof content !== 'object') {
        return '<div style="color: var(--text-secondary); font-style: italic;">無內容資料</div>';
    }

    // 定義欄位分類
    const metadataFields = ['companyName', 'date', 'id', 'index', 'slideId', 'presentationId', 'createdAt', 'updatedAt'];
    const textFields = ['title', 'subtitle', 'heading', 'header'];
    const descriptionFields = ['description', 'text', 'paragraph', 'content', 'body'];
    const listFields = ['bullets', 'points', 'items', 'list'];

    let html = '';

    // 遍歷 content 物件的所有鍵值
    for (const [key, value] of Object.entries(content)) {
        // 跳過 metadata 和空值
        if (metadataFields.includes(key) || value === null || value === undefined || value === '') {
            continue;
        }

        const displayKey = key.replace(/([A-Z])/g, ' $1').trim().replace(/^./, str => str.toUpperCase());

        // 根據欄位類型決定渲染方式
        if (textFields.includes(key)) {
            // 標題類欄位 → 大號粗體字
            html += `<div style="font-size: 1.1rem; font-weight: 600; color: var(--primary-color);">${value}</div>`;
        } else if (descriptionFields.includes(key)) {
            // 描述類欄位 → 一般文字段落
            html += `<div style="line-height: 1.6; color: var(--text-primary);">${value}</div>`;
        } else if (listFields.includes(key) && Array.isArray(value)) {
            // 列表類欄位 → 項目符號列表
            html += `
                <ul style="margin: 0; padding-left: 1.5rem;">
                    ${value.map(item => `<li style="margin-bottom: 0.25rem;">${item}</li>`).join('')}
                </ul>
            `;
        } else if (Array.isArray(value)) {
            // 其他陣列 → 編號列表 + JSON
            html += `
                <div style="padding-left: 1rem;">
                    ${value.map((item, idx) => {
                        if (typeof item === 'object') {
                            return `<div><strong>${idx + 1}.</strong> ${JSON.stringify(item, null, 2)}</div>`;
                        }
                        return `<div><strong>${idx + 1}.</strong> ${item}</div>`;
                    }).join('')}
                </div>
            `;
        } else if (typeof value === 'object') {
            // 巢狀物件 → JSON 顯示
            html += `<pre style="background: #f5f5f5; padding: 0.5rem; border-radius: 4px; overflow-x: auto;">${JSON.stringify(value, null, 2)}</pre>`;
        } else {
            // 其他類型 → 直接文字顯示
            html += `<div>${displayKey}: ${value}</div>`;
        }
    }

    return html || '<div style="color: var(--text-secondary); font-style: italic;">無可顯示的內容</div>';
}
```

### 2. 潛在問題點

#### 問題 1: Presenton API `content` 物件欄位名稱可能不符合預期

**假設**: Presenton API 可能使用的欄位名稱:
- `main_content` 而非 `description`
- `slide_text` 而非 `text`
- `bullet_points` 而非 `bullets`
- 或其他完全不同的命名

**結果**: `renderSlideContent()` 無法識別這些欄位，導致：
- 所有內容被歸類為「其他類型」
- 顯示為 `Field Name: value` 的原始格式
- 或完全被 metadata 過濾器跳過

#### 問題 2: `content` 物件可能是字串而非物件

**情境**: Presenton 可能直接回傳字串內容:
```json
{
  "content": "這是投影片的完整文字內容..."
}
```

**結果**: `renderSlideContent()` 檢查 `typeof content !== 'object'` 時回傳「無內容資料」

#### 問題 3: 沒有 `presentationId` 導致永遠使用基本模式

**情境**: `this.presentationId` 未被正確設定

**結果**: 永遠進入 `else` 分支，只顯示基本的 `slide.content[]` 要點，而非完整的 API 數據

#### 問題 4: API 呼叫失敗或回傳格式不符

**情境**: `fetchSlideDetails()` 失敗或回傳結構與預期不符

**結果**: `detailedSlide` 為 `null`，退回到基本顯示模式

## 診斷步驟

### Step 1: 確認 `presentationId` 是否被正確設定

**檢查點**: 在前端生成完成後檢查
```javascript
// 應該在 renderPresentation() 函數中設定
this.presentationId = taskId;  // 或 response.presentation_id
```

**測試方法**:
1. 開啟瀏覽器 DevTools → Console
2. 生成投影片後執行: `app.presentationId`
3. 應該看到類似 `"cm3uu7mmi000008kyfnjd5uy1"` 的 ID

### Step 2: 檢查 API 是否成功呼叫並回傳數據

**測試方法**:
1. 開啟 DevTools → Network tab
2. 點擊任一投影片縮圖
3. 查看是否有 `GET /api/presentation/{id}` 請求
4. 檢查 Response 數據結構

**預期回傳格式**:
```json
{
  "id": "cm3uu7mmi000008kyfnjd5uy1",
  "slides": [
    {
      "id": "slide_001",
      "index": 0,
      "layout_group": "content",
      "layout": "title-and-content",
      "content": {
        "title": "投影片標題",
        "description": "投影片內容描述...",
        "bullets": ["要點 1", "要點 2", "要點 3"]
      },
      "speaker_note": "演講者備註..."
    },
    ...
  ]
}
```

### Step 3: 確認 `content` 物件的實際欄位名稱

**問題**: 我們不知道 Presenton 實際使用什麼欄位名稱

**解決方法**:
1. 使用測試腳本: `/scripts/test_presentation_api.sh <presentation_id>`
2. 或在瀏覽器 Console 手動呼叫:
   ```javascript
   fetch('/api/presentation/cm3uu7mmi000008kyfnjd5uy1')
     .then(r => r.json())
     .then(data => console.log(data.slides[0].content))
   ```
3. 記錄所有欄位名稱

### Step 4: 檢查 `renderSlideContent()` 是否被呼叫

**測試方法**: 在函數開頭加入 `console.log`
```javascript
renderSlideContent(content) {
    console.log('renderSlideContent called with:', content);
    // ... 原有邏輯
}
```

**預期輸出**: 每次點擊投影片時應該在 Console 看到內容物件

## 可能的解決方案

### 方案 A: 改進 `renderSlideContent()` 的通用性

**問題**: 當前邏輯依賴特定欄位名稱，不夠靈活

**改進方向**:
1. **啟發式欄位檢測**: 不依賴固定欄位名稱，而是根據資料類型和內容特徵判斷
2. **全部顯示策略**: 顯示所有非 metadata 欄位，不管是否匹配預定義列表
3. **智能格式化**: 根據值的長度和類型自動選擇最佳顯示方式

**改進後的邏輯**:
```javascript
renderSlideContent(content) {
    if (!content || typeof content !== 'object') {
        return '<div style="color: var(--text-secondary); font-style: italic;">無內容資料</div>';
    }

    const metadataFields = ['id', 'index', 'slideId', 'presentationId', 'createdAt', 'updatedAt'];
    let html = '';

    for (const [key, value] of Object.entries(content)) {
        // 只跳過 metadata，顯示所有其他內容
        if (metadataFields.includes(key) || value === null || value === undefined || value === '') {
            continue;
        }

        const displayKey = key
            .replace(/([A-Z])/g, ' $1')  // camelCase → camel Case
            .replace(/_/g, ' ')           // snake_case → snake case
            .trim()
            .replace(/^./, str => str.toUpperCase());  // 首字母大寫

        if (typeof value === 'string') {
            // 字串類型: 根據長度決定顯示方式
            if (value.length < 50) {
                // 短文字: 標題樣式
                html += `
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 1.1rem; font-weight: 600; color: var(--primary-color);">
                            ${value}
                        </div>
                    </div>
                `;
            } else {
                // 長文字: 段落樣式
                html += `
                    <div style="margin-bottom: 1rem;">
                        <div style="font-weight: 500; margin-bottom: 0.5rem; color: var(--text-secondary);">
                            ${displayKey}
                        </div>
                        <div style="line-height: 1.6; color: var(--text-primary);">
                            ${value}
                        </div>
                    </div>
                `;
            }
        } else if (Array.isArray(value)) {
            // 陣列類型: 項目符號列表
            html += `
                <div style="margin-bottom: 1rem;">
                    <div style="font-weight: 500; margin-bottom: 0.5rem; color: var(--text-secondary);">
                        ${displayKey}
                    </div>
                    <ul style="margin: 0; padding-left: 1.5rem; line-height: 1.8;">
                        ${value.map(item => {
                            if (typeof item === 'object') {
                                return `<li style="margin-bottom: 0.5rem;">${JSON.stringify(item)}</li>`;
                            }
                            return `<li style="margin-bottom: 0.5rem;">${item}</li>`;
                        }).join('')}
                    </ul>
                </div>
            `;
        } else if (typeof value === 'object') {
            // 物件類型: 格式化 JSON 顯示
            html += `
                <div style="margin-bottom: 1rem;">
                    <div style="font-weight: 500; margin-bottom: 0.5rem; color: var(--text-secondary);">
                        ${displayKey}
                    </div>
                    <pre style="background: var(--bg-tertiary); padding: 1rem; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; line-height: 1.4; margin: 0;">
${JSON.stringify(value, null, 2)}</pre>
                </div>
            `;
        } else {
            // 其他類型: 簡單 key-value 顯示
            html += `
                <div style="margin-bottom: 0.75rem;">
                    <span style="font-weight: 500; color: var(--text-secondary);">${displayKey}:</span>
                    <span style="margin-left: 0.5rem;">${value}</span>
                </div>
            `;
        }
    }

    return html || '<div style="color: var(--text-secondary); font-style: italic;">無可顯示的內容</div>';
}
```

### 方案 B: 處理字串類型的 `content`

**情況**: 如果 `content` 是字串而非物件

**修改 `selectSlide()` 函數**:
```javascript
if (detailedSlide.content) {
    let renderedContent;
    if (typeof detailedSlide.content === 'string') {
        // 直接顯示字串內容
        renderedContent = `<div style="line-height: 1.6; white-space: pre-wrap;">${detailedSlide.content}</div>`;
    } else if (typeof detailedSlide.content === 'object') {
        // 使用 renderSlideContent 處理物件
        renderedContent = this.renderSlideContent(detailedSlide.content);
    } else {
        renderedContent = '<div style="color: var(--text-secondary); font-style: italic;">無法渲染此內容類型</div>';
    }

    previewHtml += `
        <div>
            <div style="font-weight: 600; margin-bottom: 0.5rem;">投影片內容</div>
            <div style="padding: 1rem; background: var(--bg-secondary); border-radius: 6px; font-size: 0.875rem; max-height: 400px; overflow-y: auto;">
                ${renderedContent}
            </div>
        </div>
    `;
}
```

### 方案 C: Debug 模式顯示原始數據

**目的**: 幫助診斷問題

**在 `selectSlide()` 中加入 debug 顯示**:
```javascript
// 在詳細內容區域後加入
if (detailedSlide && window.location.search.includes('debug=true')) {
    previewHtml += `
        <div style="margin-top: 1.5rem; padding: 1rem; background: #f0f0f0; border-radius: 6px;">
            <div style="font-weight: 600; margin-bottom: 0.5rem;">Debug 資訊</div>
            <details>
                <summary style="cursor: pointer; color: var(--primary-color);">查看原始投影片數據</summary>
                <pre style="margin-top: 0.5rem; background: white; padding: 1rem; border-radius: 4px; overflow-x: auto; font-size: 0.75rem;">
${JSON.stringify(detailedSlide, null, 2)}</pre>
            </details>
        </div>
    `;
}
```

**使用方法**: 瀏覽器網址加上 `?debug=true`，例如 `http://localhost:8080?debug=true`

## 建議執行順序

1. **立即可行**: 實作方案 C (Debug 模式)，快速確認實際數據結構
2. **診斷**: 使用 DevTools 和測試腳本檢查 API 回傳格式
3. **修復**: 根據實際數據結構實作方案 A 或方案 B
4. **測試**: 生成新 PPT 並測試各種投影片類型的顯示
5. **優化**: 根據使用回饋持續改進顯示邏輯

## 總結

**問題核心**: `renderSlideContent()` 函數的欄位匹配邏輯可能與 Presenton API 實際回傳的數據結構不符

**診斷關鍵**: 確認實際的 `content` 物件欄位名稱和資料類型

**解決方向**:
- **短期**: 改用更通用的顯示邏輯，不依賴特定欄位名稱
- **長期**: 建立完整的 Presenton API 數據模型文檔，確保前後端對齊

---

**文檔日期**: 2025-11-13
**相關問題**: 投影片內容預覽不清楚
**影響範圍**: 前端 UI 顯示邏輯
**優先級**: 中 (功能性問題，不影響核心生成功能)
