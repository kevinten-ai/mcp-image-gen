# Gemini Image Gen MCP Server

<p align="center">
  <img src="docs/banner.png" alt="Banner" width="800">
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-compatible-green.svg" alt="MCP"></a>
  <img src="https://img.shields.io/badge/version-1.2.0-blue.svg" alt="Version 1.2.0">
</p>

<p align="center">
  基于 Google Gemini 和 Imagen 的 AI 图片生成、编辑与超分 MCP 服务器。<br>
  生成、编辑（局部重绘）、超分放大 — 一站式图片处理。<br>
  支持 Claude Code、Claude Desktop、Cursor 及所有 MCP 兼容客户端。
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

## 特性

- **3 个工具** — `generate_image`（生图）、`edit_image`（局部重绘/扩图）、`upscale_image`（2x/4x 超分）
- **双模式** — AI Studio（免费）或 Vertex AI（GCP 赠金）
- **多模型** — Gemini 2.0 Flash + Imagen 3.0 + **Imagen 4**（Fast & Ultra）
- **动态切换模型** — 通过 `model` 参数每次请求可选择不同模型，无需重启
- **内置指南** — MCP Resources 提供模型选型和配置文档
- **智能错误恢复** — 遇到配额限制时自动建议切换模型
- 生成图片自动保存到磁盘
- 内置 SOCKS 代理支持

## 效果演示

<p align="center">
  <img src="docs/demo.png" alt="Demo" width="700">
</p>

## 架构

<p align="center">
  <img src="docs/architecture.png" alt="Architecture" width="700">
</p>

```
用户提示词 → AI 助手（Claude / Cursor）→ MCP Server → Gemini API / Vertex AI
                                            ↓
                                      保存到磁盘 + 展示图片
```

### 工作原理

服务器将两种不同的 Google API 统一在一个接口下：

| API | 模型 | 端点 | 请求格式 |
|---|---|---|---|
| **Predict API** | `imagen-3.0-*`, `imagen-4.0-*` | 仅 Vertex AI | `instances[].prompt` |
| **GenerateContent API** | `gemini-2.0-*` | AI Studio + Vertex AI | `contents[].parts[].text` |
| **Capability API** | `imagen-3.0-capability-001` | 仅 Vertex AI | `instances[].referenceImages[]`（编辑）|
| **Upscale API** | `imagen-4.0-upscale-preview` | 仅 Vertex AI | `instances[].image`（超分）|

服务器根据模型名称前缀自动选择正确的 API —— `imagen*` 走 Predict，其他走 GenerateContent。你无需关心这个区别。

## 快速开始

### 方案 A：AI Studio（免费，推荐入门）

**1. 获取 API Key** — 访问 https://aistudio.google.com/apikey → 创建 API Key → 复制

**2. 配置 MCP**

<details>
<summary><b>Claude Code（命令行）</b></summary>

```bash
claude mcp add --transport stdio mcp-image \
  --env GEMINI_API_KEY=你的api_key \
  -- uv --directory /path/to/mcp-image-gen run image-gen
```
</details>

<details>
<summary><b>Claude Desktop / Cursor（JSON 配置）</b></summary>

```json
{
  "mcpServers": {
    "mcp-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-image-gen", "run", "image-gen"],
      "env": {
        "GEMINI_API_KEY": "你的api_key"
      }
    }
  }
}
```
</details>

**3. 使用** — 直接用自然语言告诉 AI 助手：

```
"生成一张龙在雪山上空飞翔的图片"
```

图片会在对话中直接显示，同时自动保存到 `output/` 目录。

### 方案 B：Vertex AI（更高质量，GCP 赠金）

使用 GCP 计费 + Imagen 3.0，获得更高质量的生成结果。

**1. 前置条件**
- 已启用计费的 GCP 项目（[创建项目](https://console.cloud.google.com/projectcreate)）
- 已启用 Vertex AI API（[启用](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)）
- GCP API Key（[创建](https://console.cloud.google.com/apis/credentials)）

**2. 安装（含 Vertex AI 依赖）**

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen
uv sync --extra vertex
```

**3. 配置 MCP**

<details>
<summary><b>Claude Code（命令行）</b></summary>

```bash
claude mcp add --transport stdio mcp-image \
  --env GEMINI_PROVIDER=vertex-ai \
  --env GEMINI_API_KEY=你的gcp_api_key \
  --env GCP_PROJECT_ID=你的项目ID \
  --env GCP_REGION=us-central1 \
  --env GEMINI_MODEL=imagen-3.0-fast-generate-001 \
  -- uv --directory /path/to/mcp-image-gen --extra vertex run image-gen
```
</details>

<details>
<summary><b>Claude Desktop / Cursor（JSON 配置）</b></summary>

```json
{
  "mcpServers": {
    "mcp-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-image-gen", "--extra", "vertex", "run", "image-gen"],
      "env": {
        "GEMINI_PROVIDER": "vertex-ai",
        "GEMINI_API_KEY": "你的gcp_api_key",
        "GCP_PROJECT_ID": "你的项目ID",
        "GCP_REGION": "us-central1",
        "GEMINI_MODEL": "imagen-3.0-fast-generate-001"
      }
    }
  }
}
```
</details>

> **认证方式：** Vertex AI 支持两种认证：
> 1. **GCP API Key**（推荐）— 设置 `GEMINI_API_KEY`，简单无额外依赖
> 2. **OAuth2 / ADC** — 运行 `gcloud auth application-default login`，未设置 API Key 时自动使用 ADC，需要 `--extra vertex` 安装 `google-auth` 依赖

## 使用指南

### 基础生图

用自然语言描述即可：

```
"巴黎街头的温馨咖啡馆，日落时分"
"赛博朋克风格的未来城市天际线"
"向日葵田野的水彩画"
```

### 提示词技巧

- **具体描述**："一只金毛幼犬在秋天落叶中玩耍，柔和自然光" 比 "一只狗" 效果好得多
- **指定风格**：添加 "数字艺术"、"写实风格"、"水彩画"、"油画"、"动漫风格" 等
- **描述光线**："黄金时刻"、"戏剧性光影"、"柔和漫射光"
- **指定构图**："特写肖像"、"广角风景"、"鸟瞰视角"
- **避免文字**：图片模型通常不擅长渲染文字，在提示词中加 "No text" 可获得更干净的结果

### 切换模型

#### 每次请求动态选择（推荐）

调用工具时传入 `model` 参数：

```
generate_image(prompt="一张日落风景图", model="imagen-3.0-fast-generate-001")
```

AI 助手可以根据需求动态选择模型。遇到配额限制时，错误信息会自动建议切换到其他模型。

#### 选择决策流程

```
需要生成图片？
  ├─ 免费 / 没有 GCP 账号？
  │   └─ AI Studio: gemini-2.0-flash-exp-image-generation ✅
  │
  └─ 有 GCP 计费账号？
      ├─ 需要最高质量？
      │   └─ imagen-3.0-generate-002（~$0.04/张）
      │
      ├─ 需要快速迭代 / 低成本？
      │   └─ imagen-3.0-fast-generate-001（~$0.02/张）✅ 推荐默认
      │
      └─ 某个模型遇到配额限制？
          └─ 切换到另一个 — 每个模型有独立配额
```

#### 通过环境变量设置默认模型

设置 `GEMINI_MODEL` 配置未传 `model` 参数时使用的默认模型：

```bash
# AI Studio（Gemini 模型）
GEMINI_MODEL=gemini-2.0-flash-exp-image-generation      # 免费实验版（默认）
GEMINI_MODEL=gemini-2.0-flash-preview-image-generation   # 预览版

# Vertex AI（Imagen 模型）
GEMINI_MODEL=imagen-3.0-generate-002       # 高质量
GEMINI_MODEL=imagen-3.0-fast-generate-001  # 更快，成本更低 — Vertex AI 推荐默认值
```

### MCP Resources

服务器内置文档，AI 助手可自动读取参考：

| 资源 URI | 说明 |
|---|---|
| `guide://models` | 模型对比、价格、配额提示、选型指南 |
| `guide://providers` | 服务商配置、认证方式、问题排查 |

AI 助手（Claude 等）可以读取这些资源来自主做出模型选择决策，无需人工干预。

### 自定义输出目录

```bash
--env IMAGE_OUTPUT_DIR=/你的/图片/保存/路径
```

图片以时间戳命名保存：`imagen_20260321_234225.png` 或 `gemini_20260321_234225.png`。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `GEMINI_PROVIDER` | 否 | `ai-studio` | `ai-studio` 或 `vertex-ai` |
| `GEMINI_API_KEY` | 是* | — | API Key（AI Studio 或 GCP）。*使用 ADC 时非必填 |
| `GEMINI_MODEL` | 否 | `gemini-2.0-flash-exp-image-generation` | 默认模型（可通过 `model` 参数逐次覆盖） |
| `IMAGE_OUTPUT_DIR` | 否 | `./output` | 图片保存目录 |
| `GCP_PROJECT_ID` | Vertex AI | — | GCP 项目 ID |
| `GCP_REGION` | 否 | `us-central1` | Vertex AI 区域 |

## 支持的模型

### AI Studio（Gemini）— 免费

| 模型 ID | 质量 | 速度 | 价格 | 适用场景 |
|---|---|---|---|---|
| `gemini-2.0-flash-exp-image-generation` | 良好 | 快 | 免费 | 入门体验、实验 |
| `gemini-2.0-flash-preview-image-generation` | 良好 | 快 | 免费 | 预览功能 |

### Vertex AI（Imagen）— GCP 赠金

| 模型 ID | 质量 | 速度 | 价格 | 适用场景 |
|---|---|---|---|---|
| `imagen-4.0-generate-001` | **高** | 快 | ~$0.02/张 | 性价比最高，推荐 |
| `imagen-4.0-ultra-generate-001` | **最高** | 较慢 | ~$0.06/张 | 顶级质量 |
| `imagen-3.0-generate-002` | 高 | 较慢 | ~$0.04/张 | 旧版稳定 |
| `imagen-3.0-fast-generate-001` | 良好 | **快** | ~$0.02/张 | 旧版快速 |
| `gemini-2.0-flash-preview-image-generation` | 良好 | 快 | 按量计费 | 多模态文图混合 |

### Vertex AI — 专用模型

| 模型 ID | 工具 | 价格 | 说明 |
|---|---|---|---|
| `imagen-3.0-capability-001` | `edit_image` | ~$0.04/次 | 局部重绘、扩图、背景替换 |
| `imagen-4.0-upscale-preview` | `upscale_image` | Preview | 2x/4x 超分辨率 |

> **关键提示**：每个模型有独立的 API 配额。某个模型遇到 429 错误时，切换到其他模型即可。

## 常见问题排查

### 错误速查

| 错误 | 根因 | 解决方案 |
|---|---|---|
| `GEMINI_API_KEY is required` | MCP 配置中缺少 API Key | 在 MCP 服务器 env 配置中设置 `GEMINI_API_KEY` |
| `GCP_PROJECT_ID is required` | 使用 Vertex AI 但未设置项目 ID | 在 MCP 服务器 env 配置中设置 `GCP_PROJECT_ID` |

### 配额与计费错误（429）

这是最常见的错误。有**两种不同的 429 错误**，原因完全不同：

#### `429: Quota exceeded for online_prediction_requests_per_base_model`

**含义**：你触发了某个模型的每分钟 API 调用次数限制。

**快速修复**：通过 `model` 参数切换到其他模型 — 每个模型有独立配额：
```
generate_image(prompt="...", model="imagen-3.0-fast-generate-001")
```

**长期修复**：申请提高配额：
1. 进入 [GCP Console → IAM & Admin → Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. 搜索 `online_prediction_requests_per_base_model`
3. 找到对应模型（如 `imagen-3.0-generate`）
4. 点击 **Edit Quotas** → 申请更高额度（默认通常只有 5 QPM）

#### `429: Quota exceeded ... spending cap`

**含义**：你触发了自设的账单消费上限，**不是** API 速率限制。

**修复**：
1. 进入 [GCP Console → Billing → Budgets & alerts](https://console.cloud.google.com/billing)
2. 找到设有消费上限的预算
3. 提高或移除上限

> **省钱提示**：`imagen-3.0-fast-generate-001` 每张约 $0.02，是高质量版本的一半。设为默认可显著降低消费。

### 认证错误

| 错误 | 根因 | 解决方案 |
|---|---|---|
| `401 API keys not supported` | 该模型不接受 API Key 认证 | 使用 ADC：运行 `gcloud auth application-default login`，删除 `GEMINI_API_KEY` |
| `403 Permission denied` | API Key 缺少 Vertex AI 权限 | 在 GCP Console 启用 Vertex AI API，或检查 API Key 限制 |
| `Vertex AI auth failed` | 找不到有效凭据 | 设置 `GEMINI_API_KEY` 或运行 `gcloud auth application-default login` |

### 模型错误

| 错误 | 根因 | 解决方案 |
|---|---|---|
| `404 model not found` | 模型 ID 与 provider 不匹配 | AI Studio 用 `gemini-*`，Vertex AI 同时支持 `imagen-*` 和 `gemini-*` |
| `User location is not supported` | 模型有地区限制 | 换一个 `GCP_REGION` 或换模型。`gemini-2.0-flash-exp-*` 限制最少 |
| `No image generated` | 模型拒绝或返回空 | 用更具体的提示词，避免模糊或受限内容 |

### 连接错误

| 错误 | 根因 | 解决方案 |
|---|---|---|
| `ConnectTimeout` | 网络问题或需要代理 | 如在防火墙后面，通过 `httpx` 环境变量配置 SOCKS 代理 |
| `Failed to parse response` | API 返回非预期格式 | 检查模型 ID 是否正确，API 可能临时故障 |

## 前置要求

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — 安装命令：`curl -LsSf https://astral.sh/uv/install.sh | sh`

## 本地开发

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen

# 安装依赖（Vertex AI 支持加 --extra vertex）
uv sync

# 复制并配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 直接运行服务器
uv run image-gen
```

### 使用 MCP Inspector 调试

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-image-gen run image-gen
```

## 相关项目

- [mcp-video-gen](https://github.com/kevinten-ai/mcp-video-gen) — 多平台 AI 视频生成 MCP 服务器
- [mcp-3d-gen](https://github.com/kevinten-ai/mcp-3d-gen) — AI 3D 模型生成 MCP 服务器

## 许可证

MIT — 详见 [LICENSE](LICENSE)。
