# 本機測試

method-1:


```bash
docker compose up -d presenton
```

method-2:

```bash
# CORRECTED version - use correct container path
docker run -it --rm \
  -p 8000:3000 \
  -v "$(pwd)/app_data/chroma:/app/servers/fastapi/chroma" \
  presenton:arm64-local
```



deprecated

#docker run -it --rm -p 5000:80 -v "$(pwd)/app_data:/app_data" presenton:arm64-local
