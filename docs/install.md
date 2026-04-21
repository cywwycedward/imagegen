# 安装指南

## 前置条件

- **Python**: >= 3.10
- **uv**: 推荐使用 [uv](https://docs.astral.sh/uv/) 进行安装和管理

如果尚未安装 uv，请参考 [uv 官方文档](https://docs.astral.sh/uv/getting-started/installation/) 进行安装。

---

## 安装方式

### 方式一：作为全局 CLI 工具安装（推荐）

从项目根目录执行：

```bash
uv tool install .
```

安装完成后，即可在任意位置直接使用 `imagegen` 命令：

```bash
imagegen --help
```

### 方式二：开发模式安装

克隆项目后，在项目根目录同步依赖：

```bash
# 同步所有依赖（包含开发和测试依赖）
uv sync --group dev --group test
```

通过 `uv run` 运行 CLI：

```bash
uv run imagegen --help
```

也可以通过 `python -m` 方式运行：

```bash
uv run python -m imagegen --help
```

---

## 验证安装

安装成功后，运行以下命令验证：

```bash
# 查看帮助信息
imagegen --help

# 查看提供商列表
imagegen provider list
```

首次运行时，如果没有找到已有的配置文件，工具会自动在用户配置目录下创建一份默认的 `provider.json`。详见 [配置说明](configuration.md)。

---

## 依赖说明

imagegen 依赖以下 Python 包，均在安装时自动拉取：

| 包 | 版本要求 | 用途 |
|---|---|---|
| click | >= 8.1.0 | 命令行接口 |
| google-genai | >= 1.0.0 | Google GenAI SDK 调用 |
| rich | >= 13.0.0 | 终端表格与状态渲染 |
| Pillow | >= 10.0.0 | 图像数据处理 |

### 开发依赖（可选）

| 包 | 版本要求 | 用途 |
|---|---|---|
| ruff | >= 0.8.0 | 代码检查 |
| mypy | >= 1.13.0 | 类型检查 |
| pytest | >= 8.0.0 | 单元测试 |

安装开发依赖：

```bash
uv sync --group dev --group test
```

---

## 卸载

如果通过 `uv tool install` 安装，可通过以下命令卸载：

```bash
uv tool uninstall imagegen
```
