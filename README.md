# halcon1811-mcp

[English](README.en.md)

让聊天中的 AI 通过本地 MCP，为 **HALCON 18.11 / HDevelop** 生成代码、自动保存程序，并在软件窗口中打开。需要运行时，可以继续执行并查询状态。

```text
你输入操作需求 → 聊天 AI 分析并查算子文档 → 生成 HDevelop 代码
             → MCP 保存 .hdev → HDevelop 加载 → 按要求执行
```

AI 来自你正在使用的 MCP 客户端。本项目提供 HALCON 本机工具，不需要额外的 AI API 密钥。

## 环境要求

- Windows 交互桌面。
- Python 3.10 或以上版本。
- 已安装 HALCON 18.11 / HDevelop，并有可用的开发授权。
- 支持本地 stdio MCP 的客户端。

已在 Windows、Python 3.13.6、HALCON 18.11 上实测。其他 HALCON 版本尚未验证。
HALCON 软件、库、许可证和官方文档均不随本项目分发；算子参考从本机安装目录读取。

## 安装

从源码安装：

```powershell
git clone https://github.com/Austinlu29/halcon1811-mcp.git
cd halcon1811-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
```

也可以从 GitHub Releases 下载 `.whl`，在自己的 Python 环境中用 `python -m pip install 文件名.whl` 安装。
本项目当前没有发布到 PyPI。

## MCP 配置

先找到本机 `hdevelop.exe`。例如：

```text
C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe
```

### Codex

将命令中的项目目录和 HALCON 路径替换为自己的实际路径：

```powershell
codex mcp add halcon1811-ui --env "HALCON_HDEVELOP_EXE=C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" -- C:/tools/halcon1811-mcp/.venv/Scripts/python.exe -m halcon1811_mcp
```

随后按客户端的 MCP 设置提示重启或重新加载连接。

### 其他 stdio MCP 客户端

```json
{
  "mcpServers": {
    "halcon1811-ui": {
      "command": "C:/tools/halcon1811-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "halcon1811_mcp"],
      "env": {
        "HALCON_HDEVELOP_EXE": "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe",
        "HALCON_MCP_DATA_DIR": "C:/HALCONPrograms"
      }
    }
  }
}
```

完整配置示例见 [examples/mcp.json](examples/mcp.json)。

## 聊天中怎样使用

例如：

> 使用 HALCON MCP，读取 C:/images/part.png，转灰度并进行 3×3 均值滤波，用 128–255 做阈值分割，筛选面积 500–100000 的连通域。生成代码，保存为“零件区域检测”，并在 HDevelop 打开。

AI 会查本机算子参考、生成兼容代码，再调用保存工具。需要执行时继续说：

> 运行刚才的程序，并检查是否执行完成。

保存工具接收普通 HDevelop `main` 代码，自动转换为 `.hdev` XML。每次保存创建独立版本目录，不覆盖以前的程序。
目录同时保留 `.hdev`、纯文本代码、用户需求、AI 分析及执行记录。

## MCP 工具

| 工具 | 作用 |
|---|---|
| `halcon_environment` | 检查 HDevelop、保存目录和本机算子文档 |
| `halcon_operator_help` | 读取安装版本的算子参数和说明 |
| `halcon_save_program` | 保存任意 main 代码，可同时在 HDevelop 打开 |
| `halcon_open_program` | 重新打开已保存程序 |
| `halcon_run_program` | 在可见 HDevelop 窗口执行程序 |
| `halcon_execution_status` | 查询完成、HALCON 异常或等待状态 |
| `halcon_list_programs` | 列出最近保存的版本 |
| `generate_threshold_program` | 生成内置阈值分割演示 |
| `run_threshold_demo` | 运行演示，返回区域数量、面积和中心坐标 |

保存和执行是独立操作。`halcon_save_program` 默认打开程序而不执行；`halcon_run_program` 返回执行编号，随后查询状态。

## 环境变量

| 变量 | 用途 |
|---|---|
| `HALCON_HDEVELOP_EXE` | 显式指定 `hdevelop.exe`，建议设置 |
| `HALCONROOT` | HALCON 安装目录，用于自动发现 |
| `HALCON_MCP_DATA_DIR` | 所有生成数据的根目录 |
| `HALCON_PROGRAM_DIR` | 单独覆盖通用程序的保存目录 |

Windows 的默认数据目录为 `%LOCALAPPDATA%/halcon1811-mcp`。程序保存在 `programs/`，演示任务保存在 `runs/`。

## 演示与测试

生成一张内置图片和阈值分割程序：

```powershell
.\.venv\Scripts\halcon1811-demo.exe generate
```

运行演示：

```powershell
.\.venv\Scripts\halcon1811-demo.exe run --exe "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe"
```

默认参数预期检测到 2 个大目标。可加 `--mode keyboard` 验证 F5 执行。
可选的参数操作界面用 `halcon1811-demo gui` 启动，需要 Python 自带的 Tkinter。

不依赖 HALCON 的单元测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

已验证：灰度图片、RGB 图片、零区域、F5 执行、错误图片失败记录，以及真实 MCP 协议下的保存、加载和执行。
验证范围和开发步骤见 [docs/testing.md](docs/testing.md)。

## 当前范围

- 支持 main 中的算子和已安装的外部过程；新增多个本地过程定义尚未实现。
- 程序通过文件加载显示在 HDevelop 中，尚不支持向已有编辑器定位插入点并粘贴。
- 每次打开或运行使用独立 HDevelop 窗口，完成后保留供检查。
- `stop()`、绘制 ROI 等交互算子可能等待 HDevelop 中的人工操作；状态会保持等待，不会误报完成。
- HALCON 执行异常返回错误码；语法加载错误仍需在 HDevelop 中查看。
- 生成逻辑由聊天 AI 负责，MCP 本身不调用模型 API。
