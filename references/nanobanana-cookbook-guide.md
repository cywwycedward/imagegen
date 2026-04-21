# Nano Banana 系列模型调用实践指南

> 基于 [Google Gemini Cookbook](https://github.com/google-gemini/cookbook) 官方 Notebook
> 源文件：[`quickstarts/Get_Started_Nano_Banana.ipynb`](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_Started_Nano_Banana.ipynb)

---

## 目录

- [模型概览](#模型概览)
- [环境准备](#环境准备)
- [基础用法：生成图片](#基础用法生成图片)
- [图片编辑（Image-to-Image）](#图片编辑image-to-image)
- [控制宽高比](#控制宽高比)
- [生成多张图片 / 故事模式](#生成多张图片--故事模式)
- [Chat 多轮对话模式（推荐）](#chat-多轮对话模式推荐)
- [多图融合](#多图融合)
- [Gemini 3 系列高级功能](#gemini-3-系列高级功能)
  - [Thinking 思维模式](#thinking-思维模式)
  - [Search Grounding 搜索锚定](#search-grounding-搜索锚定)
  - [Image Grounding 图片搜索锚定（NB2 独有）](#image-grounding-图片搜索锚定nb2-独有)
  - [高分辨率输出（2K / 4K）](#高分辨率输出2k--4k)
  - [低延迟 512px 模式（NB2 独有）](#低延迟-512px-模式nb2-独有)
  - [多语言图文生成与翻译](#多语言图文生成与翻译)
  - [14 张参考图融合](#14-张参考图融合)
- [实用 Prompt 示例集](#实用-prompt-示例集)
- [与 Imagen 的区别](#与-imagen-的区别)
- [三款模型对比速查](#三款模型对比速查)
- [参考链接](#参考链接)

---

## 模型概览

Nano Banana 是 Google Gemini 的**原生图像生成**能力系列，共有 3 款模型：

| 模型 | Model ID | 代号 | 定位 |
|---|---|---|---|
| **Nano Banana** | `gemini-2.5-flash-image` | nano-banana | 便宜快速，默认首选 |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | nano-banana-pro | 支持 Thinking + Google Search Grounding，擅长图表/排版 |
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | nano-banana-2 | 速度与质量最佳平衡，支持 Search Grounding + Thinking + 512px + Image Grounding |

### 核心能力

- 文本到图像（Text-to-Image）
- 图像到图像 / 图像编辑（Image-to-Image）
- 多轮对话中迭代修改图像
- 多图融合（最多 3 张 / 6 张高保真 / 14 张 Pro&NB2）
- 文字渲染（Pro 和 NB2 表现更优）
- 搜索锚定（Pro 和 NB2）
- 多分辨率输出：512px / 1K / 2K / 4K（Pro 和 NB2）

---

## 环境准备

### 1. 安装 SDK

```bash
pip install -U "google-genai>=1.65.0"  # NB2 支持需要此最低版本
```

### 2. 设置 API Key

```python
# Colab 环境
from google.colab import userdata
GOOGLE_API_KEY = userdata.get('GOOGLE_API_KEY')

# 本地环境
import os
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
```

### 3. 初始化客户端

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=GOOGLE_API_KEY)
```

### 4. 选择模型

```python
MODEL_ID = "gemini-2.5-flash-image"  # 默认选择
# 或
MODEL_ID = "gemini-3.1-flash-image-preview"  # NB2
# 或
MODEL_ID = "gemini-3-pro-image-preview"  # Pro
```

### 5. 通用工具函数

```python
from IPython.display import display, Markdown, HTML

def display_response(response):
    """遍历响应的所有 part，显示文本或图片"""
    for part in response.parts:
        if part.thought:  # 跳过思维过程
            continue
        if part.text:
            display(Markdown(part.text))
        elif image := part.as_image():
            image.show()

    # 显示搜索锚定来源（如果有）
    if (response.candidates
        and response.candidates[0].grounding_metadata
        and response.candidates[0].grounding_metadata.search_entry_point):
        display(HTML(
            response.candidates[0].grounding_metadata.search_entry_point.rendered_content
        ))


def save_image(response, path):
    """保存响应中的图片（如有多张，仅保存最后一张）"""
    for part in response.parts:
        if image := part.as_image():
            image.save(path)
```

---

## 基础用法：生成图片

使用方式与任何 Gemini 模型完全一致，调用 `generate_content` 即可：

```python
prompt = "Create a photorealistic image of a siamese cat with a green left eye and a blue right one"

response = client.models.generate_content(
    model=MODEL_ID,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image']
        # 如果只要图片不要文字：response_modalities=['Image']
    )
)

display_response(response)
save_image(response, 'cat.png')
```

> **Tips**:
> - `response_modalities` 是可选的，对图像模型来说默认就包含图像输出
> - 设为 `['Image']` 可以只返回图片、不返回文本描述

---

## 图片编辑（Image-to-Image）

在 `contents` 中同时传入文本提示和参考图片：

```python
import PIL

response = client.models.generate_content(
    model=MODEL_ID,
    contents=[
        "Create a side view picture of that cat, in a tropical forest, eating a banana",
        PIL.Image.open('cat.png')
    ]
)

display_response(response)
save_image(response, 'cat_tropical.png')
```

---

## 控制宽高比

通过 `image_config.aspect_ratio` 指定输出比例。Token 数量与宽高比无关，只取决于模型和分辨率。

```python
response = client.models.generate_content(
    model=MODEL_ID,
    contents=[
        "The cat in a fancy restaurant",
        PIL.Image.open('cat_tropical.png')
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
        )
    )
)
```

### 支持的宽高比

| 比例 | Nano Banana | Pro | NB2 |
|---|---|---|---|
| `1:1` `9:16` `16:9` `3:4` `4:3` `3:2` `2:3` `5:4` `4:5` `21:9` | ✅ | ✅ | ✅ |
| `auto` | ❌ | ✅ | ❌ |
| `1:4` `4:1` `8:1` `1:8` | ❌ | ❌ | ✅ |

---

## 生成多张图片 / 故事模式

直接在 prompt 中要求多张图片输出：

```python
prompt = "Show me how to bake macarons with images"
# 或更复杂的叙事：
# prompt = "Create a beautifully entertaining 8 part story with 8 images..."

response = client.models.generate_content(
    model=MODEL_ID,
    contents=prompt,
)

display_response(response)
```

> 模型会在一次响应中输出多张图片，并穿插文字说明。

---

## Chat 多轮对话模式（推荐）

多轮对话是编辑和迭代图像的**推荐方式**，模型会记住上下文：

```python
chat = client.chats.create(model=MODEL_ID)

# 第 1 轮：创建图像
response = chat.send_message("create a plastic toy fox figurine in a kid's bedroom")
display_response(response)
save_image(response, "figurine.png")

# 第 2 轮：修改图像
response = chat.send_message("Add a blue planet on the figurine's helmet")
display_response(response)

# 第 3 轮：改变场景
response = chat.send_message("Move that figurine on a beach")
display_response(response)

# 第 4 轮：改变动作
response = chat.send_message("Now it should be base-jumping from a spaceship")
display_response(response)

# 可在特定轮次指定宽高比
response = chat.send_message(
    "Bring it back to the bedroom",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9"),
    ),
)
```

---

## 多图融合

可以传入多张图片进行融合创作：

- **Nano Banana**：最多 3 张（6 张高保真模式）
- **Pro / NB2**：最多 14 张

```python
response = client.models.generate_content(
    model=MODEL_ID,
    contents=[
        "Create a picture of that figurine riding that cat in a fantasy world.",
        PIL.Image.open('cat.png'),
        PIL.Image.open('figurine.png')
    ],
)
```

---

## Gemini 3 系列高级功能

以下功能仅适用于 **Nano Banana Pro** (`gemini-3-pro-image-preview`) 和 **Nano Banana 2** (`gemini-3.1-flash-image-preview`)。

```python
GEMINI3_MODEL_ID = "gemini-3.1-flash-image-preview"
# 或
GEMINI3_MODEL_ID = "gemini-3-pro-image-preview"
```

### Thinking 思维模式

Gemini 3 模型在生成图片前会"思考"，对复杂推理任务特别有用。NB2 还引入了**Thinking Levels**，可以控制推理深度。

```python
response = client.models.generate_content(
    model=GEMINI3_MODEL_ID,
    contents="Create an unusual but realistic image that might go viral",
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
        ),
        thinking_config=types.ThinkingConfig(
            thinking_level="High",      # "Minimal" 或 "High"（仅 NB2）
            include_thoughts=True       # 设为 True 可查看思维过程
        )
    )
)
```

#### 查看思维过程

```python
for part in response.parts:
    if part.thought:
        if part.text:
            display(Markdown(part.text))
```

#### Thought Signatures

Gemini 3 模型的输出包含 `thought_signature`，用于多轮对话时帮助模型记住之前的思考过程和搜索结果：

```python
for part in response.parts:
    if part.thought_signature:
        print(part.thought_signature)
```

### Search Grounding 搜索锚定

让模型使用 Google Search 获取实时信息后生成图片（Pro 和 NB2 均支持）：

```python
response = client.models.generate_content(
    model=GEMINI3_MODEL_ID,
    contents="Visualize the current weather forecast for the next 5 days in Tokyo as a clean, modern weather chart",
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image'],  # 注意：搜索锚定目前不支持 Image-only 模式
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
        ),
        tools=[{"google_search": {}}]
    )
)

# 查看搜索来源
display(HTML(
    response.candidates[0].grounding_metadata.search_entry_point.rendered_content
))
```

> **注意**：使用搜索锚定时，`response_modalities` 必须包含 `'Text'`，不能只设为 `['Image']`。

### Image Grounding 图片搜索锚定（NB2 独有）

NB2 可以搜索 Google 图片来锚定生成结果。适合需要真实世界参考的场景（地标、特定动物种类、品牌物品等）：

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="A detailed painting of a Timareta Thelxione butterfly resting on a flower",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        tools=[
            types.Tool(google_search=types.GoogleSearch(
                search_types=types.SearchTypes(
                    web_search=types.WebSearch(),
                    image_search=types.ImageSearch()  # NB2 独有的图片搜索锚定
                )
            ))
        ]
    )
)
```

### 高分辨率输出（2K / 4K）

Pro 和 NB2 支持 1K / 2K / 4K 分辨率。NB2 还支持 512px。

```python
response = client.models.generate_content(
    model=GEMINI3_MODEL_ID,
    contents="A photo of an oak tree experiencing every season",
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image'],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="4K"  # "512px" / "1K" / "2K" / "4K"
        )
    )
)
```

> Token 数量与宽高比无关，仅取决于模型和分辨率。详见 [定价文档](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-image-preview)。

### 低延迟 512px 模式（NB2 独有）

NB2 引入 512px 分辨率模式，针对速度和低延迟场景优化：

```python
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="A cute pixel art robot",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            image_size="512px"
        )
    )
)
```

> **Tip**: 用 512px 分辨率 + Batch API 批量生成大量图片（成本最低），然后挑选最佳结果用更高分辨率重新生成。

### 多语言图文生成与翻译

Pro 和 NB2 支持多语言图文生成。可以在 Chat 模式中生成信息图后直接翻译：

```python
chat = client.chats.create(
    model=GEMINI3_MODEL_ID,
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image'],
        tools=[{"google_search": {}}]
    )
)

# 生成西班牙语信息图
response = chat.send_message(
    "Make an infographic explaining Einstein's theory of General Relativity for a 6th grader in Spanish",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9"),
    )
)
save_image(response, "relativity_ES.png")

# 翻译为日语，保持其他内容不变
response = chat.send_message(
    "Translate this infographic in Japanese, keeping everything else the same",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(image_size="2K"),
    )
)
save_image(response, "relativity_JP.png")
```

### 14 张参考图融合

Pro 和 NB2 支持最多传入 14 张参考图：

```python
response = client.models.generate_content(
    model=GEMINI3_MODEL_ID,
    contents=[
        "Create a marketing photoshoot of those items from my daughter's bedroom.",
        PIL.Image.open('sweets.png'),
        PIL.Image.open('car.png'),
        PIL.Image.open('rabbit.png'),
        PIL.Image.open('spartan.png'),
        PIL.Image.open('cactus.png'),
        PIL.Image.open('cards.png'),
    ],
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image'],
        image_config=types.ImageConfig(
            aspect_ratio="5:4",
            image_size="1K"
        ),
    )
)
```

---

## 实用 Prompt 示例集

以下是 Cookbook 中收录的高质量 Prompt 模板：

### 1. 复古风格转换（80 年代）

```python
prompt = "Create a photograph of the person in this image as if they were living in the 1980s. The photograph should capture the distinct fashion, hairstyles, and overall atmosphere of that time period."
response = client.models.generate_content(
    model=MODEL_ID,
    contents=[prompt, PIL.Image.open('portrait.png')]
)
```

### 2. 手办/小模型生成

```python
prompt = """create a 1/7 scale commercialized figurine of the characters in the picture, 
in a realistic style, in a real environment. The figurine is placed on a computer desk. 
The figurine has a round transparent acrylic base, with no text on the base. 
The content on the computer screen is a 3D modeling process of this figurine. 
Next to the computer screen is a toy packaging box, designed in a style reminiscent 
of high-quality collectible figures, printed with original artwork."""
```

### 3. 贴纸生成（Pop Art 风格）

```python
prompt = """Create a single sticker in the distinct Pop Art style. 
Bold, thick black outlines. Vibrant primary and secondary colors in flat blocks. 
Visible Ben-Day dots or halftone patterns. Include stylized text within speech bubbles. 
The user's face from the uploaded photo must be the main character, 
with an interesting dye-cut outline shape."""
```

### 4. 黑白照片上色

```python
prompt = "Restore and colorize this image from 1932."
response = client.models.generate_content(
    model=MODEL_ID,
    contents=[prompt, PIL.Image.open('old_photo.jpg')]
)
```

### 5. 地图视角转换

```python
prompt = "Show me what we see from the red arrow"
response = client.models.generate_content(
    model=MODEL_ID,
    contents=[prompt, PIL.Image.open('map_screenshot.png')]
)
```

### 6. 等距建筑风格

```python
prompt = "Take this location and make the landmark an isometric image (building only), in the style of the game Theme Park."
```

### 7. 搜索锚定 + 人物可视化（Pro / NB2）

```python
prompt = "Search the web then generate an image of isometric perspective, detailed pixel art that shows the career of [人物名]"
response = client.models.generate_content(
    model=GEMINI3_MODEL_ID,
    contents=[prompt],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9"),
        tools=[{"google_search": {}}]
    )
)
```

### 8. 文字密集型信息图（Pro / NB2）

```python
prompt = "Show me an infographic about how sonnets work, using a sonnet about bananas written in it, along with a lengthy literary analysis of the poem. good vintage aesthetics"
```

### 9. Meme 风格再创作 + Chat（Pro / NB2）

```python
chat = client.chats.create(
    model=GEMINI3_MODEL_ID,
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9"),
        tools=[{"google_search": {}}]
    )
)

response = chat.send_message("There's a famous meme about a dog in a house on fire saying 'this is fine', can you do a papier maché version of it?")
response = chat.send_message("Now do a new version with generic building blocks")
response = chat.send_message("What about a crochet version?")
```

### 10. 精灵图（Sprite Sheet）生成（Pro / NB2）

```python
prompt = "Sprite sheet of a jumping illustration, 3x3 grid, white background, sequence, frame by frame animation, square aspect ratio. Follow the structure of the attached reference image exactly."
response = client.models.generate_content(
    model=GEMINI3_MODEL_ID,
    contents=[prompt, PIL.Image.open("grid_3x3_1024.png")],
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="1:1"),
    )
)
```

**将精灵图转为 GIF 动画**：

```python
import PIL
from IPython.display import display, Image

image = PIL.Image.open('sprites.png')
total_width, total_height = image.size
frame_width = (total_width - 2) // 3
frame_height = (total_height - 2) // 3

frames = []
for row in range(3):
    for col in range(3):
        left = col * (frame_width + 1)
        upper = row * (frame_height + 1)
        frames.append(image.crop((left, upper, left + frame_width, upper + frame_height)))

frames[0].save('sprite.gif', save_all=True, append_images=frames[1:], duration=200, loop=0)
```

---

## 与 Imagen 的区别

| 特性 | Nano Banana 系列 | Imagen |
|---|---|---|
| 调用方式 | `generate_content`（统一 API） | 专用 Imagen API |
| 交互模式 | 支持多轮对话迭代 | 单次生成 |
| 多模态 | 支持文本+图片混合输入输出 | 仅文本到图片 |
| 图片编辑 | 通过对话自然描述修改 | 通过 mask 等参数控制 |
| 适用场景 | 需要迭代修改、多轮对话的场景 | 需要精确控制的一次性生成 |

> 详见 [Imagen 入门 Notebook](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_imagen.ipynb) 和 [官方文档](https://ai.google.dev/gemini-api/docs/image-generation#choose-a-model)

---

## 三款模型对比速查

| 维度 | Nano Banana | Nano Banana Pro | Nano Banana 2 |
|---|---|---|---|
| **Model ID** | `gemini-2.5-flash-image` | `gemini-3-pro-image-preview` | `gemini-3.1-flash-image-preview` |
| **SDK 最低版本** | `google-genai>=1.0` | `google-genai>=1.0` | `google-genai>=1.65.0` |
| **最大分辨率** | 1K | 4K | 4K |
| **512px 模式** | ❌ | ❌ | ✅ |
| **生成速度** | 2-4s | 10-20s | 4-8s |
| **Thinking** | ❌ | ✅ | ✅ (含 Thinking Levels) |
| **Search Grounding** | ❌ | ✅ | ✅ |
| **Image Grounding** | ❌ | ❌ | ✅ |
| **最大参考图数** | 3 (6 高保真) | 14 | 14 |
| **文字渲染** | 基础 | 优秀 (美感最佳) | 优秀 (~87% 准确率) |
| **宽高比** | 10 种标准 | 10 种标准 + auto | 14 种 (含超宽) |
| **推荐场景** | 快速原型、批量生成 | 奢华品质、复杂构图 | 90% 通用任务的默认选择 |

### 模型选择决策树

```
需要生成图片？
│
├── 要求极快速度 (< 4s)？ → Nano Banana
│
├── 追求最高美学品质？ → Nano Banana Pro
│
├── 文字密集设计？
│   ├── 美感优先？ → Pro
│   └── 准确率优先？ → NB2 (87%)
│
├── 需要真实世界参考？ → NB2 (Image Grounding)
│
├── 需要超宽比例 (8:1, 1:8)？ → NB2
│
├── 角色/物体一致性？ → NB2
│
└── 其他场景？ → NB2 (默认推荐)
```

---

## 参考链接

- **官方 Notebook**: [Get_Started_Nano_Banana.ipynb](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_Started_Nano_Banana.ipynb)
- **Colab 直接运行**: [在 Colab 中打开](https://colab.research.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Get_Started_Nano_Banana.ipynb)
- **官方文档**: [Gemini Image Generation](https://ai.google.dev/gemini-api/docs/image-generation)
- **模型选择指南**: [Choose a Model](https://ai.google.dev/gemini-api/docs/image-generation#choose-a-model)
- **定价**: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- **Python SDK**: [google-genai](https://github.com/googleapis/python-genai)
- **AI Studio 示例应用**: [Nano-banana Apps](https://aistudio.google.com/apps?source=showcase&showcaseTag=nano-banana)
- **Imagen 入门**: [Get_started_imagen.ipynb](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_imagen.ipynb)
- **Gemini Cookbook 主页**: [google-gemini/cookbook](https://github.com/google-gemini/cookbook)
