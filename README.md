# Gemini Image Gen MCP Server

![Banner](docs/banner.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)

A lightweight [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server for AI image generation using Google Gemini. Works with Claude Code, Claude Desktop, Cursor, and any MCP-compatible client.

**[中文文档](README_CN.md)**

## Features

- Text-to-image generation powered by Google Gemini
- Multiple model support (Nano Banana 2, experimental, Pro)
- Auto-save generated images to disk
- SOCKS proxy support out of the box
- Simple single-tool interface — just describe what you want

## Demo

![Demo](docs/demo.png)

## Architecture

![Architecture](docs/architecture.png)

```
User Prompt → AI Assistant (Claude / Cursor) → MCP Server → Gemini API
                                                   ↓
                                             Save to disk + Display
```

## Quick Start

### 1. Get a Gemini API Key

Go to [Google AI Studio](https://aistudio.google.com/apikey) and create an API key. No credit card required for the experimental model.

> For higher quality models (Nano Banana 2 / Pro), you need to [enable billing](https://aistudio.google.com/billing) on your Google Cloud project.

### 2. Install

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen
uv sync
```

### 3. Configure MCP

#### Claude Code

```bash
claude mcp add --transport stdio gemini-image \
  --env GEMINI_API_KEY=your_api_key \
  -- uv --directory /path/to/mcp-image-gen run image-gen
```

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows):

```json
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

#### Cursor

Add to `.cursor/mcp.json` in your project root or `~/.cursor/mcp.json` globally. Same JSON format as above.

### 4. Use it

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

```bash
# Experimental — free, widely available (default)
--env GEMINI_MODEL=gemini-2.0-flash-exp-image-generation

# Nano Banana 2 — higher quality, paid tier
--env GEMINI_MODEL=gemini-3.1-flash-image-preview

# Nano Banana Pro — best quality, paid tier
--env GEMINI_MODEL=gemini-3-pro-image-preview
```

### Custom Output Directory

```bash
--env IMAGE_OUTPUT_DIR=/absolute/path/to/your/images
```

Images are saved as `gemini_YYYYMMDD_HHMMSS.png`.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key from [AI Studio](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | No | `gemini-2.0-flash-exp-image-generation` | Model to use for generation |
| `IMAGE_OUTPUT_DIR` | No | `./output` | Directory to save generated images |

## Supported Models

| Model ID | Name | Quality | Pricing |
|---|---|---|---|
| `gemini-2.0-flash-exp-image-generation` | Experimental | Good | Free |
| `gemini-3.1-flash-image-preview` | Nano Banana 2 | High | ~$0.039/image |
| `gemini-3-pro-image-preview` | Nano Banana Pro | Best | ~$0.134/image |
| `gemini-2.5-flash-image` | Nano Banana | Good | ~$0.039/image |

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Local Development

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen

# Install dependencies
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
| `429 quota exceeded` | Enable billing at [AI Studio](https://aistudio.google.com/billing), or switch to the experimental model |
| `User location is not supported` | Some models have regional restrictions. Try `gemini-2.0-flash-exp-image-generation` |
| `SOCKS proxy error` | The `httpx[socks]` dependency is included. Run `uv sync` to install |
| `No image generated` | Try a more descriptive prompt, or rephrase your request |

## License

MIT — see [LICENSE](LICENSE) for details.
