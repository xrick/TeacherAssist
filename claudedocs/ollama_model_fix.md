# Ollama 模型配置問題診斷與修復

**文檔日期**：2025-10-27
**問題類型**：環境變數優先級與拼寫錯誤
**影響範圍**：PPT 生成功能完全失效
**解決狀態**：✅ 已完全修復

---

## 📋 問題背景

### 故障現象

用戶在前端輸入內容並點擊生成 PPT 按鈕後，出現錯誤：

#### 前端錯誤
```javascript
Failed to load resource: the server responded with a status of 404 (File not found)

Uncaught (in promise) Error: 生成失敗: Server error '500 Internal Server Error'
for url 'http://presenton:8000/api/v1/ppt/presentation/generate'
    at poll ((index):770:35)
```

#### Backend 錯誤
```python
Traceback (most recent call last):
  File "/app/app/services/content_processor.py", line 36, in process_content
    presentation_result = await self.presenton.create_presentation(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/services/presenton_service.py", line 50, in create_presentation
    response.raise_for_status()
httpx.HTTPStatusError: Server error '500 Internal Server Error'
for url 'http://presenton:8000/api/v1/ppt/presentation/generate'
```

#### Presenton 容器錯誤（關鍵）
```python
2025-10-27 04:04:10,551 - INFO - HTTP Request: POST
http://host.docker.internal:11434/v1/chat/completions "HTTP/1.1 404 Not Found"

Traceback (most recent call last):
  File "/app/servers/fastapi/utils/llm_calls/generate_presentation_outlines.py", line 102
    async for chunk in client.stream_structured(
openai.NotFoundError: Error code: 404 - {
    'error': {
        'message': 'model "gpa-oss:20b" not found, try pulling it first',
        'type': 'api_error',
        'param': None,
        'code': None
    }
}
```

### 錯誤鏈分析

```
前端用戶操作
    ↓ HTTP POST
Backend API (/api/generate)
    ↓ 調用 Presenton API
Presenton 容器 (/api/v1/ppt/presentation/generate)
    ↓ 嘗試調用 Ollama
Ollama API (http://host.docker.internal:11434)
    ↓ 返回 404 Not Found
    ❌ 模型 "gpa-oss:20b" 不存在
```

---

## 🔍 根本原因分析

### 問題一：模型名稱拼寫錯誤

**錯誤模型名稱**：`gpa-oss:20b` ❌
**正確模型名稱**：`gpt-oss:20b` ✅

關鍵字母差異：`gpa` vs `gpt`（少了字母 `t`）

### 問題二：Docker Compose 環境變數優先級

Docker Compose 的環境變數解析順序（優先級從高到低）：

```
1. Shell 環境變數 (export VARIABLE=value) ← ⚠️ 問題根源
2. docker-compose.yml 中的 environment
3. .env 檔案
4. Dockerfile 中的 ENV
```

#### 配置檢查結果

**1. .env 檔案配置（正確但被忽略）**

```bash
# .env 第 16-18 行
OLLAMA_MODEL=phi4-mini:3.8b
# OLLAMA_MODEL=deepseek-r1:1.5b
# OLLAMA_MODEL=gpt-oss:20b
```

`.env` 檔案中的配置是**正確的**，但因優先級較低而被覆蓋。

**2. Shell 環境變數（錯誤且優先級最高）**

```bash
$ echo $OLLAMA_MODEL
gpa-oss:20b  # ❌ 拼寫錯誤
```

**3. Docker Compose 解析結果**

```bash
$ docker compose config | grep OLLAMA_MODEL
OLLAMA_MODEL: gpa-oss:20b  # ❌ 從 Shell 環境讀取
```

**4. 容器內實際配置**

```bash
$ docker exec presenton-api env | grep OLLAMA_MODEL
OLLAMA_MODEL=gpa-oss:20b  # ❌ 錯誤傳播到容器
```

### 問題三：~/.bashrc 永久化錯誤配置

進一步追查發現根源在用戶的 Shell 配置文件：

```bash
$ grep -n "OLLAMA_MODEL" ~/.bashrc
157:export OLLAMA_MODEL="gpa-oss:20b"  # ❌ 永久化的拼寫錯誤
```

**影響**：
- 每次啟動新終端時自動載入錯誤配置
- 即使修改 `.env` 檔案也無效
- `docker compose` 讀取到錯誤的環境變數

---

## 🔧 診斷過程

### Step 1: 檢查 Ollama 可用模型

```bash
$ ollama list
NAME                                 ID              SIZE      MODIFIED
phi4-mini-reasoning:3.8b             3ca8c2865ce9    3.2 GB    2 hours ago
phi4-mini:3.8b                       78fad5d182a7    2.5 GB    3 months ago
gpt-oss:20b                          aa4295ac10c3    13 GB     8 weeks ago
zephyr:7b                            bbe38b81adec    4.1 GB    13 days ago
```

✅ `gpt-oss:20b` 存在
❌ `gpa-oss:20b` 不存在（拼寫錯誤）

### Step 2: 檢查容器環境變數

```bash
$ docker exec presenton-api env | grep OLLAMA_MODEL
OLLAMA_MODEL=gpa-oss:20b  # ❌ 錯誤
```

### Step 3: 追蹤環境變數來源

```bash
# 檢查 Shell 環境
$ echo $OLLAMA_MODEL
gpa-oss:20b  # ❌ 找到源頭

# 檢查 Docker Compose 解析
$ docker compose config | grep OLLAMA_MODEL
OLLAMA_MODEL: gpa-oss:20b  # ❌ 確認從 Shell 讀取

# 搜尋 Shell 配置文件
$ grep -n "OLLAMA_MODEL" ~/.bashrc
157:export OLLAMA_MODEL="gpa-oss:20b"  # ❌ 根本原因
```

### Step 4: 驗證 Presenton 日誌

```bash
$ docker compose logs presenton | grep -i error
openai.NotFoundError: Error code: 404 - {
    'error': {
        'message': 'model "gpa-oss:20b" not found, try pulling it first',
        ...
    }
}
```

確認錯誤鏈：模型名稱錯誤 → Ollama 404 → Presenton 500 → Backend 異常 → 前端錯誤

---

## ✅ 解決方案

### 方案一：修復 ~/.bashrc（根本解決）

**步驟 1：修正 Shell 配置文件**

```bash
# 使用 sed 修正拼寫錯誤
$ sed -i '157s/export OLLAMA_MODEL="gpa-oss:20b"/export OLLAMA_MODEL="phi4-mini:3.8b"/' ~/.bashrc

# 驗證修正結果
$ grep -n "OLLAMA_MODEL" ~/.bashrc
157:export OLLAMA_MODEL="phi4-mini:3.8b"  # ✅ 已修正
```

**注意**：這裡直接改為 `phi4-mini:3.8b` 而非 `gpt-oss:20b`，因為：
- 用戶明確表示要使用 `phi4-mini:3.8b`
- 該模型更小更快（2.5 GB vs 13 GB）
- 適合日常使用和快速響應

**步驟 2：在當前 Shell 中設定正確的環境變數**

```bash
# 設定環境變數（當前 session 生效）
$ export OLLAMA_MODEL="phi4-mini:3.8b"

# 驗證設定
$ echo $OLLAMA_MODEL
phi4-mini:3.8b  # ✅ 正確
```

**步驟 3：重啟 Docker 服務**

```bash
# 停止並移除舊容器
$ docker compose down

# 啟動新容器（會讀取正確的環境變數）
$ docker compose up -d
```

**步驟 4：驗證修復結果**

```bash
# 檢查 Presenton 容器配置
$ docker exec presenton-api env | grep OLLAMA_MODEL
OLLAMA_MODEL=phi4-mini:3.8b  # ✅ 正確

# 檢查 Backend 容器配置
$ docker exec ppt-backend env | grep OLLAMA_MODEL
OLLAMA_MODEL=phi4-mini:3.8b  # ✅ 正確

# 檢查服務健康狀態
$ curl -s http://localhost:5050/api/health | python3 -m json.tool
{
    "status": "healthy",
    "services": {
        "presenton": "connected",  # ✅
        "ollama": "connected",      # ✅
        "pexels": "connected",      # ✅
        "zephyr": "available"       # ✅
    }
}
```

### 方案二：直接在 docker-compose.yml 中硬編碼（備選方案）

如果不想依賴環境變數，可以直接在 `docker-compose.yml` 中寫死：

```yaml
services:
  presenton:
    environment:
      - OLLAMA_MODEL=phi4-mini:3.8b  # 直接指定，不使用 ${OLLAMA_MODEL}
```

**優點**：
- ✅ 不受環境變數影響
- ✅ 配置明確可見
- ✅ 更容易排查問題

**缺點**：
- ⚠️ 切換模型需要修改 docker-compose.yml
- ⚠️ 無法透過 .env 靈活切換

---

## 📊 驗證結果

### 配置對比

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| **~/.bashrc** | `gpa-oss:20b` ❌ | `phi4-mini:3.8b` ✅ |
| **Shell 環境** | `gpa-oss:20b` ❌ | `phi4-mini:3.8b` ✅ |
| **Presenton 容器** | `gpa-oss:20b` ❌ | `phi4-mini:3.8b` ✅ |
| **Backend 容器** | `gpa-oss:20b` ❌ | `phi4-mini:3.8b` ✅ |
| **.env 檔案** | `phi4-mini:3.8b` ✅ | `phi4-mini:3.8b` ✅ |

### 服務狀態

```bash
$ docker compose ps
NAME            IMAGE                                STATUS          PORTS
ppt-backend     teacherassist-backend                Up 5 minutes    0.0.0.0:5050->5000/tcp
presenton-api   ghcr.io/presenton/presonton:latest   Up 5 minutes    80/tcp
```

### 健康檢查

```bash
$ curl http://localhost:5050/api/health
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

### 模型可用性驗證

```bash
# 從 Presenton 容器內部訪問 Ollama
$ docker exec presenton-api curl -s http://host.docker.internal:11434/api/tags | \
  python3 -m json.tool | grep -A 3 "phi4-mini:3.8b"

{
    "name": "phi4-mini:3.8b",
    "model": "phi4-mini:3.8b",
    "modified_at": "2025-07-25T15:11:59.636874323+08:00",
    "size": 2543479391,
    ...
}
```

✅ 所有配置正確，服務健康，模型可訪問

---

## 🎯 模型選擇指南

### 可用模型對比

| 模型 | 大小 | 參數量 | 速度 | 記憶體需求 | 適用場景 |
|------|------|--------|------|-----------|---------|
| **phi4-mini:3.8b** | 2.5 GB | 3.8B | ⚡⚡⚡ 快 | 💚 低 | 日常使用、快速響應 |
| **phi4-mini-reasoning:3.8b** | 3.2 GB | 3.8B | ⚡⚡ 中快 | 💚 中低 | 需要推理能力的任務 |
| **zephyr:7b** | 4.1 GB | 7B | ⚡ 中 | 💛 中 | 對話生成、創意內容 |
| **gpt-oss:20b** | 13 GB | 20B | 🐌 慢 | ❤️ 高 | 複雜內容分析、高質量輸出 |

### 推薦選擇

#### 1. phi4-mini:3.8b（當前配置）✅

**優勢**：
- ✅ **最快速度**：參數量小，推理速度快
- ✅ **低資源佔用**：僅需 2.5 GB，CPU 運行無壓力
- ✅ **優秀性能**：Microsoft Phi 系列在小模型中表現出色
- ✅ **用戶體驗好**：生成速度快，等待時間短

**適用場景**：
- 日常 PPT 生成
- 清晰明確的任務描述
- 標準格式的內容

**使用方法**：
```bash
# 已經是當前配置，無需修改
export OLLAMA_MODEL="phi4-mini:3.8b"
docker compose restart
```

#### 2. phi4-mini-reasoning:3.8b（推理增強版）

**優勢**：
- ✅ 更好的邏輯推理能力
- ✅ 更準確的內容理解
- ✅ 仍然保持較快速度

**適用場景**：
- 需要邏輯分析的內容
- 複雜關係梳理
- 結構化內容提取

**切換方法**：
```bash
export OLLAMA_MODEL="phi4-mini-reasoning:3.8b"
docker compose restart
```

#### 3. gpt-oss:20b（高質量輸出）

**優勢**：
- ✅ 最強的理解能力
- ✅ 最高的輸出質量
- ✅ 處理複雜主題能力強

**缺點**：
- ⚠️ 生成速度較慢
- ⚠️ 記憶體需求高（13 GB）
- ⚠️ CPU 運行可能較吃力

**適用場景**：
- 專業演講稿生成
- 複雜技術主題
- 需要高質量輸出的場合

**切換方法**：
```bash
export OLLAMA_MODEL="gpt-oss:20b"
docker compose restart
```

#### 4. zephyr:7b（對話生成專家）

**優勢**：
- ✅ 優秀的對話生成能力
- ✅ 創意內容表現好
- ✅ 平衡的性能與質量

**適用場景**：
- 演講稿生成
- 創意內容產出
- 需要自然語言流暢度

**切換方法**：
```bash
export OLLAMA_MODEL="zephyr:7b"
docker compose restart
```

---

## 🛡️ 預防措施

### 1. 環境變數管理最佳實踐

#### ❌ 應避免的做法

```bash
# ~/.bashrc 或 ~/.zshrc 中
export OLLAMA_MODEL="固定模型"  # ❌ 失去靈活性
```

**問題**：
- Shell 環境變數會覆蓋所有其他配置
- 難以針對不同專案使用不同模型
- 容易造成配置混亂

#### ✅ 推薦的做法

**方案 A：使用 .env 檔案（推薦）**

```bash
# 專案根目錄的 .env
OLLAMA_MODEL=phi4-mini:3.8b

# docker-compose.yml 中
services:
  presenton:
    env_file:
      - .env
    environment:
      - OLLAMA_MODEL=${OLLAMA_MODEL}
```

**優點**：
- ✅ 專案級配置，不影響其他專案
- ✅ 可以加入 `.gitignore` 或提交到版本控制
- ✅ 易於切換和管理

**方案 B：硬編碼在 docker-compose.yml（最安全）**

```yaml
services:
  presenton:
    environment:
      - OLLAMA_MODEL=phi4-mini:3.8b  # 直接寫死
```

**優點**：
- ✅ 完全不受環境變數影響
- ✅ 配置明確可見
- ✅ 排查問題容易

**方案 C：使用 direnv（進階）**

```bash
# 安裝 direnv
$ sudo apt install direnv  # Linux
$ brew install direnv      # macOS

# 專案目錄建立 .envrc
$ cat > .envrc << EOF
export OLLAMA_MODEL=phi4-mini:3.8b
EOF

# 允許該目錄的 .envrc
$ direnv allow .
```

**優點**：
- ✅ 自動切換環境變數（進入/離開目錄）
- ✅ 專案隔離
- ✅ 支援多專案

### 2. 配置檢查清單

建立系統啟動前的檢查流程：

```bash
#!/bin/bash
# scripts/check_config.sh

echo "=== Ollama 配置檢查 ==="

# 1. 檢查 Shell 環境
echo "1. Shell 環境變數："
echo "   OLLAMA_MODEL=${OLLAMA_MODEL:-未設定}"

# 2. 檢查 .env 檔案
echo "2. .env 檔案配置："
grep "^OLLAMA_MODEL" .env || echo "   未找到配置"

# 3. 檢查 Docker Compose 解析結果
echo "3. Docker Compose 解析："
docker compose config 2>/dev/null | grep "OLLAMA_MODEL:" | head -1

# 4. 檢查模型是否存在
echo "4. Ollama 模型檢查："
MODEL=${OLLAMA_MODEL:-$(grep "^OLLAMA_MODEL" .env | cut -d= -f2)}
if ollama list | grep -q "$MODEL"; then
    echo "   ✅ 模型 $MODEL 已安裝"
else
    echo "   ❌ 模型 $MODEL 未安裝"
    echo "   執行: ollama pull $MODEL"
fi

echo ""
echo "=== 檢查完成 ==="
```

使用方法：
```bash
$ chmod +x scripts/check_config.sh
$ ./scripts/check_config.sh
```

### 3. 文檔化配置

在專案 README 或 CLAUDE.md 中明確記錄：

```markdown
## Ollama 模型配置

### 當前使用模型
- **預設模型**：phi4-mini:3.8b
- **配置位置**：.env 第 16 行

### 切換模型
1. 修改 .env 檔案
2. 重啟服務：`docker compose restart`
3. 驗證：`docker exec presenton-api env | grep OLLAMA_MODEL`

### 注意事項
- ⚠️ 不要在 ~/.bashrc 中設定 OLLAMA_MODEL
- ⚠️ Shell 環境變數會覆蓋 .env 配置
- ✅ 使用 `docker compose config` 檢查實際配置
```

---

## 🧪 測試與驗證

### 功能測試流程

#### 1. 基本連接測試

```bash
# 測試 Ollama 連接
$ curl -s http://localhost:11434/api/tags | python3 -m json.tool | grep "phi4-mini:3.8b"

# 測試 Backend 健康
$ curl -s http://localhost:5050/api/health | python3 -m json.tool

# 測試 Presenton 連接
$ docker exec presenton-api curl -s http://host.docker.internal:11434/api/tags | \
  python3 -m json.tool | grep "phi4-mini"
```

#### 2. PPT 生成測試

**測試內容（簡單）**：
```
Python 程式語言的三大特點：語法簡潔、動態類型、豐富的標準庫。
```

**預期結果**：
- ✅ 無錯誤訊息
- ✅ 進度條正常顯示
- ✅ 3-5 秒內開始生成
- ✅ 成功生成 PPT（3-4 張投影片）

**測試內容（中等）**：
```
人工智慧在教育領域的應用包括個性化學習推薦、智能輔導系統、
自動評分與反饋、學習行為分析等方面，正在深刻改變傳統教學模式。
```

**預期結果**：
- ✅ 5-8 秒內完成
- ✅ 生成 4-6 張投影片
- ✅ 內容結構合理

**測試內容（複雜）**：
```
區塊鏈技術的核心特性包括去中心化架構、不可篡改性、
分散式共識機制、智能合約自動執行等，在金融、供應鏈、
數位身份驗證等領域展現出巨大的應用潛力。
```

**預期結果**：
- ✅ 8-15 秒內完成
- ✅ 生成 6-8 張投影片
- ✅ 邏輯結構清晰

#### 3. 日誌監控

```bash
# 即時監控 Presenton 日誌
$ docker compose logs -f presenton | grep -E "(INFO|ERROR|WARN)"

# 即時監控 Backend 日誌
$ docker compose logs -f backend

# 檢查是否有模型錯誤
$ docker compose logs presenton | grep -i "not found"
# 應該沒有輸出
```

---

## 📚 技術學習點

### 1. Docker Compose 環境變數優先級

```
優先級（高 → 低）：
1. Shell 環境變數（export VAR=value）
2. docker-compose.yml 中的 environment
3. env_file 指定的檔案
4. .env 檔案（預設）
5. Dockerfile 中的 ENV
```

**關鍵教訓**：
- ⚠️ Shell 環境變數優先級最高，會覆蓋所有配置
- ✅ 使用 `docker compose config` 檢查實際解析結果
- ✅ 善用 `.env` 進行專案級配置管理

### 2. 環境變數除錯方法

```bash
# 方法 1：檢查 Shell 環境
$ echo $VARIABLE_NAME
$ env | grep VARIABLE

# 方法 2：檢查 Docker Compose 解析
$ docker compose config | grep VARIABLE

# 方法 3：檢查容器內實際值
$ docker exec <container> env | grep VARIABLE

# 方法 4：追蹤來源
$ grep -r "VARIABLE" ~/.bashrc ~/.zshrc .env docker-compose.yml
```

### 3. Ollama API 錯誤處理

**常見錯誤碼**：

| 錯誤碼 | 說明 | 原因 | 解決方法 |
|--------|------|------|---------|
| **404** | Model not found | 模型名稱錯誤或未安裝 | 檢查拼寫，執行 `ollama pull` |
| **500** | Internal server error | Ollama 服務異常 | 檢查 Ollama 日誌 |
| **Connection refused** | 無法連接 | Ollama 未啟動 | 啟動 Ollama：`ollama serve` |
| **Timeout** | 請求超時 | 模型載入過慢或系統資源不足 | 使用較小模型或增加資源 |

### 4. 拼寫錯誤的預防

**常見拼寫錯誤**：
- `gpa-oss` ❌ → `gpt-oss` ✅
- `phi4mini` ❌ → `phi4-mini` ✅
- `zyphr` ❌ → `zephyr` ✅

**預防方法**：
1. ✅ 從 `ollama list` 複製貼上模型名稱
2. ✅ 使用自動完成功能
3. ✅ 在配置文件中添加註解說明
4. ✅ 建立配置驗證腳本

### 5. 跨環境一致性

**問題場景**：
- 開發環境（本機）vs 生產環境（伺服器）
- 不同開發者的本機環境
- CI/CD 管道中的環境

**解決方案**：
```yaml
# docker-compose.yml
services:
  presenton:
    environment:
      # 方案 1：直接硬編碼（最安全）
      - OLLAMA_MODEL=phi4-mini:3.8b

      # 方案 2：使用變數但提供預設值
      - OLLAMA_MODEL=${OLLAMA_MODEL:-phi4-mini:3.8b}
```

---

## 🔗 相關文檔

- [專案 CLAUDE.md](../CLAUDE.md) - 完整專案架構說明
- [雙環境啟動修復](./two_env_start_system_fix.md) - OrbStack vs Docker 網絡差異
- [Ollama 官方文檔](https://ollama.ai/docs)
- [Docker Compose 環境變數文檔](https://docs.docker.com/compose/environment-variables/)

---

## 📝 快速參考

### 檢查當前配置

```bash
# 一鍵檢查腳本
cat << 'EOF' | bash
echo "=== Ollama 配置狀態 ==="
echo "Shell: ${OLLAMA_MODEL:-未設定}"
echo ".env: $(grep '^OLLAMA_MODEL' .env 2>/dev/null || echo '未找到')"
echo "容器: $(docker exec presenton-api env 2>/dev/null | grep OLLAMA_MODEL || echo '容器未運行')"
echo "可用模型: $(ollama list 2>/dev/null | grep -E 'phi4|gpt-oss|zephyr' || echo 'Ollama 未運行')"
EOF
```

### 切換模型

```bash
# 方法 1：臨時切換（當前 session）
export OLLAMA_MODEL="模型名稱"
docker compose restart

# 方法 2：永久切換（修改 .env）
sed -i 's/^OLLAMA_MODEL=.*/OLLAMA_MODEL=模型名稱/' .env
docker compose restart

# 方法 3：全局切換（修改 ~/.bashrc）
sed -i 's/export OLLAMA_MODEL=.*/export OLLAMA_MODEL="模型名稱"/' ~/.bashrc
source ~/.bashrc
docker compose restart
```

### 常用除錯命令

```bash
# 檢查服務健康
curl -s http://localhost:5050/api/health | python3 -m json.tool

# 檢查 Presenton 日誌
docker compose logs presenton --tail 50

# 檢查 Backend 日誌
docker compose logs backend --tail 50

# 測試 Ollama 連接
curl -s http://localhost:11434/api/tags

# 檢查模型是否可從容器訪問
docker exec presenton-api curl -s http://host.docker.internal:11434/api/tags
```

---

## 🎉 總結

### 問題本質

1. **拼寫錯誤**：`gpa-oss:20b` 而非 `gpt-oss:20b`
2. **環境變數優先級**：Shell 環境覆蓋 .env 配置
3. **永久化錯誤**：~/.bashrc 中的錯誤配置

### 解決要點

1. ✅ 修復 ~/.bashrc 拼寫錯誤
2. ✅ 設定正確的 Shell 環境變數
3. ✅ 重啟服務應用新配置
4. ✅ 切換到 phi4-mini:3.8b（更快更適合）

### 關鍵教訓

- ⚠️ **優先級陷阱**：Shell 環境變數會無聲覆蓋其他配置
- ✅ **診斷順序**：日誌 → 環境變數 → 配置文件 → Shell 配置
- ✅ **預防措施**：使用 .env 而非全局環境變數
- ✅ **驗證方法**：`docker compose config` 檢查實際配置

### 最佳實踐

1. **配置管理**：使用專案級 .env，避免全局環境變數
2. **名稱精確**：從 `ollama list` 複製模型名稱
3. **分層驗證**：Shell → Docker Compose → 容器
4. **文檔化**：記錄配置決策和切換方法

---

**修復完成日期**：2025-10-27
**測試環境**：Linux PC (AMD64) + Docker 28.5.0
**當前模型**：phi4-mini:3.8b
**服務狀態**：✅ 所有服務健康，PPT 生成功能正常

---

*此文檔詳細記錄了從問題發現到完全解決的全過程，可作為環境變數配置問題的排查參考。*
