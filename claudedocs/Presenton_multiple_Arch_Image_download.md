<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Does presenton have a docker image in arm format?

Presenton 有官方 Docker 鏡像，並且支援 ARM 架構。官方說明推薦使用 multi-arch 方式建置，並且在 ghcr.io/presenton/presenton:latest 提供公開鏡像，適用於 Linux/MacOS（Bash）與 Windows（PowerShell），可直接在 ARM 裝置上運行。[^1]

### Docker 安裝指令範例

```
docker run -it --name presenton -p 5000:80 -v "./app_data:/app_data" ghcr.io/presenton/presenton:latest
```


### 支援架構說明

- 官方鏡像支援 x86 及 arm64（多架構），無需自行編譯。[^1]
- 可以指定 LLM 與 GPU 驅動參數，配合本地模型與 NVIDIA Container Toolkit。[^1]


### 小結

Presenton 官方 Docker 鏡像已支援 ARM 架構（arm64），可直接於 ARM 平台部署與運行，無需額外修改，只需拉取最新版 multi-arch 鏡像。[^1]

<div align="center">⁂</div>

[^1]: https://www.docker.com/blog/multi-arch-images/

