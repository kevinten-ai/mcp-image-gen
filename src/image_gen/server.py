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

# Model to use for image generation
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp-image-generation")

# Output directory for saved images
IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", os.path.join(os.getcwd(), "output"))

# AI Studio: API key from https://aistudio.google.com/apikey
# Vertex AI: GCP API key or uses ADC (Application Default Credentials)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Vertex AI specific
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# ── Server ───────────────────────────────────────────────────────────────────
server = Server("gemini-image-gen")


def _is_imagen_model() -> bool:
    """Imagen models use the predict API; Gemini models use generateContent."""
    return GEMINI_MODEL.startswith("imagen")


def _get_vertex_access_token() -> str:
    """Get OAuth2 access token for Vertex AI using Application Default Credentials."""
    import google.auth
    import google.auth.transport.requests

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def _build_request_url_and_headers() -> tuple[str, dict[str, str]]:
    """Build the API URL and auth headers based on provider and model type."""
    if GEMINI_PROVIDER == "vertex-ai":
        if not GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID is required when GEMINI_PROVIDER=vertex-ai")

        # Imagen models use predict endpoint; Gemini models use generateContent
        action = "predict" if _is_imagen_model() else "generateContent"
        base_url = (
            f"https://{GCP_REGION}-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/"
            f"publishers/google/models/{GEMINI_MODEL}:{action}"
        )

        # Prefer API key (simpler); fall back to OAuth2/ADC
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
        # AI Studio
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when GEMINI_PROVIDER=ai-studio")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        )
        return url, {}


def _build_request_body(prompt: str) -> dict[str, Any]:
    """Build the request body based on model type."""
    if _is_imagen_model():
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
    data: dict[str, Any], output_dir: Path
) -> list[types.TextContent | types.ImageContent]:
    """Parse API response and save images. Handles both Imagen and Gemini formats."""
    results: list[types.TextContent | types.ImageContent] = []

    if _is_imagen_model():
        # Imagen: {"predictions": [{"bytesBase64Encoded": "...", "mimeType": "..."}]}
        for pred in data.get("predictions", []):
            image_data = pred["bytesBase64Encoded"]
            mime = pred.get("mimeType", "image/png")
            ext = "jpg" if "jpeg" in mime else "png"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = output_dir / f"imagen_{timestamp}.{ext}"
            filepath.write_bytes(base64.b64decode(image_data))
            results.append(types.TextContent(type="text", text=f"Saved: {filepath}"))
            results.append(types.ImageContent(type="image", data=image_data, mimeType=mime))
    else:
        # Gemini: {"candidates": [{"content": {"parts": [...]}}]}
        parts = data["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                image_data = part["inlineData"]["data"]
                mime = part["inlineData"].get("mimeType", "image/png")
                ext = "jpg" if "jpeg" in mime else "png"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = output_dir / f"gemini_{timestamp}.{ext}"
                filepath.write_bytes(base64.b64decode(image_data))
                results.append(types.TextContent(type="text", text=f"Saved: {filepath}"))
                results.append(types.ImageContent(type="image", data=image_data, mimeType=mime))
            elif "text" in part:
                results.append(types.TextContent(type="text", text=part["text"]))

    return results


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_image",
            description="Generate an image from a text prompt using Google Gemini or Imagen",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt for image generation",
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

    try:
        url, headers = _build_request_url_and_headers()
    except ValueError as e:
        return [types.TextContent(type="text", text=str(e))]

    request_body = _build_request_body(prompt)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=request_body, headers=headers, timeout=120.0)

        try:
            data = response.json()
        except Exception:
            return [types.TextContent(type="text", text=f"Failed to parse response (HTTP {response.status_code})")]

        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            return [types.TextContent(type="text", text=f"API error ({response.status_code}): {error_msg}")]

        try:
            output_dir = Path(IMAGE_OUTPUT_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            results = _parse_image_results(data, output_dir)
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
                server_version="1.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
