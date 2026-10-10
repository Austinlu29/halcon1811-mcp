# halcon1811-mcp

[English](README.en.md)

让聊天中的 AI 通过本地 MCP，为 **HALCON 18.11 / HDevelop** 生成代码、自动保存程序，并在软件窗口中打开。需要运行时，可以继续执行并查询状态。

```text
你输入操作需求 → 聊天 AI 分析并查算子文档 → 生成 HDevelop 代码
             → MCP 保存 .hdev → HDevelop 加载 → 按要求执行
```

AI 来自你正在使用的 MCP 客户端。本项目提供 HALCON 本机工具，不需要额外的 AI API 密钥。

本项目也可以接入 Claude Desktop、Claude Code、Cursor、VS Code 和自定义 Python Agent。
下方教程说明配置文件放置位置、如何检查连接、如何输入需求和如何处理报错。

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

## 其他 Agent 的详细使用方法

### 1. 先准备本机环境

先安装并登录你选择的 Agent 客户端，并确认当前账号与会话支持工具调用。
以下示例假设仓库安装在 `C:/tools/halcon1811-mcp`，HALCON 安装在 `C:/Program Files/MVTec/HALCON-18.11-Steady`。
这些都是示例路径：如果仓库或 HALCON 安装在其他位置，请替换为实际路径。JSON 中使用 `/` 可避免 Windows 反斜杠转义问题。

先确认包安装在准备启动 MCP 的那个 Python 环境中：

```powershell
Set-Location C:/tools/halcon1811-mcp
.\.venv\Scripts\python.exe -c "import halcon1811_mcp; print(halcon1811_mcp.__version__)"
Test-Path "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe"
```

预期输出包版本和 `True`。若导入失败，执行 `.\.venv\Scripts\python.exe -m pip install .`。
先手动打开 HDevelop，确认授权正常。MCP 进程应在这台 Windows 电脑的交互桌面上启动。

接入需要配置三个关键项：

| 配置 | 含义 | 示例 |
|---|---|---|
| `command` | 安装本项目的 Python 绝对路径 | `C:/tools/halcon1811-mcp/.venv/Scripts/python.exe` |
| `args` | 启动 MCP 的模块参数 | `["-m", "halcon1811_mcp"]` |
| `env.HALCON_HDEVELOP_EXE` | HALCON 程序路径 | `.../bin/x64-win64/hdevelop.exe` |

`HALCON_MCP_DATA_DIR` 可选，用来统一指定输出目录，例如 `C:/HALCONPrograms`。
本服务采用 stdio，由客户端启动子进程；不需要填写 HTTP 地址或端口。
在终端直接运行 `python -m halcon1811_mcp` 时，它会等待协议输入；终端持续等待通常是服务等待客户端连接。

### 2. Claude Desktop

1. 在 Windows 版 Claude Desktop 的设置中找到 **Developer / 开发者**，选择 **Edit Config / 编辑配置**。
2. 配置文件通常位于 `%APPDATA%/Claude/claude_desktop_config.json`。
3. 把下方服务加入文件。如果已有其他 MCP 服务，将 `halcon1811-ui` 合并到现有 `mcpServers` 对象中。
4. 替换 Python、HALCON 和输出目录路径，保存 JSON，完全退出并重新启动 Claude Desktop。
5. 在连接器或工具列表中确认 `halcon1811-ui` 已加载。

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

连接后先发送：

> 请调用 HALCON MCP 的 halcon_environment，告诉我是否找到 HDevelop、算子文档和程序保存目录。

成功后发送实际需求：

> 使用 HALCON 18.11 读取 C:/images/part.png，转灰度后使用 128–255 阈值分割，筛选面积 500–100000 的连通域，在原图上显示绿色轮廓。生成 main 代码，保存为“零件检测”，并在 HDevelop 打开；先不要执行。

需要运行时接着发送：

> 执行刚才保存的程序，并查询到完成或失败状态后告诉我结果。

客户端可能在工具调用前显示授权提示。界面入口以实际安装版本为准。
[官方本地 MCP 接入说明](https://modelcontextprotocol.io/docs/develop/connect-local-servers)。

### 3. Claude Code

在本机 Windows 的 PowerShell 中注册 stdio 服务：

```powershell
claude mcp add --scope user --env "HALCON_HDEVELOP_EXE=C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" "HALCON_MCP_DATA_DIR=C:/HALCONPrograms" --transport stdio halcon1811-ui -- C:/tools/halcon1811-mcp/.venv/Scripts/python.exe -m halcon1811_mcp
```

这里 `--scope user` 表示当前用户的跨项目配置；`--` 后面是 Python 服务启动命令。
`--env` 后的环境变量与服务名称之间放置 `--transport stdio`，避免 CLI 把名称当成环境变量。

检查注册情况：

```powershell
claude mcp list
claude mcp get halcon1811-ui
```

启动 Claude Code，在会话中输入 `/mcp` 检查连接状态，然后使用上一节相同的中文需求。
如果在 WSL、SSH 或云端运行 Claude Code，应先确认 MCP 实际启动的位置；本项目需要 Windows 上的 HDevelop 和交互桌面。
[Claude Code 官方 MCP 文档](https://code.claude.com/docs/en/mcp)。

### 4. Cursor Agent

1. 为当前项目配置时，在项目目录创建 `.cursor/mcp.json`。
2. 为所有项目配置时，使用用户目录下的 `.cursor/mcp.json`，Windows 通常是 `%USERPROFILE%/.cursor/mcp.json`。
3. 配置内容采用上面 Claude Desktop 的完整 JSON，顶层同样是 `mcpServers`。
4. 保存并重新启动 Cursor，在 MCP 设置或工具列表中确认服务可用。
5. 在本地 Agent 会话中选择能调用工具的模式，输入需求。

先输入连接检查：

> 使用 halcon1811-ui 的 halcon_environment 检查本机安装，请实际调用工具。

再输入程序生成需求：

> 调用 HALCON MCP 检查 read_image、threshold、connection、select_shape 的本机参数说明，生成亮区域检测代码，自动保存为“亮区域检测”，并在 HDevelop 中打开。

如果 Agent 只返回文字代码，可补充：

> 请调用 halcon_save_program，把刚才生成的 main 代码保存到本机，并返回 .hdev 的完整路径。

输出面板中的 MCP Logs 可以查看启动错误。
[Cursor 官方 MCP 配置文档](https://prod.cursor.com/help/customization/mcp)。

### 5. VS Code / Copilot Agent

VS Code 有两种配置格式，可选其一。

**便携格式：**在项目根目录创建 `.mcp.json`，使用上面 `mcpServers` 格式的 JSON。较新的 VS Code 文档推荐新配置采用这种便携位置。

**VS Code 原生格式：**在项目中创建 `.vscode/mcp.json`，使用下面的 `servers` 对象。可复制 [examples/vscode-mcp.json](examples/vscode-mcp.json)。

```json
{
  "servers": {
    "halcon1811-ui": {
      "type": "stdio",
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

配置后按以下步骤使用：

1. 打开命令面板，运行 `MCP: List Servers`，选择 `halcon1811-ui` 并启动服务。
2. 确认当前工作区和 MCP 服务的信任状态允许启动该本地程序。
3. 在 Chat 中选择可调用工具的 Agent 会话，启用 HALCON MCP 工具。
4. 先请求调用 `halcon_environment`，再输入代码生成与自动保存需求。
5. 报错时在服务管理中选择 `Show Output` 查看 MCP 日志。

如果使用远程工作区，应确认进程启动在装有 HALCON 的 Windows 主机，而不是没有 HDevelop 的远程容器。
[VS Code 官方 MCP 文档](https://code.visualstudio.com/docs/agent-customization/mcp-servers)。

### 6. 自定义 Python Agent

自己的 Agent 也可以用 MCP Python SDK 连接服务。仓库提供可运行的 [examples/python_agent_client.py](examples/python_agent_client.py)，使用已安装的 SDK 1.x，无需添加新的客户端依赖。

这个示例负责 **MCP 连接、代码保存、打开和执行状态查询**。它接收上游 Agent 已经生成的 HDevelop 文本文件；自然语言理解和代码生成仍由你接入的模型负责。

先只检查连接，列出工具并查询 HALCON 环境：

```powershell
.\.venv\Scripts\python.exe examples/python_agent_client.py --inspect-only --hdevelop "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" --data-dir C:/HALCONPrograms
```

预期能列出本项目的 9 个工具，并显示 `installed: true`、`operator_docs_available: true`。

准备代码：让你的模型根据需求输出 UTF-8 编码的纯 HDevelop main 代码，例如保存到 `C:/generated/part_detection.txt`。不要包含 Markdown 围栏或 `.hdev` XML。

保存并在 HDevelop 打开：

```powershell
.\.venv\Scripts\python.exe examples/python_agent_client.py --hdevelop "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" --data-dir C:/HALCONPrograms --code-file C:/generated/part_detection.txt --name "零件检测" --request "阈值分割并筛选目标区域"
```

增加 `--execute`，示例会执行程序，并每秒查询一次状态，最多等待 `--timeout` 指定的秒数（默认 60 秒）：

```powershell
.\.venv\Scripts\python.exe examples/python_agent_client.py --hdevelop "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" --data-dir C:/HALCONPrograms --code-file C:/generated/part_detection.txt --name "零件检测" --execute --timeout 60
```

使用 `--save-only` 可以只保存，既不打开窗口也不执行。`--save-only` 与 `--execute` 互斥。
也可以把 `--analysis-file` 指向模型输出的 UTF-8 分析文件，以便将分析过程一起保存。

自定义 Agent 中的调用逻辑可以写成：

```python
# session 是已初始化的 mcp.ClientSession。
# generated_code 是你的模型根据用户需求生成的纯 HDevelop 代码。
saved = await session.call_tool("halcon_save_program", {
    "name": "零件检测",
    "code": generated_code,
    "request": user_request,
    "analysis": generated_analysis,
    "open_window": True,
})
```

如果自己的框架支持通用 tool calling，可使用下面的工具分发流程，而不必为每个算子单独写 Python 接口：

```text
session.list_tools() 得到工具名称、描述、inputSchema
    → 转换为你的模型/Agent 框架要求的工具格式
    → 模型根据用户需求选择工具并生成参数
    → session.call_tool(name, arguments)
    → 将返回结果交给模型继续分析
    → 最终回复程序路径、执行状态和输出文件
```

不同模型服务的 tool schema 和调用结果格式可能不同；MCP 一侧的 `list_tools`、`call_tool` 保持一致。
模型 API 的登录或密钥由你的 Agent 配置。本项目不会读取或保存这些模型密钥。
[官方 MCP Python SDK 1.x](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x)。

### 7. 一次完整操作应该得到什么

推荐各 Agent 采用以下顺序：

| 阶段 | 工具 | 成功检查 |
|---|---|---|
| 环境检查 | `halcon_environment` | 找到 HDevelop 与本机算子参考 |
| 算子核对 | `halcon_operator_help` | 必要算子的 `found` 为 `true` |
| 生成与保存 | `halcon_save_program` | `saved: true`，取得 `program_id` 和 `script` |
| 打开查看 | 保存时 `open_window: true` 或 `halcon_open_program` | 返回窗口进程信息，在 HDevelop 检查代码 |
| 按要求执行 | `halcon_run_program` | 取得 `execution_id` |
| 查询结果 | `halcon_execution_status` | 最终 `completed` 或 `failed` |

保存工具的主要返回值示意：

```json
{
  "program_id": "本次生成的32位编号",
  "saved": true,
  "opened": true,
  "script": "C:/HALCONPrograms/programs/本次编号/零件检测.hdev",
  "analysis_file": "C:/HALCONPrograms/programs/本次编号/analysis.md"
}
```

`saved: true` 表示文件已写入磁盘；`opened: true` 表示 HDevelop 启动请求已成功。
HDevelop 窗口已经打开与算子执行完成是两个不同状态，完成情况由 `halcon_execution_status` 判断。

### 8. 常见问题与排查

| 现象 | 检查方法 |
|---|---|
| `No module named halcon1811_mcp` | 用配置中 `command` 指向的同一个 Python 执行 `-m pip install .` |
| `ENOENT` 或找不到可执行文件 | 检查 `command` 是否为存在的 Python 绝对路径 |
| 工具列表中没有 HALCON 服务 | 检查配置位置、JSON 顶层字段和服务启用状态，再重新加载客户端 |
| 没有找到 HDevelop | 检查 `HALCON_HDEVELOP_EXE`，对它执行 PowerShell `Test-Path` |
| 找不到算子文档 | 查看 `halcon_environment` 的 `operator_docs`，确认安装了 HALCON 本地文档 |
| 只有文字代码，没有自动保存 | 明确要求调用 `halcon_save_program`，并检查 Agent 是否启用了工具 |
| 已保存但没有打开窗口 | 检查返回值的 `open_error`、交互桌面和 HALCON 开发授权 |
| 执行一直 `running_or_waiting` | 查看 HDevelop 的加载错误、断点、`stop()` 或绘制 ROI 等等待操作 |
| 终端启动服务后一直等待 | stdio 服务在等待 MCP 客户端输入；用客户端连接或 Python 示例检查 |
| 多次调用后出现多个 HDevelop 窗口 | 本项目每次加载/执行使用独立窗口，任务结束后可手动关闭 |

本项目没有内置图片生成工具。类似“生成笔的照片并测量角度”的需求，需要 Agent 先用其图片工具生成照片，或使用已有照片，再将真实图片路径交给 HALCON 程序。

客户端操作步骤根据官方文档整理；本机已验证 Python SDK 的连接、保存和 HALCON 执行。Claude Desktop、Claude Code、Cursor、VS Code 的具体界面尚未逐一实测。

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
