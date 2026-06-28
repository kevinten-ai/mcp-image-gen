# CLAUDE.md — mcp-image-gen

## Project Overview

MCP server for AI image generation via Google Gemini and Imagen. Tools include `generate_image`, plus Vertex-only `edit_image` and `upscale_image`, with dynamic model selection per request.

## Architecture

- **Entry**: `src/image_gen/__init__.py` → `server.main()` via asyncio
- **Core**: `src/image_gen/server.py` — all logic in one file
- **Two API patterns**: Imagen models use Vertex AI Predict API, Gemini models use GenerateContent API. Routing is automatic based on model name prefix (`imagen*` → predict).

## Key Design Decisions

- `model` parameter is optional on the tool — defaults to `GEMINI_MODEL` env var
- Model catalog (`MODELS` dict) drives both tool schema `enum` and resource content
- MCP Resources (`guide://models`, `guide://providers`) provide AI assistants with selection guidance
- On 429 errors, the response auto-suggests switching to an alternative model

## Development

```bash
uv sync                    # basic deps
uv sync --extra vertex     # with Vertex AI / google-auth
uv run image-gen           # run server
```

## Common Pitfalls

- Imagen models are Vertex AI only — don't use `imagen-*` with the `ai-studio` provider
- New generation defaults should use GA Gemini image model IDs, not expired `*-preview` IDs
- Each model has **independent** API quota — 429 on one model doesn't mean all are blocked
- Two kinds of 429: "quota exceeded" (rate limit) vs "spending cap" (billing limit) — different fixes
- Vertex AI default QPM quota is very low (~5). Request increase via GCP Console.
