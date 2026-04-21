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
│       ├── generate.py         # 图像生成与编辑核心逻辑
│       ├── chat.py             # 多轮对话 REPL 模式
│       ├── session.py          # 会话管理（创建/加载/保存/列表）
│       └── provider.json.example  # 提供商配置示例文件
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
│   ├── init
│   ├── list [--model]
│   └── sessions
├── generate <prompt> <model_spec> <output> [--aspect-ratio] [--image-size] [--grounding]
├── edit <prompt> <model_spec> <output> --image <path>... [--aspect-ratio] [--image-size] [--grounding]
└── chat <model_spec> [--output-dir] [--session] [--aspect-ratio] [--image-size] [--grounding]
```

#### `provider list` 命令

- **默认模式**: 显示所有已配置提供商名称（单列表格）
- **`--model` 标志**: 显示双列表格 — 模型名称 + 提供商名称
- **空配置提示**: 当 `provider.json` 中没有提供商时，输出黄色警告信息
- **渲染**: 使用 `rich.Table` 格式化输出

#### `provider sessions` 命令

- 功能：列出所有聊天会话历史
- 显示信息：会话 ID、所用模型、对话轮数、创建时间

#### `generate` 命令

三个**位置参数**（全部必填）：

| 参数/选项 | 类型 | 必填 | 含义 | 示例 |
|-----------|------|------|------|------|
| `prompt` | 位置参数 | 是 | 图像生成提示词 | `"a photorealistic cat"` |
| `model_spec` | 位置参数 | 是 | 提供商/模型名称 | `"my-provider/gemini-2.5-flash-image"` |
| `output` | 位置参数 | 是 | 输出文件路径 | `"cat.png"` |
| `--aspect-ratio` | 选项 | 否 | 图像宽高比 | `--aspect-ratio 16:9` |
| `--image-size` | 选项 | 否 | 图像分辨率 | `--image-size 2K` |
| `--grounding` | 选项 | 否 | 搜索增强 | `--grounding google-search` |

**设计决策**: 移除 `api` 位置参数，改由 `provider.json` 统一管理 API key。核心输入保持全位置参数设计，以简化快速调用体验。

#### `edit` 命令

支持使用参考图像对生成结果进行编辑控制。三个位置参数与 `generate` 相同：

| 参数/选项 | 类型 | 必填 | 含义 | 示例 |
|-----------|------|------|------|------|
| `prompt` | 位置参数 | 是 | 图像编辑提示词 | `"change background to winter"` |
| `model_spec` | 位置参数 | 是 | 提供商/模型名称 | `"my-provider/gemini-3-pro-image-preview"` |
| `output` | 位置参数 | 是 | 输出文件路径 | `"edited.png"` |
| `--image` | 选项 | 是(多次) | 参考图像路径 | `--image src1.png --image src2.jpg` |
| `--aspect-ratio` | 选项 | 否 | 图像宽高比 | `--aspect-ratio 1:1` |
| `--image-size` | 选项 | 否 | 图像分辨率 | `--image-size 4K` |
| `--grounding` | 选项 | 否 | 搜索增强 | `--grounding image-search` |

内部流程：使用 Pillow 打开指定的多张图像，将其与提示词拼接后 `[prompt, *images]` 一同发送至 API。

#### `chat` 命令

多轮交互式图像生成，支持上下文保持。

- **1 个位置参数**：`model_spec`（必填）
- **选项**：`--output-dir` (默认当前目录)、`--session` (用于恢复历史会话 ID)、`--aspect-ratio`、`--image-size`、`--grounding`

**特性：**
- 交互式 REPL 循环，支持斜杠指令 (`/image`, `/aspect`, `/size`, `/session`, `/help`, `/quit`)。
- 会话自动保存到 `~/.config/imagegen/sessions/{id}/`，支持后续使用 `--session` 恢复。
- 对话中可通过斜杠指令动态覆盖当前轮次的宽高比或分辨率选项。
- 生成的图像自动按轮次保存为 `turn_001.png`, `turn_002.png` 格式。

### 4. `provider.py` — 提供商管理

#### 配置文件查找策略

采用**三级回退**策略查找 `provider.json`：

1. **CWD/.imagegen/provider.json** — 当前工作目录的项目级配置，优先级最高
2. **~/.config/imagegen/provider.json** — 用户级全局配置（通过 `user_config_dir()` 确定具体平台路径）
3. **包内嵌示例文件** — 作为兜底策略，若不存在配置则将 `provider.json.example` 复制到用户级目录

```python
def _find_provider_file() -> Path:
    # Level 1 — 项目级配置
    local_path = Path.cwd() / ".imagegen" / PROVIDER_FILENAME
    if local_path.is_file():
        return local_path

    # Level 2 — 用户级配置
    user_path = user_config_dir() / PROVIDER_FILENAME
    if user_path.is_file():
        return user_path

    # Level 3 — 首次运行：复制示例文件到用户配置目录
    user_path = ensure_user_config()
    return user_path
```

#### 关键函数

| 函数 | 签名 | 职责 |
|------|------|------|
| `user_config_dir()` | `() -> Path` | 返回平台相关的用户配置目录 |
| `_find_provider_file()` | `() -> Path` | 三级回退查找 provider.json |
| `ensure_user_config()` | `() -> Path` | 首次运行时复制示例配置 |
| `load_providers()` | `() -> list[dict[str, Any]]` | 加载提供商列表 |
| `resolve_model()` | `(provider_model: str) -> tuple[str, str, str, str, dict[str, Any]]` | 解析 provider/model，返回 (base_url, model_key, display_name, api_key, options) |
| `_get_model_options()` | `(model_info: dict) -> dict[str, Any]` | 提取模型选项，缺失时应用默认值 |
| `validate_option()` | `(value, allowed, option_name, model_key) -> None` | 验证选项值，无效时 exit(1) |

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

| 函数 | 签名 | 职责 |
|------|------|------|
| `_build_grounding_tools()` | `(grounding: str \| None) -> list[types.Tool] \| None` | 构建搜索增强工具列表 |
| `build_image_config()` | `(aspect_ratio, image_size) -> types.ImageConfig \| None` | 构建图像配置 |
| `build_config()` | `(aspect_ratio, image_size, grounding) -> GenerateContentConfig` | 构建完整生成配置 |
| `_extract_image()` | `(response, output) -> None` | 从响应中提取图像并保存 |
| `generate_image()` | `(..., aspect_ratio, image_size, grounding) -> None` | 文本到图像生成 |
| `edit_image()` | `(prompt, images, ..., aspect_ratio, image_size, grounding) -> None` | 图像编辑（多图输入） |

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

### 6. `chat.py` — 多轮对话

多轮交互式环境的实现。

| 函数 | 签名 | 职责 |
|------|------|------|
| `_parse_input(raw)` | `(str) -> tuple[str, list[Path]]` | 解析用户输入，提取 `/image` 指令附加的图像路径 |
| `run_chat()` | `(base_url, model_name, api_key, output_dir, ...)` | REPL 主循环，处理指令与对话交互 |

#### 交互式指令集

| 指令 | 用法示例 | 说明 |
|------|----------|------|
| `/image` | `/image ./ref.png` | 附加一张或多张参考图片到当前轮次提示词中 |
| `/aspect` | `/aspect 16:9` | 覆盖当前轮次的宽高比选项 |
| `/size` | `/size 4K` | 覆盖当前轮次的分辨率选项 |
| `/session` | `/session` | 打印当前会话 ID |
| `/help` | `/help` | 打印帮助信息 |
| `/quit` | `/quit` | 退出 REPL |

#### 执行流程

```
1. 通过 session.py 创建或加载现有会话历史
2. 构造 API client.chats
3. 进入 REPL 循环 (读取输入 → 解析指令 → _parse_input)
4. 将当前输入（连同可能附加的图像与选项覆盖）发送至 chat.send_message
5. 从响应中调用 generate._extract_image() 落盘保存图像
6. 调用 session.save_turn() 记录此轮次
```

### 7. `session.py` — 会话管理

负责持久化管理多轮对话上下文。

| 函数 | 签名 | 职责 |
|------|------|------|
| `_sessions_dir()` | `() -> Path` | 确定全局会话存储根目录（位于用户配置目录中） |
| `create_session()` | `(model_spec: str) -> tuple[str, Path]` | 创建带有唯一 ID 的新会话目录并初始化元数据 |
| `load_session()` | `(session_id: str) -> tuple[Path, dict[str, Any]]` | 加载指定的已有会话 |
| `save_turn()` | `(session_dir, turn_index, prompt, image_path, input_images)` | 落盘单轮对话数据（提示词、引用的图片路径、生成的图片路径） |
| `list_sessions()` | `() -> list[dict]` | 扫描并列出所有会话基本信息 |

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
                    "name": "Model Display Name",
                    "options": {
                        "aspect_ratio": ["1:1", "9:16", "16:9"],
                        "image_size": ["1K"],
                        "grounding": []
                    }
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
| `providers[].name` | string | 是 | 提供商唯一标识，用于 CLI 中的 `provider_name/model_key` 格式 |
| `providers[].baseUrl` | string | 是 | API 基础 URL（传入 `genai.Client` 的 `http_options.base_url`） |
| `providers[].apiKey` | string | 否 | 此提供商专用的 API key |
| `providers[].models` | object | 是 | 模型映射，key 为小写无空格的模型标识 |
| `providers[].models[key].name` | string | 是 | 模型显示名称，传入 API 的 `model` 参数 |
| `providers[].models[key].options` | object | 否 | 模型能力选项（宽高比、分辨率、搜索增强） |
| `providers[].models[key].options.aspect_ratio` | string[] | 否 | 支持的宽高比列表，默认支持 10 种标准比例 |
| `providers[].models[key].options.image_size` | string[] | 否 | 支持的分辨率列表，默认 `["1K"]` |
| `providers[].models[key].options.grounding` | string[] | 否 | 支持的搜索增强类型：`google-search`, `image-search` |

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

采用 **Git Flow** 分支模型。

### 分支模型概览

```
main                  # 生产就绪版本，只能从其他分支合并，不能直接修改。
└── develop           # 主开发分支，包含所有要发布到下一个release的代码，该分支主要合并其他分支内容。
    └── feature/*     # 功能分支，基于develop分支创建，开发新功能，待开发完毕合并至develop分支。
    └── release/*     # 发布分支，基于develop分支创建，该分支专为测试—发布新的版本而开辟，待发布完成后合并到develop和main分支去。
    └── hotfix/*      # 修复分支，基于main分支创建，待修复完成后合并到develop和main分支去，同时在main上打一个tag。
```

### 分支管理规范

#### 分支命名

| 分支类型 | 命名格式 | 示例 | 来源分支 | 合并目标 |
|----------|---------|------|---------|---------|
| 主分支 | `main` | `main` | — | — |
| 开发分支 | `develop` | `develop` | `main`（初始化时） | — |
| 功能分支 | `feature/<简短描述>` | `feature/add-aspect-ratio` | `develop` | `develop` |
| 发布分支 | `release/<版本号>` | `release/1.2.0` | `develop` | `develop` + `main` |
| 修复分支 | `hotfix/<简短描述>` | `hotfix/fix-base64-decode` | `main` | `develop` + `main` |

**命名规则：**

- 全部使用**小写字母**，单词间用**连字符** `-` 分隔。
- 分支名应简洁，清晰描述意图，**不超过 4 个单词**。
- 禁止使用中文、空格、下划线。
- 功能分支如关联 Issue，可包含 Issue 编号：`feature/42-add-aspect-ratio`。

#### 分支生命周期

**feature 分支：**

```bash
# 1. 从 develop 创建
git checkout develop
git pull origin develop
git checkout -b feature/add-aspect-ratio

# 2. 开发过程中保持与 develop 同步
git fetch origin
git rebase origin/develop

# 3. 开发完成后合并回 develop（见合并规范）
# 4. 合并完成后删除 feature 分支
git branch -d feature/add-aspect-ratio
git push origin --delete feature/add-aspect-ratio
```

**release 分支：**

```bash
# 1. 从 develop 创建
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# 2. 仅允许 bug 修复、文档更新、版本号变更
#    禁止在 release 分支添加新功能

# 3. 发布就绪后：
#    - 合并到 main，打 tag
#    - 合并回 develop（同步修复内容）
#    - 删除 release 分支
```

**hotfix 分支：**

```bash
# 1. 从 main 创建
git checkout main
git pull origin main
git checkout -b hotfix/fix-base64-decode

# 2. 修复问题，提交

# 3. 修复完成后：
#    - 合并到 main，打 tag（patch 版本号 +1）
#    - 合并回 develop（同步修复内容）
#    - 如果当前有活跃的 release 分支，则合并到 release 分支而非 develop
#    - 删除 hotfix 分支
```

**分支保护规则（推荐）：**

- `main` 和 `develop` 启用分支保护，禁止直接 push。
- 所有合并通过 Pull Request 进行，需至少 1 人 review。
- PR 合并前需通过 CI 检查（lint + test + type check）。

---

### Commit Message 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

#### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **Header**（必填）：`<type>(<scope>): <subject>`，不超过 72 个字符。
- **Body**（可选）：详细说明变更动机与实现，与 header 之间空一行。每行不超过 72 个字符。
- **Footer**（可选）：Breaking Changes 声明或 Issue 引用。

#### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(cli): add --aspect-ratio option` |
| `fix` | Bug 修复 | `fix(generate): handle base64 string in response` |
| `docs` | 仅文档变更 | `docs: update development guide` |
| `style` | 代码格式（不影响逻辑） | `style: fix ruff formatting warnings` |
| `refactor` | 重构（不改功能，不修 bug） | `refactor(provider): extract config loader` |
| `test` | 测试相关 | `test(provider): add resolve_model tests` |
| `chore` | 构建/工具/依赖变更 | `chore: bump google-genai to 1.2.0` |
| `perf` | 性能优化 | `perf(generate): reduce image decode overhead` |
| `ci` | CI/CD 配置 | `ci: add GitHub Actions workflow` |
| `build` | 构建系统变更 | `build: migrate to uv_build 0.12` |

#### Scope（可选）

Scope 标注受影响的模块，使用源码模块名称：

- `cli` — 命令行接口相关
- `provider` — 提供商管理相关
- `generate` — 图像生成相关
- `config` — 配置文件相关
- `chat` — 多轮对话相关
- `session` — 会话管理相关
- 无 scope 表示跨模块或项目级别变更

#### Subject 规则

- 使用**祈使语气**（英文）：`add` 而非 `added` 或 `adds`。
- **首字母小写**，结尾**不加句号**。
- 简洁描述"做了什么"，而非"为什么做"（"为什么"放 body 中）。

#### Breaking Changes

在 footer 中使用 `BREAKING CHANGE:` 前缀声明不兼容变更，或在 type 后加 `!`：

```
feat(cli)!: change model_spec format from colon to slash

BREAKING CHANGE: model_spec 参数格式从 "provider:model" 变更为
"provider/model"，以避免与 URL 中的冒号冲突。

迁移方法：将所有调用中的 ":" 替换为 "/"。
```

#### 示例

```bash
# 简单提交
git commit -m "feat(cli): add --aspect-ratio option for image generation"

# 修复 + Issue 引用
git commit -m "fix(generate): handle empty candidates in API response

当 API 返回空的 candidates 数组时，之前会抛出 IndexError。
现在改为输出有意义的错误信息到 stderr 并 exit(1)。

Closes #15"

# 不兼容变更
git commit -m "feat(provider)!: switch to YAML config format

BREAKING CHANGE: provider.json 已弃用，改用 provider.yaml。
运行 'imagegen migrate-config' 进行自动迁移。"
```

---

### 合并与 Rebase 规范

#### 策略总览

| 场景 | 策略 | 命令 | 理由 |
|------|------|------|------|
| feature → develop | **Squash Merge** | `git merge --squash feature/xxx` | 保持 develop 历史整洁，每个 feature 一条提交 |
| release → main | **Merge Commit**（`--no-ff`） | `git merge --no-ff release/x.y.z` | 保留发布历史节点，便于回溯 |
| release → develop | **Merge Commit**（`--no-ff`） | `git merge --no-ff release/x.y.z` | 同步修复内容到开发分支 |
| hotfix → main | **Merge Commit**（`--no-ff`） | `git merge --no-ff hotfix/xxx` | 保留修复历史节点 |
| hotfix → develop | **Merge Commit**（`--no-ff`） | `git merge --no-ff hotfix/xxx` | 同步修复内容到开发分支 |
| develop 同步到 feature | **Rebase** | `git rebase origin/develop` | 保持 feature 分支线性历史 |

#### Squash Merge 流程（feature → develop）

```bash
git checkout develop
git pull origin develop
git merge --squash feature/add-aspect-ratio

# Squash 后需手动写 commit message，遵循 Conventional Commits 格式
git commit -m "feat(cli): add --aspect-ratio option for image generation"

# 清理
git branch -d feature/add-aspect-ratio
git push origin --delete feature/add-aspect-ratio
```

#### Merge Commit 流程（release/hotfix → main）

```bash
git checkout main
git pull origin main
git merge --no-ff release/1.2.0 -m "release: v1.2.0"

# 打 tag（见版本与发布规范）
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# 同步回 develop
git checkout develop
git merge --no-ff release/1.2.0 -m "chore: merge release/1.2.0 back to develop"
git push origin develop

# 清理
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

#### Rebase 规则

- **仅对未推送到远程的本地分支执行 rebase。**
- **已推送的共享分支（develop、main）禁止 rebase。**
- 多人协作的 feature 分支，推送后禁止 rebase（改用 merge）。
- Rebase 过程中如遇冲突，按下方冲突处理规范解决。

```bash
# 同步 develop 到本地 feature 分支
git checkout feature/add-aspect-ratio
git fetch origin
git rebase origin/develop

# 如已推送过该 feature 分支，rebase 后需 force push
git push --force-with-lease origin feature/add-aspect-ratio
```

> **`--force-with-lease` vs `--force`**: 始终使用 `--force-with-lease`，它会检查远程是否有其他人推送的新提交，防止覆盖他人工作。禁止使用 `--force`。

---

### 冲突处理规范

#### 处理原则

1. **谁引入冲突，谁负责解决。** 合并/rebase 的发起者负责解决冲突。
2. **理解再解决。** 不要盲目接受某一方——阅读双方变更意图后再决定保留方式。
3. **解决后必须验证。** 冲突解决后运行完整验证（lint + type check + test）。

#### 解决流程

```bash
# 1. 冲突发生后，查看冲突文件列表
git status

# 2. 逐个打开冲突文件，定位冲突标记
<<<<<<< HEAD
# 当前分支的内容
=======
# 合入分支的内容
>>>>>>> feature/xxx

# 3. 理解双方变更意图，手动合并（不要简单选择一方）

# 4. 删除所有冲突标记（<<<, ===, >>>）

# 5. 标记冲突已解决
git add <resolved-file>

# 6. 继续操作
git rebase --continue   # 如果是 rebase 过程中
git merge --continue    # 如果是 merge 过程中（Git 2.12+）
git commit              # 如果是 merge 过程中（经典方式）

# 7. 验证
uv run ruff check src/
uv run mypy src/
uv run pytest
```

#### 常见冲突场景与策略

| 场景 | 推荐策略 |
|------|---------|
| 同一函数的不同修改 | 阅读双方意图，手动合并逻辑 |
| `provider.json` 中添加不同提供商 | 保留双方新增内容 |
| `pyproject.toml` 依赖版本冲突 | 取较新版本，确认兼容性 |
| `uv.lock` 冲突 | 接受当前分支版本，然后运行 `uv sync` 重新生成 |
| 文件删除 vs 修改 | 与对方开发者沟通确认 |

#### 中止操作

如冲突过于复杂或判断失误，可中止操作回到冲突前状态：

```bash
git rebase --abort    # 中止 rebase
git merge --abort     # 中止 merge
```

---

### 版本与发布规范

#### 语义化版本号（SemVer）

版本号格式：`MAJOR.MINOR.PATCH`

| 段 | 含义 | 递增条件 |
|----|------|---------|
| **MAJOR** | 主版本号 | 不兼容的 API 变更（Breaking Changes） |
| **MINOR** | 次版本号 | 向后兼容的新功能 |
| **PATCH** | 修订号 | 向后兼容的 Bug 修复 |

**版本递增示例：**

```
1.0.0 → 1.0.1  (patch: 修复 base64 解码 bug)
1.0.1 → 1.1.0  (minor: 新增 --aspect-ratio 选项)
1.1.0 → 2.0.0  (major: model_spec 格式从 ":" 变更为 "/")
```

**预发布版本：**

```
1.2.0-alpha.1   # 内部测试
1.2.0-beta.1    # 外部测试
1.2.0-rc.1      # 发布候选
```

#### 版本号同步

版本号存在于以下位置，发布时**必须同步更新**：

| 文件 | 字段 | 示例 |
|------|------|------|
| `pyproject.toml` | `version` | `version = "1.2.0"` |
| `src/imagegen/__init__.py` | `__version__` | `__version__ = "1.2.0"` |

#### Tag 规范

- Tag 名称格式：`v<MAJOR>.<MINOR>.<PATCH>`，例如 `v1.2.0`。
- 使用**附注标签**（annotated tag），包含版本说明。
- Tag 只打在 `main` 分支上。

```bash
# 创建附注标签
git tag -a v1.2.0 -m "Release v1.2.0

- feat(cli): add --aspect-ratio option
- fix(generate): handle empty candidates
- docs: update development guide"

# 推送标签
git push origin v1.2.0

# 查看所有标签
git tag -l "v*"

# 查看特定标签详情
git show v1.2.0
```

#### 发布流程

```bash
# 1. 从 develop 创建 release 分支
git checkout develop
git pull origin develop
git checkout -b release/1.2.0

# 2. 更新版本号
#    - pyproject.toml: version = "1.2.0"
#    - src/imagegen/__init__.py: __version__ = "1.2.0"

# 3. 生成 Changelog（见下方）

# 4. 提交版本变更
git add -A
git commit -m "release: prepare v1.2.0"

# 5. 最终验证
uv run ruff check src/
uv run mypy src/
uv run pytest

# 6. 合并到 main
git checkout main
git pull origin main
git merge --no-ff release/1.2.0 -m "release: v1.2.0"

# 7. 打 tag
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# 8. 合并回 develop
git checkout develop
git merge --no-ff release/1.2.0 -m "chore: merge release/1.2.0 back to develop"
git push origin develop

# 9. 清理
git branch -d release/1.2.0
git push origin --delete release/1.2.0

# 10. 构建发行包
uv build
```

#### Changelog 生成

从 Git 历史自动生成 Changelog，基于 Conventional Commits 格式解析。

**手动生成：**

```bash
# 生成两个版本之间的变更日志
git log v1.1.0..v1.2.0 --oneline --no-merges

# 按 type 分类输出（用于手动整理）
git log v1.1.0..v1.2.0 --oneline --no-merges --grep="^feat"
git log v1.1.0..v1.2.0 --oneline --no-merges --grep="^fix"
```

**Changelog 格式（`CHANGELOG.md`）：**

```markdown
# Changelog

## [1.2.0] - 2026-04-21

### Features
- **cli**: add --aspect-ratio option for image generation (#18)
- **generate**: support batch image generation (#22)

### Bug Fixes
- **generate**: handle empty candidates in API response (#15)
- **provider**: fix CWD lookup on Windows (#20)

### Documentation
- update development guide with Git workflow

## [1.1.0] - 2026-03-15

### Features
- **provider**: add multi-provider support

### Bug Fixes
- **cli**: fix --model flag display formatting
```

**自动生成工具（推荐）：**

可集成 [git-cliff](https://git-cliff.org/) 自动从 Conventional Commits 生成结构化 Changelog：

```bash
# 安装
pip install git-cliff

# 生成完整 Changelog
git-cliff -o CHANGELOG.md

# 生成指定版本范围
git-cliff v1.1.0..v1.2.0 --prepend CHANGELOG.md

# 与发布流程集成：在 release 分支中执行
git-cliff --tag v1.2.0 -o CHANGELOG.md
git add CHANGELOG.md
git commit -m "docs: update changelog for v1.2.0"
```

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

# 列出所有对话会话记录
imagegen provider sessions
```

### 生成图像

```bash
# 基本用法
imagegen generate "a photorealistic cat sitting on a windowsill" \
    "my-provider/gemini-2.5-flash-image" \
    "cat.png"

# 使用选项覆盖宽高比、分辨率并开启搜索增强
imagegen generate "luxury perfume bottle with golden light" \
    "my-provider/gemini-3-pro-image-preview" \
    "perfume.png" \
    --aspect-ratio 16:9 \
    --image-size 2K \
    --grounding google-search
```

### 编辑图像

```bash
# 提供一张或多张参考图片给模型进行编辑
imagegen edit "change the background to a snowy mountain" \
    "my-provider/gemini-3-pro-image-preview" \
    "edited.png" \
    --image original.png
```

### 多轮对话

```bash
# 启动一个新的交互式会话
imagegen chat "my-provider/gemini-3.1-flash-image-preview" --output-dir ./my_session

# 在 REPL 内的交互示例
> draw a cute puppy
[Saved to: ./my_session/turn_001.png]
> /aspect 16:9
> make it running in a park
[Saved to: ./my_session/turn_002.png]
> /quit

# 恢复之前的会话
imagegen chat "my-provider/gemini-3.1-flash-image-preview" --session abc123def456
```

### 通过 python -m 运行

```bash
uv run python -m imagegen --help
uv run python -m imagegen generate "a cat" "prov/model" "out.png"
```

---

### 设计决策记录

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| CLI 参数风格 | 全位置 vs 混合命名 | 全位置 | 匹配原始设计需求 |
| provider.json 查找 | CWD / 用户文件夹 / 三级回退 | 三级回退 | 灵活性 + 开箱即用 |
| 默认 provider.json 内容 | 预填提供商 / 空模板 | 空模板 | 用户自行填写，避免无效默认值 |
| API 无图像响应处理 | 静默 / 保存文本 / 打印+退出 | 打印文本到 stderr + exit(1) | 用户可看到模型的解释 |

---

## 扩展指南

### 添加新命令

在 `cli.py` 中通过 `@main.command()` 装饰器添加：

```python
@main.command()
@click.argument("prompt")
@click.argument("model_spec")
@click.argument("output")
@click.option("--style", default="realistic", help="Image style")
def stylized(prompt: str, model_spec: str, output: str, style: str) -> None:
    """Generate an image with a specific style."""
    # 实现具体逻辑
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

### 添加 API 配置选项

1. 在 `provider.json` 配置选项：

```json
"options": {
    "style": ["realistic", "anime", "watercolor"]
}
```

2. 在命令中添加可选参数：

```python
@click.option("--style", help="Image style")
```

3. 在 `provider.py` 的 `_get_model_options` 与 `validate_option` 中注册支持。

4. 传递到生成逻辑配置：

```python
# 组装到 API payload 或附加到 prompt
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

- [x] `uv run imagegen --help` — 显示 `generate`, `edit`, `chat` 和 `provider` 命令
- [x] `uv run imagegen provider list` — 空配置时显示警告
- [x] `uv run imagegen provider list --model` — 空配置时显示警告
- [x] `uv run imagegen provider sessions` — 显示会话列表
- [x] `uv run imagegen generate --help` — 显示 3 个位置参数和选项
- [x] `uv run imagegen edit --help` — 显示 edit 命令参数及 `--image`
- [x] `uv run imagegen chat --help` — 显示 chat 命令参数
- [x] LSP 诊断 — 所有源文件 0 错误
