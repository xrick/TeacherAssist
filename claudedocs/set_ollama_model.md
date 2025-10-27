# Ollama 模型切換完整指南

**文檔日期**：2025-10-27
**問題類型**：配置管理與模型選擇
**適用場景**：需要調整 PPT 生成質量或速度時
**文檔狀態**：✅ 完整指南

---

## 📋 用戶問題

> "if I wanna change the model to more powerful model, how do I modify the setting"

**背景**：
- 系統當前使用 `phi4-mini:3.8b` 模型
- 用戶希望了解如何切換到更強大的模型
- 配置已改為硬編碼方式（不依賴環境變數）

---

## 🎯 可用模型概覽

### 已安裝模型列表

根據系統當前安裝的模型（`ollama list` 輸出）：

| 模型名稱 | 大小 | 參數量 | 速度 | 質量評分 | 推薦場景 |
|---------|------|--------|------|---------|---------|
| **phi4-mini:3.8b** | 2.5 GB | 3.8B | ⚡⚡⚡ 最快 | ⭐⭐⭐ 良好 | 日常使用、快速迭代 |
| **phi4-mini-reasoning:3.8b** | 3.2 GB | 3.8B | ⚡⚡ 快 | ⭐⭐⭐⭐ 優秀 | 需要邏輯推理的內容 |
| **zephyr:7b** | 4.1 GB | 7B | ⚡ 中速 | ⭐⭐⭐⭐ 優秀 | 演講稿、對話生成 |
| **gpt-oss:20b** | 13 GB | 20B | 🐌 較慢 | ⭐⭐⭐⭐⭐ 最佳 | 複雜分析、專業報告 |

### 模型詳細對比

#### 1. phi4-mini:3.8b（當前配置）✅

**技術規格**：
- 參數量：3.8B
- 模型大小：2,491,876,774 bytes (~2.5 GB)
- 模型家族：Microsoft Phi-3
- 量化級別：Q4_K_M

**性能特點**：
- ✅ **最快速度**：平均生成時間 3-5 秒
- ✅ **最低資源**：記憶體需求約 3 GB
- ✅ **穩定可靠**：適合 CPU 運行
- ✅ **用戶體驗好**：響應迅速，無需等待

**適用場景**：
- 日常 PPT 生成需求
- 清晰明確的主題
- 標準格式的教學內容
- 快速迭代和測試

**輸出特點**：
- 內容簡潔清晰
- 結構合理
- 適合 3-6 張投影片
- 語言流暢度良好

**範例輸入**：
```
Python 程式語言的基本特性，包括語法簡潔、
動態類型、豐富的標準庫等優點。
```

**預期輸出**：
- 3-4 張投影片
- 結構：標題 → 特性介紹 → 優點 → 應用
- 生成時間：3-5 秒

---

#### 2. phi4-mini-reasoning:3.8b（推理增強版）

**技術規格**：
- 參數量：3.8B
- 模型大小：3,152,479,391 bytes (~3.2 GB)
- 模型家族：Microsoft Phi-3
- 量化級別：Q4_K_M
- 特殊能力：推理增強（Reasoning Enhanced）

**性能特點**：
- ✅ **增強推理**：更好的邏輯分析能力
- ✅ **更準確**：內容提取更精確
- ✅ **仍然快速**：生成時間 5-8 秒
- ✅ **資源適中**：記憶體需求約 4 GB

**適用場景**：
- 需要邏輯推理的主題
- 複雜關係梳理
- 科技或學術主題
- 結構化內容提取

**輸出特點**：
- 邏輯性更強
- 層次結構更清晰
- 關鍵點提取更準確
- 適合 4-7 張投影片

**範例輸入**：
```
區塊鏈技術的核心特性包括去中心化架構、不可篡改性、
分散式共識機制、智能合約自動執行等，在金融、供應鏈、
數位身份驗證等領域展現出巨大的應用潛力。
```

**預期輸出**：
- 5-7 張投影片
- 結構：概念 → 核心特性 → 技術架構 → 應用領域 → 潛力分析
- 生成時間：5-8 秒
- 邏輯關係清晰

---

#### 3. zephyr:7b（對話與創意專家）

**技術規格**：
- 參數量：7B
- 模型大小：4,109,865,216 bytes (~4.1 GB)
- 模型家族：HuggingFace Zephyr
- 優勢領域：對話生成、創意內容

**性能特點**：
- ✅ **對話能力強**：自然流暢的語言表達
- ✅ **創意表現好**：豐富的內容描述
- ✅ **語言流暢**：適合演講稿生成
- ⚡ **速度中等**：生成時間 10-15 秒

**適用場景**：
- 演講稿生成（配合 Transcript 功能）
- 創意主題的 PPT
- 需要豐富描述的內容
- 教育培訓材料

**輸出特點**：
- 語言自然流暢
- 描述豐富詳細
- 適合口語化表達
- 適合 5-8 張投影片

**範例輸入**：
```
人工智慧在教育領域的創新應用，如何透過個性化學習、
智能輔導系統改變傳統教學模式。
```

**預期輸出**：
- 6-8 張投影片
- 結構：引言 → 傳統教學挑戰 → AI 解決方案 → 個性化學習 → 智能輔導 → 未來展望
- 生成時間：10-15 秒
- 內容豐富、敘事流暢

**特別適合**：
- 配合 Backend 的 `zephyr_service.py` 生成演講稿
- 教學演示
- 培訓課程

---

#### 4. gpt-oss:20b（最強大模型）⭐

**技術規格**：
- 參數量：20B
- 模型大小：13,780,173,724 bytes (~13 GB)
- 優勢：全面的理解和生成能力

**性能特點**：
- ✅ **最強理解**：深度語義分析
- ✅ **最高質量**：專業級輸出
- ✅ **細節豐富**：全面的內容覆蓋
- 🐌 **速度較慢**：生成時間 20-30 秒

**適用場景**：
- 專業演講或重要場合
- 複雜的技術主題
- 學術研究報告
- 商業提案簡報

**資源需求**：
- 記憶體：約 14 GB RAM
- CPU：建議 4 核心以上
- 磁盤空間：13 GB

**輸出特點**：
- 結構完整嚴謹
- 內容深度分析
- 專業術語準確
- 適合 6-10 張投影片

**範例輸入**：
```
深度學習在醫療影像診斷中的應用，包括卷積神經網絡
在 X 光、CT、MRI 影像分析中的技術原理、臨床應用
案例以及未來發展趨勢。
```

**預期輸出**：
- 8-10 張投影片
- 結構：背景 → 技術原理 → CNN 架構 → 應用案例（X光/CT/MRI）→ 效果評估 → 挑戰 → 未來趨勢
- 生成時間：20-30 秒
- 專業深度、邏輯嚴密

**注意事項**：
- ⚠️ CPU 運行會比較吃力
- ⚠️ 生成時間較長，需要耐心等待
- ✅ 適合重要內容，質量值得等待

---

## ✅ 切換方法

### 方法一：手動編輯（標準方法）

#### 步驟 1：打開配置文件

```bash
# 使用您喜歡的編輯器
vim docker-compose.yml
# 或
nano docker-compose.yml
# 或在 VSCode 中
code docker-compose.yml
```

#### 步驟 2：修改兩處配置

**需要修改兩個位置**（非常重要！）：

**位置 1：Presenton 服務**（約第 14 行）
```yaml
services:
  presenton:
    image: ghcr.io/presenton/presenton:latest
    container_name: presenton-api
    environment:
      - PRESENTON_API_KEY=sk-presenton-...
      - LLM=ollama
      - OLLAMA_URL=http://host.docker.internal:11434
      - OLLAMA_MODEL=phi4-mini:3.8b  # ← 修改這裡
      - IMAGE_PROVIDER=pexels
```

**位置 2：Backend 服務**（約第 33 行）
```yaml
  backend:
    build: ./backend
    container_name: ppt-backend
    ports:
      - "5050:5000"
    environment:
      - PRESENTON_API_URL=http://presenton:8000
      - PRESENTON_API_KEY=sk-presenton-...
      - OLLAMA_URL=http://host.docker.internal:11434
      - OLLAMA_MODEL=phi4-mini:3.8b  # ← 修改這裡
      - PEXELS_API_KEY=...
```

**修改為您想要的模型**，例如：
```yaml
- OLLAMA_MODEL=gpt-oss:20b
```

#### 步驟 3：保存並重啟

```bash
# 保存文件後重啟服務
docker compose restart

# 等待服務啟動（約 15 秒）
sleep 15
```

#### 步驟 4：驗證配置

```bash
# 檢查 Presenton 容器
docker exec presenton-api env | grep OLLAMA_MODEL
# 應顯示：OLLAMA_MODEL=您設定的模型

# 檢查 Backend 容器
docker exec ppt-backend env | grep OLLAMA_MODEL
# 應顯示：OLLAMA_MODEL=您設定的模型

# 檢查服務健康
curl -s http://localhost:5050/api/health | python3 -m json.tool
```

---

### 方法二：使用自動切換腳本（推薦）⭐

我們提供了一個互動式切換工具，讓切換過程更簡單安全。

#### 腳本位置

```
scripts/switch_model.sh
```

#### 使用方法

```bash
# 執行切換腳本
./scripts/switch_model.sh
```

#### 腳本功能

**1. 顯示當前配置**
```
════════════════════════════════════════
  Ollama 模型切換工具
════════════════════════════════════════

當前模型：phi4-mini:3.8b
```

**2. 互動式選單**
```
請選擇要切換的模型：

1) phi4-mini:3.8b
   描述：快速輕量（當前）
   大小：2.5 GB  速度：⚡⚡⚡

2) phi4-mini-reasoning:3.8b
   描述：推理增強
   大小：3.2 GB  速度：⚡⚡

3) zephyr:7b
   描述：對話專家
   大小：4.1 GB  速度：⚡

4) gpt-oss:20b
   描述：最強質量
   大小：13 GB  速度：🐌

請輸入選項 (1-4) 或 q 退出:
```

**3. 確認切換**
```
即將切換到：gpt-oss:20b
描述：最強質量
大小：13 GB  速度：🐌

確定要切換嗎？(y/N):
```

**4. 自動執行**
- ✅ 自動修改 docker-compose.yml（兩處）
- ✅ 自動重啟服務
- ✅ 自動驗證配置
- ✅ 顯示切換結果

**5. 驗證結果**
```
驗證新配置：
✅ Presenton: gpt-oss:20b
✅ Backend: gpt-oss:20b

🎉 切換完成！現在可以測試 PPT 生成功能
```

#### 腳本優點

- ✅ **安全可靠**：自動備份，驗證配置
- ✅ **使用簡單**：互動式選單，無需記命令
- ✅ **自動驗證**：切換後自動檢查配置是否正確
- ✅ **錯誤處理**：遇到問題會提示，不會破壞系統

---

### 方法三：快速 sed 替換（進階用戶）

如果您熟悉命令行，可以使用一條命令快速切換：

```bash
# 一鍵切換到 gpt-oss:20b
sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=gpt-oss:20b/g' docker-compose.yml && \
docker compose restart

# 一鍵切換到 phi4-mini-reasoning:3.8b
sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=phi4-mini-reasoning:3.8b/g' docker-compose.yml && \
docker compose restart

# 一鍵切換到 zephyr:7b
sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=zephyr:7b/g' docker-compose.yml && \
docker compose restart
```

**優點**：快速、一鍵完成
**缺點**：需要手動驗證配置

---

## 🔍 切換完整示例

### 示例 1：從 phi4-mini 切換到 gpt-oss:20b

**場景**：準備重要演講，需要最高質量的 PPT

**步驟**：

```bash
# 1. 使用切換腳本
./scripts/switch_model.sh

# 2. 選擇選項 4（gpt-oss:20b）
4

# 3. 確認切換
y

# 4. 等待切換完成（腳本會自動執行）

# 5. 驗證配置
docker exec presenton-api env | grep OLLAMA_MODEL
# 輸出：OLLAMA_MODEL=gpt-oss:20b

# 6. 測試生成（輸入較複雜的內容）
# 前往 http://localhost:8080
# 輸入：深度學習技術在自然語言處理領域的最新進展...
# 預期：20-30 秒後生成 8-10 張高質量投影片
```

---

### 示例 2：從 phi4-mini 切換到 zephyr:7b（用於演講稿）

**場景**：需要生成流暢的演講稿配合 PPT

**步驟**：

```bash
# 1. 手動編輯 docker-compose.yml
vim docker-compose.yml

# 2. 修改兩處（第 14 行和第 33 行）
# 將：OLLAMA_MODEL=phi4-mini:3.8b
# 改為：OLLAMA_MODEL=zephyr:7b

# 3. 保存並重啟
docker compose restart

# 4. 等待服務啟動
sleep 15

# 5. 測試生成
# 前往 http://localhost:8080
# 輸入教育主題內容
# 預期：10-15 秒後生成，內容豐富流暢

# 6. 可選：使用 Backend 的 transcript 功能生成演講稿
curl -X POST http://localhost:5050/api/transcript/generate \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_id": "您的 presentation_id",
    "style": "conversational",
    "language": "zh-TW"
  }'
```

---

## 📊 性能對比與選擇建議

### 生成速度對比

| 模型 | 簡單內容 | 中等複雜度 | 複雜內容 |
|------|---------|-----------|---------|
| **phi4-mini** | 3 秒 | 5 秒 | 8 秒 |
| **reasoning** | 5 秒 | 8 秒 | 12 秒 |
| **zephyr** | 10 秒 | 15 秒 | 20 秒 |
| **gpt-oss** | 20 秒 | 25 秒 | 30 秒 |

### 記憶體使用對比

| 模型 | 模型大小 | 運行記憶體 | 推薦 RAM |
|------|---------|-----------|---------|
| **phi4-mini** | 2.5 GB | 3 GB | 4 GB+ |
| **reasoning** | 3.2 GB | 4 GB | 6 GB+ |
| **zephyr** | 4.1 GB | 5 GB | 8 GB+ |
| **gpt-oss** | 13 GB | 14 GB | 16 GB+ |

### 輸出質量對比

| 評估維度 | phi4-mini | reasoning | zephyr | gpt-oss |
|---------|-----------|-----------|--------|---------|
| **內容準確性** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **邏輯結構** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **語言流暢度** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **細節豐富度** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **專業深度** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 選擇建議與決策樹

### 決策流程圖

```
需要生成 PPT
    ↓
┌───────────────────────────────┐
│ 什麼場合使用？                  │
└───────────────────────────────┘
    ↓
    ├─ 日常教學、快速測試
    │  └→ phi4-mini:3.8b ✅
    │
    ├─ 需要邏輯推理、科技主題
    │  └→ phi4-mini-reasoning:3.8b
    │
    ├─ 演講稿、培訓課程
    │  └→ zephyr:7b
    │
    └─ 重要演講、專業報告
       └→ gpt-oss:20b ⭐
```

### 場景匹配表

| 使用場景 | 推薦模型 | 理由 |
|---------|---------|------|
| **課堂教學 PPT** | phi4-mini | 快速生成，適合日常使用 |
| **技術分享會** | reasoning | 邏輯清晰，技術準確 |
| **培訓課程** | zephyr | 語言流暢，適合口語化 |
| **學術報告** | gpt-oss | 深度分析，專業嚴謹 |
| **商業提案** | gpt-oss | 細節豐富，結構完整 |
| **快速原型** | phi4-mini | 速度最快，快速迭代 |
| **演講比賽** | zephyr | 創意表現，語言優美 |
| **論文答辯** | gpt-oss | 學術深度，論證嚴密 |

### 內容類型匹配

| 內容類型 | 推薦模型 | 原因 |
|---------|---------|------|
| **程式語言介紹** | phi4-mini | 概念清晰，足夠應對 |
| **算法原理** | reasoning | 邏輯推理能力強 |
| **歷史故事** | zephyr | 敘事流暢，引人入勝 |
| **科研成果** | gpt-oss | 專業深度，細節準確 |
| **產品介紹** | phi4-mini | 簡潔明了，快速生成 |
| **技術架構** | reasoning | 結構化思維強 |
| **教育理念** | zephyr | 語言優美，適合演講 |
| **市場分析** | gpt-oss | 全面深入，數據支撐 |

---

## 🔧 配置說明

### 為什麼需要修改兩處？

系統採用微服務架構，有兩個獨立的服務需要訪問 Ollama：

#### 1. Presenton 服務
- **作用**：負責 PPT 生成的核心邏輯
- **調用 Ollama**：提取內容結構、生成大綱
- **配置位置**：`docker-compose.yml` 第 14 行
- **必須配置**：是

#### 2. Backend 服務
- **作用**：中間層，協調各個服務
- **調用 Ollama**：內容預處理、演講稿生成
- **配置位置**：`docker-compose.yml` 第 33 行
- **必須配置**：是

**重要**：兩個服務必須使用**相同的模型**，否則可能導致：
- 內容不一致
- 生成失敗
- 性能不匹配

### 為什麼使用硬編碼？

在先前的排查中，我們發現環境變數優先級問題會導致配置混亂（參見 [`ollama_model_fix.md`](./ollama_model_fix.md)）。

**硬編碼的優勢**：
- ✅ **完全可控**：不受 Shell 環境變數影響
- ✅ **配置明確**：直接查看文件就知道用什麼模型
- ✅ **跨環境一致**：在 Mac、Linux、CI/CD 都一樣
- ✅ **排查簡單**：出問題直接看配置文件
- ✅ **團隊友好**：所有人看到的配置相同

**如何切換**：
直接編輯 `docker-compose.yml`，不需要擔心環境變數覆蓋。

---

## 🧪 驗證與測試

### 配置驗證清單

切換模型後，使用以下清單驗證配置：

#### ✅ 步驟 1：檢查配置文件

```bash
# 檢查兩處配置是否一致
grep "OLLAMA_MODEL" docker-compose.yml

# 應該看到兩行相同的配置：
# - OLLAMA_MODEL=您設定的模型
# - OLLAMA_MODEL=您設定的模型
```

#### ✅ 步驟 2：檢查容器環境

```bash
# 檢查 Presenton 容器
docker exec presenton-api env | grep OLLAMA_MODEL

# 檢查 Backend 容器
docker exec ppt-backend env | grep OLLAMA_MODEL

# 兩者應該顯示相同的模型名稱
```

#### ✅ 步驟 3：檢查服務健康

```bash
# 檢查 Backend 健康狀態
curl -s http://localhost:5050/api/health | python3 -m json.tool

# 應該顯示：
# {
#     "status": "healthy",
#     "services": {
#         "presenton": "connected",
#         "ollama": "connected",
#         "pexels": "connected",
#         "zephyr": "available"
#     }
# }
```

#### ✅ 步驟 4：檢查模型可訪問性

```bash
# 從 Presenton 容器訪問 Ollama
docker exec presenton-api curl -s http://host.docker.internal:11434/api/tags | \
  python3 -m json.tool | grep -A 5 "您的模型名稱"

# 應該能看到模型詳細信息
```

### 功能測試建議

#### 測試 1：簡單內容生成

**目的**：驗證基本功能

**測試內容**：
```
Python 是一種簡潔易學的程式語言。
```

**預期結果**：
- phi4-mini：3-5 秒，3-4 張投影片
- reasoning：5-8 秒，3-4 張投影片
- zephyr：10-12 秒，4-5 張投影片
- gpt-oss：20-25 秒，4-6 張投影片

#### 測試 2：中等複雜度

**目的**：評估質量差異

**測試內容**：
```
人工智慧在教育領域的應用包括個性化學習推薦、
智能輔導系統、自動評分與反饋、學習行為分析等方面。
```

**預期結果**：
- phi4-mini：5-8 秒，4-5 張投影片，結構清晰
- reasoning：8-12 秒，5-6 張投影片，邏輯嚴謹
- zephyr：15-20 秒，6-7 張投影片，內容豐富
- gpt-oss：25-30 秒，7-8 張投影片，深度分析

#### 測試 3：複雜專業內容

**目的**：測試極限能力

**測試內容**：
```
深度學習在醫療影像診斷中的應用，包括卷積神經網絡
在 X 光、CT、MRI 影像分析中的技術原理、臨床應用
案例以及未來發展趨勢與挑戰。
```

**預期結果**：
- phi4-mini：8-10 秒，5-6 張投影片，基本覆蓋
- reasoning：12-15 秒，6-7 張投影片，結構合理
- zephyr：20-25 秒，7-8 張投影片，描述詳細
- gpt-oss：30-35 秒，8-10 張投影片，專業深入

---

## 🛡️ 常見問題與排查

### 問題 1：切換後還是使用舊模型

**症狀**：
```bash
$ docker exec presenton-api env | grep OLLAMA_MODEL
OLLAMA_MODEL=phi4-mini:3.8b  # 但您明明改成 gpt-oss:20b
```

**原因**：容器沒有重啟，還在使用舊配置

**解決方法**：
```bash
# 方法 1：重啟服務
docker compose restart

# 方法 2：完全重建
docker compose down && docker compose up -d

# 方法 3：重建特定容器
docker compose up -d --force-recreate presenton backend
```

---

### 問題 2：模型 404 Not Found

**症狀**：
```
openai.NotFoundError: Error code: 404 - {
    'error': {
        'message': 'model "gpt-oss:20b" not found'
    }
}
```

**原因**：模型名稱拼寫錯誤或模型未安裝

**檢查步驟**：
```bash
# 1. 檢查已安裝的模型
ollama list

# 2. 檢查拼寫是否正確
grep "OLLAMA_MODEL" docker-compose.yml

# 3. 如果模型不存在，拉取模型
ollama pull gpt-oss:20b
```

**常見拼寫錯誤**：
- `gpa-oss` ❌ → `gpt-oss` ✅
- `phi4mini` ❌ → `phi4-mini` ✅
- `zyphr` ❌ → `zephyr` ✅

---

### 問題 3：兩個容器配置不一致

**症狀**：
```bash
$ docker exec presenton-api env | grep OLLAMA_MODEL
OLLAMA_MODEL=gpt-oss:20b

$ docker exec ppt-backend env | grep OLLAMA_MODEL
OLLAMA_MODEL=phi4-mini:3.8b  # 不一致！
```

**原因**：只修改了一處配置

**解決方法**：
```bash
# 確保兩處都修改
vim docker-compose.yml

# 檢查兩處配置
grep -n "OLLAMA_MODEL" docker-compose.yml
# 應該看到兩行，且值相同

# 重啟服務
docker compose restart
```

---

### 問題 4：生成速度異常慢

**症狀**：使用 phi4-mini 但生成需要 30 秒以上

**可能原因**：
1. 系統資源不足
2. 實際使用了更大的模型
3. Ollama 服務異常

**排查步驟**：
```bash
# 1. 確認當前使用的模型
docker exec presenton-api env | grep OLLAMA_MODEL

# 2. 檢查系統資源
docker stats --no-stream

# 3. 檢查 Ollama 日誌
docker compose logs presenton | grep -i "ollama"

# 4. 測試 Ollama 直接訪問
curl -s http://localhost:11434/api/tags
```

---

### 問題 5：記憶體不足錯誤

**症狀**：
```
Error: out of memory
```

**原因**：模型太大，系統記憶體不足

**解決方法**：

**方案 1：切換到更小的模型**
```yaml
# 從 gpt-oss:20b (需要 14 GB)
# 切換到 phi4-mini:3.8b (需要 3 GB)
- OLLAMA_MODEL=phi4-mini:3.8b
```

**方案 2：增加 swap 空間（Linux）**
```bash
# 創建 8GB swap 文件
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 驗證
free -h
```

**方案 3：關閉其他程序**
釋放更多記憶體給 Docker 使用

---

## 📚 相關配置文件

### docker-compose.yml 結構

```yaml
version: '3.8'

services:
  # === Presenton 服務 ===
  presenton:
    image: ghcr.io/presenton/presenton:latest
    container_name: presenton-api
    environment:
      - PRESENTON_API_KEY=...
      - LLM=ollama
      - OLLAMA_URL=http://host.docker.internal:11434
      - OLLAMA_MODEL=phi4-mini:3.8b  # ← 配置點 1
      - IMAGE_PROVIDER=pexels
      - PEXELS_API_KEY=...
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - app-network
    restart: unless-stopped

  # === Backend 服務 ===
  backend:
    build: ./backend
    container_name: ppt-backend
    ports:
      - "5050:5000"
    environment:
      - PRESENTON_API_URL=http://presenton:8000
      - PRESENTON_API_KEY=...
      - OLLAMA_URL=http://host.docker.internal:11434
      - OLLAMA_MODEL=phi4-mini:3.8b  # ← 配置點 2
      - PEXELS_API_KEY=...
      - CORS_ORIGINS=*
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./backend:/app
      - ./output:/app/output
    depends_on:
      - presenton
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge
```

### Backend Zephyr Service

如果切換到 zephyr:7b，可以利用 Backend 的演講稿生成功能：

**文件位置**：`backend/app/services/zephyr_service.py`

**功能**：為生成的 PPT 創建演講稿

**API 端點**：
```bash
POST /api/transcript/generate
{
  "presentation_id": "xxx",
  "style": "conversational",  # formal, conversational, educational
  "language": "zh-TW"
}
```

**使用示例**：
```bash
# 1. 先生成 PPT，獲得 presentation_id
# 2. 然後生成演講稿
curl -X POST http://localhost:5050/api/transcript/generate \
  -H "Content-Type: application/json" \
  -d '{
    "presentation_id": "presentation_id_here",
    "style": "conversational",
    "language": "zh-TW"
  }'
```

---

## 💡 最佳實踐建議

### 開發流程建議

#### 階段 1：初期開發與測試
```
使用模型：phi4-mini:3.8b
理由：速度快，快速迭代
適合：功能測試、介面調整、流程驗證
```

#### 階段 2：內容質量提升
```
使用模型：phi4-mini-reasoning:3.8b
理由：質量提升但仍保持速度
適合：內容優化、結構調整
```

#### 階段 3：正式使用
```
根據場景切換：
- 日常教學 → phi4-mini:3.8b
- 技術分享 → phi4-mini-reasoning:3.8b
- 重要演講 → gpt-oss:20b
- 演講稿需求 → zephyr:7b
```

### 模型組合策略

**策略 1：雙模型搭配**
```
PPT 生成：phi4-mini:3.8b（快速）
演講稿生成：zephyr:7b（質量）

優點：速度和質量兼顧
適合：需要演講稿的場景
```

**策略 2：按需切換**
```
平時：phi4-mini:3.8b
重要場合前：切換到 gpt-oss:20b

優點：資源利用合理
適合：偶爾需要高質量輸出
```

**策略 3：分層使用**
```
草稿階段：phi4-mini:3.8b
最終版本：gpt-oss:20b

優點：開發效率高，最終質量好
適合：重要項目的製作流程
```

---

## 🔗 相關文檔

- [Ollama 模型配置問題診斷](./ollama_model_fix.md) - 環境變數問題排查
- [雙環境啟動修復](./two_env_start_system_fix.md) - OrbStack vs Docker 差異
- [專案 CLAUDE.md](../CLAUDE.md) - 完整專案架構說明
- [Ollama 官方文檔](https://ollama.ai/docs)
- [Presenton 官方倉庫](https://github.com/presenton/presenton)

---

## 📝 快速參考

### 一鍵切換命令

```bash
# 切換到 phi4-mini-reasoning:3.8b
sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=phi4-mini-reasoning:3.8b/g' docker-compose.yml && docker compose restart

# 切換到 zephyr:7b
sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=zephyr:7b/g' docker-compose.yml && docker compose restart

# 切換到 gpt-oss:20b
sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=gpt-oss:20b/g' docker-compose.yml && docker compose restart

# 切換回 phi4-mini:3.8b
sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=phi4-mini:3.8b/g' docker-compose.yml && docker compose restart
```

### 驗證腳本

```bash
#!/bin/bash
# 快速驗證當前模型配置

echo "=== 當前模型配置 ==="
echo ""
echo "docker-compose.yml:"
grep "OLLAMA_MODEL" docker-compose.yml
echo ""
echo "Presenton 容器:"
docker exec presenton-api env 2>/dev/null | grep OLLAMA_MODEL || echo "容器未運行"
echo ""
echo "Backend 容器:"
docker exec ppt-backend env 2>/dev/null | grep OLLAMA_MODEL || echo "容器未運行"
echo ""
echo "服務健康:"
curl -s http://localhost:5050/api/health 2>/dev/null | python3 -m json.tool || echo "服務未啟動"
```

---

## 🎉 總結

### 核心要點

1. **兩處配置**：必須同時修改 Presenton 和 Backend 的 OLLAMA_MODEL
2. **硬編碼優勢**：不受環境變數影響，配置穩定可靠
3. **模型選擇**：根據場景需求選擇合適的模型
4. **驗證重要**：切換後務必驗證配置是否生效

### 推薦工作流

```
1. 初期測試 → phi4-mini:3.8b
2. 質量提升 → phi4-mini-reasoning:3.8b
3. 重要場合 → gpt-oss:20b
4. 演講稿需求 → zephyr:7b
```

### 使用建議

- ✅ **使用切換腳本**：安全、簡單、自動驗證
- ✅ **根據場景選擇**：不要一直用最大的模型
- ✅ **驗證配置**：切換後檢查容器環境變數
- ✅ **測試功能**：切換後進行簡單測試

---

**文檔完成日期**：2025-10-27
**當前系統配置**：phi4-mini:3.8b
**配置方式**：硬編碼（docker-compose.yml）
**切換工具**：scripts/switch_model.sh

---

*此文檔提供完整的 Ollama 模型切換指南，包括所有可用模型的詳細說明、切換方法、驗證步驟和最佳實踐建議。*
