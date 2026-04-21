# 使用指南

本文档介绍 imagegen 的全部功能和用法。阅读本文档前，请确保已完成 [安装](install.md) 和 [配置](configuration.md)。

---

## 概览

imagegen 提供以下核心功能：

| 命令 | 用途 |
|---|---|
| `imagegen generate` | 根据文本提示词生成图像 |
| `imagegen edit` | 基于参考图像进行编辑 |
| `imagegen chat` | 多轮交互式图像生成对话 |
| `imagegen provider list` | 查看已配置的提供商和模型 |
| `imagegen provider init` | 初始化配置文件 |
| `imagegen provider sessions` | 查看聊天会话历史 |

---

## 图像生成

### 基本用法

```bash
imagegen generate <prompt> <model_spec> <output>
```

- **prompt**: 图像生成提示词
- **model_spec**: 提供商/模型标识，格式为 `provider_name/model_key`
- **output**: 输出文件路径

```bash
imagegen generate "a photorealistic cat sitting on a windowsill" \
    "my-provider/gemini-2.5-flash-image" \
    "cat.png"
```

### 可选参数

| 选项 | 说明 | 示例 |
|---|---|---|
| `--aspect-ratio` | 图像宽高比 | `--aspect-ratio 16:9` |
| `--image-size` | 图像分辨率 | `--image-size 2K` |
| `--grounding` | 搜索增强模式 | `--grounding google-search` |

```bash
imagegen generate "luxury perfume bottle with golden light" \
    "my-provider/gemini-3-pro-image-preview" \
    "perfume.png" \
    --aspect-ratio 16:9 \
    --image-size 2K \
    --grounding google-search
```

> **注意**: 可用的 `--aspect-ratio`、`--image-size` 和 `--grounding` 值取决于所选模型在 `provider.json` 中的 `options` 配置。使用不支持的值时，工具会输出该模型允许的值列表并退出。

---

## 图像编辑

### 基本用法

```bash
imagegen edit <prompt> <model_spec> <output> --image <path>
```

- **prompt**: 图像编辑提示词
- **model_spec**: 提供商/模型标识
- **output**: 输出文件路径
- **--image**: 参考图像路径（必填，可多次指定）

```bash
imagegen edit "change the background to a snowy mountain" \
    "my-provider/gemini-3-pro-image-preview" \
    "edited.png" \
    --image original.png
```

### 多图输入

可以通过多次指定 `--image` 来提供多张参考图像：

```bash
imagegen edit "combine these two images into a collage" \
    "my-provider/gemini-3-pro-image-preview" \
    "collage.png" \
    --image photo1.png \
    --image photo2.jpg
```

### 可选参数

与 `generate` 命令相同，支持 `--aspect-ratio`、`--image-size` 和 `--grounding` 选项。

---

## 多轮对话

### 基本用法

```bash
imagegen chat <model_spec> [--output-dir <dir>] [--session <id>]
```

- **model_spec**: 提供商/模型标识
- **--output-dir**: 图像保存目录（默认为当前目录）
- **--session**: 恢复已有会话的 ID

```bash
# 启动新会话
imagegen chat "my-provider/gemini-3.1-flash-image-preview" --output-dir ./my_session
```

启动后进入交互式 REPL 环境，直接输入提示词即可生成图像。生成的图像按轮次自动保存为 `turn_000.png`、`turn_001.png` 等。

### 交互示例

```
> draw a cute puppy
[Image saved: ./my_session/turn_000.png]
> make it running in a park
[Image saved: ./my_session/turn_001.png]
> /quit
```

### REPL 指令

在对话中可以使用以下斜杠指令：

| 指令 | 说明 | 示例 |
|---|---|---|
| `/image <path>` | 附加一张或多张图片到当前轮次 | `/image ref.png` |
| `/aspect <ratio>` | 覆盖当前轮次的宽高比 | `/aspect 16:9` |
| `/size <size>` | 覆盖当前轮次的分辨率 | `/size 4K` |
| `/session` | 显示当前会话 ID | `/session` |
| `/help` | 显示帮助信息 | `/help` |
| `/quit` | 退出对话 | `/quit` |

### 恢复会话

每次对话都会自动保存为一个会话。可以通过会话 ID 恢复：

```bash
# 查看所有会话
imagegen provider sessions

# 恢复指定会话
imagegen chat "my-provider/gemini-3.1-flash-image-preview" --session abc123def456
```

### 可选参数

与 `generate` 命令相同，支持 `--aspect-ratio`、`--image-size` 和 `--grounding` 选项，这些选项会作为整个会话的默认值。在对话中可通过 `/aspect` 和 `/size` 指令按轮次覆盖。

---

## 提供商管理

### 查看提供商

```bash
# 列出所有已配置的提供商
imagegen provider list

# 列出所有模型及其所属提供商
imagegen provider list --model
```

### 初始化配置

```bash
# 在用户配置目录下创建默认 provider.json
imagegen provider init
```

### 查看会话历史

```bash
# 列出所有聊天会话
imagegen provider sessions
```

输出包含会话 ID、使用的模型、对话轮数和创建时间。

---

## 支持的模型

| 模型 | model key | 最大分辨率 | 生成速度 | 特性 |
|---|---|---|---|---|
| Nano Banana | `gemini-2.5-flash-image` | 1K | 2-4s | 基础模型，速度最快 |
| Nano Banana Pro | `gemini-3-pro-image-preview` | 4K | 10-20s | 思考模式，美学最佳 |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | 4K | 4-8s | 图像锚定，超宽比例 |

---

## 错误处理

imagegen 在遇到错误时会将信息输出到 stderr 并以非零退出码退出：

| 错误场景 | 提示信息 |
|---|---|
| `model_spec` 格式错误 | 提示正确格式 `provider_name/model_key` |
| 提供商不存在 | 列出所有可用提供商 |
| 模型不存在 | 列出该提供商下所有可用模型 |
| 选项值不支持 | 列出该模型允许的值 |
| API 返回空响应 | `Error: empty response from API.` |
| 响应中无图像 | 输出模型返回的文本内容（如有） |

---

## 使用技巧

1. **快速测试**: 使用 `gemini-2.5-flash-image` 模型进行快速原型测试，速度最快、成本最低。
2. **高质量输出**: 切换到 `gemini-3-pro-image-preview` 获取更高分辨率和更佳美学效果。
3. **迭代修改**: 使用 `chat` 命令进行多轮对话，在上一轮结果基础上持续调整。
4. **搜索增强**: 对于需要参考现实事物的提示词，使用 `--grounding google-search` 提升准确性。
5. **图像编辑**: 使用 `edit` 命令对已有图像进行局部修改，比重新生成更精确。
