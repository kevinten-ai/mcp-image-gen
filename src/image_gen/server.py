from typing import Any
import asyncio
import base64
from datetime import datetime
from pathlib import Path
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import os

# ── Configuration ────────────────────────────────────────────────────────────
# Provider: "ai-studio" (default) or "vertex-ai"
GEMINI_PROVIDER = os.getenv("GEMINI_PROVIDER", "ai-studio")

# Default model (can be overridden per request via tool parameter)
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp-image-generation")

# Output directory for saved images
IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", os.path.join(os.getcwd(), "output"))

# AI Studio: API key from https://aistudio.google.com/apikey
# Vertex AI: GCP API key or uses ADC (Application Default Credentials)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Vertex AI specific
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# ── Model catalog ────────────────────────────────────────────────────────────
MODELS = {
    "ai-studio": {
        "gemini-2.0-flash-exp-image-generation": {
            "name": "Gemini 2.0 Flash (Experimental)",
            "quality": "Good",
            "pricing": "Free",
            "api": "generateContent",
        },
        "gemini-2.0-flash-preview-image-generation": {
            "name": "Gemini 2.0 Flash (Preview)",
            "quality": "Good",
            "pricing": "Free",
            "api": "generateContent",
        },
    },
    "vertex-ai": {
        "imagen-3.0-generate-002": {
            "name": "Imagen 3.0 (High Quality)",
            "quality": "High",
            "pricing": "~$0.04/image",
            "api": "predict",
        },
        "imagen-3.0-fast-generate-001": {
            "name": "Imagen 3.0 Fast",
            "quality": "Good",
            "pricing": "~$0.02/image",
            "api": "predict",
        },
        "gemini-2.0-flash-preview-image-generation": {
            "name": "Gemini 2.0 Flash (Preview, on Vertex)",
            "quality": "Good",
            "pricing": "Pay-per-use",
            "api": "generateContent",
        },
    },
}

# ── Resource content ─────────────────────────────────────────────────────────
MODEL_GUIDE = """# Image Generation Model Guide

## Current Configuration
- **Provider**: {provider}
- **Default model**: {default_model}

## Available Models

### AI Studio (Free, set GEMINI_PROVIDER=ai-studio)

| Model ID | Quality | Speed | Pricing | Best for |
|---|---|---|---|---|
| `gemini-2.0-flash-exp-image-generation` | Good | Fast | Free | Getting started, experimentation |
| `gemini-2.0-flash-preview-image-generation` | Good | Fast | Free | Preview features |

### Vertex AI (GCP Credits, set GEMINI_PROVIDER=vertex-ai)

| Model ID | Quality | Speed | Pricing | Best for |
|---|---|---|---|---|
| `imagen-3.0-generate-002` | **High** | Slower | ~$0.04/img | Production, marketing visuals |
| `imagen-3.0-fast-generate-001` | Good | **Fast** | ~$0.02/img | Rapid iteration, prototyping |
| `gemini-2.0-flash-preview-image-generation` | Good | Fast | Pay-per-use | Multimodal text+image |

## Model Selection Decision

```
Need an image?
  |-- Free / no GCP --> gemini-2.0-flash-exp-image-generation
  +-- Have GCP billing?
      |-- Highest quality --> imagen-3.0-generate-002
      |-- Fast/cheap --> imagen-3.0-fast-generate-001 <-- recommended default
      +-- Hit quota? --> switch model (each has independent quota)
```

## Quota & Cost Tips

- **IMPORTANT: Each model has independent API quota.** If `imagen-3.0-generate-002` returns 429, \
switching to `imagen-3.0-fast-generate-001` works because they have separate rate limits.
- Default Vertex AI quota for Imagen is often just 5 requests per minute (QPM). \
Request a quota increase at GCP Console > IAM & Admin > Quotas.
- `imagen-3.0-fast-generate-001` costs half the price ($0.02 vs $0.04) and has its own quota pool. \
Best default for Vertex AI users.
- There are TWO different 429 errors:
  - "Quota exceeded for online_prediction_requests_per_base_model" = rate limit, switch model or wait
  - "Quota exceeded ... spending cap" = billing cap, increase in GCP Billing > Budgets

## How to Switch Models

Pass the `model` parameter when calling `generate_image`:
```
generate_image(prompt="...", model="imagen-3.0-fast-generate-001")
```
If omitted, the default model ({default_model}) is used.
"""

PROVIDER_GUIDE = """# Provider Configuration Guide

## AI Studio (Default, Free)
- Set `GEMINI_PROVIDER=ai-studio`
- Get API key from https://aistudio.google.com/apikey (format: AIzaSy...)
- Set `GEMINI_API_KEY=your_key`
- Free tier with generous limits
- Models: `gemini-2.0-flash-exp-image-generation`, `gemini-2.0-flash-preview-image-generation`

## Vertex AI (GCP Credits, Higher Quality)
- Set `GEMINI_PROVIDER=vertex-ai`
- Requires: GCP project with billing enabled, Vertex AI API enabled
- Set `GCP_PROJECT_ID=your-project-id`
- Set `GCP_REGION=us-central1` (or your preferred region)
- Auth option 1: `GEMINI_API_KEY` (GCP API key, simpler)
- Auth option 2: ADC (`gcloud auth application-default login`, no API key needed)
- Models: `imagen-3.0-generate-002`, `imagen-3.0-fast-generate-001`, `gemini-2.0-flash-preview-image-generation`

## Troubleshooting

### Quota Errors (429)
| Error message contains | Cause | Fix |
|---|---|---|
| `online_prediction_requests_per_base_model` | Per-minute rate limit for that model | Switch to different model via `model` param, or wait 1 min |
| `spending cap` | Self-imposed billing limit | Increase cap in GCP Billing > Budgets & alerts |

### Auth Errors
| Error | Fix |
|---|---|
| `401 API keys not supported` | Use ADC: `gcloud auth application-default login`, remove GEMINI_API_KEY |
| `403 Permission denied` | Enable Vertex AI API in GCP Console, check API key restrictions |
| `Vertex AI auth failed` | Set GEMINI_API_KEY or configure ADC |

### Model Errors
| Error | Fix |
|---|---|
| `404 model not found` | Check model ID matches provider. AI Studio: gemini-* only. Vertex: both imagen-* and gemini-* |
| `User location is not supported` | Change GCP_REGION or try gemini-2.0-flash-exp-* (fewest restrictions) |
| `No image generated` | Use more descriptive prompt, avoid restricted content |
"""

# ── Server ───────────────────────────────────────────────────────────────────
server = Server("gemini-image-gen")


def _is_imagen_model(model: str) -> bool:
    """Imagen models use the predict API; Gemini models use generateContent."""
    return model.startswith("imagen")


def _get_vertex_access_token() -> str:
    """Get OAuth2 access token for Vertex AI using Application Default Credentials."""
    import google.auth
    import google.auth.transport.requests

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def _build_request_url_and_headers(model: str) -> tuple[str, dict[str, str]]:
    """Build the API URL and auth headers based on provider and model type."""
    if GEMINI_PROVIDER == "vertex-ai":
        if not GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID is required when GEMINI_PROVIDER=vertex-ai")

        action = "predict" if _is_imagen_model(model) else "generateContent"
        base_url = (
            f"https://{GCP_REGION}-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/"
            f"publishers/google/models/{model}:{action}"
        )

        if GEMINI_API_KEY:
            return f"{base_url}?key={GEMINI_API_KEY}", {}
        try:
            token = _get_vertex_access_token()
            return base_url, {"Authorization": f"Bearer {token}"}
        except Exception as e:
            raise ValueError(
                f"Vertex AI auth failed: {e}. "
                "Set GEMINI_API_KEY or configure ADC "
                "(gcloud auth application-default login)."
            ) from e
    else:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when GEMINI_PROVIDER=ai-studio")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model}:generateContent?key={GEMINI_API_KEY}"
        )
        return url, {}


def _build_request_body(prompt: str, model: str) -> dict[str, Any]:
    """Build the request body based on model type."""
    if _is_imagen_model(model):
        return {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1},
        }
    else:
        return {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }


def _parse_image_results(
    data: dict[str, Any], output_dir: Path, model: str
) -> list[types.TextContent | types.ImageContent]:
    """Parse API response and save images. Handles both Imagen and Gemini formats."""
    results: list[types.TextContent | types.ImageContent] = []
    prefix = "imagen" if _is_imagen_model(model) else "gemini"

    if _is_imagen_model(model):
        for pred in data.get("predictions", []):
            image_data = pred["bytesBase64Encoded"]
            mime = pred.get("mimeType", "image/png")
            ext = "jpg" if "jpeg" in mime else "png"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = output_dir / f"{prefix}_{timestamp}.{ext}"
            filepath.write_bytes(base64.b64decode(image_data))
            results.append(types.TextContent(type="text", text=f"Saved: {filepath}"))
            results.append(types.ImageContent(type="image", data=image_data, mimeType=mime))
    else:
        parts = data["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                image_data = part["inlineData"]["data"]
                mime = part["inlineData"].get("mimeType", "image/png")
                ext = "jpg" if "jpeg" in mime else "png"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = output_dir / f"{prefix}_{timestamp}.{ext}"
                filepath.write_bytes(base64.b64decode(image_data))
                results.append(types.TextContent(type="text", text=f"Saved: {filepath}"))
                results.append(types.ImageContent(type="image", data=image_data, mimeType=mime))
            elif "text" in part:
                results.append(types.TextContent(type="text", text=part["text"]))

    return results


def _available_models() -> list[str]:
    """Return model IDs available for the current provider."""
    return list(MODELS.get(GEMINI_PROVIDER, {}).keys())


# ── Resources ────────────────────────────────────────────────────────────────

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="guide://models",
            name="Model Selection Guide",
            description="Available models, pricing, quality comparison, and selection tips",
            mimeType="text/markdown",
        ),
        types.Resource(
            uri="guide://providers",
            name="Provider Configuration Guide",
            description="How to configure AI Studio and Vertex AI providers",
            mimeType="text/markdown",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: types.AnyUrl) -> str:
    uri_str = str(uri)
    if uri_str == "guide://models":
        return MODEL_GUIDE.format(provider=GEMINI_PROVIDER, default_model=DEFAULT_MODEL)
    elif uri_str == "guide://providers":
        return PROVIDER_GUIDE
    raise ValueError(f"Unknown resource: {uri_str}")


# ── Tools ────────────────────────────────────────────────────────────────────

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    models = _available_models()
    model_desc = ", ".join(f"`{m}`" for m in models) if models else "none configured"

    return [
        types.Tool(
            name="generate_image",
            description=(
                f"Generate an image from a text prompt using Google Gemini or Imagen. "
                f"Provider: {GEMINI_PROVIDER}. Default model: {DEFAULT_MODEL}. "
                f"Available models: {model_desc}. "
                f"Tip: if you hit a 429 quota error, retry with a different model."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt for image generation",
                    },
                    "model": {
                        "type": "string",
                        "description": (
                            f"Model to use (optional, default: {DEFAULT_MODEL}). "
                            f"Available: {', '.join(models)}"
                        ),
                        "enum": models if models else None,
                    },
                },
                "required": ["prompt"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        return [types.TextContent(type="text", text="Missing arguments")]

    if name != "generate_image":
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    prompt = arguments.get("prompt")
    if not prompt:
        return [types.TextContent(type="text", text="Missing prompt")]

    model = arguments.get("model", DEFAULT_MODEL)

    try:
        url, headers = _build_request_url_and_headers(model)
    except ValueError as e:
        return [types.TextContent(type="text", text=str(e))]

    request_body = _build_request_body(prompt, model)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=request_body, headers=headers, timeout=120.0)

        try:
            data = response.json()
        except Exception:
            return [types.TextContent(type="text", text=f"Failed to parse response (HTTP {response.status_code})")]

        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            hint = ""
            if response.status_code == 429:
                others = [m for m in _available_models() if m != model]
                if others:
                    hint = f" Tip: try switching to {others[0]}"
            return [types.TextContent(type="text", text=f"API error ({response.status_code}): {error_msg}{hint}")]

        try:
            output_dir = Path(IMAGE_OUTPUT_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            results = _parse_image_results(data, output_dir, model)
            if not results:
                return [types.TextContent(type="text", text="No image generated")]
            return results
        except (KeyError, IndexError) as e:
            return [types.TextContent(type="text", text=f"Failed to parse response: {e}")]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-image-gen",
                server_version="1.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
