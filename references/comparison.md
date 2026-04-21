# NanoBanana Model Comparison

> Quick reference for choosing between Nano Banana, Nano Banana Pro, and Nano Banana 2.

---

## At a Glance

| Feature | Nano Banana | Nano Banana Pro | Nano Banana 2 |
|---|---|---|---|
| **Underlying Model** | Gemini 2.5 Flash Image | Gemini 3 Pro Image Preview | Gemini 3.1 Flash Image Preview |
| **Model ID** | `gemini-2.5-flash-image` | `gemini-3-pro-image-preview` | `gemini-3.1-flash-image-preview` |
| **Max Resolution** | 1K | 4K | 4K |
| **Generation Speed** | 2–4s | 10–20s | 4–8s |
| **Aspect Ratios** | 10 standard | 10 standard + auto | 14 (incl. ultra-wide) |
| **Thinking Mode** | ❌ | ✅ | ❌ |
| **Image Grounding** | ❌ | ❌ | ✅ |
| **Text Rendering** | Basic | Exceptional | High / Professional |
| **Text Accuracy** | — | ~64% | ~87% |
| **Consistency** | — | — | 5 chars + 14 objects |
| **Cost (1K image)** | ~$0.033 | ~$0.134 | ~$0.067 |
| **Release** | Original | Second gen | Feb 26, 2026 |

---

## Decision Tree

```
Need an image?
│
├── Speed is critical (< 4s)?
│   └── ✅ Nano Banana
│
├── Maximum aesthetic quality / luxury brand?
│   └── ✅ Nano Banana Pro
│
├── Complex typography / text-heavy design?
│   ├── Aesthetic perfection matters most? → ✅ Pro
│   └── Accuracy matters most? → ✅ NB2 (87% vs 64%)
│
├── Real-world subject accuracy needed?
│   └── ✅ NB2 (Image Grounding)
│
├── Ultra-wide format (8:1, 4:1, 1:4, 1:8)?
│   └── ✅ NB2 (exclusive ratios)
│
├── Character/object consistency across series?
│   └── ✅ NB2
│
└── Everything else?
    └── ✅ NB2 (default recommendation)
```

---

## Cost Comparison

### Per-Image Cost (approximate)

| Resolution | Nano Banana | Pro | NB2 |
|---|---|---|---|
| 512px | — | — | ~$0.034 |
| 1K | ~$0.033 | ~$0.134 | ~$0.067 |
| 2K | — | ~$0.134 | ~$0.100 |
| 4K | — | ~$0.268 | ~$0.134 |

### Credits by Provider

**nanobananaapi.dev**

| Model | Credits |
|---|---|
| `gemini-2.5-flash-image` | 2 |
| `gemini-2.5-flash-image-hd` | 5 |
| `gemini-3-pro-image-preview` (1K) | 8 |
| `gemini-3-pro-image-preview-2k` | 8 |
| `gemini-3-pro-image-preview-4k` | 16 |
| `gemini-3.1-flash-image-preview-512` | 4 |
| `gemini-3.1-flash-image-preview` (1K) | 4 |
| `gemini-3.1-flash-image-preview-2k` | 6 |
| `gemini-3.1-flash-image-preview-4k` | 8 |

**nanobananapro.cloud**

| Model | Credits |
|---|---|
| `nano-banana-fast` | 5 |
| `nano-banana` | 10 |
| `nano-banana-pro` | 20 |
| `nano-banana-vip` | 30 |
| `nano-banana-pro-vip` | 40 |
| `nano-banana-2` (1K) | 20 |
| `nano-banana-2` (2K) | 30 |
| `nano-banana-2` (4K) | 50 |

---

## Aspect Ratio Support

| Ratio | Nano Banana | Pro | NB2 |
|---|---|---|---|
| 1:1 | ✅ | ✅ | ✅ |
| 9:16 | ✅ | ✅ | ✅ |
| 16:9 | ✅ | ✅ | ✅ |
| 3:4 | ✅ | ✅ | ✅ |
| 4:3 | ✅ | ✅ | ✅ |
| 3:2 | ✅ | ✅ | ✅ |
| 2:3 | ✅ | ✅ | ✅ |
| 5:4 | ✅ | ✅ | ✅ |
| 4:5 | ✅ | ✅ | ✅ |
| 21:9 | ✅ | ✅ | ✅ |
| auto | ❌ | ✅ | ❌ |
| 1:4 | ❌ | ❌ | ✅ |
| 4:1 | ❌ | ❌ | ✅ |
| 8:1 | ❌ | ❌ | ✅ |
| 1:8 | ❌ | ❌ | ✅ |

---

## API Providers Summary

| Provider | Base URL | Auth | Response Type | Supports All 3 Models |
|---|---|---|---|---|
| nanobananaapi.ai | `api.nanobananaapi.ai` | Bearer token | Async (taskId + polling) | ✅ |
| nanobananapro.cloud | `nanobananapro.cloud` | API key | Async (taskId + polling) | ✅ |
| nanobananaapi.dev | `api.nanobananaapi.dev` | Bearer token | Synchronous | ✅ |
| imgeditor.co | `imgeditor.co` | API key | Varies | ✅ |

---

## Common Usage Patterns

### 1. Rapid Iteration → Final Output

```
1. Generate 4 variants at 512px with NB2          → Fast, cheap
2. Pick best composition
3. Regenerate at 4K with NB2 (or Pro for luxury)   → Final quality
```

### 2. Text-Heavy Design

```
1. Generate with NB2 (87% text accuracy)           → Usually correct
2. If text is wrong, retry with Pro (better aesthetics) or re-prompt
3. Always verify text rendering in output
```

### 3. Brand-Consistent Series

```
1. Use NB2 for character/object consistency         → 5 chars + 14 objects
2. Supply reference images (up to 8) for style matching
3. Maintain same aspect ratio across series
```

### 4. Real-World Subjects

```
1. Use NB2 with Image Grounding                    → Web-verified accuracy
2. Be specific about the subject in the prompt
3. Cross-check output against reference photos
```

---

## Detailed Reference Docs

- [Nano Banana (Base)](./nanobanana.md)
- [Nano Banana Pro](./nanobanana-pro.md)
- [Nano Banana 2 (NB2)](./nanobanana2.md)
