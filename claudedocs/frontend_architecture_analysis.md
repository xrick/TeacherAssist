# Frontend 架構分析

**日期**: 2025-11-09
**檔案**: `frontend/index.html`
**技術棧**: 100% Vanilla HTML/CSS/JavaScript

---

## 快速總結

### ✅ 核心發現

1. **零依賴**: 完全沒有使用任何第三方函式庫
2. **單一檔案**: 所有 HTML/CSS/JavaScript 都在一個檔案中
3. **需要 HTTP Server**: 不能直接用 `file://` 協議開啟
4. **現代技術**: 使用 ES6+、Fetch API、CSS Grid 等原生功能

---

## 為什麼需要初始化 Frontend？

### 問題：為何不能直接開啟 index.html？

雖然 `index.html` 只是單一檔案，但直接用瀏覽器開啟會遇到問題：

#### file:// 協議的限制

**直接開啟** (不推薦):
```bash
# macOS
open frontend/index.html

# Windows
start frontend/index.html

# Linux
xdg-open frontend/index.html
```

**結果**: 瀏覽器使用 `file:///path/to/index.html` 協議

**問題**:

| 功能 | file:// | http:// |
|------|---------|---------|
| **CORS 跨域請求** | ❌ 被阻擋 | ✅ 正常 |
| **Fetch API** | ❌ 限制 | ✅ 正常 |
| **相對路徑** | ⚠️ 可能錯誤 | ✅ 正確 |
| **Cookie/Storage** | ⚠️ 受限 | ✅ 正常 |
| **WebSocket** | ❌ 不支援 | ✅ 支援 |
| **Service Worker** | ❌ 不支援 | ✅ 支援 |

#### CORS 錯誤實例

**使用 file:// 開啟時**:
```javascript
// frontend/index.html 中的程式碼
const response = await fetch('http://localhost:5050/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});
```

**瀏覽器 Console 錯誤**:
```
Access to fetch at 'http://localhost:5050/api/generate' from origin 'null'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header
is present on the requested resource.
```

**原因**:
- `file://` 協議的 origin 是 `null`
- Backend CORS 設定只允許 `http://` 來源
- 瀏覽器安全策略阻擋跨域請求

---

### 解決方案：HTTP Server

#### 方法 1: Python HTTP Server (推薦)

**啟動**:
```bash
cd frontend
python3 -m http.server 8080
```

**優點**:
- ✅ Python 內建，無需安裝
- ✅ 輕量、快速
- ✅ 適合開發環境

**訪問**: http://localhost:8080

#### 方法 2: Node.js HTTP Server

**安裝**:
```bash
npm install -g http-server
```

**啟動**:
```bash
cd frontend
http-server -p 8080
```

#### 方法 3: PHP 內建 Server

**啟動**:
```bash
cd frontend
php -S localhost:8080
```

#### 方法 4: Live Server (VSCode 擴充)

**安裝**: VSCode Extension - "Live Server"

**使用**: 右鍵點擊 `index.html` → "Open with Live Server"

---

## 技術架構分析

### 檔案結構

```
frontend/
└── index.html (單一檔案，包含全部內容)
    ├── HTML 結構
    ├── <style> 內嵌 CSS
    └── <script> 內嵌 JavaScript
```

**檔案大小**: ~1000 行左右

---

### 使用的原生技術

#### 1. CSS Variables (CSS 自訂屬性)

**用途**: 設計系統、主題管理

**實作**:
```css
:root {
    /* 顏色系統 */
    --primary-color: #4F46E5;
    --primary-hover: #4338CA;
    --secondary-color: #10B981;
    --accent-color: #F59E0B;

    /* 背景與表面 */
    --background: #FFFFFF;
    --surface: #F8FAFC;
    --surface-elevated: #FFFFFF;

    /* 文字顏色 */
    --text-primary: #1F2937;
    --text-secondary: #6B7280;
    --text-muted: #9CA3AF;

    /* 邊框與陰影 */
    --border: #E5E7EB;
    --border-light: #F3F4F6;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);

    /* 圓角 */
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
}

/* 使用變數 */
.button {
    background: var(--primary-color);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-md);
}

.button:hover {
    background: var(--primary-hover);
}
```

**優勢**:
- ✅ 統一的設計系統
- ✅ 易於維護和修改
- ✅ 支援動態主題切換
- ✅ 無需 SASS/LESS

#### 2. CSS Grid 佈局

**用途**: 響應式雙欄佈局

**實作**:
```css
.main-container {
    max-width: 1400px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;  /* 左右各 50% */
    gap: 2rem;                       /* 間距 */
    padding: 2rem;
    min-height: calc(100vh - 80px);
}
```

**效果**:
```
┌─────────────────────────────────────┐
│           Header (sticky)           │
├─────────────────┬───────────────────┤
│                 │                   │
│   Input Panel   │   Preview Panel   │
│                 │                   │
│  (左側 50%)     │   (右側 50%)      │
│                 │                   │
└─────────────────┴───────────────────┘
```

#### 3. Flexbox 對齊

**用途**: Header 內容排列、按鈕群組

**實作**:
```css
.header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
```

#### 4. Vanilla JavaScript Class

**用途**: 應用程式邏輯管理

**完整架構**:
```javascript
class PresentationApp {
    constructor() {
        // 配置
        this.API_BASE_URL = 'http://localhost:5050/api';
        this.presentationId = null;
        this.taskId = null;
        this.pollInterval = null;

        // DOM 元素引用
        this.contentInput = document.getElementById('content-input');
        this.generateBtn = document.getElementById('generate-btn');
        this.downloadPptxBtn = document.getElementById('download-pptx');
        this.downloadPdfBtn = document.getElementById('download-pdf');
        this.previewContent = document.getElementById('preview-content');
        this.progressBar = document.getElementById('progress-bar');
        this.progressText = document.getElementById('progress-text');

        // 初始化
        this.initializeEventListeners();
    }

    // 事件監聽器初始化
    initializeEventListeners() {
        this.generateBtn.addEventListener('click', () => this.generatePresentation());
        this.downloadPptxBtn.addEventListener('click', () => this.downloadFile('pptx'));
        this.downloadPdfBtn.addEventListener('click', () => this.downloadFile('pdf'));
        this.generateTranscriptBtn.addEventListener('click', () => this.generateTranscript());
    }

    // 主要功能方法
    async generatePresentation() { /* ... */ }
    async poll() { /* ... */ }
    renderPreview(data) { /* ... */ }
    async downloadFile(format) { /* ... */ }
    async generateTranscript() { /* ... */ }
}

// 應用程式啟動
document.addEventListener('DOMContentLoaded', () => {
    new PresentationApp();
});
```

**設計模式**:
- ✅ **單例模式**: 只建立一個 App 實例
- ✅ **封裝**: 所有狀態和方法都在 class 內
- ✅ **事件驅動**: 基於 DOM 事件的互動

#### 5. Fetch API (非同步請求)

**用途**: 與 Backend API 通訊

**實作範例**:
```javascript
async generatePresentation() {
    const content = this.contentInput.value.trim();

    if (!content || content.length < 50) {
        alert('請輸入至少 50 個字的內容');
        return;
    }

    this.generateBtn.disabled = true;
    this.generateBtn.textContent = '生成中...';

    try {
        const response = await fetch(`${this.API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                template: this.templateSelect.value,
                language: 'zh-TW'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        this.taskId = data.task_id;
        this.poll();
    } catch (error) {
        console.error('生成失敗:', error);
        alert('生成失敗: ' + error.message);
    } finally {
        this.generateBtn.disabled = false;
        this.generateBtn.textContent = '生成簡報';
    }
}
```

**特色**:
- ✅ async/await 語法
- ✅ 完整的錯誤處理
- ✅ finally 區塊清理
- ✅ 無需 axios 或其他 HTTP 函式庫

#### 6. 輪詢機制 (Polling)

**用途**: 即時追蹤簡報生成進度

**實作**:
```javascript
async poll() {
    this.pollInterval = setInterval(async () => {
        try {
            const response = await fetch(
                `${this.API_BASE_URL}/progress/${this.taskId}`
            );
            const data = await response.json();

            // 更新進度條
            this.progressBar.style.width = `${data.progress}%`;
            this.progressText.textContent = data.status;

            // 完成時停止輪詢
            if (data.status === 'completed') {
                clearInterval(this.pollInterval);
                this.presentationId = data.presentation_id;
                this.renderPreview(data.presentation);
                this.enableDownloadButtons();
            }

            // 失敗時停止輪詢
            if (data.status === 'failed') {
                clearInterval(this.pollInterval);
                alert('生成失敗: ' + data.error);
            }
        } catch (error) {
            console.error('輪詢錯誤:', error);
            clearInterval(this.pollInterval);
        }
    }, 2000); // 每 2 秒檢查一次
}
```

**優點**:
- ✅ 即時進度回饋
- ✅ 自動停止機制
- ✅ 錯誤處理完善

#### 7. 動態 HTML 渲染

**用途**: 顯示簡報預覽

**實作**:
```javascript
renderPreview(data) {
    const slides = data.slides || [];

    let html = '<div class="slides-preview">';

    slides.forEach((slide, index) => {
        html += `
            <div class="slide-card">
                <div class="slide-number">投影片 ${index + 1}</div>
                <div class="slide-title">${slide.title}</div>
                <div class="slide-type">${this.getSlideTypeLabel(slide.type)}</div>
                ${slide.image_url ?
                    `<img src="${slide.image_url}" class="slide-image" alt="${slide.title}">`
                    : ''}
                <div class="slide-content">
                    ${slide.content.map(point => `<p>• ${point}</p>`).join('')}
                </div>
            </div>
        `;
    });

    html += '</div>';
    this.previewContent.innerHTML = html;
}
```

**注意**:
- ⚠️ 使用 `innerHTML` (需注意 XSS 風險)
- ✅ Template literals 提供清晰的 HTML 結構
- ✅ 條件渲染 (圖片存在才顯示)

#### 8. 自訂 Scrollbar 樣式

**用途**: 美化捲軸外觀

**實作**:
```css
/* Webkit 瀏覽器 (Chrome, Safari, Edge) */
.preview-panel::-webkit-scrollbar {
    width: 8px;
}

.preview-panel::-webkit-scrollbar-track {
    background: var(--surface);
    border-radius: 4px;
}

.preview-panel::-webkit-scrollbar-thumb {
    background: var(--primary-color);
    border-radius: 4px;
}

.preview-panel::-webkit-scrollbar-thumb:hover {
    background: var(--primary-hover);
}

/* Firefox */
.preview-panel {
    scrollbar-width: thin;
    scrollbar-color: var(--primary-color) var(--surface);
}
```

**瀏覽器支援**:
- ✅ Chrome/Edge (Webkit)
- ✅ Firefox (標準 scrollbar 屬性)
- ⚠️ Safari (部分支援)

---

## 無使用的技術 (確認無依賴)

### 檢查方法

```bash
# 檢查外部資源引用
grep -E "(https?://|//cdn|jsdelivr|unpkg|cdnjs)" frontend/index.html
# 結果：無

# 檢查 script src
grep '<script src=' frontend/index.html
# 結果：無

# 檢查 link href (CSS)
grep '<link.*href=' frontend/index.html
# 結果：無
```

### 確認無使用

❌ **React / Vue / Angular** - 無任何框架
❌ **jQuery** - 使用原生 DOM API
❌ **Bootstrap / Tailwind** - 自訂 CSS
❌ **Axios** - 使用 Fetch API
❌ **Lodash / Underscore** - 使用原生 JavaScript
❌ **Moment.js** - 無日期處理
❌ **Chart.js** - 無圖表功能
❌ **Font Awesome** - 使用 Unicode emoji
❌ **Google Fonts** - 使用系統字型

---

## Vanilla JavaScript 的優缺點

### ✅ 優點

#### 1. 零依賴
```
# 專案結構
frontend/
└── index.html  (唯一檔案)

# 無需
- node_modules/
- package.json
- webpack.config.js
- babel.config.js
```

**好處**:
- 無版本衝突
- 無安全漏洞更新
- 無 npm install 等待
- 無 build 時間

#### 2. 極快載入速度

**效能對比**:

| 項目 | Vanilla | React (CRA) |
|------|---------|-------------|
| 首次載入 | ~50KB | ~200KB+ |
| JavaScript | 內嵌 | Bundle |
| 載入時間 | <100ms | 500ms+ |
| TTI (可互動時間) | <200ms | 1s+ |

**原因**:
- 無框架 runtime 開銷
- 無 Virtual DOM
- 直接操作原生 API

#### 3. 簡單部署

**任何 HTTP server 都可用**:
```bash
# Python
python3 -m http.server 8080

# Node.js
npx http-server -p 8080

# PHP
php -S localhost:8080

# Nginx (生產環境)
# 直接將 index.html 放入 /var/www/html
```

**無需**:
- Node.js runtime
- Build process
- Environment variables
- 複雜的 CI/CD

#### 4. 易於理解

**學習曲線**:
- HTML → CSS → JavaScript (基礎知識即可)
- 無需學習 JSX, Virtual DOM, Component lifecycle
- 無需理解 webpack, babel 配置
- 直接閱讀程式碼即可理解邏輯

#### 5. 完整控制

**精確優化**:
- 每一行程式碼都是自己寫的
- 無黑盒子行為
- 無框架限制
- 性能瓶頸清晰可見

### ⚠️ 缺點

#### 1. 手動 DOM 操作

**問題**:
```javascript
// 每次更新都要手動操作 DOM
this.previewContent.innerHTML = html;
this.progressBar.style.width = `${data.progress}%`;
this.progressText.textContent = data.status;
```

**對比 React**:
```jsx
// React 自動處理 DOM 更新
function Preview({ slides, progress, status }) {
    return (
        <div>
            <div style={{ width: `${progress}%` }}></div>
            <div>{status}</div>
            {slides.map(slide => <SlideCard {...slide} />)}
        </div>
    );
}
```

#### 2. 無元件化

**問題**:
```javascript
// 重複的 HTML 結構無法重用
html += `
    <div class="slide-card">
        <div class="slide-number">投影片 ${index + 1}</div>
        <div class="slide-title">${slide.title}</div>
        <!-- ... 重複程式碼 ... -->
    </div>
`;
```

**對比框架**:
```jsx
// 可重用的元件
<SlideCard
    number={index + 1}
    title={slide.title}
    content={slide.content}
/>
```

#### 3. 無狀態管理

**問題**:
```javascript
// 狀態散落在各處
this.presentationId = null;
this.taskId = null;
this.pollInterval = null;

// 手動同步狀態
if (data.status === 'completed') {
    this.presentationId = data.presentation_id;
    this.enableDownloadButtons();
    this.updateProgress(100);
}
```

**對比框架**:
```javascript
// Redux/Vuex 統一管理
const state = {
    presentation: { id: null, status: 'idle' },
    task: { id: null, progress: 0 }
};
```

#### 4. 無 Reactive 系統

**問題**:
```javascript
// 資料變化時需手動更新 UI
updateProgress(progress) {
    this.progressBar.style.width = `${progress}%`;
    this.progressText.textContent = `進度: ${progress}%`;
}
```

**對比框架**:
```javascript
// Vue 自動響應式更新
data() {
    return { progress: 0 };
}
// 當 progress 改變，UI 自動更新
```

#### 5. XSS 風險

**問題**:
```javascript
// 直接插入 HTML 有 XSS 風險
this.previewContent.innerHTML = html;
```

**安全做法**:
```javascript
// 應該使用 textContent 或 createElement
const div = document.createElement('div');
div.textContent = userInput; // 自動 escape
```

---

## 初始化流程詳解

### start_system.sh 中的 Frontend 初始化

**完整流程**:
```bash
# ===== Step X: 啟動 Frontend =====
echo "Step X: 啟動 Frontend 靜態服務器"
echo "-----------------------------"

# 1. 檢查 Port 8080 可用性
check_port 8080 "Frontend"

# 2. 切換到 frontend 目錄
cd frontend

# 3. 啟動 Python HTTP Server (背景執行)
print_info "啟動 Frontend 靜態服務器..."
python3 -m http.server 8080 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

# 4. 等待服務啟動
sleep 2

# 5. 驗證服務運行
if curl -s http://localhost:8080 >/dev/null 2>&1; then
    print_success "Frontend 運行在 http://localhost:8080"
else
    print_error "Frontend 啟動失敗"
    cat /tmp/frontend.log
    exit 1
fi

# 6. 記錄 PID 供後續管理
echo $FRONTEND_PID > /tmp/frontend.pid
```

### 為什麼需要這些步驟？

#### 1. Port 檢查
```bash
check_port 8080 "Frontend"
```

**目的**:
- 避免與其他服務衝突
- 確保 port 可用
- 提供友善的錯誤訊息

#### 2. 背景執行
```bash
python3 -m http.server 8080 > /tmp/frontend.log 2>&1 &
```

**細節**:
- `> /tmp/frontend.log` - 標準輸出導向檔案
- `2>&1` - 標準錯誤也導向同一檔案
- `&` - 在背景執行，不阻塞腳本

#### 3. 等待啟動
```bash
sleep 2
```

**原因**:
- HTTP server 需要時間初始化
- Bind port 需要時間
- 避免驗證時服務未就緒

#### 4. 健康檢查
```bash
curl -s http://localhost:8080 >/dev/null 2>&1
```

**驗證**:
- `-s` - 靜默模式，不顯示進度
- `>/dev/null` - 不關心輸出內容
- `2>&1` - 錯誤也導向 /dev/null
- 只檢查 exit code (0 = 成功)

---

## API 通訊架構

### Frontend → Backend 流程

```
┌─────────────┐         ┌──────────────┐
│  Frontend   │         │   Backend    │
│ localhost:  │         │  localhost:  │
│   8080      │         │    5050      │
└──────┬──────┘         └──────┬───────┘
       │                       │
       │ POST /api/generate    │
       ├──────────────────────>│
       │ {content, template}   │
       │                       │
       │<──────────────────────┤
       │ {task_id}             │
       │                       │
       │ GET /api/progress/:id │
       ├──────────────────────>│
       │ (每 2 秒輪詢)         │
       │                       │
       │<──────────────────────┤
       │ {progress, status}    │
       │                       │
       │ GET /api/download/:id │
       ├──────────────────────>│
       │                       │
       │<──────────────────────┤
       │ presentation.pptx     │
       └───────────────────────┘
```

### API 端點配置

**Frontend 配置**:
```javascript
const API_BASE_URL = 'http://localhost:5050/api';
```

**Backend CORS 配置**:
```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**為什麼需要 CORS**:
- Frontend (8080) 和 Backend (5050) 是不同的 port
- 瀏覽器視為跨域請求
- 需要 Backend 明確允許

---

## 升級建議

### 何時應該升級？

#### 保持 Vanilla 的情境
- ✅ 專案規模小 (<1000 行)
- ✅ 團隊熟悉原生 JavaScript
- ✅ 性能要求極高
- ✅ 不需要複雜互動
- ✅ SEO 不重要

#### 應該升級的情境
- ❌ 專案規模增長 (>2000 行)
- ❌ 需要大量可重用元件
- ❌ 複雜的狀態管理需求
- ❌ 多人協作開發
- ❌ 需要 TypeScript 型別安全

### 漸進式升級路徑

#### Level 1: 輕量增強 (Alpine.js)

**特色**:
- 保持 HTML 為主
- 加入 reactive 特性
- 只需 CDN 引入

**範例**:
```html
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js"></script>

<div x-data="{ progress: 0, status: 'idle' }">
    <div x-show="status === 'processing'">處理中...</div>
    <div :style="`width: ${progress}%`"></div>
</div>
```

**優點**:
- ✅ 最小改動
- ✅ 學習曲線低
- ✅ 仍是單一 HTML 檔案

#### Level 2: 現代框架 (Vue.js)

**特色**:
- 完整的元件系統
- Reactive 狀態管理
- 可選擇 Single File Component

**範例**:
```vue
<template>
    <SlideCard
        v-for="(slide, index) in slides"
        :key="index"
        :slide="slide"
        :index="index"
    />
</template>

<script setup>
import { ref } from 'vue';
const slides = ref([]);
</script>
```

#### Level 3: 企業級 (React + TypeScript)

**特色**:
- 型別安全
- 大型專案支援
- 豐富的生態系

**範例**:
```typescript
interface Slide {
    title: string;
    content: string[];
    type: 'title' | 'content' | 'conclusion';
}

const SlideCard: React.FC<{ slide: Slide }> = ({ slide }) => {
    return <div className="slide-card">{slide.title}</div>;
};
```

---

## 開發工作流程

### 本地開發

**步驟 1: 啟動 Backend**
```bash
cd /path/to/TeacherAssist
docker compose up -d backend presenton
```

**步驟 2: 啟動 Frontend**
```bash
cd frontend
python3 -m http.server 8080
```

**步驟 3: 開啟瀏覽器**
```bash
open http://localhost:8080
```

**步驟 4: 開發**
- 編輯 `index.html`
- 儲存檔案
- 重新整理瀏覽器 (F5)

### 除錯技巧

#### 1. Chrome DevTools

**Console 面板**:
```javascript
// 查看 App 實例
window.app = new PresentationApp();
console.log(window.app);

// 測試 API
fetch('http://localhost:5050/api/health')
    .then(r => r.json())
    .then(console.log);
```

**Network 面板**:
- 檢查 API 請求
- 查看回應內容
- 檢查 CORS headers

**Elements 面板**:
- 檢查 DOM 結構
- 即時編輯 CSS
- 查看計算後的樣式

#### 2. Error Logging

**在程式碼中加入 log**:
```javascript
async generatePresentation() {
    console.log('=== Generate Started ===');
    console.log('Content:', this.contentInput.value);

    try {
        const response = await fetch(url, options);
        console.log('Response:', response);

        const data = await response.json();
        console.log('Data:', data);
    } catch (error) {
        console.error('Error:', error);
        console.trace(); // 顯示 stack trace
    }
}
```

#### 3. Backend Logs

**查看 Backend 錯誤**:
```bash
docker compose logs -f backend
```

---

## 效能優化

### 目前的效能

**優點**:
- ✅ 首次載入 <100ms
- ✅ TTI (Time to Interactive) <200ms
- ✅ 無 JavaScript bundle 大小問題
- ✅ 無 hydration 成本

**可優化項目**:

#### 1. Image Lazy Loading

```html
<img
    src="${slide.image_url}"
    loading="lazy"           <!-- 加入 lazy loading -->
    alt="${slide.title}"
>
```

#### 2. CSS 優化

```css
/* 使用 will-change 提示瀏覽器優化 */
.slide-card {
    will-change: transform;
}

/* 使用 contain 限制重排範圍 */
.preview-panel {
    contain: layout style paint;
}
```

#### 3. 減少 Reflow

```javascript
// ❌ 每次都觸發 reflow
slides.forEach(slide => {
    const div = document.createElement('div');
    document.body.appendChild(div); // 每次都 reflow
});

// ✅ 只觸發一次 reflow
const fragment = document.createDocumentFragment();
slides.forEach(slide => {
    const div = document.createElement('div');
    fragment.appendChild(div);
});
document.body.appendChild(fragment); // 只 reflow 一次
```

---

## 安全考量

### 目前的安全風險

#### 1. XSS (Cross-Site Scripting)

**風險**:
```javascript
// 直接插入 HTML
this.previewContent.innerHTML = html;
```

**如果 `slide.title` 包含惡意腳本**:
```javascript
{
    title: "<img src=x onerror='alert(document.cookie)'>",
    content: ["惡意內容"]
}
```

**修復方案**:
```javascript
// 方法 1: 使用 textContent (安全但無 HTML)
element.textContent = slide.title;

// 方法 2: 手動 escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 方法 3: 使用 DOMPurify (第三方庫)
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(html);
```

#### 2. CSRF (Cross-Site Request Forgery)

**目前狀態**: 無 CSRF 保護

**風險**: 惡意網站可能代替使用者發送請求

**修復方案**:
```javascript
// 加入 CSRF token
const csrfToken = getCsrfToken();

fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
    },
    body: JSON.stringify(data)
});
```

#### 3. API Key 暴露

**目前狀態**: API 呼叫直接從 Frontend

**風險**: Backend API 端點公開暴露

**建議**:
- ✅ Backend 已有認證機制
- ✅ 使用環境變數管理 API keys
- ⚠️ 考慮加入 rate limiting

---

## 總結

### 技術決策總結

| 決策 | 理由 | 適用情境 |
|------|------|----------|
| **Vanilla JavaScript** | 零依賴、快速、簡單 | 小型專案、原型 |
| **單一 HTML 檔案** | 部署簡單 | 靜態網站 |
| **需要 HTTP Server** | CORS、安全性 | API 通訊 |
| **無框架** | 性能優先 | 載入速度要求高 |

### 未來考量

**保持現狀的條件**:
- 專案規模維持小型 (<1500 行)
- 功能不需大幅擴展
- 團隊熟悉 Vanilla JS

**升級的時機**:
- 需要元件重用 → 考慮 Alpine.js
- 需要複雜狀態 → 考慮 Vue.js
- 團隊擴大 → 考慮 React + TypeScript

---

## 相關文件

- [開發日誌 2025-11-09](./development_log_2025-11-09.md)
- [UI Scroll 優化](./ui_scroll_optimization.md)
- [Project README](../README.md)
- [Quick Start Guide](../documentation/quickstart.md)

---

**建立時間**: 2025-11-09
**作者**: Claude Code (SuperClaude Framework)
**版本**: v1.0
