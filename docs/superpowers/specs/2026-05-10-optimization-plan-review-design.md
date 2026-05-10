# imagegen 优化方案（修正版）

> 基于 `docs/optimization-plan.md` 的技术可行性审查，修正技术错误、简化设计、对齐现有代码。

---

## 一、审查背景

原方案提出 4 个优化方向、3 个 Phase。经过代码审查发现 6 个技术问题：

| # | 问题 | 严重度 | 处理方式 |
|---|------|--------|---------|
| 1 | `--verbose` 与已有 `--options` 功能重复 | 高 | 取消 `--verbose`，增强 `--options` |
| 2 | `validate_option` 函数签名与实际代码不符 | 中 | 对齐实际签名 |
| 3 | 章节编号 3.3 vs 3.4 混乱 | 低 | 修正编号 |
| 4 | 后处理不需要改 backends 返回值 | 高 | 后处理整体暂不纳入 |
| 5 | 模板 prefix/suffix 可简化 | 中 | 改为自由变量模板系统 |
| 6 | Skill 修复应引导到 `--options` 而非 `--verbose` | 中 | 对齐已有命令 |

修正后方案缩减为 2 个 Phase，去掉后处理管线。

---

## 二、Phase 1 — 参数发现与校验增强（v0.2.0）

目标：消除首次使用障碍，改善参数发现体验。

### 2.1 增强 `provider list --options` 输出

**问题**：现有 `--options` 表格列太多（7 列参数），genai 模型的 openai 专属列全是 `-`，反之亦然，信噪比低。

**方案**：按 backend 类型只显示有意义的列。

- genai 模型：显示 Aspect Ratio / Image Size / Grounding
- openai 模型：显示 Size / Quality / Background / Style

**改动范围**：`cli.py` 的 `provider_list` 函数（`if options:` 分支），修改表格构建逻辑，按 backend 分组或过滤列。

**工时**：2h

### 2.2 参数模糊匹配与建议

**问题**：用户传入 `--quality high` 但 gpt-image-2 只接受 `standard, hd, medium`，报错信息只列出可选值，不提供建议。

**方案**：在 `validate_option()` 中增加 `difflib.get_close_matches` 逻辑。

```python
# provider.py — validate_option 增强
import difflib

def validate_option(
    value: str,
    allowed: list[str],
    option_name: str,
    model_key: str,
) -> None:
    if value not in allowed:
        suggestion = difflib.get_close_matches(value, allowed, n=1, cutoff=0.4)
        msg = (
            f"{option_name} '{value}' is not supported by model '{model_key}'. "
            f"Accepted: {', '.join(allowed)}"
        )
        if suggestion:
            msg += f"\n       Did you mean: {suggestion[0]}?"
        print(msg, file=sys.stderr)
        sys.exit(1)
```

无新依赖（`difflib` 为标准库）。

**改动范围**：`provider.py` 的 `validate_option` 函数，`tests/test_provider.py` 增加模糊匹配测试。

**工时**：2h

### 2.3 Skill 文档修复

**问题**：SKILL.md 中 `--quality` 参数可选值 `auto, low, medium, high` 与 gpt-image-2 实际值 `standard, hd, medium` 不一致。

**方案**：

1. **移除硬编码参数值**：删掉 OpenAI Backend Options 表格中的具体 Values 列，改为引导到 CLI 查询：

```markdown
### OpenAI Backend Options

参数值因模型而异，使用前先查询：
`uv run imagegen provider list --options`

可用参数：`--size`, `--quality`, `--background`, `--style`,
`--output-format`, `--output-compression`, `--n`
```

2. **GenAI Backend Options 同样处理**：为一致性也改为引导查询。

3. **增加工作流模式指导**：

```markdown
## Common Workflows

### Iterative refinement
generate → check with Read → adjust prompt → overwrite same file

### Batch with templates
Use `--template` to maintain style consistency across multiple images.
Check available templates: `imagegen template list`

### Edit mode
Edit existing images with `edit` command + `--image` flag.
```

4. **模型能力实测矩阵**（标注"基于实测，可能随模型更新变化"）：

| 能力 | gpt-image-2 | gemini-2.5-flash-image | gemini-3-pro-image-preview |
|------|------------|----------------------|-----------------------------|
| 中文理解 | 一般 | 较好 | 好 |
| 网格排列 | 可控 | 基本可控 | 较好 |
| SDF 风格 | 好 | 一般 | 好 |
| 生成速度 | ~5s | ~3s | ~15s |

**改动范围**：`.claude/skills/imagegen-usage/SKILL.md`

**工时**：1h

---

## 三、Phase 2 — 自由变量模板系统（v0.3.0）

目标：通过可复用模板减少重复 prompt 劳动，支持用户自定义变量实现灵活组合。

### 3.1 模板格式

模板以 JSON 文件存储在 `~/.config/imagegen/templates/` 目录（复用 `user_config_dir()`）。

```json
{
    "name": "sdf-circle",
    "description": "SDF style circular icon with customizable fill and background",
    "variables": {
        "prompt": {
            "description": "The main subject/symbol to render inside the circle",
            "required": true
        },
        "fill_color": {
            "description": "Fill color of the shape",
            "default": "black"
        },
        "bg_color": {
            "description": "Background color",
            "default": "pure white"
        },
        "style_extra": {
            "description": "Additional style constraints appended at the end",
            "default": "Clean edges, high contrast black and white only."
        }
    },
    "template": "solid {fill_color} filled circle with white cutout symbol of {prompt}, {bg_color} background, no gradients, no shadows, flat, SDF style. {style_extra}"
}
```

### 3.2 变量解析规则

| 情况 | 行为 |
|------|------|
| 变量有 `required: true` 且未提供值 | 报错，列出缺少的变量及其描述 |
| 变量有 `default` 且未提供值 | 使用默认值 |
| 变量既没有 `required` 也没有 `default` | 等同于 `required: true` |
| 提供了模板未定义的变量 | 警告并忽略 |
| 模板中需要字面 `{` 或 `}` | 使用 `{{` 和 `}}` 转义 |

**`prompt` 的特殊处理**：CLI 位置参数 `prompt` 自动映射到模板变量 `{prompt}`（如果模板定义了该变量）。其他变量通过 `--var key=value` 传入。

### 3.3 CLI 命令

```bash
# 列出所有模板（名称 + 描述 + 变量数）
imagegen template list

# 查看模板详情（模板字符串 + 所有变量及描述和默认值）
imagegen template show <name>

# 保存模板
imagegen template save <name> \
  --template "solid {fill_color} circle, {prompt}, {bg_color} bg" \
  --description "SDF circular icon" \
  --var "prompt|The main subject" \
  --var "fill_color|Fill color of shape|black" \
  --var "bg_color|Background color|pure white"

# 删除模板
imagegen template delete <name>
```

`--var` 格式：`"名称|描述"` 或 `"名称|描述|默认值"`，用 `|` 分隔。未被 `--var` 覆盖的 `{varname}` 自动创建为 required 变量（描述为空）。

**`template list` 输出**：

```
Templates:
  sdf-circle      SDF style circular icon               vars: prompt, fill_color, bg_color, style_extra
  sdf-square      SDF style square icon                  vars: prompt, fill_color
  isometric       Isometric 2.5D miniature building      vars: prompt, angle
```

**`template show` 输出**：

```
Template: sdf-circle
Description: SDF style circular icon with customizable fill and background

Variables:
  {prompt}       (required)     The main subject/symbol to render inside the circle
  {fill_color}   default=black  Fill color of the shape
  {bg_color}     default=pure white  Background color
  {style_extra}  default=Clean edges, high contrast black and white only.  Additional style constraints

Template string:
  solid {fill_color} filled circle with white cutout symbol of {prompt}, {bg_color} background,
  no gradients, no shadows, flat, SDF style. {style_extra}
```

### 3.4 使用示例

```bash
# {prompt} ← 位置参数，其他变量使用默认值
imagegen generate "parking P symbol" model out.png --template sdf-circle

# 覆盖默认值
imagegen generate "parking P symbol" model out.png \
  --template sdf-circle \
  --var fill_color="dark blue"
```

### 3.5 错误信息

```
Error: template 'sdf-circle' requires variable 'prompt' but it was not provided.
       Description: The main subject/symbol to render inside the circle

Error: template 'sdf-circle' does not define variable 'color'.
       Defined variables: prompt, fill_color, bg_color, style_extra
```

### 3.6 `template.py` 模块设计

| 函数 | 职责 |
|------|------|
| `get_templates_dir() -> Path` | 返回 `user_config_dir() / "templates"` |
| `save_template(name, template_str, description, variables)` | 保存模板 JSON 文件 |
| `load_template(name) -> TemplateData` | 加载模板，返回带类型的数据结构 |
| `list_templates() -> list[TemplateSummary]` | 列出所有模板 |
| `delete_template(name) -> None` | 删除模板文件 |
| `extract_variables(template_str) -> list[str]` | 从模板字符串中提取 `{varname}` 列表 |
| `apply_template(template_data, prompt, var_overrides) -> str` | 解析变量、校验 required、替换占位符、返回最终 prompt |

组合后 prompt 超长时打印警告（不阻断）。

**工时**：8-10h

---

## 四、不做的事情

| 建议 | 不做的原因 |
|------|-----------|
| 批量网格生成 | 图片拼接、网格排列属于图像编排，超出本工具应用边界 |
| 原生 SDF 距离场编码 | 超出图像生成工具的职责边界，应由下游工具处理 |
| 区域化 inpainting (`--region`) | 依赖模型侧能力，非工具层面能解决 |
| 领域化 prompt 模板库内置 | 模板系统提供了用户自建模板能力，内置库维护成本高 |
| 后处理管线 | 用户决定暂不纳入，未来可作为独立 Phase 重新评估 |
| 新增 `--verbose` 标志 | 与已有 `--options` 功能重复 |

---

## 五、技术约束与风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 模板组合后 prompt 过长 | 部分模型对 prompt 长度有限制 | `apply_template` 中检查组合长度，超限时警告 |
| `--var` 解析格式（`|` 分隔） | 用户 prompt 中可能包含 `|` 字符 | `--var` 只在保存模板时使用，不影响运行时 prompt |
| 无新外部依赖 | 所有优化均基于现有依赖（Pillow、click、difflib） | — |

---

## 六、实施路线图

### Phase 1 — 修复与增强（v0.2.0）

| 任务 | 优先级 | 工时 | 改动文件 |
|------|--------|------|---------|
| Skill 文档修复 | P0 | 1h | `.claude/skills/imagegen-usage/SKILL.md` |
| 参数模糊匹配建议 | P0 | 2h | `provider.py`, `tests/test_provider.py` |
| 增强 `--options` 输出格式 | P0 | 2h | `cli.py` |

### Phase 2 — 自由变量模板系统（v0.3.0）

| 任务 | 优先级 | 工时 | 改动文件 |
|------|--------|------|---------|
| 模板系统核心 | P1 | 8-10h | 新增 `template.py`；修改 `cli.py`（template 子命令 + generate/edit 增加 `--template`/`--var`）；新增 `tests/test_template.py` |

---

## 七、改动文件清单

```
src/imagegen/
├── provider.py          # 修改：validate_option 增加 difflib 模糊匹配
├── cli.py               # 修改：--options 按 backend 过滤列；template 子命令组；generate/edit 增加 --template/--var
├── template.py          # 新增：自由变量模板系统

tests/
├── test_template.py     # 新增：模板 CRUD、变量解析、apply、错误场景
└── test_provider.py     # 修改：增加模糊匹配测试

.claude/skills/imagegen-usage/SKILL.md  # 修改：移除硬编码参数值，增加工作流指导
```
