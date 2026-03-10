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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp-image-generation")
GEMINI_BASE = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", os.path.join(os.getcwd(), "output"))

server = Server("gemini-image-gen")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_image",
            description="Generate an image from a text prompt using Google Gemini",
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


async def make_gemini_request(
    client: httpx.AsyncClient,
    prompt: str,
) -> dict[str, Any]:
    """Make a request to the Gemini API for image generation."""
    url = f"{GEMINI_BASE}?key={GEMINI_API_KEY}"
    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    response = await client.post(url, json=request_body, timeout=120.0)
    try:
        data = response.json()
    except Exception:
        return {"error": f"Failed to parse response (HTTP {response.status_code})"}

    if response.status_code != 200:
        error_msg = data.get("error", {}).get("message", "Unknown error")
        return {"error": f"Gemini API error ({response.status_code}): {error_msg}"}

    return data


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        return [types.TextContent(type="text", text="Missing arguments")]

    if name == "generate_image":
        prompt = arguments.get("prompt")
        if not prompt:
            return [types.TextContent(type="text", text="Missing prompt")]

        async with httpx.AsyncClient() as client:
            response_data = await make_gemini_request(client=client, prompt=prompt)

            if "error" in response_data:
                return [types.TextContent(type="text", text=response_data["error"])]

            try:
                parts = response_data["candidates"][0]["content"]["parts"]
                results = []
                output_dir = Path(IMAGE_OUTPUT_DIR)
                output_dir.mkdir(parents=True, exist_ok=True)
                for part in parts:
                    if "inlineData" in part:
                        image_data = part["inlineData"]["data"]
                        mime = part["inlineData"].get("mimeType", "image/png")
                        ext = "jpg" if "jpeg" in mime else "png"
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"gemini_{timestamp}.{ext}"
                        filepath = output_dir / filename
                        filepath.write_bytes(base64.b64decode(image_data))
                        results.append(
                            types.TextContent(type="text", text=f"Saved: {filepath}")
                        )
                        results.append(
                            types.ImageContent(
                                type="image",
                                data=image_data,
                                mimeType=mime,
                            )
                        )
                    elif "text" in part:
                        results.append(
                            types.TextContent(type="text", text=part["text"])
                        )
                if not results:
                    return [types.TextContent(type="text", text="No image generated")]
                return results
            except (KeyError, IndexError) as e:
                return [
                    types.TextContent(type="text", text=f"Failed to parse response: {e}")
                ]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-image-gen",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
