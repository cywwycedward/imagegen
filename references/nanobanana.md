# Nano Banana (Base)

> **Model**: Gemini 2.5 Flash Image (`gemini-2.5-flash-image`)
> **Category**: Speed-optimized image generation
> **Max Resolution**: 1K (1024×1024)
> **Generation Speed**: 2–4 seconds

---

## Overview

Nano Banana is the base-tier model in the NanoBanana family, built on Google's Gemini 2.5 Flash Image architecture. It prioritizes speed over maximum quality, making it ideal for rapid prototyping, thumbnail generation, and high-volume batch workflows where sub-4-second latency matters more than 4K output.

---

## Key Features

| Feature | Value |
|---|---|
| Architecture | Gemini 2.5 Flash Image |
| Max Resolution | 1K (1024×1024) |
| Generation Speed | 2–4s |
| Modes | Text-to-Image, Image-to-Image |
| Number of Images | 1–4 per request |
| Watermark | SynthID (embedded) |
| Text Rendering | Basic |
| Thinking Mode | No |
| Image Grounding | No |
| Approximate Cost | ~$0.033 per 1K image |

### Supported Aspect Ratios (10 standard)

`1:1` · `9:16` · `16:9` · `3:4` · `4:3` · `3:2` · `2:3` · `5:4` · `4:5` · `21:9`

---

## API Reference (by Provider)

### Provider 1 — nanobananaapi.ai

**Endpoint**

```
POST https://api.nanobananaapi.ai/api/v1/nanobanana/generate
```

**Authentication**: Bearer token in `Authorization` header.

**Request Body** (JSON)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | ✅ | Text description of the image to generate |
| `type` | string | ✅ | `TEXTTOIAMGE` or `IMAGETOIAMGE` |
| `callBackUrl` | string | ✅ | Webhook URL for async result delivery |
| `numImages` | integer | ❌ | Number of images (1–4, default 1) |
| `imageUrls` | string[] | ❌ | Reference image URLs (for image-to-image) |
| `watermark` | boolean | ❌ | Enable/disable watermark |
| `image_size` | string | ❌ | Aspect ratio (e.g. `1:1`, `16:9`) |

**Example Request**

```bash
curl -X POST https://api.nanobananaapi.ai/api/v1/nanobanana/generate \
  -H "Authorization: Bearer $NB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic cityscape at sunset, cyberpunk style",
    "type": "TEXTTOIAMGE",
    "callBackUrl": "https://example.com/webhook",
    "numImages": 2,
    "image_size": "16:9"
  }'
```

**Response** — Returns a `taskId` for async polling.

**Poll for Result**

```
GET https://api.nanobananaapi.ai/api/v1/nanobanana/record-info?taskId={taskId}
```

**Task Status Codes**

| Code | Meaning |
|---|---|
| `0` | GENERATING |
| `1` | SUCCESS |
| `2` | CREATE_TASK_FAILED |
| `3` | GENERATE_FAILED |

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
| `model` | string | ✅ | `nano-banana` (10 credits) or `nano-banana-fast` (5 credits) |
| `mode` | string | ❌ | `text-to-image` (default) or `image-to-image` |
| `aspectRatio` | string | ❌ | Aspect ratio |
| `outputFormat` | string | ❌ | `png` |
| `isPublic` | boolean | ❌ | Make result publicly accessible |
| `imageFile` | file | ❌ | Reference image file (≤10MB, up to 8 files) |
| `imageUrl` | string | ❌ | Reference image URL |

**Credit Costs**

| Model Variant | Credits |
|---|---|
| `nano-banana-fast` | 5 |
| `nano-banana` | 10 |
| `nano-banana-vip` | 30 |

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
| `model` | string | ✅ | `gemini-2.5-flash-image` (2 credits) or `gemini-2.5-flash-image-hd` (5 credits) |
| `num` | integer | ❌ | Number of images |
| `image_size` | string | ❌ | Aspect ratio |
| `service_tier` | string | ❌ | `default` or `priority` |

**Response**: Synchronous — returns image URL directly.

---

### Provider 4 — imgeditor.co

**Endpoint**

```
POST https://imgeditor.co/api/v1/images/generate
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | ✅ | Image description |
| `model` | string | ✅ | `nano-banana` |
| `mode` | string | ❌ | `text` or `image` |
| `image_url` | string | ❌ | Reference image (for image mode) |
| `aspect_ratio` | string | ❌ | Aspect ratio |
| `resolution` | string | ❌ | `1K` |
| `num_images` | integer | ❌ | 1–4 |
| `output_format` | string | ❌ | Output format |

---

## Usage Tips

1. **Best for**: Rapid prototyping, thumbnail generation, batch workflows, social media content at standard resolution.
2. **Speed advantage**: At 2–4s per image, Nano Banana is the fastest model in the family — ideal for interactive workflows where users expect near-instant results.
3. **Cost efficiency**: At ~$0.033 per image, it's 2× cheaper than NB2 and 4× cheaper than Pro.
4. **Resolution limit**: Max 1K — if you need 2K/4K output, use Nano Banana 2 or Pro instead.
5. **Text rendering**: Basic quality only. For text-heavy images (posters, signage, UI mockups), prefer Pro or NB2.
6. **Image-to-image**: Supported across all providers. Supply reference images via `imageUrls`, `imageFile`, or `image_url` depending on provider.
7. **Batch mode**: Some providers offer batch pricing (up to 50% discount) for 12–24h delivery windows.
8. **SynthID**: All outputs include Google's SynthID watermark embedded in the image data.

---

## When to Use Nano Banana vs. Other Models

| Scenario | Recommended Model |
|---|---|
| Quick prototypes / drafts | ✅ Nano Banana |
| Thumbnails / avatars | ✅ Nano Banana |
| High-volume batch generation | ✅ Nano Banana |
| 4K output needed | ❌ Use NB2 or Pro |
| Typography / text in images | ❌ Use Pro or NB2 |
| Complex multi-character scenes | ❌ Use NB2 |
| Maximum aesthetic quality | ❌ Use Pro |
