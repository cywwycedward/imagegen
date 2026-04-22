# imagegen

CLI tool for generating and editing images using NanoBanana API providers.

## Features

- **Text-to-image generation** — generate images from text prompts
- **Image editing** — edit existing images with text instructions and reference images
- **Multi-turn chat** — interactive REPL for iterative image generation with session persistence
- **Multi-provider support** — configure multiple API providers and models via `provider.json`
- **Configurable options** — aspect ratio, image size, and search grounding per model

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (recommended)

## Installation

### As a global CLI tool (recommended)

```bash
uv tool install .
```

After installation, use `imagegen` directly:

```bash
imagegen --help
```

### Development mode

```bash
# Clone the project and sync dependencies
uv sync --group dev --group test

# Run via uv
uv run imagegen --help
```

## Configuration

imagegen uses `provider.json` to manage API providers and models. The config file is searched in this order:

| Priority | Path | Description |
|---|---|---|
| 1 (highest) | `<cwd>/.imagegen/provider.json` | Project-level config |
| 2 | `~/.config/imagegen/provider.json` | User-level global config |
| 3 (auto-created) | Same as above | Auto-created from built-in example on first run |

Initialize the config manually:

```bash
imagegen provider init
```

### Example `provider.json`

```json
{
    "providers": [
        {
            "name": "my-provider",
            "baseUrl": "https://api.example.com",
            "apiKey": "your-api-key",
            "models": {
                "gemini-2.5-flash-image": {
                    "name": "gemini-2.5-flash-image",
                    "options": {
                        "aspect_ratio": ["1:1", "16:9", "9:16"],
                        "image_size": ["1K"],
                        "grounding": []
                    }
                }
            }
        }
    ]
}
```

> **Security**: Do not commit API keys to version control. Add `.imagegen/provider.json` to `.gitignore`.

See [Configuration docs](docs/configuration.md) for full schema and field reference.

## Usage

### Generate an image

```bash
imagegen generate <prompt> <model_spec> <output> [options]
```

```bash
imagegen generate "a photorealistic cat sitting on a windowsill" \
    "my-provider/gemini-2.5-flash-image" \
    "cat.png"

# With options
imagegen generate "luxury perfume bottle with golden light" \
    "my-provider/gemini-3-pro-image-preview" \
    "perfume.png" \
    --aspect-ratio 16:9 \
    --image-size 2K \
    --grounding google-search
```

| Option | Description | Example |
|---|---|---|
| `--aspect-ratio` | Image aspect ratio | `--aspect-ratio 16:9` |
| `--image-size` | Image resolution | `--image-size 2K` |
| `--grounding` | Search-enhanced generation | `--grounding google-search` |

### Edit an image

```bash
imagegen edit <prompt> <model_spec> <output> --image <path> [options]
```

```bash
imagegen edit "change the background to a snowy mountain" \
    "my-provider/gemini-3-pro-image-preview" \
    "edited.png" \
    --image original.png

# Multiple reference images
imagegen edit "combine these two images into a collage" \
    "my-provider/gemini-3-pro-image-preview" \
    "collage.png" \
    --image photo1.png \
    --image photo2.jpg
```

### Multi-turn chat

```bash
imagegen chat <model_spec> [--output-dir <dir>] [--session <id>] [options]
```

```bash
# Start a new interactive session
imagegen chat "my-provider/gemini-3.1-flash-image-preview" --output-dir ./my_session
```

Generated images are saved as `turn_000.png`, `turn_001.png`, etc.

#### REPL commands

| Command | Description |
|---|---|
| `/image <path>` | Attach reference image(s) to current turn |
| `/aspect <ratio>` | Override aspect ratio for current turn |
| `/size <size>` | Override resolution for current turn |
| `/session` | Show current session ID |
| `/help` | Show help |
| `/quit` | Exit chat |

#### Resume a session

```bash
# List all sessions
imagegen provider sessions

# Resume by session ID
imagegen chat "my-provider/gemini-3.1-flash-image-preview" --session <session-id>
```

### Provider management

```bash
# List configured providers
imagegen provider list

# List all models with their providers
imagegen provider list --model

# List models with supported options
imagegen provider list --options

# Initialize config file
imagegen provider init

# List chat sessions
imagegen provider sessions
```

## Supported Models

| Model | Model Key | Max Resolution | Speed | Features |
|---|---|---|---|---|
| Nano Banana | `gemini-2.5-flash-image` | 1K | 2-4s | Base model, fastest |
| Nano Banana Pro | `gemini-3-pro-image-preview` | 4K | 10-20s | Thinking mode, best aesthetics |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | 4K | 4-8s | Image anchoring, ultra-wide ratios |

## Development

```bash
# Sync dev dependencies
uv sync --group dev --group test

# Lint
uv run ruff check src/

# Type check
uv run mypy src/

# Test
uv run pytest
```

See [Development docs](docs/development.md) for architecture, module details, and contribution guidelines.

## Documentation

- [Installation](docs/install.md)
- [Configuration](docs/configuration.md)
- [User Guide](docs/user-guide.md)
- [Development](docs/development.md)

## License

MIT
