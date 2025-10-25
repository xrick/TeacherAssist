# Start/Stop Services Scripts – Functional Overview

本文對 `scripts/start_system.sh` 與 `scripts/stop_system.sh` 的用途、流程與相依條件進行說明，聚焦於現有行為的觀察性描述。

## scripts/start_system.sh

用途：一鍵啟動 TeacherAssist 系統所需的所有服務，包含本機 Ollama 服務、Docker 內的 Presenton 與 Backend，以及本機前端靜態伺服器。

核心流程（按序）：

1) 前置需求檢查

- 檢查 Docker 是否已安裝並可用（以 `docker --version` 驗證）。
- 檢查 Docker Compose（以 `docker-compose --version` 驗證）。
- 檢查 Ollama 是否已安裝（以 `ollama` 指令存在性驗證）。
- 檢查專案根目錄 `.env` 是否存在，若不存在則中止。

2) Port 可用性檢查

- 檢查 5050（Backend）、8000（Presenton）、8080（Frontend）是否已被占用；若被占用，提供互動式選項嘗試結束該程序，否則中止。

3) 啟動本機 Ollama 服務

- 當前未偵測到 `http://localhost:11434/api/tags` 回應時，會啟動 `ollama serve` 並將輸出導向 `/tmp/ollama.log`。
- 啟動後再次以 `/api/tags` 驗證是否成功，失敗時中止並輸出日誌片段。

4) 檢查（並可互動下載）模型

- 檢查 `gpt-oss:20b` 是否存在；若不存在，詢問是否下載，否則中止。
- 檢查 `zephyr:7b` 是否存在；若不存在，詢問是否下載；若跳過則提示「演講稿功能將不可用」。

5) 停止舊容器並清理

- 執行 `docker-compose down` 停止並移除既有容器（若有）。

6) 啟動 Docker 服務

- 執行 `docker-compose up -d --build` 以背景模式建置並啟動容器（`presenton` 與 `backend`）。
- 簡短等待後進入服務健康檢查。

7) 服務健康檢查

- Presenton：以 `http://localhost:8000/` 連線測試；若無回應，輸出 `docker-compose logs presenton` 片段並中止。
- Backend：以 `http://localhost:5050/api/health` 連線測試；若回應，解析 JSON 中的 `status` 與 `services` 欄位並輸出。

8) 啟動前端靜態伺服器

- 以 `python3 -m http.server 8080` 啟動，標準輸出寫入 `/tmp/frontend.log`，PID 寫入 `/tmp/frontend.pid`。
- 以 `HEAD /` 檢查是否 `200 OK`；若失敗，輸出日誌片段並中止。

9) 完成訊息與常用指令提示

- 顯示各服務端點 URL 與常見診斷指令（`docker-compose ps/logs`、`curl` 檢查健康等）。

主要相依條件與假設：

- 需要可用之 Docker 與 Docker Compose（目前指令使用 `docker-compose`）。
- 需要本機可啟動之 Ollama（HTTP 介面於 `localhost:11434`）。
- 預期 `.env` 存在；若不存在則中止。
- 期望 Port 5050/8000/8080 可用；若被占用需釋放。
- 啟動流程內含模型檢查邏輯，當前檢查項為 `gpt-oss:20b` 與 `zephyr:7b`。

與模型/設定的關聯觀察：

- Docker Compose 目前在 `backend` 服務中指定 `OLLAMA_MODEL=gpt-oss:20b`。
- Backend 程式的設定預設 `ollama_model` 為 `gpt-oss:20b`。
- Transcript 流程的服務類別（`zephyr_service.py`）使用固定模型名稱 `zephyr:7b`。
- `start_system.sh` 內部僅檢查/下載 `gpt-oss:20b` 與 `zephyr:7b` 兩個模型。

## scripts/stop_system.sh

用途：一鍵停止 TeacherAssist 系統所啟動之所有服務，包含本機前端、Docker 容器與（可選）本機 Ollama 服務，並做簡要清理與驗證。

核心流程（按序）：

1) 停止前端靜態伺服器

- 讀取 `/tmp/frontend.pid` 並嘗試結束該 PID；若無 PID 檔，則以程序名稱匹配 `python3.*http.server.*8080` 嘗試結束。

2) 停止 Docker 容器

- 檢查 Docker daemon 可用後，若 `docker-compose ps -q` 有輸出，執行 `docker-compose down` 以停止並移除所有容器。

3) 可選停止 Ollama 服務

- 若偵測到 `ollama` 進程存在，提示使用者是否終止；選擇終止時先嘗試正常結束，仍存在則以 `-9` 強制結束。

4) 清理臨時檔案

- 移除 `/tmp/frontend.log`、`/tmp/frontend.pid`、`/tmp/ollama.log` 等暫存檔。

5) 驗證停止狀態

- 檢查 5050/8000/8080 三個 Port 是否已釋放，並輸出簡要結果。

主要相依條件與假設：

- 需要可用之 Docker daemon 方可確保容器停止/移除。
- 前端停止依賴先前由 `start_system.sh` 產生之 PID 檔或以進程名搜索。

## 模型與配置觀察（位置對照）

模型名稱目前出現於以下位置：

- Docker Compose：`backend` 服務的環境變數 `OLLAMA_MODEL=gpt-oss:20b`（固定字面值）。
- Backend 設定：`backend/app/config.py` 預設 `ollama_model = "gpt-oss:20b"`（可為環境變數覆蓋）。
- Transcript 服務：`backend/app/services/zephyr_service.py` 固定使用 `zephyr:7b`。
- 啟動腳本：`scripts/start_system.sh` 內檢查/下載 `gpt-oss:20b` 與 `zephyr:7b`。

以上為現況描述，利於後續依需求對模型或配置進行一致性調整與驗證。


