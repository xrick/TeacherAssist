[MODE: RESEARCH]

結論

- 在「容器內」要連你本機的 Ollama，請用 OLLAMA_HOST=http://host.docker.internal:11434（Mac/Windows Docker Desktop）。
- 在「本機進程」（非容器）要連本機 Ollama，才用 OLLAMA_HOST=http://localhost:11434。
- 後端容器目前使用的是 OLLAMA_URL（你的後端程式讀這個變數）；Presenton 則使用 OLLAMA_HOST。兩者名稱不同，需分別設定。

為什麼不是容器內用 localhost

- 容器內的 localhost 指容器自己，不是宿主機；要連宿主 Ollama 必須用 host.docker.internal（Mac/Windows），Linux 通常用 172.17.0.1。

你現在應如何配置（建議）

- docker-compose.yml（backend 服務）:
  - 保持 OLLAMA_URL=http://host.docker.internal:11434（後端程式讀取此變數，指向宿主 Ollama）
- docker-compose.override.yml（presenton 服務）:
  - 增加 environment: OLLAMA_HOST=http://host.docker.internal:11434（Presenton 使用 OLLAMA_HOST）
- .env 裡的 OLLAMA_HOST=http://localhost:11434:
  - 這只對「直接在本機執行的程式」有效；對容器沒用。容器內仍應用 host.docker.internal。

快速自檢

- 在 TeacherAssist 根目錄:
  - docker compose config | sed -n '/presenton:/,/^[^ ]/p' 應可看到 OLLAMA_HOST=http://host.docker.internal:11434
  - docker compose config | sed -n '/backend:/,/^[^ ]/p' 應可看到 OLLAMA_URL=http://host.docker.internal:11434
- 進容器測試（任一容器）:
  - docker exec -it presenton-api sh -c 'curl -s http://host.docker.internal:11434/api/tags | head -c 80'
  - 若有回應 JSON，即能連到宿主 Ollama
