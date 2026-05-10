# imagegen 工具优化改进技术文档

> 基于用户反馈（docs/feedback/imagegen工具使用反馈与优化建议.md）与当前工具应用定位，梳理优化方向、技术方案与实施优先级。

---

## 一、当前工具定位

imagegen 是一个面向开发者和 AI Agent 的 CLI 图像生成工具，核心价值：

- **多后端统一接口**：通过 `provider.json` 配置，以统一的 `provider/model` 规范调用 GenAI 和 OpenAI 两类后端
- **Agent 友好**：位置参数设计、明确的错误信息、可组合的 CLI 命令，适合 AI Agent（如 Claude Code）自动调用
- **开箱即用**：3 级配置回退、自动初始化、内置示例配置

当前版本（0.1.0）完成了核心的 generate / edit / chat 三大功能，基本功能完整，但从实际高密度使用反馈来看，在**参数发现性、工作流效率、专业场景支持**三个方面存在明确的改进空间。

---

## 二、问题分析与优化方向

根据用户反馈，结合代码分析，归纳出以下五个核心优化方向：

| # | 方向 | 核心痛点 | 影响范围 |
|---|------|---------|---------|
| 1 | 参数发现与校验 | `--quality` 可选值与实际不一致，参数试错成本高 | 所有用户 |
| 2 | Prompt 模板系统 | 每张图写 15-25 行 prompt，风格一致性靠人工维护 | 高频用户 |
| 3 | 后处理管线 | SDF 二值化、去背景等常见需求无工具支持 | 专业场景 |
| 4 | Skill 文档准确性 | 硬编码参数值过时，缺少工作流指导 | Agent 调用 |

---

## 三、优化方案

### 3.1 参数发现与模型能力查询

**问题**：用户传入 `--quality high` 但 gpt-image-2 只接受 `standard, hd, medium`，首次调用即失败。当前 `provider list --options` 能展示参数，但用户需要额外一步查询。

**方案**：增强 `provider list` 子命令，支持按模型查询完整参数信息。

#### 3.1.1 `provider list --model --verbose` 模式

在现有 `provider list --model` 输出中增加 `--verbose` 标志，展示每个模型的完整可选参数值：

```
$ imagegen provider list --model --verbose

Provider: aipai-openai (backend: openai)
  gpt-image-2
    --size:       auto, 1024x1024, 1536x1024, 1024x1536
    --quality:    standard, hd, medium
    --background: auto, transparent, opaque
```

**改动范围**：`cli.py` 的 `provider_list` 命令，增加 `--verbose` 选项，调用 `provider.get_model_options()` 获取并格式化输出。

#### 3.1.2 参数模糊匹配与建议

当用户传入无效参数值时，除了报错还提供最接近的有效值建议：

```
Error: --quality 'high' is not supported by model 'gpt-image-2'.
       Accepted: standard, hd, medium
       Did you mean: hd?
```

**改动范围**：`provider.py` 的 `validate_option()` 函数，增加 Levenshtein 距离或简单子串匹配逻辑。无需引入新依赖，可用标准库 `difflib.get_close_matches` 实现。

#### 实现细节

```python
# provider.py — validate_option 增强
import difflib

def validate_option(name: str, value: str, allowed: list[str], model_name: str) -> None:
    if value not in allowed:
        suggestion = difflib.get_close_matches(value, allowed, n=1, cutoff=0.4)
        msg = f"--{name} '{value}' is not supported by model '{model_name}'. Accepted: {', '.join(allowed)}"
        if suggestion:
            msg += f"\n       Did you mean: {suggestion[0]}?"
        click.echo(msg, err=True)
        sys.exit(1)
```

**优先级**：P0 — 直接影响首次使用成功率  
**工作量**：~2h  

---

### 3.2 Prompt 模板系统

**问题**：每次生成都要手写大段描述性 prompt，同一风格的多张图需要复制粘贴调整，风格一致性完全依赖人工。

**方案**：增加轻量级模板系统，支持保存、复用和组合 prompt 片段。

#### 3.2.1 模板存储

模板以 JSON 文件存储在用户配置目录：

```
~/.config/imagegen/templates/
├── sdf-circle.json
├── sdf-square.json
└── isometric.json
```

模板格式：

```json
{
    "name": "sdf-circle",
    "description": "SDF style circular icon",
    "prefix": "solid black filled circle with white cutout symbol, pure white background, no gradients, no shadows, flat, SDF style.",
    "suffix": "Clean edges, no anti-aliasing, high contrast black and white only."
}
```

生成时，实际 prompt = `prefix + 用户 prompt + suffix`。

#### 3.2.2 CLI 命令

```bash
# 管理模板
imagegen template list
imagegen template save <name> --prefix "..." --suffix "..."
imagegen template show <name>
imagegen template delete <name>

# 使用模板
imagegen generate "parking P symbol" model out.png --template sdf-circle
```

#### 3.2.3 实现架构

新增模块 `src/imagegen/template.py`：

| 函数 | 职责 |
|------|------|
| `get_templates_dir() -> Path` | 返回模板目录路径 |
| `save_template(name, prefix, suffix, description)` | 保存模板到 JSON 文件 |
| `load_template(name) -> dict` | 加载指定模板 |
| `list_templates() -> list[dict]` | 列出所有模板 |
| `apply_template(template, prompt) -> str` | 组合模板与用户 prompt |

CLI 入口在 `cli.py` 新增 `template` 子命令组，`generate` 和 `edit` 命令增加 `--template` 选项。

**优先级**：P1 — 显著降低高频用户的重复劳动  
**工作量**：~6h  

---

### 3.3 后处理管线

**问题**：生成的"纯黑白"图标存在灰度过渡、抗锯齿，不是真正的 SDF 可用质量。去背景、二值化是手动操作。

**方案**：增加可组合的后处理步骤，通过 `--postprocess` 选项触发。

#### 3.4.1 支持的后处理操作

| 操作 | 标识 | 说明 |
|------|------|------|
| 去背景 | `remove-bg` | 将白色/指定颜色背景转为透明 |
| 二值化 | `binarize` | 消除灰度过渡，阈值化为纯黑白 |
| 裁切 | `trim` | 去除四周空白边距 |

操作可组合：`--postprocess remove-bg,binarize,trim`

#### 3.4.2 实现架构

新增模块 `src/imagegen/postprocess.py`：

```python
from PIL import Image

def remove_background(img: Image.Image, color: tuple = (255, 255, 255), threshold: int = 30) -> Image.Image:
    """将指定颜色背景转为透明。"""

def binarize(img: Image.Image, threshold: int = 128) -> Image.Image:
    """灰度二值化。"""

def trim(img: Image.Image, padding: int = 0) -> Image.Image:
    """裁切空白边距。"""

def apply_pipeline(img: Image.Image, steps: list[str]) -> Image.Image:
    """按顺序执行后处理步骤。"""
```

CLI 集成：在 `generate` 和 `edit` 命令增加 `--postprocess` 选项，在图片保存前调用管线。

**优先级**：P2 — 专业场景增值，非通用需求  
**工作量**：~4h  
**依赖**：Pillow（已有依赖），无新依赖

---

### 3.4 imagegen-usage Skill 文档修复

**问题**：Skill 中 `--quality` 参数文档值 (`auto, low, medium, high`) 与 gpt-image-2 实际支持值 (`standard, hd, medium`) 不一致，直接导致用户首次调用失败。

**方案**：

#### 3.4.1 移除硬编码参数值

Skill 文档中不再列出具体参数可选值，改为引导用户通过 CLI 查询：

```markdown
## 参数查询

使用前先查询模型支持的参数：
`imagegen provider list --model --verbose`
```

#### 3.4.2 增加工作流模式指导

在 Skill 中补充三种常见工作流：

1. **迭代模式**：generate → 检查 → 调整 prompt → 覆盖重生成
2. **批量模式**：使用模板 + batch 命令生成系列图片
3. **编辑模式**：基于已有图片进行局部修改

#### 3.4.3 增加模型能力实测矩阵

补充基于实际使用的模型对比信息：

| 能力 | gpt-image-2 | gemini-2.5-flash-image | gemini-3-pro-image-preview |
|------|------------|----------------------|--------------------------|
| 中文理解 | 一般 | 较好 | 好 |
| 网格排列 | 可控 | 基本可控 | 较好 |
| SDF 风格 | 好 | 一般 | 好 |
| 生成速度 | ~5s | ~3s | ~15s |

**优先级**：P0 — 文档错误直接导致失败  
**工作量**：~1h  

---

## 四、实施路线图

### Phase 1 — 修复与增强（v0.2.0）

目标：消除首次使用障碍，改善参数发现体验。

| 任务 | 优先级 | 工作量 | 改动文件 |
|------|--------|--------|---------|
| Skill 文档修复 | P0 | 1h | `.claude/skills/imagegen-usage/SKILL.md` |
| 参数模糊匹配建议 | P0 | 2h | `provider.py` |
| `provider list --verbose` | P0 | 2h | `cli.py` |

### Phase 2 — 效率工具（v0.3.0）

目标：通过模板能力减少重复劳动。

| 任务 | 优先级 | 工作量 | 改动文件 |
|------|--------|--------|---------|
| Prompt 模板系统 | P1 | 6h | 新增 `template.py`，修改 `cli.py` |

### Phase 3 — 专业场景（v0.4.0）

目标：为图标、地图等专业场景提供原生支持。

| 任务 | 优先级 | 工作量 | 改动文件 |
|------|--------|--------|---------|
| 后处理管线 | P2 | 4h | 新增 `postprocess.py`，修改 `cli.py`、`backends/` |

---

## 五、不做的事情

以下建议在反馈中被提及，但经评估后暂不纳入路线图：

| 建议 | 不做的原因 |
|------|-----------|
| 批量网格生成 | 图片拼接、网格排列属于图像编排而非图像生成，超出本工具的应用边界 |
| 原生 SDF 距离场编码 | 超出图像生成工具的职责边界，应由下游工具（如 image-sdf）处理 |
| 区域化 inpainting 语义 (`--region "row2-col1"`) | 依赖模型侧 inpainting 能力，非工具层面能解决 |
| 领域化 prompt 模板库内置 | 模板系统（3.2）提供了用户自建模板的能力，内置库维护成本高且难以覆盖所有领域 |

---

## 六、技术约束与风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 模板组合后 prompt 过长 | 部分模型对 prompt 长度有限制 | 在 apply_template 中检查组合长度，超限时警告 |
| 后处理结果与预期不符 | 二值化阈值、背景颜色容差需要调优 | 提供 `--threshold` 等可调参数，默认值基于常见场景 |
| 无新外部依赖 | 所有优化均基于现有依赖（Pillow、click、difflib），不引入新的运行时依赖 | — |

---

## 附录：改动文件清单

```
src/imagegen/
├── provider.py          # 修改：validate_option 增加模糊匹配
├── cli.py               # 修改：--verbose、--template、--postprocess、template 命令
├── template.py          # 新增：模板管理模块
├── postprocess.py       # 新增：图片后处理管线
└── backends/
    ├── __init__.py      # 修改：generate 返回值增加图片路径（供后处理使用）
    ├── genai.py         # 修改：返回值调整
    └── openai.py        # 修改：返回值调整

tests/
├── test_template.py     # 新增
├── test_postprocess.py  # 新增
└── test_provider.py     # 修改：增加模糊匹配测试

.claude/skills/imagegen-usage/SKILL.md  # 修改：文档修复
```
