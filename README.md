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
  AI image generation, editing & upscaling via Google Gemini and Imagen.<br>
  Generate, edit (inpainting), and upscale images — all through one MCP server.<br>
  Works with Claude Code, Claude Desktop, Cursor, and any MCP-compatible client.
</p>

<p align="center">
  <a href="README_CN.md">中文文档</a>
</p>

## Features

- **3 tools** — `generate_image`, `edit_image` (inpainting/outpainting), `upscale_image` (2x/4x)
- **Dual provider** — AI Studio (free) or Vertex AI (GCP credits)
- **Multi-model** — Gemini 2.0 Flash + Imagen 3.0 + **Imagen 4** (Fast & Ultra)
- **Dynamic model switching** — choose model per request via `model` parameter, no restart needed
- **Built-in guides** — MCP Resources with model selection tips and provider docs
- **Smart error recovery** — auto-suggests alternative models on quota errors
- Auto-save generated images to disk
- SOCKS proxy support out of the box

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

### How It Works

The server handles two distinct Google APIs under one unified interface:

| API | Models | Endpoint | Request Format |
|---|---|---|---|
| **Predict API** | `imagen-3.0-*`, `imagen-4.0-*` | Vertex AI only | `instances[].prompt` |
| **GenerateContent API** | `gemini-2.0-*` | AI Studio + Vertex AI | `contents[].parts[].text` |
| **Capability API** | `imagen-3.0-capability-001` | Vertex AI only | `instances[].referenceImages[]` (edit) |
| **Upscale API** | `imagen-4.0-upscale-preview` | Vertex AI only | `instances[].image` (upscale) |

The server automatically selects the correct API based on the model name prefix — `imagen*` routes to Predict, everything else to GenerateContent. You don't need to worry about this distinction.

## Quick Start

### Option A: AI Studio (Free, Recommended for Getting Started)

**1. Get API Key** — visit https://aistudio.google.com/apikey → Create API Key → copy it

**2. Configure MCP**

<details>
<summary><b>Claude Code (CLI)</b></summary>

```bash
claude mcp add --transport stdio mcp-image \
  --env GEMINI_API_KEY=your_api_key \
  -- uv --directory /path/to/mcp-image-gen run image-gen
```
</details>

<details>
<summary><b>Claude Desktop / Cursor (JSON config)</b></summary>

```json
{
  "mcpServers": {
    "mcp-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-image-gen", "run", "image-gen"],
      "env": {
        "GEMINI_API_KEY": "your_api_key"
      }
    }
  }
}
```
</details>

**3. Use it** — just ask your AI assistant:

```
"Generate an image of a dragon flying over mountains at dawn"
```

The image will be displayed inline and automatically saved to the `output/` directory.

### Option B: Vertex AI (Higher Quality, GCP Credits)

Use GCP billing with Imagen 4 / 3.0 for higher quality results, plus image editing and upscaling.

**1. Prerequisites**
- A GCP project with billing enabled ([create one](https://console.cloud.google.com/projectcreate))
- Vertex AI API enabled ([enable it](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com))
- A GCP API key ([create one](https://console.cloud.google.com/apis/credentials))

**2. Install with Vertex AI support**

```bash
git clone https://github.com/kevinten-ai/mcp-image-gen.git
cd mcp-image-gen
uv sync --extra vertex
```

**3. Configure MCP**

<details>
<summary><b>Claude Code (CLI)</b></summary>

```bash
claude mcp add --transport stdio mcp-image \
  --env GEMINI_PROVIDER=vertex-ai \
  --env GEMINI_API_KEY=your_gcp_api_key \
  --env GCP_PROJECT_ID=your-project-id \
  --env GCP_REGION=us-central1 \
  --env GEMINI_MODEL=imagen-3.0-fast-generate-001 \
  -- uv --directory /path/to/mcp-image-gen --extra vertex run image-gen
```
</details>

<details>
<summary><b>Claude Desktop / Cursor (JSON config)</b></summary>

```json
{
  "mcpServers": {
    "mcp-image": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-image-gen", "--extra", "vertex", "run", "image-gen"],
      "env": {
        "GEMINI_PROVIDER": "vertex-ai",
        "GEMINI_API_KEY": "your_gcp_api_key",
        "GCP_PROJECT_ID": "your-project-id",
        "GCP_REGION": "us-central1",
        "GEMINI_MODEL": "imagen-3.0-fast-generate-001"
      }
    }
  }
}
```
</details>

> **Auth options:** Vertex AI supports two authentication methods:
> 1. **GCP API Key** (recommended) — set `GEMINI_API_KEY`. Simple, no extra deps.
> 2. **OAuth2 / ADC** — run `gcloud auth application-default login`. The server auto-detects ADC when no API key is set. Requires `--extra vertex` for `google-auth` dependency.

## Tools

### generate_image — Text to Image
Generate images from text prompts.
```
"A cozy cafe in Paris at sunset"
```

### edit_image — Image Editing (Vertex AI only)
Edit existing images with text instructions. Supports inpainting, outpainting, and background swap.
```
edit_image(prompt="Add a red hat", image_path="/path/to/photo.png")
edit_image(prompt="Replace background with beach", image_path="photo.png", edit_mode="product-image")
edit_image(prompt="Expand the sky", image_path="photo.png", mask_path="mask.png", edit_mode="outpainting")
```

### upscale_image — Super Resolution (Vertex AI only)
Upscale images to 2x or 4x resolution.
```
upscale_image(image_path="/path/to/photo.png", upscale_factor="x4")
```

## Usage Guide

### Tips for Better Results

- **Be specific**: "A golden retriever puppy playing in autumn leaves, soft natural lighting" works better than "a dog"
- **Mention style**: Add terms like "digital art", "photorealistic", "watercolor", "oil painting", "anime style"
- **Describe lighting**: "golden hour", "dramatic lighting", "soft diffused light"
- **Specify composition**: "close-up portrait", "wide-angle landscape", "bird's eye view"
- **No text**: Image models generally struggle with rendering text. Use "No text" in prompts for cleaner results.

### Choosing a Model

#### Per-request switching (recommended)

Pass the `model` parameter when calling the tool:

```
generate_image(prompt="a sunset landscape", model="imagen-3.0-fast-generate-001")
```

AI assistants can dynamically pick the best model per request. If one model hits a quota limit, the error response automatically suggests an alternative.

#### Decision flowchart

```
Need an image?
  ├─ Free / no GCP account?
  │   └─ AI Studio: gemini-2.0-flash-exp-image-generation ✅
  │
  └─ Have GCP billing?
      ├─ Need highest quality?
      │   └─ imagen-4.0-ultra-generate-001 (~$0.06/img)
      │
      ├─ Best value (recommended)?
      │   └─ imagen-4.0-generate-001 (~$0.02/img) ✅
      │
      ├─ Need to edit an image?
      │   └─ edit_image tool (uses imagen-3.0-capability-001)
      │
      ├─ Need to upscale?
      │   └─ upscale_image tool (uses imagen-4.0-upscale-preview)
      │
      └─ Hit quota on one model?
          └─ Switch to another — each model has independent quota
```

#### Default via environment variable

Set `GEMINI_MODEL` to configure the default model used when no `model` parameter is passed:

```bash
# AI Studio (Gemini models)
GEMINI_MODEL=gemini-2.0-flash-exp-image-generation      # free, experimental (default)
GEMINI_MODEL=gemini-2.0-flash-preview-image-generation   # preview

# Vertex AI (Imagen models)
GEMINI_MODEL=imagen-3.0-generate-002       # high quality
GEMINI_MODEL=imagen-3.0-fast-generate-001  # faster, lower cost — recommended for Vertex AI
```

### MCP Resources

The server exposes built-in documentation that AI assistants can automatically read:

| Resource URI | Description |
|---|---|
| `guide://models` | Model comparison, pricing, quota tips, and selection guide |
| `guide://providers` | Provider setup, authentication, and troubleshooting |

AI assistants (Claude, etc.) can read these resources to make informed model choices without human intervention.

### Custom Output Directory

```bash
--env IMAGE_OUTPUT_DIR=/absolute/path/to/your/images
```

Images are saved with timestamps: `imagen_20260321_234225.png` or `gemini_20260321_234225.png`.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_PROVIDER` | No | `ai-studio` | `ai-studio` or `vertex-ai` |
| `GEMINI_API_KEY` | Yes* | — | API key (AI Studio or GCP). *Not required if using ADC. |
| `GEMINI_MODEL` | No | `gemini-2.0-flash-exp-image-generation` | Default model (can be overridden per request via `model` parameter) |
| `IMAGE_OUTPUT_DIR` | No | `./output` | Directory to save generated images |
| `GCP_PROJECT_ID` | Vertex AI only | — | GCP project ID |
| `GCP_REGION` | No | `us-central1` | GCP region for Vertex AI |

## Supported Models

### AI Studio (Gemini) — Free

| Model ID | Quality | Speed | Pricing | Best for |
|---|---|---|---|---|
| `gemini-2.0-flash-exp-image-generation` | Good | Fast | Free | Getting started, experimentation |
| `gemini-2.0-flash-preview-image-generation` | Good | Fast | Free | Preview features |

### Vertex AI (Imagen) — GCP Credits

| Model ID | Quality | Speed | Pricing | Best for |
|---|---|---|---|---|
| `imagen-4.0-generate-001` | **High** | Fast | ~$0.02/image | Best value, recommended |
| `imagen-4.0-ultra-generate-001` | **Highest** | Slower | ~$0.06/image | Premium quality |
| `imagen-3.0-generate-002` | High | Slower | ~$0.04/image | Legacy, stable |
| `imagen-3.0-fast-generate-001` | Good | **Fast** | ~$0.02/image | Legacy fast |
| `gemini-2.0-flash-preview-image-generation` | Good | Fast | Pay-per-use | Multimodal text+image |

### Vertex AI — Specialized Models

| Model ID | Tool | Pricing | Notes |
|---|---|---|---|
| `imagen-3.0-capability-001` | `edit_image` | ~$0.04/edit | Inpainting, outpainting, bg swap |
| `imagen-4.0-upscale-preview` | `upscale_image` | Preview | 2x/4x super resolution |

> **Key insight**: Each model has its own independent API quota. If one model hits a 429, switching to another will work because they use separate rate limits.

## Troubleshooting

### Error Reference

| Error | Root Cause | Solution |
|---|---|---|
| `GEMINI_API_KEY is required` | Missing API key in env config | Set `GEMINI_API_KEY` in your MCP server env config |
| `GCP_PROJECT_ID is required` | Using Vertex AI without project ID | Set `GCP_PROJECT_ID` in your MCP server env config |

### Quota & Billing Errors (429)

These are the most common errors. There are **two distinct 429 errors** with different causes:

#### `429: Quota exceeded for online_prediction_requests_per_base_model`

**What it means:** You've hit the per-minute API call rate limit for a specific model.

**Quick fix:** Switch to a different model via the `model` parameter — each model has independent quota:
```
generate_image(prompt="...", model="imagen-3.0-fast-generate-001")
```

**Long-term fix:** Request a quota increase:
1. Go to [GCP Console → IAM & Admin → Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter by `online_prediction_requests_per_base_model`
3. Find your model (e.g., `imagen-3.0-generate`)
4. Click **Edit Quotas** → request a higher limit (default is often just 5 QPM)

#### `429: Quota exceeded ... spending cap`

**What it means:** You've hit a self-imposed billing spending limit, NOT an API rate limit.

**Fix:**
1. Go to [GCP Console → Billing → Budgets & alerts](https://console.cloud.google.com/billing)
2. Find the budget with a spending cap
3. Increase or remove the cap

> **Tip:** `imagen-3.0-fast-generate-001` costs ~$0.02/image vs $0.04 for the high-quality version. Setting it as default halves your spending.

### Authentication Errors

| Error | Root Cause | Solution |
|---|---|---|
| `401 API keys not supported` | Model doesn't accept API key auth | Use ADC: run `gcloud auth application-default login`, remove `GEMINI_API_KEY` |
| `403 Permission denied` | API key lacks Vertex AI permissions | Enable Vertex AI API in GCP Console, or check API key restrictions |
| `Vertex AI auth failed` | No valid credentials found | Set `GEMINI_API_KEY` or run `gcloud auth application-default login` |

### Model Errors

| Error | Root Cause | Solution |
|---|---|---|
| `404 model not found` | Wrong model ID for provider | AI Studio uses `gemini-*`, Vertex AI supports both `imagen-*` and `gemini-*` |
| `User location is not supported` | Regional restriction on model | Try a different region (`GCP_REGION`) or model. `gemini-2.0-flash-exp-*` has fewest restrictions |
| `No image generated` | Model declined or returned empty | Try a more descriptive prompt, avoid ambiguous or restricted content |

### Connection Errors

| Error | Root Cause | Solution |
|---|---|---|
| `ConnectTimeout` | Network issue or proxy needed | If behind a firewall, configure SOCKS proxy via `httpx` env vars |
| `Failed to parse response` | Unexpected API response | Check model ID is correct, API may be temporarily down |

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

### Debug with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-image-gen run image-gen
```

## Related Projects

- [mcp-video-gen](https://github.com/kevinten-ai/mcp-video-gen) — Multi-provider AI video generation MCP server
- [mcp-3d-gen](https://github.com/kevinten-ai/mcp-3d-gen) — AI 3D model generation MCP server

## License

MIT — see [LICENSE](LICENSE) for details.
