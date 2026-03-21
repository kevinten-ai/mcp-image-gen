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
  A lightweight <a href="https://modelcontextprotocol.io/">MCP</a> server for AI image generation using Google Gemini and Imagen.<br>
  Works with Claude Code, Claude Desktop, Cursor, and any MCP-compatible client.
</p>

<p align="center">
  <a href="README_CN.md">中文文档</a>
</p>

## Features

- **Dual provider** — AI Studio (free) or Vertex AI (GCP credits)
- **Multi-model** — Gemini image generation + Imagen 3.0
- Auto-save generated images to disk
- SOCKS proxy support out of the box
- Simple single-tool interface — just describe what you want

## Demo

<p align="center">
  <img src="docs/demo.png" alt="Demo" width="700">
</p>

## Architecture

<p align="center">
  <img src="docs/architecture.png" alt="Architecture" width="700">
</p>

```
User Prompt → AI Assistant (Claude / Cursor) → MCP Server → Gemini API / Vertex AI
                                                   ↓
                                             Save to disk + Display
```

## Quick Start

### Option A: AI Studio (Free, Recommended)

**1. Get API Key** — visit https://aistudio.google.com/apikey → Create API Key → copy it

**2. Configure MCP**

```bash
# Claude Code
claude mcp add --transport stdio gemini-image \
  --env GEMINI_API_KEY=your_api_key \
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
        "GEMINI_API_KEY": "your_api_key"
      }
    }
  }
}
```

### Option B: Vertex AI (GCP Free Credits)

Use GCP billing with Imagen 3.0 for higher quality results.

**1. Prerequisites**
- A GCP project with billing enabled
- Vertex AI API enabled
- A GCP API key (from [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials))

**2. Install with Vertex AI support**

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen
uv sync --extra vertex
```

**3. Configure MCP**

```json
{
  "mcpServers": {
    "gemini-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-image-gen", "--extra", "vertex", "run", "image-gen"],
      "env": {
        "GEMINI_PROVIDER": "vertex-ai",
        "GEMINI_API_KEY": "your_gcp_api_key",
        "GCP_PROJECT_ID": "your-project-id",
        "GCP_REGION": "us-central1",
        "GEMINI_MODEL": "imagen-3.0-generate-002"
      }
    }
  }
}
```

> **Tip:** Vertex AI also supports OAuth2/ADC authentication. If `GEMINI_API_KEY` is not set, the server will use `gcloud auth application-default login` credentials.

### 3. Use it

Just ask your AI assistant to generate an image:

```
"Generate an image of a dragon flying over mountains at dawn"
```

The image will be displayed inline and automatically saved to the `output/` directory.

## Usage Guide

### Basic Image Generation

Simply describe what you want in natural language:

```
"A cozy cafe in Paris at sunset"
"A futuristic city skyline with flying cars"
"A watercolor painting of a sunflower field"
```

### Tips for Better Results

- **Be specific**: "A golden retriever puppy playing in autumn leaves, soft natural lighting" works better than "a dog"
- **Mention style**: Add terms like "digital art", "photorealistic", "watercolor", "oil painting", "anime style"
- **Describe lighting**: "golden hour", "dramatic lighting", "soft diffused light"
- **Specify composition**: "close-up portrait", "wide-angle landscape", "bird's eye view"

### Choosing a Model

Set `GEMINI_MODEL` to switch models:

**AI Studio (Gemini models):**
```bash
--env GEMINI_MODEL=gemini-2.0-flash-exp-image-generation      # free, experimental (default)
--env GEMINI_MODEL=gemini-2.0-flash-preview-image-generation   # preview
```

**Vertex AI (Imagen models):**
```bash
--env GEMINI_MODEL=imagen-3.0-generate-002       # high quality
--env GEMINI_MODEL=imagen-3.0-fast-generate-001   # faster, lower cost
```

### Custom Output Directory

```bash
--env IMAGE_OUTPUT_DIR=/absolute/path/to/your/images
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_PROVIDER` | No | `ai-studio` | `ai-studio` or `vertex-ai` |
| `GEMINI_API_KEY` | Yes | — | API key (AI Studio or GCP) |
| `GEMINI_MODEL` | No | `gemini-2.0-flash-exp-image-generation` | Model for generation |
| `IMAGE_OUTPUT_DIR` | No | `./output` | Directory to save images |
| `GCP_PROJECT_ID` | Vertex AI | — | GCP project ID |
| `GCP_REGION` | No | `us-central1` | GCP region |

## Supported Models

### AI Studio (Gemini)

| Model ID | Quality | Pricing |
|---|---|---|
| `gemini-2.0-flash-exp-image-generation` | Good | Free |
| `gemini-2.0-flash-preview-image-generation` | Good | Free |

### Vertex AI (Imagen)

| Model ID | Quality | Pricing |
|---|---|---|
| `imagen-3.0-generate-002` | High | ~$0.04/image |
| `imagen-3.0-fast-generate-001` | Good | ~$0.02/image |

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Local Development

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen

# Install dependencies (add --extra vertex for Vertex AI support)
uv sync

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API key

# Run the server directly
uv run image-gen
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `GEMINI_API_KEY not set` | Set the environment variable in your MCP config |
| `429 quota exceeded` | Enable billing or switch to the free experimental model |
| `429 spending cap exceeded` | Increase your GCP spending cap in Billing → Budgets |
| `404 model not found` | Check model name — Vertex AI and AI Studio use different model IDs |
| `401 API keys not supported` | Some Vertex AI models need OAuth2 — run `gcloud auth application-default login` |
| `User location is not supported` | Some models have regional restrictions. Try `gemini-2.0-flash-exp-image-generation` |
| `No image generated` | Try a more descriptive prompt, or rephrase your request |

## Related Projects

- [mcp-video-gen](https://github.com/kevinten-ai/mcp-video-gen) — Multi-provider AI video generation MCP server

## License

MIT — see [LICENSE](LICENSE) for details.
