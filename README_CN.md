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
  一个轻量级的 <a href="https://modelcontextprotocol.io/">MCP</a> 服务器，基于 Google Gemini 实现 AI 图片生成。<br>
  支持 Claude Code、Claude Desktop、Cursor 及所有 MCP 兼容客户端。
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

## 特性

- 基于 Google Gemini 的文生图能力
- 多模型支持（Nano Banana 2、实验版、Pro）
- 生成图片自动保存到磁盘
- 内置 SOCKS 代理支持
- 极简接口 — 描述你想要的即可

## 效果演示

<p align="center">
  <img src="docs/demo.png" alt="Demo" width="700">
</p>

## 架构

<p align="center">
  <img src="docs/architecture.png" alt="Architecture" width="700">
</p>

```
用户提示词 → AI 助手（Claude / Cursor）→ MCP Server → Gemini API
                                            ↓
                                      保存到磁盘 + 展示图片
```

## 快速开始

### 1. 获取 Gemini API Key

| 项目 | 详情 |
|---|---|
| 平台 | Google AI Studio |
| 地址 | https://aistudio.google.com/apikey |
| 免费额度 | **实验版模型完全免费，无需信用卡** |
| 环境变量 | `GEMINI_API_KEY` |

**注册步骤：**
1. 访问 https://aistudio.google.com/apikey
2. 使用 Google 账号登录
3. 点击 **"Create API Key"**（创建 API Key）
4. 选择或创建一个 Google Cloud 项目
5. 复制生成的 Key（格式：`AIzaSy...`）

> 如需使用更高质量模型（Nano Banana 2 / Pro），需要在 [AI Studio 计费页面](https://aistudio.google.com/billing) 开启付费。

### 2. 安装

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen
uv sync
```

### 3. 配置 MCP

#### Claude Code

```bash
claude mcp add --transport stdio gemini-image \
  --env GEMINI_API_KEY=你的api_key \
  -- uv --directory /path/to/mcp-image-gen run image-gen
```

#### Claude Desktop

编辑配置文件 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%/Claude/claude_desktop_config.json`（Windows）：

```json
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

#### Cursor

添加到项目根目录的 `.cursor/mcp.json` 或全局 `~/.cursor/mcp.json`，JSON 格式同上。

### 4. 使用

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

通过 `GEMINI_MODEL` 环境变量切换模型：

```bash
# 实验版 — 免费，广泛可用（默认）
--env GEMINI_MODEL=gemini-2.0-flash-exp-image-generation

# Nano Banana 2 — 更高质量，需付费
--env GEMINI_MODEL=gemini-3.1-flash-image-preview

# Nano Banana Pro — 最佳质量，需付费
--env GEMINI_MODEL=gemini-3-pro-image-preview
```

### 自定义输出目录

```bash
--env IMAGE_OUTPUT_DIR=/你的/图片/保存/路径
```

图片保存格式为 `gemini_YYYYMMDD_HHMMSS.png`。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `GEMINI_API_KEY` | 是 | — | Google Gemini API Key，从 [AI Studio](https://aistudio.google.com/apikey) 获取 |
| `GEMINI_MODEL` | 否 | `gemini-2.0-flash-exp-image-generation` | 图片生成模型 |
| `IMAGE_OUTPUT_DIR` | 否 | `./output` | 图片保存目录 |

## 支持的模型

| 模型 ID | 名称 | 质量 | 价格 |
|---|---|---|---|
| `gemini-2.0-flash-exp-image-generation` | 实验版 | 良好 | 免费 |
| `gemini-3.1-flash-image-preview` | Nano Banana 2 | 高 | ~$0.039/张 |
| `gemini-3-pro-image-preview` | Nano Banana Pro | 最佳 | ~$0.134/张 |
| `gemini-2.5-flash-image` | Nano Banana | 良好 | ~$0.039/张 |

## 前置要求

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — 安装命令：`curl -LsSf https://astral.sh/uv/install.sh | sh`

## 本地开发

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen

# 安装依赖
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
| `429 quota exceeded` | 在 [AI Studio](https://aistudio.google.com/billing) 开启付费，或切换到实验版模型 |
| `User location is not supported` | 部分模型有地区限制，尝试使用 `gemini-2.0-flash-exp-image-generation` |
| `SOCKS proxy error` | 已内置 `httpx[socks]` 依赖，运行 `uv sync` 安装即可 |
| `No image generated` | 尝试更具体的描述，或换一种说法 |

## 相关项目

- [mcp-video-gen](https://github.com/kevinten-ai/mcp-video-gen) — 多平台 AI 视频生成 MCP 服务器

## 许可证

MIT — 详见 [LICENSE](LICENSE)。
