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
