# Nano Banana Pro

> **Model**: Gemini 3 Pro Image Preview (`gemini-3-pro-image-preview`)
> **Category**: Premium quality with deep reasoning
> **Max Resolution**: 4K (4096×4096)
> **Generation Speed**: 10–20 seconds

---

## Overview

Nano Banana Pro is the premium tier of the NanoBanana family, built on Google's Gemini 3 Pro architecture with a unique "thinking mode" that reasons about composition, lighting, and aesthetics before generating. It produces the highest aesthetic quality in the lineup at the cost of slower generation times. Best suited for hero images, luxury brand visuals, complex typography, and any output where quality trumps speed.

---

## Key Features

| Feature | Value |
|---|---|
| Architecture | Gemini 3 Pro Image Preview |
| Max Resolution | 4K (4096×4096) |
| Generation Speed | 10–20s |
| Modes | Text-to-Image, Image-to-Image |
| Reference Images | Up to 8 |
| Watermark | SynthID (embedded) |
| Text Rendering | Exceptional |
| Thinking Mode | ✅ Yes (deep reasoning about composition) |
| Image Grounding | No |
| Text Accuracy | ~64% |
| Approximate Cost | ~$0.134 per 1K image |

### Supported Aspect Ratios (10 standard + auto)

`1:1` · `2:3` · `3:2` · `3:4` · `4:3` · `4:5` · `5:4` · `9:16` · `16:9` · `21:9` · `auto`

### Resolution Options

`1K` (1024×1024) · `2K` (2048×2048) · `4K` (4096×4096)

---

## API Reference (by Provider)

### Provider 1 — nanobananaapi.ai

**Endpoint**

```
POST https://api.nanobananaapi.ai/api/v1/nanobanana/generate-pro
```

**Authentication**: Bearer token in `Authorization` header.

**Request Body** (JSON)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | ✅ | Detailed text description |
| `callBackUrl` | string | ❌ | Webhook URL for async delivery |
| `imageUrls` | string[] | ❌ | Reference image URLs (up to 8) |
| `resolution` | string | ❌ | `1K`, `2K`, or `4K` |
| `aspectRatio` | string | ❌ | Aspect ratio (see list above, or `auto`) |

**Example Request**

```bash
curl -X POST https://api.nanobananaapi.ai/api/v1/nanobanana/generate-pro \
  -H "Authorization: Bearer $NB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Elegant perfume bottle on marble surface, dramatic studio lighting, luxury brand photography, gold accents, shallow depth of field",
    "resolution": "4K",
    "aspectRatio": "3:4",
    "callBackUrl": "https://example.com/webhook"
  }'
```

**Response** — Returns `taskId` for async polling.

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
| `model` | string | ✅ | `nano-banana-pro` (20 credits) or `nano-banana-pro-vip` (40 credits) |
| `mode` | string | ❌ | `text-to-image` or `image-to-image` |
| `aspectRatio` | string | ❌ | Aspect ratio |
| `imageSize` | string | ❌ | `1K`, `2K`, or `4K` |
| `outputFormat` | string | ❌ | `png` |
| `isPublic` | boolean | ❌ | Public accessibility |
| `imageFile` | file | ❌ | Reference images (≤10MB each, up to 8) |
| `imageUrl` | string | ❌ | Reference image URL |

**Credit Costs**

| Model Variant | Credits |
|---|---|
| `nano-banana-pro` | 20 |
| `nano-banana-pro-vip` | 40 |

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
| `model` | string | ✅ | `gemini-3-pro-image-preview` (8 credits at 1K), `gemini-3-pro-image-preview-2k` (8 credits), or `gemini-3-pro-image-preview-4k` (16 credits) |
| `num` | integer | ❌ | Number of images |
| `image_size` | string | ❌ | Aspect ratio |
| `service_tier` | string | ❌ | `default` or `priority` |

**Credit Costs**

| Model Variant | Credits |
|---|---|
| `gemini-3-pro-image-preview` (1K) | 8 |
| `gemini-3-pro-image-preview-2k` | 8 |
| `gemini-3-pro-image-preview-4k` | 16 |

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
| `model` | string | ✅ | `nano-banana-pro` |
| `mode` | string | ❌ | `text` or `image` |
| `image_url` | string | ❌ | Reference image |
| `aspect_ratio` | string | ❌ | Aspect ratio |
| `resolution` | string | ❌ | `1K`, `2K`, or `4K` |
| `num_images` | integer | ❌ | 1–4 |
| `output_format` | string | ❌ | Output format |

---

## Thinking Mode — How It Works

Nano Banana Pro's unique feature is its **thinking mode**: before generating pixels, the model internally reasons about:

- **Composition**: Subject placement, rule of thirds, visual hierarchy
- **Lighting**: Direction, color temperature, shadow depth
- **Aesthetics**: Color harmony, mood, style consistency
- **Typography**: Letter spacing, font weight, readability (when text is in the prompt)

This extra reasoning step is why generation takes 10–20s vs. 2–4s for the base model, but it produces measurably better results for complex scenes.

---

## Usage Tips

1. **Best for**: Hero images, luxury brand photography, editorial content, typography-heavy designs, complex multi-element compositions.
2. **Thinking mode advantage**: Pro excels at interpreting nuanced prompts — you can describe mood, atmosphere, and artistic style and it will reason about how to achieve them.
3. **Typography**: Pro has the best text rendering in the family. For signage, logos, and UI mockups with text, it's the top choice.
4. **Multi-reference workflow**: Supply up to 8 reference images for style transfer, character consistency, or scene composition guidance.
5. **Resolution strategy**: Start at 1K for prompt iteration (faster, same cost on some providers), then regenerate final at 4K.
6. **Cost awareness**: At ~$0.134 per 1K image (4× the base model), reserve Pro for final deliverables, not exploration.
7. **Speed expectation**: 10–20s is significantly slower. For interactive UIs, show a progress indicator or use the callback/webhook pattern.
8. **Complex scenes**: Pro handles intricate multi-subject scenes better than the base model due to its reasoning step.
9. **Luxury/fashion**: The aesthetic quality makes Pro ideal for product photography simulations, fashion editorials, and brand content.
10. **Text accuracy caveat**: Despite being the best at text *aesthetics*, Pro's measured text accuracy is ~64% — always verify text rendering in outputs.

---

## When to Use Pro vs. Other Models

| Scenario | Recommended Model |
|---|---|
| Hero images / key visuals | ✅ Pro |
| Typography / text-heavy designs | ✅ Pro |
| Luxury brand / editorial content | ✅ Pro |
| Complex artistic compositions | ✅ Pro |
| Style transfer with many references | ✅ Pro |
| Rapid prototyping | ❌ Use Nano Banana |
| Budget-sensitive batch work | ❌ Use Nano Banana |
| General-purpose with 4K | ❌ Use NB2 (faster, cheaper) |
| Character consistency across series | ❌ Use NB2 |
| Web-grounded visual accuracy | ❌ Use NB2 |
