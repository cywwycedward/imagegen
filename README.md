# imagegen

CLI tool for generating images using NanoBanana API providers.

## Installation

```bash
uv tool install .
```

## Setup

Create a `provider.json` in your working directory:

```json
{
    "providers": [
        {
            "name": "my-provider",
            "baseUrl": "https://api.example.com",
            "apiKey": "",
            "models": {
                "gemini-2.5-flash-image": {
                    "name": "gemini-2.5-flash-image"
                }
            }
        }
    ]
}
```

## Usage

### List providers

```bash
imagegen provider list
imagegen provider list --model
```

### Generate an image

```bash
imagegen generate "a photorealistic cat" "my-provider/gemini-2.5-flash-image" "cat.png"
```

Arguments (all positional):
1. `prompt` — image generation prompt
2. `model` — format: `provider_name/model_key`
3. `output` — output file path

The API key is read from `provider.json` automatically.
