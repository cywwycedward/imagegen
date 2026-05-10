# imagegen 工具与 imagegen-usage Skill 使用反馈与优化建议

> 基于景区导览图地图符号生成的实际使用场景，涵盖 20+ 次密集调用的完整体验总结。

---

## 一、imagegen-usage Skill 使用总结

### 使用时机

对话开始时通过 `Skill` 工具调用了 `imagegen-usage`，获取了：

- CLI 命令结构（`generate` / `edit` / `chat`）
- model_spec 格式（`provider_name/model_key`）
- OpenAI 后端可用参数（`--size`, `--quality`, `--background` 等）
- 模型选择决策树

### Skill 实际帮助了什么

- 快速确认了命令格式 `uv run imagegen generate "<prompt>" "<provider/model>" "<output>" [options]`
- 明确了需要先运行 `provider list --model` 发现可用模型
- 了解了 OpenAI 后端和 GenAI 后端的参数差异

### Skill 没有覆盖到的

- **`--quality` 参数的实际可选值不准确**：Skill 文档写的是 `auto, low, medium, high`，但 gpt-image-2 实际只接受 `standard, hd, medium`，导致第一次生成报错
- **无 SDF / 地图符号领域的 prompt 指导**：这是一个专业场景，Skill 只提供了通用的 prompt 模式
- **缺少批量生成或网格排列的 prompt 模板**：3×3 网格排列是常见需求，但 Skill 没有相关示例

---

## 二、imagegen 工具使用总结

### 使用统计

| 项目           | 数量                           |
| -------------- | ------------------------------ |
| 总生成次数     | ~20 次                         |
| 使用模型       | `aipai-openai/gpt-image-2`    |
| 图片尺寸       | 全部 `1024x1024`              |
| 质量设置       | `hd`（首次尝试 `high` 失败后改为 `hd`） |
| 生成失败次数   | 1 次（`--quality high` 参数错误）       |
| 用户中断重生成 | 2 次（复杂符号风格调整）               |

### 使用模式

1. **单次生成 + 预览检查**：每次 `generate` 后用 `Read` 查看图片
2. **并行生成**：对无依赖的图片（如设施图和景点图）同时发起两个 `generate` 调用
3. **迭代修正**：根据用户反馈调整 prompt 后覆盖重新生成同一文件

### 遇到的问题

1. **参数试错**：`--quality high` 不被接受，需要靠报错信息才知道实际可选值
2. **prompt 工程负担重**：每张图需要写 15-25 行详细的英文 prompt 描述每个图标的位置、内容、风格
3. **无法局部修改**：9 个图标中只想改 1 个（如警务符号），必须重新生成整张图
4. **无法控制精确布局**：3×3 网格的间距、对齐、大小一致性完全依赖模型理解，无法精确参数化
5. **SDF 质量不可控**：生成的"纯黑白"图标可能存在灰度过渡、抗锯齿等问题，不一定是真正的 SDF 可用质量

---

## 三、优化建议

### 对 imagegen-usage Skill 的建议

#### 1. 参数文档应从工具实时获取，而非硬编码

Skill 中应提示用户运行 `uv run imagegen generate --help` 或类似命令来获取当前模型实际支持的参数值，而非在 Skill 中维护一份可能过时的列表。当前 `--quality` 的文档值与实际值不一致直接导致了首次失败。

#### 2. 增加领域化 prompt 模板库

当前 Skill 只有通用的 prompt 示例。建议增加常见领域模板：

- **图标 / UI 设计**：网格排列、SDF、扁平化风格
- **产品摄影**：材质、打光、角度
- **插画**：风格参考（水彩、线稿、像素风等）
- **建筑 / 地图**：鸟瞰、等距、符号化

#### 3. 增加批量 / 迭代工作流指导

当前 Skill 只覆盖了单次生成。实际使用中常见的模式是：

- 生成 → 检查 → 调整 prompt → 重新生成（迭代）
- 同一套风格生成多张（批量）
- 对已有图片做局部修改（edit）

建议在 Skill 中增加这些工作流的最佳实践。

#### 4. 模型能力矩阵应更实用

当前的模型选择决策树偏理论。建议补充实际使用经验：

- gpt-image-2 对中文理解能力如何？
- 哪个模型更擅长精确的网格排列？
- 哪个模型更擅长保持多图标一致性？

---

### 对 imagegen 工具本身的建议

#### 1. 参数校验前置 + 友好提示

当前报错信息已经不错：

```
--quality 'high' is not supported by model 'gpt-image-2'. Accepted: standard, hd, medium
```

但建议进一步改进：

- 在 `provider list --model --options` 中直接列出每个模型实际支持的参数值
- 或支持 `uv run imagegen generate --help --model aipai-openai/gpt-image-2` 按模型显示可用选项

#### 2. 增加网格 / 批量模式

建议增加原生的网格生成选项：

```bash
uv run imagegen generate "<prompt>" model output.png \
  --grid 3x3 \
  --labels "Parking,Dock,Restroom,..." \
  --style "sdf-circle"
```

减少用户在 prompt 中描述布局的负担。

#### 3. 增加 SDF 后处理管线

对于地图图标场景，建议集成：

```bash
uv run imagegen generate ... --postprocess sdf
```

自动完成：

1. 去背景（白 → 透明）
2. 二值化（消除灰度过渡）
3. SDF 距离场编码（调用 image-sdf 或 tiny-sdf）
4. 输出 SDF-ready PNG

#### 4. 支持局部重生成 / inpainting

当 3×3 网格中只有 1 个图标不满意时，当前必须重新生成全部 9 个。建议支持：

```bash
uv run imagegen edit "change icon at row2-col1 to Chinese police badge" \
  model output.png --image original.png --region "row2-col1"
```

#### 5. 增加 prompt 模板 / 预设系统

允许用户保存和复用 prompt 模板：

```bash
uv run imagegen template save "sdf-circle" \
  "solid black filled circle with white cutout symbol, pure white background,
   no gradients, no shadows, flat, SDF style"

uv run imagegen generate "parking P symbol" model out.png \
  --template sdf-circle
```

---

## 四、总体评价

imagegen 作为一个 CLI 图像生成工具，基本功能完整，命令结构清晰。在本次 20+ 次密集使用中，**生成成功率很高（仅 1 次参数错误）**，生成速度也可接受。

主要痛点集中在：

- **prompt 工程的重复劳动**：每张图需要大量描述性文本，风格一致性完全靠人工维护
- **缺乏专业场景的工作流支持**：SDF、网格排列、批量生成等常见模式没有原生支持
- **Skill 文档准确性**：参数可选值与实际不一致，需要修复

imagegen-usage Skill 在起步阶段提供了有效的命令结构和参数参考，但在深入使用后的指导价值有限。建议向领域化、模板化、工作流化的方向增强。

---

## 附录：本次生成的文件清单

### Style 1 — 圆形 SDF 图标

| 文件名 | 内容 |
| ------ | ---- |
| `style1_circular_sdf_batch1.png` | 设施类：停车场、码头、厕所、男厕、女厕、母婴室、购物、售票处、游客中心 |
| `style1_circular_sdf_batch2.png` | 服务类：出入口、餐厅、咖啡厅、消防、公安、急救、主要景点、次要景点、游客中心 |
| `style1_circular_sdf_attractions.png` | 景点类（9种）：亭子、宝塔、宫殿、寺庙、摩天轮、牌坊、长城、古桥、山景 |

### Style 2 — 方形 SDF 图标

| 文件名 | 内容 |
| ------ | ---- |
| `style2_square_sdf_batch1.png` | 设施类（同 Style 1） |
| `style2_square_sdf_batch2.png` | 服务类（同 Style 1） |
| `style2_square_sdf_attractions.png` | 景点类（9种，同 Style 1） |

### Style 3 — 卡通多色符号（非 SDF）

| 文件名 | 内容 |
| ------ | ---- |
| `style3_complex_attractions.png` | 景点类卡通符号 |
| `style3_complex_facilities.png` | 设施类卡通符号 |

### Style 4 — 气泡 Pin 标记

| 文件名 | 内容 |
| ------ | ---- |
| `style4_pin_bubble_facilities.png` | 彩色版设施 Pin（非 SDF） |
| `style4_pin_bubble_attractions.png` | 彩色版景点 Pin（非 SDF） |
| `style4_pin_sdf_facilities.png` | SDF 版设施 Pin |
| `style4_pin_sdf_attractions.png` | SDF 版景点 Pin |

### Style 5 — 中国古典印章风格

| 文件名 | 内容 |
| ------ | ---- |
| `style5_chinese_seal_facilities.png` | 彩色版设施印章（非 SDF） |
| `style5_chinese_seal_attractions.png` | 彩色版景点印章（非 SDF） |
| `style5_seal_sdf_facilities.png` | SDF 版设施印章 |
| `style5_seal_sdf_attractions.png` | SDF 版景点印章 |

### Style 6 — 线性描边风格（非 SDF）

| 文件名 | 内容 |
| ------ | ---- |
| `style6_line_outline_facilities.png` | 线性设施图标 |
| `style6_line_outline_attractions.png` | 线性景点图标 |

### Style 7 — 等距 2.5D 微缩风格（非 SDF）

| 文件名 | 内容 |
| ------ | ---- |
| `style7_isometric_facilities.png` | 等距设施小建筑 |
| `style7_isometric_attractions.png` | 等距景点小建筑 |

### Style 8 — 瓦当风格 SDF

| 文件名 | 内容 |
| ------ | ---- |
| `style8_wadang_sdf_facilities.png` | 瓦当设施图标 |
| `style8_wadang_sdf_attractions.png` | 瓦当景点图标 |

### Style 9 — 花窗窗棂风格 SDF

| 文件名 | 内容 |
| ------ | ---- |
| `style9_lattice_sdf_facilities.png` | 窗棂设施图标 |
| `style9_lattice_sdf_attractions.png` | 窗棂景点图标 |

### Style 10 — 折扇风格 SDF

| 文件名 | 内容 |
| ------ | ---- |
| `style10_fan_sdf_facilities.png` | 折扇设施图标 |
| `style10_fan_sdf_attractions.png` | 折扇景点图标 |

### Style 11 — 如意云纹风格 SDF

| 文件名 | 内容 |
| ------ | ---- |
| `style11_ruyi_cloud_sdf_facilities.png` | 云纹设施图标 |
| `style11_ruyi_cloud_sdf_attractions.png` | 云纹景点图标 |
