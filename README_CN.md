# Gemini Image Gen MCP Server

<p align="center">
  <img src="docs/banner.png" alt="Banner" width="800">
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-compatible-green.svg" alt="MCP"></a>
</p>

<p align="center">
  一个轻量级的 <a href="https://modelcontextprotocol.io/">MCP</a> 服务器，基于 Google Gemini 和 Imagen 实现 AI 图片生成。<br>
  支持 Claude Code、Claude Desktop、Cursor 及所有 MCP 兼容客户端。
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

## 特性

- **双模式** — AI Studio（免费）或 Vertex AI（GCP 赠金）
- **多模型** — Gemini 图片生成 + Imagen 3.0
- **动态切换模型** — 每次请求可选择不同模型，无需重启
- **内置指南** — MCP Resources 提供模型选型和配置文档
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

## 快速开始

### 方案 A：AI Studio（免费，推荐）

**1. 获取 API Key** — 访问 https://aistudio.google.com/apikey → 创建 API Key → 复制

**2. 配置 MCP**

```bash
# Claude Code
claude mcp add --transport stdio gemini-image \
  --env GEMINI_API_KEY=你的api_key \
  -- uv --directory /path/to/mcp-image-gen run image-gen
```

```json
// Claude Desktop / Cursor
{
  "mcpServers": {
    "gemini-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-image-gen", "run", "image-gen"],
      "env": {
        "GEMINI_API_KEY": "你的api_key"
      }
    }
  }
}
```

### 方案 B：Vertex AI（使用 GCP 赠金）

使用 GCP 计费 + Imagen 3.0，获得更高质量的生成结果。

**1. 前置条件**
- 已启用计费的 GCP 项目
- 已启用 Vertex AI API
- GCP API Key（从 [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials) 获取）

**2. 安装（含 Vertex AI 依赖）**

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen
uv sync --extra vertex
```

**3. 配置 MCP**

```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-image-gen", "--extra", "vertex", "run", "image-gen"],
      "env": {
        "GEMINI_PROVIDER": "vertex-ai",
        "GEMINI_API_KEY": "你的gcp_api_key",
        "GCP_PROJECT_ID": "你的项目ID",
        "GCP_REGION": "us-central1",
        "GEMINI_MODEL": "imagen-3.0-generate-002"
      }
    }
  }
}
```

> **提示：** Vertex AI 也支持 OAuth2/ADC 认证。未设置 `GEMINI_API_KEY` 时，服务器会使用 `gcloud auth application-default login` 凭据。

### 3. 使用

直接用自然语言告诉 AI 助手你想生成什么图片：

```
"生成一张龙在雪山上空飞翔的图片"
```

图片会在对话中直接显示，同时自动保存到 `output/` 目录。

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

### 切换模型

**方式一：每次请求动态选择（推荐）** — 传入 `model` 参数：

```
"生成一张日落风景图" → model: imagen-3.0-fast-generate-001
```

AI 助手可以根据需求动态选择模型。遇到配额限制时，会自动建议切换到其他模型。

**方式二：通过环境变量设置默认模型：**

**AI Studio（Gemini 模型）：**
```bash
--env GEMINI_MODEL=gemini-2.0-flash-exp-image-generation      # 免费实验版（默认）
--env GEMINI_MODEL=gemini-2.0-flash-preview-image-generation   # 预览版
```

**Vertex AI（Imagen 模型）：**
```bash
--env GEMINI_MODEL=imagen-3.0-generate-002       # 高质量
--env GEMINI_MODEL=imagen-3.0-fast-generate-001   # 更快，成本更低
```

### MCP Resources

服务器内置指南文档，AI 助手可自动读取参考：

| 资源 URI | 说明 |
|---|---|
| `guide://models` | 模型对比、价格、选型建议 |
| `guide://providers` | 服务商配置和问题排查 |

### 自定义输出目录

```bash
--env IMAGE_OUTPUT_DIR=/你的/图片/保存/路径
```

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `GEMINI_PROVIDER` | 否 | `ai-studio` | `ai-studio` 或 `vertex-ai` |
| `GEMINI_API_KEY` | 是 | — | API Key（AI Studio 或 GCP） |
| `GEMINI_MODEL` | 否 | `gemini-2.0-flash-exp-image-generation` | 默认模型（可在每次请求中覆盖） |
| `IMAGE_OUTPUT_DIR` | 否 | `./output` | 图片保存目录 |
| `GCP_PROJECT_ID` | Vertex AI | — | GCP 项目 ID |
| `GCP_REGION` | 否 | `us-central1` | GCP 区域 |

## 支持的模型

### AI Studio（Gemini）

| 模型 ID | 质量 | 价格 |
|---|---|---|
| `gemini-2.0-flash-exp-image-generation` | 良好 | 免费 |
| `gemini-2.0-flash-preview-image-generation` | 良好 | 免费 |

### Vertex AI（Imagen）

| 模型 ID | 质量 | 价格 |
|---|---|---|
| `imagen-3.0-generate-002` | 高 | ~$0.04/张 |
| `imagen-3.0-fast-generate-001` | 良好 | ~$0.02/张 |

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

## 常见问题

| 问题 | 解决方案 |
|---|---|
| `GEMINI_API_KEY not set` | 在 MCP 配置中设置环境变量 |
| `429 quota exceeded` | 通过 `model` 参数切换模型（如 `imagen-3.0-fast-generate-001`），或申请提高配额 |
| `429 spending cap exceeded` | 在 GCP Billing → Budgets 中提高消费上限 |
| `404 model not found` | 检查模型名 — Vertex AI 和 AI Studio 使用不同的模型 ID |
| `401 API keys not supported` | 部分 Vertex AI 模型需要 OAuth2 — 运行 `gcloud auth application-default login` |
| `User location is not supported` | 部分模型有地区限制，尝试 `gemini-2.0-flash-exp-image-generation` |
| `No image generated` | 尝试更具体的描述，或换一种说法 |

## 相关项目

- [mcp-video-gen](https://github.com/kevinten-ai/mcp-video-gen) — 多平台 AI 视频生成 MCP 服务器

## 许可证

MIT — 详见 [LICENSE](LICENSE)。
