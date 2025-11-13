配置修改方法
方法 1: 直接修改 docker-compose.yml (推薦)
當前配置 (docker-compose.yml:15-17, 42-44):
services:
  presenton:
    environment:
      # - OLLAMA_URL=http://host.docker.internal:11434  # home (local Ollama)
      - OLLAMA_URL=http://192.168.200.48:11434  # office (default)
      - OLLAMA_MODEL=gpt-oss:20b  #phi4-mini:3.8b

  backend:
    environment:
      # - OLLAMA_URL=http://host.docker.internal:11434  # home (local Ollama)
      - OLLAMA_URL=http://192.168.200.48:11434  # office (default)
      - OLLAMA_MODEL=gpt-oss:20b    #phi4-mini:3.8b
修改步驟:
切換到本地 Ollama (Home):
# 編輯 docker-compose.yml
# 將第 15-17 行和 42-44 行改為:
- OLLAMA_URL=http://host.docker.internal:11434  # home (local Ollama)
# - OLLAMA_URL=http://192.168.200.48:11434  # office (註解掉)
- OLLAMA_MODEL=phi4-mini:3.8b
或切換到遠端 Ollama (Office):
# 保持當前配置，或修改 IP:
# - OLLAMA_URL=http://host.docker.internal:11434  # home (註解掉)
- OLLAMA_URL=http://192.168.200.48:11434  # office
- OLLAMA_MODEL=gpt-oss:20b
或使用自訂 Ollama 伺服器:
- OLLAMA_URL=http://你的IP:11434
- OLLAMA_MODEL=你想用的模型名稱
方法 2: 使用 .env 檔案 (更靈活)
創建或編輯 .env (如果使用環境變數):
# 編輯 .env 檔案
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=phi4-mini:3.8b
修改 docker-compose.yml 使用變數:
services:
  presenton:
    environment:
      - OLLAMA_URL=${OLLAMA_URL:-http://host.docker.internal:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-phi4-mini:3.8b}

  backend:
    environment:
      - OLLAMA_URL=${OLLAMA_URL:-http://host.docker.internal:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-phi4-mini:3.8b}
方法 3: 使用切換腳本 (最方便)
使用已有的切換腳本 (scripts/switch_model.sh):
# 互動式切換模型
./scripts/switch_model.sh

# 會顯示選單:
# 1. phi4-mini:3.8b (快速輕量)
# 2. phi4-mini-reasoning:3.8b (推理增強)
# 3. zephyr:7b (對話專家)
# 4. gpt-oss:20b (最強質量)
⚠️ 注意: 這個腳本只修改 .env 檔案，如果你的 docker-compose.yml 使用硬編碼值（當前狀態），需要手動修改。
重建 Backend 映像檔
情境 1: 只修改環境變數 (不需要重建映像檔)
原因: 環境變數是在容器啟動時注入的，不需要重建映像檔 操作:
# 1. 修改 docker-compose.yml 或 .env

# 2. 重啟服務 (會使用新的環境變數)
docker compose down
docker compose up -d

# 或只重啟 backend 服務
docker compose restart backend
驗證:
# 檢查容器的環境變數
docker exec ppt-backend env | grep OLLAMA

# 預期輸出:
# OLLAMA_URL=http://host.docker.internal:11434
# OLLAMA_MODEL=phi4-mini:3.8b
情境 2: 修改了 Backend 程式碼 (需要重建映像檔)
什麼時候需要重建:
修改了 backend/ 目錄下的 Python 程式碼
修改了 backend/requirements.txt 依賴
修改了 backend/Dockerfile
完整重建流程:
# 1. 停止並移除舊容器
docker compose down

# 2. 重建 backend 映像檔 (強制不使用快取)
docker compose build --no-cache backend

# 3. 啟動服務
docker compose up -d

# 4. 查看啟動日誌
docker compose logs -f backend
快速重建 (使用快取，較快):
# 重建並啟動 backend
docker compose up -d --build backend

# 等於:
# docker compose build backend
# docker compose up -d backend
只重建特定服務:
# 只重建 backend，不重建 presenton
docker compose build backend

# 只重啟 backend 服務
docker compose up -d backend
情境 3: 清理並完全重建 (最徹底)
適用情境:
遇到無法解釋的錯誤
映像檔可能損壞
需要清理舊版本
# 1. 停止並移除所有容器
docker compose down

# 2. 移除舊的 backend 映像檔
docker rmi teacherassist-backend:latest

# 3. 重建並啟動
docker compose up -d --build

# 或分步執行:
docker compose build --no-cache
docker compose up -d
完整操作範例
範例 A: 從 Office 切換到 Home (本地 Ollama)
# Step 1: 修改 docker-compose.yml
# 編輯第 15-17 行和 42-44 行:

# Presenton 服務:
- OLLAMA_URL=http://host.docker.internal:11434  # 取消註解
# - OLLAMA_URL=http://192.168.200.48:11434     # 註解掉
- OLLAMA_MODEL=phi4-mini:3.8b

# Backend 服務:
- OLLAMA_URL=http://host.docker.internal:11434  # 取消註解
# - OLLAMA_URL=http://192.168.200.48:11434     # 註解掉
- OLLAMA_MODEL=phi4-mini:3.8b

# Step 2: 確認本地 Ollama 正在運行
ollama list

# Step 3: 確認模型已下載
# 如果沒有 phi4-mini:3.8b，先下載:
ollama pull phi4-mini:3.8b

# Step 4: 重啟服務 (不需要重建映像檔)
docker compose down
docker compose up -d

# Step 5: 檢查服務健康狀態
sleep 10
curl -s http://localhost:5050/api/health | python3 -m json.tool

# 預期輸出:
# {
#     "status": "healthy",
#     "services": {
#         "presenton": "connected",
#         "ollama": "connected",  # ← 應該顯示 connected
#         "pexels": "connected"
#     }
# }
範例 B: 切換模型到 gpt-oss:20b
# Step 1: 確認模型已下載
ollama list | grep gpt-oss

# 如果沒有，下載模型 (約 13GB)
ollama pull gpt-oss:20b

# Step 2: 修改 docker-compose.yml
# 第 17 行和 44 行改為:
- OLLAMA_MODEL=gpt-oss:20b

# Step 3: 重啟服務
docker compose restart backend
docker compose restart presenton

# Step 4: 驗證配置
docker exec ppt-backend env | grep OLLAMA_MODEL
# 預期: OLLAMA_MODEL=gpt-oss:20b

# Step 5: 測試生成 PPT (應該會使用新模型)
範例 C: 修改程式碼後重建
# 假設你修改了 backend/app/services/ollama_service.py

# Step 1: 確認修改已儲存
ls -l backend/app/services/ollama_service.py

# Step 2: 重建 backend 映像檔
docker compose build backend

# Step 3: 停止並啟動新版本
docker compose up -d backend

# Step 4: 查看日誌確認新代碼運行
docker compose logs -f backend

# Step 5: 測試功能
curl http://localhost:5050/api/health
常見問題排查
Q1: 修改後服務無法連線到 Ollama
檢查步驟:
# 1. 確認 Ollama 服務正在運行
curl http://localhost:11434/api/tags

# 如果失敗，啟動 Ollama
ollama serve

# 2. 檢查容器能否訪問 host.docker.internal
docker exec ppt-backend ping -c 3 host.docker.internal

# 3. 測試從容器內訪問 Ollama
docker exec ppt-backend curl http://host.docker.internal:11434/api/tags

# 4. 查看 backend 日誌
docker compose logs backend | grep -i ollama
Q2: 環境變數沒有生效
原因: Docker Compose 可能使用了舊容器 解決方法:
# 強制重新創建容器
docker compose up -d --force-recreate backend

# 或完全重啟
docker compose down
docker compose up -d
Q3: 重建映像檔後磁碟空間不足
清理舊映像檔:
# 查看 Docker 磁碟使用
docker system df

# 清理未使用的映像檔
docker image prune -a

# 或清理所有未使用的資源
docker system prune -a --volumes
Q4: Backend 容器不斷重啟
診斷:
# 查看容器狀態
docker compose ps

# 查看詳細日誌
docker compose logs backend --tail 100

# 常見原因:
# - Ollama 無法連線
# - Python 依賴缺失
# - 環境變數配置錯誤
關鍵要點總結
環境變數修改:
✅ 修改 docker-compose.yml → docker compose restart
✅ 修改 .env → docker compose restart
❌ 不需要重建映像檔
程式碼修改:
✅ 修改 backend/ 程式碼 → docker compose build backend
✅ 修改 Dockerfile → docker compose build --no-cache backend
✅ 需要重建映像檔
最佳實踐:
使用 .env 檔案管理環境變數（更靈活）
在 docker-compose.yml 中保留註解（方便切換）
修改配置後先用 docker exec 驗證環境變數
測試前先確認 Ollama 模型已下載
快速參考:
# 只改配置: docker compose restart backend
# 改程式碼: docker compose up -d --build backend
# 完全重建: docker compose down && docker compose build --no-cache && docker compose up -d
需要我協助執行任何具體的配置切換或重建操作嗎？
