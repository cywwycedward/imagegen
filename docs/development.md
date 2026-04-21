# imagegen 开发文档

## 项目概览

`imagegen` 是一个基于 uv 构建的 Python CLI 工具，用于通过 NanoBanana API 提供商生成图像。它封装了 Google GenAI SDK，支持多提供商、多模型的统一调用接口。

- **版本**: 0.1.0
- **Python 要求**: >= 3.10
- **构建后端**: uv_build
- **CLI 框架**: click
- **入口点**: `imagegen = "imagegen.cli:main"`

---

## 目录结构

```
imagegen/
├── pyproject.toml              # 项目元数据、依赖、入口点、构建系统配置
├── README.md                   # 用户级使用文档
├── provider.json               # 提供商配置文件（API 端点、模型映射）
├── .gitignore                  # Git 忽略规则
├── uv.lock                     # uv 锁定文件（44 个包）
├── docs/                       # 开发文档目录
│   └── development.md          # 本文件
├── references/                 # NanoBanana 模型参考文档
│   ├── nanobanana.md           # 基础模型文档
│   ├── nanobanana-pro.md       # Pro 模型文档
│   ├── nanobanana2.md          # NB2 模型文档
│   ├── comparison.md           # 模型对比
│   └── nanobanana-cookbook-guide.md  # SDK 使用指南
├── src/
│   └── imagegen/
│       ├── __init__.py         # 包初始化 + 版本号
│       ├── __main__.py         # python -m imagegen 支持
│       ├── cli.py              # CLI 命令定义（click）
│       ├── provider.py         # 提供商配置加载与模型解析
│       └── generate.py         # 图像生成核心逻辑
└── tests/
    └── __init__.py             # 测试包初始化
```

---

## 技术栈

| 组件 | 技术选型 | 版本要求 | 用途 |
|------|---------|---------|------|
| 包管理 | uv | - | 项目脚手架、依赖管理、构建 |
| 构建后端 | uv_build | >=0.11.7, <0.12 | 纯 Python 包构建 |
| CLI | click | >=8.1.0 | 命令行接口 |
| API 客户端 | google-genai | >=1.0.0 | Google GenAI SDK 调用 |
| 表格输出 | rich | >=13.0.0 | 终端表格渲染 |
| 图像处理 | Pillow | >=10.0.0 | 图像数据处理 |

### 开发依赖

| 依赖组 | 包 | 用途 |
|--------|---|------|
| dev | ruff>=0.8.0, mypy>=1.13.0 | 代码检查与类型检查 |
| test | pytest>=8.0.0 | 单元测试 |

---

## 模块详解

### 1. `__init__.py` — 包初始化

```python
"""imagegen — CLI tool for generating images using NanoBanana API providers."""

__version__ = "0.1.0"
```

定义包级文档字符串和版本号。版本号与 `pyproject.toml` 中的 `version` 字段保持同步。

### 2. `__main__.py` — 模块入口

```python
from imagegen.cli import main

if __name__ == "__main__":
    main()
```

支持 `python -m imagegen` 方式运行。

### 3. `cli.py` — 命令行接口

#### 架构

使用 click 的命令组（Group）模式组织命令：

```
imagegen (Group)
├── provider (SubGroup)
│   └── list [--model]
└── generate <prompt> <model_spec> <api> <output>
```

#### `provider list` 命令

- **默认模式**: 显示所有已配置提供商名称（单列表格）
- **`--model` 标志**: 显示双列表格 — 模型名称 + 提供商名称
- **空配置提示**: 当 `provider.json` 中没有提供商时，输出黄色警告信息
- **渲染**: 使用 `rich.Table` 格式化输出

#### `generate` 命令

四个**位置参数**（全部必填）：

| 参数 | 含义 | 示例 |
|------|------|------|
| `prompt` | 图像生成提示词 | `"a photorealistic cat"` |
| `model_spec` | 提供商/模型名称 | `"my-provider/gemini-2.5-flash-image"` |
| `api` | API 密钥 | `"sk-abc123"` |
| `output` | 输出文件路径 | `"cat.png"` |

**设计决策**: 选择全位置参数而非命名参数（`--api`, `--output`），以简化快速调用体验。

### 4. `provider.py` — 提供商管理

#### 配置文件查找策略

采用**两级回退**策略查找 `provider.json`：

1. **当前工作目录 (CWD)** — 优先级最高，允许用户在不同项目中使用不同配置
2. **包内嵌资源** — 通过 `importlib.resources` 回退到随包分发的默认配置

```python
def _find_provider_file() -> Path:
    cwd_path = Path.cwd() / PROVIDER_FILENAME
    if cwd_path.is_file():
        return cwd_path

    package_ref = resources.files("imagegen").joinpath(PROVIDER_FILENAME)
    if package_ref.is_file():
        return Path(str(package_ref))

    print(f"Error: {PROVIDER_FILENAME} not found in CWD or package.", file=sys.stderr)
    sys.exit(1)
```

#### 关键函数

| 函数 | 签名 | 职责 |
|------|------|------|
| `_find_provider_file()` | `() -> Path` | 查找 provider.json 文件路径 |
| `load_providers()` | `() -> list[dict[str, Any]]` | 加载并返回提供商列表 |
| `resolve_model()` | `(provider_model: str) -> tuple[str, str, str]` | 解析 `provider/model` 格式，返回 `(base_url, model_display_name, model_key)` |

#### `resolve_model` 流程

```
输入: "my-provider/gemini-2.5-flash-image"
  │
  ├── split("/") → provider_name="my-provider", model_key="gemini-2.5-flash-image"
  │
  ├── 在 providers 中查找 name == provider_name
  │   └── 未找到 → stderr 输出可用提供商列表 + exit(1)
  │
  └── 在 provider.models 中查找 model_key
      ├── 找到 → 返回 (baseUrl, models[key]["name"], key)
      └── 未找到 → stderr 输出可用模型列表 + exit(1)
```

### 5. `generate.py` — 图像生成

#### API 调用流程

```
1. 创建 genai.Client（自定义 base_url + API key）
2. 调用 client.models.generate_content()
   - model: 来自 provider.json 的模型显示名
   - contents: 用户提示词
   - config: response_modalities=["IMAGE", "TEXT"]
3. 解析响应
   - 提取 candidates[0].content.parts
   - 遍历 parts 查找 inline_data（图像数据）
   - 支持 bytes 和 base64 字符串两种格式
4. 保存图像 → output 路径（自动创建父目录）
```

#### 错误处理策略

| 场景 | 处理方式 |
|------|---------|
| API 返回空响应 | stderr 输出 "empty response" + exit(1) |
| 响应中无图像但有文本 | stderr 输出文本内容（模型可能说明了无法生成的原因）+ exit(1) |
| 响应中无图像也无文本 | stderr 输出 "no image in response" + exit(1) |
| inline_data.data 为 None | 跳过该 part，继续检查下一个 |
| inline_data.data 为 base64 字符串 | 自动 decode 为 bytes |

#### null 安全提取

API 响应的多层嵌套结构需要逐层检查 null：

```python
candidate = response.candidates[0] if response.candidates else None
content = candidate.content if candidate else None
parts = content.parts if content else None
```

此模式避免了 `Optional` 类型的链式属性访问导致的类型错误（Pyright 严格模式下）。

---

## provider.json 配置规范

### Schema

```json
{
    "providers": [
        {
            "name": "provider-name",
            "baseUrl": "https://api.example.com",
            "apiKey": "",
            "models": {
                "model-key": {
                    "name": "Model Display Name"
                }
            }
        }
    ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `providers` | array | 是 | 提供商列表 |
| `providers[].name` | string | 是 | 提供商唯一标识，用于 CLI 中的 `provider_name/model_name` 格式 |
| `providers[].baseUrl` | string | 是 | API 基础 URL（传入 `genai.Client` 的 `http_options.base_url`） |
| `providers[].apiKey` | string | 否 | 可在此预配置 API key（当前 CLI 使用位置参数传入，此字段保留） |
| `providers[].models` | object | 是 | 模型映射，key 为小写无空格的模型标识 |
| `providers[].models[key].name` | string | 是 | 模型显示名称，传入 API 的 `model` 参数 |

### 模型命名规范

- **model key**（JSON 中的键）: 全小写，无空格，使用连字符分隔。例如 `gemini-2.5-flash-image`
- **model name**（`name` 字段值）: API 接受的模型标识符。例如 `gemini-2.5-flash-image`
- CLI 中的 `model_spec` 格式: `{provider.name}/{model_key}`

---

## 支持的模型

基于 NanoBanana 模型家族，当前支持以下模型：

| 模型 | 模型 ID | 最大分辨率 | 生成速度 | 单张成本 | 特性 |
|------|---------|-----------|---------|---------|------|
| Nano Banana | `gemini-2.5-flash-image` | 1K | 2-4s | ~$0.033 | 基础模型，速度最快 |
| Nano Banana Pro | `gemini-3-pro-image-preview` | 4K | 10-20s | ~$0.134 | 思考模式，美学最佳 |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | 4K | 4-8s | ~$0.067 | 图像锚定，超宽比例 |

### 可用提供商

| 提供商 | Base URL | 认证方式 |
|--------|----------|---------|
| nanobananaapi.ai | `https://api.nanobananaapi.ai` | Bearer token |
| nanobananapro.cloud | `https://nanobananapro.cloud` | API key |
| nanobananaapi.dev | `https://api.nanobananaapi.dev` | Bearer token |
| imgeditor.co | `https://imgeditor.co` | API key |

---

## Git 工作流

采用 **Git Flow** 分支模型：

```
main                  # 生产就绪版本
└── develop           # 开发主线
    └── feature/*     # 功能分支
```

### 分支说明

| 分支 | 用途 | 合并目标 |
|------|------|---------|
| `main` | 稳定发布版本 | - |
| `develop` | 开发集成分支 | main |
| `feature/initial-setup` | 初始项目搭建 | develop |

### 提交历史

```
main:    2cb0bd0  chore: initial commit with reference docs
develop: (从 main 创建)
feature/initial-setup: (从 develop 创建，当前工作分支)
```

---

## 构建与安装

### 开发环境

```bash
# 克隆项目后进入目录
cd uv_tools/imagegen

# 同步依赖（包括开发依赖）
uv sync --group dev --group test

# 运行 CLI
uv run imagegen --help
```

### 安装为全局工具

```bash
# 从项目目录安装
uv tool install .

# 之后可直接使用
imagegen --help
```

### 构建发行包

```bash
# 构建 sdist + wheel
uv build

# 验证构建（确保不依赖本地 sources）
uv build --no-sources
```

---

## 使用示例

### 查看提供商

```bash
# 列出所有提供商
imagegen provider list

# 列出所有模型及其提供商
imagegen provider list --model
```

### 生成图像

```bash
# 基本用法
imagegen generate "a photorealistic cat sitting on a windowsill" \
    "my-provider/gemini-2.5-flash-image" \
    "your-api-key" \
    "cat.png"

# 使用 Pro 模型（更高质量）
imagegen generate "luxury perfume bottle with golden light" \
    "my-provider/gemini-3-pro-image-preview" \
    "your-api-key" \
    "perfume.png"

# 使用 NB2 模型（平衡速度与质量）
imagegen generate "modern city skyline at sunset, ultra-wide" \
    "my-provider/gemini-3.1-flash-image-preview" \
    "your-api-key" \
    "skyline.png"
```

### 通过 python -m 运行

```bash
uv run python -m imagegen --help
uv run python -m imagegen generate "a cat" "prov/model" "key" "out.png"
```

---

## 开发过程记录

### 搭建顺序

1. 初始化 Git 仓库，创建 `main` → `develop` → `feature/initial-setup` 分支
2. 使用 `uv init --package --build-backend uv_build imagegen` 创建项目骨架
3. 配置 `pyproject.toml`（依赖、入口点、开发依赖组）
4. 创建 `provider.json` 模板
5. 实现 `src/imagegen/__init__.py` 和 `__main__.py`
6. 实现 `src/imagegen/provider.py`（提供商配置加载与模型解析）
7. 实现 `src/imagegen/generate.py`（API 调用与图像保存）
8. 实现 `src/imagegen/cli.py`（click CLI 命令定义）
9. 创建 `README.md`
10. 运行 `uv sync` 同步依赖并验证安装
11. LSP 诊断检查并修复类型错误
12. CLI 功能验证

### 遇到的问题与修复

#### 问题 1: `uv sync` 失败 — 缺少 `__init__.py`

uv_build 后端要求 `src/imagegen/__init__.py` 存在才能识别包结构。

**修复**: 创建 `__init__.py` 文件，包含文档字符串和版本号。

#### 问题 2: `uv sync` 失败 — 缺少 `README.md`

`pyproject.toml` 中配置了 `readme = "README.md"`，构建时会验证该文件存在。

**修复**: 创建 `README.md` 文件。

#### 问题 3: Pyright 类型错误 — Optional 成员访问

`generate.py` 中直接访问 `response.candidates[0].content.parts` 会导致 Pyright 报告 4 个类型错误，因为链路上的每个属性都可能为 `None`。

**修复**: 采用逐层 null 安全提取模式：

```python
# 之前（类型不安全）
parts = response.candidates[0].content.parts

# 之后（null 安全）
candidate = response.candidates[0] if response.candidates else None
content = candidate.content if candidate else None
parts = content.parts if content else None
```

### 设计决策记录

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| CLI 参数风格 | 全位置 vs 混合命名 | 全位置 | 匹配原始设计需求 |
| provider.json 查找 | CWD / 包内 / 两级回退 | 两级回退 | 灵活性 + 开箱即用 |
| 默认 provider.json 内容 | 预填提供商 / 空模板 | 空模板 | 用户自行填写，避免无效默认值 |
| API 无图像响应处理 | 静默 / 保存文本 / 打印+退出 | 打印文本到 stderr + exit(1) | 用户可看到模型的解释 |

---

## pyproject.toml 完整配置

```toml
[project]
name = "imagegen"
version = "0.1.0"
description = "CLI tool for generating images using NanoBanana API providers"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1.0",
    "google-genai>=1.0.0",
    "rich>=13.0.0",
    "Pillow>=10.0.0",
]

[project.scripts]
imagegen = "imagegen.cli:main"

[build-system]
requires = ["uv_build>=0.11.7,<0.12"]
build-backend = "uv_build"

[dependency-groups]
dev = ["ruff>=0.8.0", "mypy>=1.13.0"]
test = ["pytest>=8.0.0"]
```

---

## 扩展指南

### 添加新命令

在 `cli.py` 中通过 `@main.command()` 装饰器添加：

```python
@main.command()
@click.argument("input_image")
@click.argument("prompt")
@click.argument("model_spec")
@click.argument("api")
@click.argument("output")
def edit(input_image: str, prompt: str, model_spec: str, api: str, output: str) -> None:
    """Edit an existing image with a text prompt."""
    # 实现图像编辑逻辑
    pass
```

### 添加新提供商

在 `provider.json` 的 `providers` 数组中追加：

```json
{
    "name": "new-provider",
    "baseUrl": "https://api.new-provider.com",
    "apiKey": "",
    "models": {
        "model-id": {
            "name": "model-id"
        }
    }
}
```

### 添加 API 配置选项（如 aspect ratio）

1. 在 `generate` 命令中添加可选参数：

```python
@click.option("--aspect-ratio", default="1:1", help="Image aspect ratio")
```

2. 在 `generate_image()` 函数中将参数传入 `GenerateContentConfig`：

```python
config=types.GenerateContentConfig(
    response_modalities=["IMAGE", "TEXT"],
    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
)
```

---

## 测试

### 运行测试

```bash
uv run pytest
```

### 代码检查

```bash
# 格式检查
uv run ruff check src/

# 类型检查
uv run mypy src/
```

### 手动验证清单

- [x] `uv run imagegen --help` — 显示 `generate` 和 `provider` 命令
- [x] `uv run imagegen provider list` — 空配置时显示警告
- [x] `uv run imagegen provider list --model` — 空配置时显示警告
- [x] `uv run imagegen generate --help` — 显示 4 个位置参数
- [x] LSP 诊断 — 所有源文件 0 错误
