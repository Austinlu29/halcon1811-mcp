# halcon1811-mcp

[中文](README.md)

A local stdio MCP server for **HALCON 18.11 / HDevelop on Windows**.
Your chat assistant interprets a task, consults locally installed operator documentation and writes HDevelop code.
The MCP server saves the code as a `.hdev` program, opens it visibly in HDevelop, and can execute it on request.

## Requirements

- Windows desktop session.
- Python 3.10+.
- Installed HALCON 18.11 / HDevelop with a valid development license.
- An MCP client supporting local stdio servers.

HALCON binaries, licenses and official documentation are not included. No additional model API key is needed: your MCP client provides the AI.

## Install

```powershell
git clone https://github.com/Austinlu29/halcon1811-mcp.git
cd halcon1811-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
```

Alternatively install a wheel downloaded from GitHub Releases. This project is not currently on PyPI.

## Configure

Use the configuration in [examples/mcp.json](examples/mcp.json), replacing its executable and environment paths.
Start the server using the environment's Python executable with arguments `-m halcon1811_mcp`.
Set `HALCON_HDEVELOP_EXE` to your `hdevelop.exe` and optionally set `HALCON_MCP_DATA_DIR`.
Generated files default to `%LOCALAPPDATA%/halcon1811-mcp` on Windows.

For Codex:

```powershell
codex mcp add halcon1811-ui --env "HALCON_HDEVELOP_EXE=C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" -- C:/tools/halcon1811-mcp/.venv/Scripts/python.exe -m halcon1811_mcp
```

Reload the MCP connection as required by the client.

## Other agents and clients

See the [detailed setup guide in the main README](README.md#其他-agent-的详细使用方法) for step-by-step connection checks, prompts and troubleshooting.

| Client | Configuration |
|---|---|
| Claude Desktop on Windows | Merge [examples/mcp.json](examples/mcp.json) into `%APPDATA%/Claude/claude_desktop_config.json`; replace paths and restart |
| Claude Code | Register a local stdio server with the command below |
| Cursor Agent | Merge the same `mcpServers` entry into project or user `.cursor/mcp.json`; reload the client |
| VS Code / Copilot Agent | Use a portable project `.mcp.json`, or copy [examples/vscode-mcp.json](examples/vscode-mcp.json) to `.vscode/mcp.json` |
| Custom Python agent | Use [examples/python_agent_client.py](examples/python_agent_client.py) to submit generated main code |

Claude Code:

```powershell
claude mcp add --scope user --env "HALCON_HDEVELOP_EXE=C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" "HALCON_MCP_DATA_DIR=C:/HALCONPrograms" --transport stdio halcon1811-ui -- C:/tools/halcon1811-mcp/.venv/Scripts/python.exe -m halcon1811_mcp
claude mcp list
```

Verify the connection by asking the agent to call `halcon_environment`. Then ask it to read local operator references, generate code, call `halcon_save_program`, and return the `.hdev` path. Execute separately through `halcon_run_program` and query `halcon_execution_status`.

For a custom Python agent, first inspect the connection:

```powershell
.\.venv\Scripts\python.exe examples/python_agent_client.py --inspect-only --hdevelop "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe"
```

Then submit a UTF-8 source file produced by your model:

```powershell
.\.venv\Scripts\python.exe examples/python_agent_client.py --code-file C:/generated/part_detection.txt --name part_detection --hdevelop "C:/Program Files/MVTec/HALCON-18.11-Steady/bin/x64-win64/hdevelop.exe" --data-dir C:/HALCONPrograms
```

Add `--execute` to run and poll for completion, or `--save-only` to persist without opening a window. `--analysis-file` accepts your agent's generated analysis. The example is the MCP transport/tool bridge; your model or agent framework supplies natural-language understanding and code generation.

Run the server on the Windows host containing HALCON, rather than a remote container without an interactive HDevelop session. The clients' setup instructions follow their official documentation; their UIs have not each been tested here.

References: [Claude Desktop](https://modelcontextprotocol.io/docs/develop/connect-local-servers), [Claude Code](https://code.claude.com/docs/en/mcp), [Cursor](https://prod.cursor.com/help/customization/mcp), [VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

## Example request

> Use HALCON MCP to read C:/images/part.png, convert it to grayscale, apply a 3×3 mean filter and a 128–255 threshold, select connected regions with areas between 500 and 100000, save the generated program and open it in HDevelop.

The assistant calls `halcon_save_program` with plain main code. Saving retains `.hdev`, plain source and request/analysis files in a new version directory.
Execution is separate: call `halcon_run_program`, then `halcon_execution_status` with the returned identifiers.

## Tools

`halcon_environment`, `halcon_operator_help`, `halcon_save_program`, `halcon_open_program`,
`halcon_run_program`, `halcon_execution_status`, `halcon_list_programs`,
`generate_threshold_program`, and `run_threshold_demo`.

## Development

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tested with Python 3.13.6 and HALCON 18.11 on Windows. See [testing notes](docs/testing.md).
Other HALCON versions are unverified. Local procedure definitions and insertion into an existing editor are not implemented.
Interactive operators can remain waiting; successful key delivery is not treated as execution completion.
