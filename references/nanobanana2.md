# Nano Banana 2 (NB2)

> **Model**: Gemini 3.1 Flash Image Preview (`gemini-3.1-flash-image-preview`)
> **Category**: Pro-level quality at Flash speed
> **Max Resolution**: 4K (4096×4096)
> **Generation Speed**: 4–8 seconds
> **Released**: February 26, 2026

---

## Overview

Nano Banana 2 (NB2) is the latest model in the NanoBanana family, built on Google's Gemini 3.1 Flash architecture. It bridges the gap between the base model's speed and Pro's quality — delivering 4K output in 4–8 seconds with near-Pro aesthetic quality. NB2 introduces two breakthrough features: **Image Grounding** (web search for visual accuracy) and **ultra-wide aspect ratios** not available on other models. It's the recommended default for 90% of image generation tasks.

---

## Key Features

| Feature | Value |
|---|---|
| Architecture | Gemini 3.1 Flash Image Preview |
| Max Resolution | 4K (4096×4096) |
| Generation Speed | 4–8s |
| Modes | Text-to-Image, Image-to-Image |
| Number of Images | 1–4 per request |
| Watermark | SynthID (embedded) |
| Text Rendering | High / Professional |
| Thinking Mode | No |
| Image Grounding | ✅ Yes (web search for visual accuracy) |
| Text Accuracy | ~87% |
| Consistency | 5 characters + 14 objects across series |
| Approximate Cost | ~$0.067 per 1K image |

### Supported Aspect Ratios (14 — including ultra-wide)

**Standard** (shared with other models):
`1:1` · `9:16` · `16:9` · `3:4` · `4:3` · `3:2` · `2:3` · `5:4` · `4:5` · `21:9`

**NB2-exclusive ultra-wide/tall**:
`1:4` · `4:1` · `8:1` · `1:8`

### Resolution Options

`512` (512×512) · `1K` (1024×1024) · `2K` (2048×2048) · `4K` (4096×4096)

---

## Image Grounding — Unique to NB2

NB2's **Image Grounding** feature performs a web search before generation to ensure visual accuracy. When you reference real-world entities (landmarks, products, celebrities, species), the model grounds its output in actual web images rather than hallucinating details.

**How it works**:
1. Prompt analysis — model identifies real-world entities
2. Web image search — retrieves reference visuals
3. Grounded generation — synthesizes output informed by real references

**Best for**: Architectural rendering of real buildings, product visualizations, nature/wildlife accuracy, brand-consistent content.

---

## API Reference (by Provider)

### Provider 1 — nanobananaapi.ai

NB2 uses the same base endpoint as the original Nano Banana (the model selection happens server-side or may require a specific model parameter depending on the provider's current API version).

**Endpoint**

```
POST https://api.nanobananaapi.ai/api/v1/nanobanana/generate
```

**Authentication**: Bearer token in `Authorization` header.

Refer to the [base model docs](./nanobanana.md) for full parameter documentation. NB2-specific parameters (resolution, ultra-wide aspect ratios) may be available via provider updates.

---

### Provider 2 — nanobananapro.cloud

**Endpoint**

```
POST https://nanobananapro.cloud/api/v1/image/nano-banana
```

**Content-Type**: `multipart/form-data`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | ✅ | Image description |
| `model` | string | ✅ | `nano-banana-2` |
| `mode` | string | ❌ | `text-to-image` or `image-to-image` |
| `aspectRatio` | string | ❌ | Aspect ratio (including NB2-exclusive ratios) |
| `imageSize` | string | ❌ | `1K`, `2K`, or `4K` |
| `outputFormat` | string | ❌ | `png` |
| `isPublic` | boolean | ❌ | Public accessibility |
| `imageFile` | file | ❌ | Reference images (≤10MB each, up to 8) |
| `imageUrl` | string | ❌ | Reference image URL |

**Credit Costs (by resolution)**

| Resolution | Credits |
|---|---|
| 1K | 20 |
| 2K | 30 |
| 4K | 50 |

**Poll for Result**

```
POST https://nanobananapro.cloud/api/v1/image/nano-banana/result
Body: { "taskId": "..." }
```

---

### Provider 3 — nanobananaapi.dev

**Endpoint**

```
POST https://api.nanobananaapi.dev/v1/images/generate
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | ✅ | Image description |
| `model` | string | ✅ | See model variants below |
| `num` | integer | ❌ | Number of images |
| `image_size` | string | ❌ | Aspect ratio (including NB2-exclusive: `1:4`, `4:1`, `8:1`, `1:8`) |
| `service_tier` | string | ❌ | `default` or `priority` |

**Model Variants & Credits**

| Model | Resolution | Credits |
|---|---|---|
| `gemini-3.1-flash-image-preview-512` | 512px | 4 |
| `gemini-3.1-flash-image-preview` | 1K | 4 |
| `gemini-3.1-flash-image-preview-2k` | 2K | 6 |
| `gemini-3.1-flash-image-preview-4k` | 4K | 8 |

**Response**: Synchronous — returns image URL directly.

**Example Request**

```bash
curl -X POST https://api.nanobananaapi.dev/v1/images/generate \
  -H "Authorization: Bearer $NB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Panoramic view of the Golden Gate Bridge at sunset, ultra-wide cinematic composition, warm golden hour light",
    "model": "gemini-3.1-flash-image-preview-4k",
    "image_size": "21:9",
    "num": 1
  }'
```

---

### Provider 4 — imgeditor.co

**Endpoint**

```
POST https://imgeditor.co/api/v1/images/generate
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | ✅ | Image description |
| `model` | string | ✅ | `nano-banana-2` |
| `mode` | string | ❌ | `text` or `image` |
| `image_url` | string | ❌ | Reference image |
| `aspect_ratio` | string | ❌ | Aspect ratio |
| `resolution` | string | ❌ | `1K`, `2K`, or `4K` |
| `num_images` | integer | ❌ | 1–4 |
| `output_format` | string | ❌ | Output format |

---

## Usage Tips

1. **Default choice**: Use NB2 for 90% of image generation tasks. It offers the best balance of speed, quality, and cost.
2. **512px iteration strategy**: Generate at 512px resolution for fast prompt iteration (cheapest, fastest), then regenerate the best result at 4K for final output.
3. **Image Grounding**: When referencing real-world subjects (buildings, products, animals), NB2's grounding feature ensures higher accuracy than the other models.
4. **Character consistency**: NB2 can maintain visual consistency across a series — up to 5 characters and 14 objects. Use this for comics, storyboards, and product lineups.
5. **Ultra-wide formats**: NB2-exclusive ratios (`21:9`, `8:1`, `4:1`) are perfect for website hero banners, cinematic compositions, and panoramic scenes.
6. **Text rendering**: At ~87% text accuracy, NB2 handles text significantly better than Pro (~64%). For signage, watermarks, and UI text, NB2 is the safer bet.
7. **Cost-effective 4K**: At ~$0.067/image (1K), NB2 delivers 4K quality at half the price of Pro.
8. **Batch mode**: Some providers offer batch pricing with 50% discounts for 12–24h delivery windows — ideal for bulk content generation.
9. **SynthID**: All outputs include Google's SynthID watermark. This is non-removable and embedded in the image data.

---

## When to Use NB2 vs. Other Models

| Scenario | Recommended Model |
|---|---|
| General-purpose image generation | ✅ NB2 |
| 4K output at reasonable speed | ✅ NB2 |
| Real-world subject accuracy | ✅ NB2 (grounding) |
| Character/object consistency | ✅ NB2 |
| Ultra-wide / panoramic formats | ✅ NB2 (exclusive ratios) |
| Text in images | ✅ NB2 (87% accuracy) |
| Website banners / hero images | ✅ NB2 |
| Maximum aesthetic quality (luxury) | ❌ Use Pro |
| Deep reasoning about composition | ❌ Use Pro |
| Cheapest/fastest possible | ❌ Use Nano Banana base |
| Sub-2s latency needed | ❌ Use Nano Banana base |
