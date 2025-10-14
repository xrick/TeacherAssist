# Presenton 500 錯誤修復 - 缺少 LLM Provider 配置

**錯誤**: `Server error '500 Internal Server Error' for url 'http://presenton:8000/api/v1/ppt/presentation/generate'`
**日期**: 2025-10-14
**狀態**: ✅ 已修復

---

## 🔍 問題診斷

### 錯誤訊息

**Frontend**:
```
Uncaught (in promise) Error: 生成失敗: Server error '500 Internal Server Error'
```

**Presenton 日誌**:
```python
ValueError: None is not a valid LLMProvider

fastapi.exceptions.HTTPException: 500: Invalid LLM provider.
Please select one of: openai, google, anthropic, ollama, custom
```

### 根本原因

Presenton 容器**缺少 `LLM_PROVIDER` 環境變數**，導致無法初始化 LLM 提供者。

---

## 📊 技術分析

### Presenton LLM Provider 架構

Presenton 支援多種 LLM 提供者：
- `openai` - OpenAI GPT models
- `google` - Google Gemini models
- `anthropic` - Anthropic Claude models
- `ollama` - 本地 Ollama models (我們使用的)
- `custom` - 自定義 LLM endpoint

### 錯誤堆疊追蹤

```python
# Presenton 內部流程
presentation.py:generate_presentation_sync()
  ↓
generate_presentation_handler()
  ↓
generate_ppt_outline()
  ↓
get_model()  # ← 這裡失敗
  ↓
get_llm_provider()  # ← 讀取環境變數 LLM_PROVIDER
  ↓
ValueError: None is not a valid LLMProvider  # ← 環境變數未設置
```

### 環境變數檢查

**修復前**:
```bash
$ docker exec presenton-api env | grep LLM
# 無輸出 ❌

$ docker exec presenton-api env | grep OLLAMA
OLLAMA_URL=http://host.docker.internal:11434  # ✅ 有 URL 但沒 provider
```

**問題**: 有 `OLLAMA_URL` 但沒有 `LLM_PROVIDER=ollama`

---

## ✅ 修復方案

### 文件修改: docker-compose.yml

#### 修改前

```yaml
presenton:
  image: ghcr.io/presenton/presenton:latest
  container_name: presenton-api
  ports:
    - "8000:8000"
  environment:
    - PRESENTON_API_KEY=sk-presenton-...
    - OLLAMA_URL=http://host.docker.internal:11434  # ❌ 缺少 provider
    - IMAGE_PROVIDER=pexels
    - PEXELS_API_KEY=...
```

#### 修改後

```yaml
presenton:
  image: ghcr.io/presenton/presenton:latest
  container_name: presenton-api
  ports:
    - "8000:8000"
  environment:
    - PRESENTON_API_KEY=sk-presenton-...
    - LLM_PROVIDER=ollama  # ✅ 添加這行
    - OLLAMA_URL=http://host.docker.internal:11434
    - IMAGE_PROVIDER=pexels
    - PEXELS_API_KEY=...
```

**關鍵變更**: 添加 `LLM_PROVIDER=ollama`

---

## 🔄 應用修復

### 步驟 1: 修改 docker-compose.yml

```bash
nano docker-compose.yml
# 在 presenton 的 environment 區塊添加:
# - LLM_PROVIDER=ollama
```

### 步驟 2: 重啟服務

```bash
# 方法 1: 僅重啟 Presenton (可能不生效)
docker-compose restart presenton

# 方法 2: 完全重啟 (推薦)
docker-compose down
docker-compose up -d
```

### 步驟 3: 驗證環境變數

```bash
docker exec presenton-api env | grep -E "LLM_PROVIDER|OLLAMA"
```

**預期輸出**:
```
LLM_PROVIDER=ollama  # ✅
OLLAMA_URL=http://host.docker.internal:11434  # ✅
```

### 步驟 4: 檢查服務健康

```bash
curl http://localhost:5000/api/health
```

**預期輸出**:
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

---

## 🧪 功能測試

### 端到端測試

1. **訪問 Frontend**: http://localhost:8080

2. **輸入測試內容**:
   ```
   人工智慧技術正在改變我們的生活。
   機器學習讓電腦能夠從數據中學習。
   深度學習是機器學習的一個分支，使用神經網路模型。
   自然語言處理讓機器能夠理解和生成人類語言。
   計算機視覺讓機器能夠識別和理解圖像。
   AI 的應用領域包括醫療、教育、金融和交通。
   ```

3. **選擇模板**: 教學簡報

4. **點擊生成**

5. **觀察進度**:
   - 20% - 正在準備內容...
   - 40% - 正在發送給簡報生成引擎...
   - 60% - 正在生成簡報...
   - 100% - 簡報生成完成...

6. **驗證結果**:
   - ✅ 無 500 錯誤
   - ✅ 簡報成功生成
   - ✅ 可以下載 PPTX/PDF

---

## 📋 Presenton 環境變數完整清單

### 必需環境變數

| 變數 | 值 | 說明 |
|------|-----|------|
| **LLM_PROVIDER** | ollama | LLM 提供者 (必需) |
| **OLLAMA_URL** | http://host.docker.internal:11434 | Ollama API URL |
| **IMAGE_PROVIDER** | pexels | 圖片提供者 |
| **PEXELS_API_KEY** | your-api-key | Pexels API 金鑰 |
| **PRESENTON_API_KEY** | sk-presenton-... | Presenton API 金鑰 |

### 可選環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| OLLAMA_MODEL | llama2 | 預設使用的 Ollama 模型 |
| WEB_SEARCH | false | 是否啟用網路搜尋 |
| DEFAULT_LANGUAGE | English | 預設語言 |
| DEFAULT_TEMPLATE | general | 預設模板 |

---

## 🐛 故障排除

### 問題 1: 重啟後環境變數未生效

**症狀**:
```bash
$ docker-compose restart presenton
$ docker exec presenton-api env | grep LLM_PROVIDER
# 無輸出
```

**原因**: `restart` 不會重新讀取 docker-compose.yml

**解決**:
```bash
docker-compose down
docker-compose up -d
```

### 問題 2: 仍然收到 500 錯誤

**檢查清單**:

1. **驗證環境變數**:
   ```bash
   docker exec presenton-api env | grep LLM_PROVIDER
   ```

2. **檢查 Ollama 連接**:
   ```bash
   docker exec presenton-api curl http://host.docker.internal:11434/api/tags
   ```

3. **查看 Presenton 日誌**:
   ```bash
   docker-compose logs presenton | tail -50
   ```

4. **重新構建容器** (如果修改了 Dockerfile):
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

### 問題 3: Ollama 模型未找到

**症狀**:
```
Model 'llama2' not found
```

**解決**:
1. 檢查 Ollama 中可用的模型:
   ```bash
   ollama list
   ```

2. 如果需要，拉取模型:
   ```bash
   ollama pull llama2
   # 或使用我們的模型
   ollama pull gpt-oss:20b
   ```

3. 設置 OLLAMA_MODEL 環境變數 (可選):
   ```yaml
   environment:
     - LLM_PROVIDER=ollama
     - OLLAMA_URL=http://host.docker.internal:11434
     - OLLAMA_MODEL=gpt-oss:20b  # 指定模型
   ```

---

## 📚 相關問題和修復

### 之前的相關修復

1. **[404 錯誤](presenton_api_fix.md)** - API 端點路徑錯誤
2. **[422 錯誤](presenton_422_fix.md)** - 請求格式不符
3. **[Ollama Docker 連接](ollama_docker_fix.md)** - 網路隔離問題

### 完整錯誤鏈

```
Frontend Error → Backend 500 → Presenton Internal Error
                                      ↓
                            LLM Provider 未配置
```

---

## 💡 經驗教訓

### 1. 環境變數的完整性

❌ **錯誤做法**: 只配置 URL，忽略 provider 類型
```yaml
environment:
  - OLLAMA_URL=http://...  # 不完整
```

✅ **正確做法**: 同時配置 provider 和 URL
```yaml
environment:
  - LLM_PROVIDER=ollama  # 指定類型
  - OLLAMA_URL=http://...  # 指定位置
```

### 2. Docker Compose 重啟機制

- `docker-compose restart` - 重啟容器，不重新讀取 compose 文件
- `docker-compose down && up` - 完全重建，讀取最新配置

**最佳實踐**: 修改 docker-compose.yml 後使用 `down && up`

### 3. 第三方服務配置檢查

整合第三方服務時的檢查清單:
- [ ] 查看官方文檔的環境變數要求
- [ ] 檢查必需 vs 可選配置
- [ ] 驗證環境變數是否正確設置
- [ ] 查看日誌確認配置生效
- [ ] 測試基本功能

---

## ✅ 修復檢查清單

- [x] 識別 500 錯誤原因 (LLM Provider 未設置)
- [x] 在 docker-compose.yml 添加 LLM_PROVIDER=ollama
- [x] 完全重啟服務 (down && up)
- [x] 驗證環境變數正確設置
- [x] 確認 Presenton 可以訪問 Ollama
- [x] 測試簡報生成功能
- [x] 驗證下載功能
- [x] 創建文檔記錄修復過程

---

## 📖 快速參考

### 完整的 Presenton 配置範例

```yaml
presenton:
  image: ghcr.io/presenton/presenton:latest
  container_name: presenton-api
  ports:
    - "8000:8000"
  environment:
    # API 認證
    - PRESENTON_API_KEY=your-api-key

    # LLM 配置 (必需)
    - LLM_PROVIDER=ollama
    - OLLAMA_URL=http://host.docker.internal:11434
    - OLLAMA_MODEL=gpt-oss:20b  # 可選，指定模型

    # 圖片服務 (必需)
    - IMAGE_PROVIDER=pexels
    - PEXELS_API_KEY=your-pexels-key

    # 其他可選配置
    - WEB_SEARCH=false
    - DEFAULT_LANGUAGE=zh-TW
    - DEFAULT_TEMPLATE=educational

  extra_hosts:
    - "host.docker.internal:host-gateway"
  networks:
    - app-network
  restart: unless-stopped
```

### 驗證命令速查

```bash
# 檢查環境變數
docker exec presenton-api env | grep -E "LLM|OLLAMA|IMAGE"

# 檢查服務健康
curl http://localhost:5000/api/health

# 查看日誌
docker-compose logs presenton | tail -50

# 測試 Ollama 連接
docker exec presenton-api curl http://host.docker.internal:11434/api/tags

# 重啟服務
docker-compose down && docker-compose up -d
```

---

**修復完成時間**: 2025-10-14
**修復工程師**: SuperClaude
**驗證狀態**: ✅ 所有測試通過
**生產就緒**: ✅ 可以部署
