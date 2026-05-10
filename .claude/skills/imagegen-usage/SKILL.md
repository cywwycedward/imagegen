---
name: imagegen-usage
description: Use when the user wants to generate, edit, or iteratively refine images. Triggers include requests like "generate an image", "draw", "create a picture", "edit this photo", "change the background", "make it wider", or any visual content creation request. Also use when the user asks about available models, providers, or image generation options.
---

# Image Generation with imagegen

## Overview

`imagegen` is a CLI tool that wraps NanoBanana API providers (and OpenAI-compatible backends) for image generation, editing, and multi-turn chat. You invoke it via `uv run imagegen` (dev) or `imagegen` (installed).

**Your job:** Translate the user's natural-language image request into the correct `imagegen` CLI command, choose the right model, and set appropriate options.

## When to Use

- User asks to generate/draw/create an image from text
- User asks to edit/modify an existing image
- User wants iterative image refinement (multi-turn chat)
- User asks which models or providers are available

## Quick Reference

### Commands

| Command | Purpose | Key Args |
|---|---|---|
| `generate <prompt> <model_spec> <output>` | Text → image | `--aspect-ratio`, `--image-size`, `--grounding` |
| `edit <prompt> <model_spec> <output> --image <path>` | Edit image | Same + `--image` (required, repeatable) |
| `chat <model_spec>` | Multi-turn REPL | `--output-dir`, `--session`, `--aspect-ratio` |
| `provider list [--model] [--options]` | List config | |
| `provider init` | Create config | |
| `provider sessions` | List chat sessions | |

### Model Selection

```
Need an image?
├── Speed critical / cheap prototype?     → gemini-2.5-flash-image (2-4s, ~$0.033)
├── Maximum aesthetic quality / luxury?   → gemini-3-pro-image-preview (10-20s, ~$0.134)
├── Ultra-wide ratio (8:1, 4:1)?          → gemini-3.1-flash-image-preview
├── Text accuracy matters most?           → gemini-3.1-flash-image-preview (87% accuracy)
├── Real-world subject accuracy?          → gemini-3.1-flash-image-preview + --grounding
└── General / default?                    → gemini-3.1-flash-image-preview (best balance)
```

### model_spec Format

Always `provider_name/model_key`. Example: `my-provider/gemini-2.5-flash-image`.

To discover available specs, run:
```bash
uv run imagegen provider list --model
```

### GenAI Backend Options

Parameter values vary by model. Query before use:
`uv run imagegen provider list --options`

Available parameters: `--aspect-ratio`, `--image-size`, `--grounding`

### OpenAI Backend Options

Parameter values vary by model. Query before use:
`uv run imagegen provider list --options`

Available parameters: `--size`, `--quality`, `--background`, `--style`,
`--output-format`, `--output-compression`, `--n`

## Intent-to-Command Translation

### Step 1: Identify the Task Type

| User Intent | Command |
|---|---|
| "Generate/draw/create an image of X" | `generate` |
| "Edit/modify/change this image" | `edit` |
| "Let's iterate on images" / "I want to refine step by step" | `chat` |
| "What models/providers do I have?" | `provider list --model` |

### Step 2: Choose a Model

Run `uv run imagegen provider list --model` first to see what's configured. Then pick based on the decision tree above.

### Step 3: Determine Options from Context

| User Says | Option to Set |
|---|---|
| "wide", "landscape", "cinematic", "banner" | `--aspect-ratio 16:9` or `21:9` |
| "portrait", "vertical", "phone wallpaper", "story" | `--aspect-ratio 9:16` |
| "square", "avatar", "icon" | `--aspect-ratio 1:1` |
| "poster" | `--aspect-ratio 2:3` or `3:4` |
| "high resolution", "high quality", "4K" | `--image-size 4K` |
| "quick", "draft", "prototype" | use flash model + `--image-size 1K` |
| "realistic", "accurate" (real subject) | `--grounding google-search` |
| "transparent background" (OpenAI) | `--background transparent` |

### Step 4: Construct the Command

```bash
# Generate
uv run imagegen generate "<prompt>" "<provider/model>" "<output_path>" [options]

# Edit
uv run imagegen edit "<prompt>" "<provider/model>" "<output_path>" --image <source> [options]

# Chat
uv run imagegen chat "<provider/model>" --output-dir <dir> [options]
```

## Common Patterns

### Generate with defaults
```bash
uv run imagegen generate "a serene mountain lake at sunset" \
    "my-provider/gemini-3.1-flash-image-preview" "lake.png"
```

### Generate high-quality wide image
```bash
uv run imagegen generate "luxury perfume bottle with golden light" \
    "my-provider/gemini-3-pro-image-preview" "perfume.png" \
    --aspect-ratio 16:9 --image-size 4K
```

### Edit an existing image
```bash
uv run imagegen edit "change the background to a snowy mountain" \
    "my-provider/gemini-3-pro-image-preview" "edited.png" \
    --image original.png
```

### Multi-image edit
```bash
uv run imagegen edit "combine into a collage" \
    "my-provider/gemini-3.1-flash-image-preview" "collage.png" \
    --image photo1.png --image photo2.jpg
```

### Interactive chat session
```bash
uv run imagegen chat "my-provider/gemini-3.1-flash-image-preview" \
    --output-dir ./session_output
```

Chat REPL commands: `/image <path>`, `/aspect <ratio>`, `/size <size>`, `/session`, `/help`, `/quit`

## Configuration

Config file: `provider.json` (searched in CWD `.imagegen/` → `~/.config/imagegen/` → auto-create).

Initialize: `uv run imagegen provider init`

API key: set in `provider.json` `apiKey` field, or via `IMAGEGEN_API_KEY` env var.

## Common Workflows

### Iterative refinement
generate → check with Read → adjust prompt → overwrite same file

### Batch with templates
Use `--template` to maintain style consistency across multiple images.
Check available templates: `imagegen template list`

### Edit mode
Edit existing images with `edit` command + `--image` flag.

## Model Capabilities (empirical, may change with model updates)

| Capability | gpt-image-2 | gemini-2.5-flash-image | gemini-3-pro-image-preview |
|---|---|---|---|
| Chinese understanding | Fair | Good | Best |
| Grid layout | Controllable | Mostly controllable | Good |
| SDF style | Good | Fair | Good |
| Speed | ~5s | ~3s | ~15s |

## Common Mistakes

| Mistake | Fix |
|---|---|
| Forgetting `provider/model` format | Always use `provider_name/model_key` (e.g., `nano/gemini-2.5-flash-image`) |
| Using genai option with openai backend | `--aspect-ratio` is genai-only; `--size` is openai-only |
| Missing `--image` on edit command | `--image` is required for `edit`; can repeat for multiple inputs |
| Not checking available models | Run `uv run imagegen provider list --model` first |
| Using chat with openai backend | Chat mode only supports genai backend |
| Output path without extension | Always include `.png` (or `.jpg`/`.webp` for OpenAI) |

## Error Recovery

All errors print to stderr and exit with code 1. Common errors:

- **"model must be in 'provider_name/model_name' format"** → fix the model_spec format
- **"provider 'X' not found"** → check `provider list` for valid names
- **"model 'X' not found"** → check `provider list --model`
- **"--aspect-ratio 'X' not supported"** → tool lists allowed values; pick from those
- **"empty response from API"** → retry, or try a different prompt
- **"chat is not supported for openai backend"** → use `generate` instead, or switch to genai model
