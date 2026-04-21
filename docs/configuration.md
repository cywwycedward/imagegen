# 配置说明

imagegen 通过 `provider.json` 配置文件管理 API 提供商和模型。本文档说明配置文件的位置、格式及各字段含义。

---

## 配置文件位置

imagegen 按以下优先级查找 `provider.json`：

| 优先级 | 路径 | 说明 |
|---|---|---|
| 1（最高） | `<当前工作目录>/.imagegen/provider.json` | 项目级配置，适合为不同项目设置不同提供商 |
| 2 | `~/.config/imagegen/provider.json` | 用户级全局配置（Linux/macOS）；Windows 下为 `%APPDATA%/imagegen/provider.json` |
| 3（自动创建） | 同上 | 若以上路径均不存在，首次运行时自动从包内示例文件复制到用户配置目录 |

### 初始化配置

可以通过以下命令手动初始化用户配置文件：

```bash
imagegen provider init
```

该命令会在用户配置目录下创建 `provider.json`（如果尚不存在），并输出文件路径。

---

## 配置文件格式

`provider.json` 采用 JSON 格式，完整 Schema 如下：

```json
{
    "providers": [
        {
            "name": "my-provider",
            "baseUrl": "https://api.example.com",
            "apiKey": "your-api-key-here",
            "models": {
                "model-key": {
                    "name": "Model Display Name",
                    "options": {
                        "aspect_ratio": ["1:1", "9:16", "16:9"],
                        "image_size": ["1K", "2K"],
                        "grounding": ["google-search"]
                    }
                }
            }
        }
    ]
}
```

---

## 字段说明

### 顶层

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `providers` | array | 是 | 提供商列表 |

### Provider 对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | 是 | 提供商唯一标识，用于 CLI 命令中的 `provider_name/model_key` 格式引用 |
| `baseUrl` | string | 是 | API 基础 URL，传入 GenAI SDK 的 `http_options.base_url` |
| `apiKey` | string | 否 | 此提供商的 API 密钥。留空则需要通过其他方式提供认证 |
| `models` | object | 是 | 模型映射表，key 为模型标识，value 为模型配置对象 |

### Model 对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | 是 | 模型显示名称，同时作为传入 API 的 `model` 参数 |
| `options` | object | 否 | 模型能力选项（缺省时使用默认值） |

### Options 对象

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `aspect_ratio` | string[] | `["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]` | 模型支持的宽高比列表 |
| `image_size` | string[] | `["1K"]` | 模型支持的分辨率列表 |
| `grounding` | string[] | `[]`（不支持） | 模型支持的搜索增强类型：`google-search`、`image-search` |

---

## 配置示例

### 单提供商、单模型

```json
{
    "providers": [
        {
            "name": "nano",
            "baseUrl": "https://api.nanobananaapi.ai",
            "apiKey": "sk-xxxxxxxxxxxxxxxx",
            "models": {
                "gemini-2.5-flash-image": {
                    "name": "gemini-2.5-flash-image"
                }
            }
        }
    ]
}
```

### 多提供商、多模型

```json
{
    "providers": [
        {
            "name": "nano-fast",
            "baseUrl": "https://api.nanobananaapi.ai",
            "apiKey": "sk-aaaaaa",
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
        },
        {
            "name": "nano-pro",
            "baseUrl": "https://nanobananapro.cloud",
            "apiKey": "sk-bbbbbb",
            "models": {
                "gemini-3-pro-image-preview": {
                    "name": "gemini-3-pro-image-preview",
                    "options": {
                        "aspect_ratio": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
                        "image_size": ["1K", "2K", "4K"],
                        "grounding": ["google-search", "image-search"]
                    }
                },
                "gemini-3.1-flash-image-preview": {
                    "name": "gemini-3.1-flash-image-preview",
                    "options": {
                        "image_size": ["1K", "2K", "4K"],
                        "grounding": ["google-search"]
                    }
                }
            }
        }
    ]
}
```

---

## 命名规范

- **provider name**: 全小写，使用连字符分隔，例如 `my-provider`
- **model key**（JSON 中的键）: 全小写，无空格，使用连字符分隔，例如 `gemini-2.5-flash-image`
- **model name**（`name` 字段值）: API 接受的模型标识符，通常与 model key 一致
- CLI 中引用格式：`provider_name/model_key`，例如 `nano-pro/gemini-3-pro-image-preview`

---

## 项目级配置 vs 用户级配置

| 场景 | 推荐方式 |
|---|---|
| 个人日常使用，所有项目共享同一套提供商 | 用户级配置（`~/.config/imagegen/provider.json`） |
| 不同项目使用不同提供商或 API 密钥 | 项目级配置（`<项目目录>/.imagegen/provider.json`） |
| 团队协作，提供商配置需要版本控制 | 项目级配置，但注意 **不要将 apiKey 提交到代码仓库** |

> **安全提醒**: `provider.json` 中包含 API 密钥，请确保该文件不会被提交到公开的代码仓库中。建议将 `.imagegen/provider.json` 加入 `.gitignore`。

---

## 验证配置

配置完成后，可通过以下命令验证：

```bash
# 列出所有已配置的提供商
imagegen provider list

# 列出所有已配置的模型及其所属提供商
imagegen provider list --model
```

如果 `provider.json` 中没有配置任何提供商，命令会输出黄色警告提示。
