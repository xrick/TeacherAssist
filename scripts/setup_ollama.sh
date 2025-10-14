#!/bin/bash
# scripts/setup_ollama.sh
# 設定 Ollama 讓 Docker 容器可以訪問

echo "🔧 設定 Ollama 服務"

# 檢查是否有現有的 Ollama 進程
if pgrep -x "ollama" > /dev/null; then
    echo "停止現有 Ollama 進程..."
    killall ollama 2>/dev/null
    sleep 2
fi

# 啟動 Ollama，監聽 0.0.0.0
echo "啟動 Ollama (監聽 0.0.0.0:11434)..."
OLLAMA_HOST=0.0.0.0:11434 ollama serve > /tmp/ollama.log 2>&1 &

sleep 3

# 驗證啟動
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama 服務啟動成功"
    echo "監聽地址:"
    ss -tlnp | grep 11434 || lsof -i :11434
else
    echo "❌ Ollama 服務啟動失敗"
    cat /tmp/ollama.log
    exit 1
fi
